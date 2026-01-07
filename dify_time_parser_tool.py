# dify_time_parser_tool.py
from datetime import datetime, timedelta
import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class TimeExpressionParser:
    """完整的时间表达式解析器（方案1）"""
    
    def __init__(self, base_date: datetime = None):
        self.base_date = base_date or datetime.now()
        self._init_time_patterns()
        logger.info(f"时间解析器初始化完成，基准日期: {self.base_date.strftime('%Y-%m-%d')}")
    
    def _init_time_patterns(self):
        """初始化时间匹配模式"""
        self.relative_patterns = {
            r'(今天|今日|当天|刚刚|现在)': 0,
            r'(昨天|昨日|前一天)': -1,
            r'(前天|前日)': -2,
            r'(大前天)': -3,
            r'(明天|明日|后一天)': 1,
            r'(后天|后日)': 2,
            r'(大后天)': 3,
            r'(上周|上星期)': 'last_week',
            r'(本周|这周)': 'current_week',
            r'(下周|下星期)': 'next_week',
            r'(上月|上个月)': 'last_month',
            r'(本月|这个月)': 'current_month',
            r'(下月|下个月)': 'next_month',
        }
        
        self.quantity_patterns = {
            r'(\d+)[ ]*天前': ('days', -1),
            r'(\d+)[ ]*天之后': ('days', 1),
            r'(\d+)[ ]*周前': ('weeks', -1),
            r'(\d+)[ ]*周之后': ('weeks', 1),
        }
    
    def parse_time_expression(self, text: str) -> Dict:
        """解析时间表达式"""
        logger.info(f"开始解析时间表达式: '{text}'")
        
        # 1. 尝试解析绝对日期
        absolute_result = self._parse_absolute_date(text)
        if absolute_result:
            return absolute_result
        
        # 2. 解析相对时间表达式
        relative_result = self._parse_relative_time(text)
        if relative_result:
            return relative_result
        
        # 3. 默认返回最近一周
        return self._get_default_range()
    
    def _parse_absolute_date(self, text: str) -> Optional[Dict]:
        """解析绝对日期"""
        patterns = [
            r'(\d{4})[-\/\.](\d{1,2})[-\/\.](\d{1,2})',
            r'(\d{4})年(\d{1,2})月(\d{1,2})日?',
            r'(\d{1,2})月(\d{1,2})日?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if len(match.groups()) == 3:
                        year, month, day = map(int, match.groups())
                    else:
                        month, day = map(int, match.groups())
                        year = self.base_date.year
                    
                    target_date = datetime(year, month, day)
                    
                    return {
                        'start_date': target_date.strftime('%Y-%m-%d'),
                        'end_date': target_date.strftime('%Y-%m-%d'),
                        'time_type': 'absolute',
                        'time_expression': f'{year}年{month}月{day}日',
                        'confidence': 0.95,
                        'date_range_type': 'single_day'
                    }
                except ValueError:
                    continue
        return None
    
    def _parse_relative_time(self, text: str) -> Optional[Dict]:
        """解析相对时间"""
        text_lower = text.lower()
        
        # 检查相对时间关键词
        for pattern, offset in self.relative_patterns.items():
            if re.search(pattern, text_lower):
                return self._calculate_relative_range(offset, pattern)
        
        # 检查数字+时间单位模式
        for pattern, (unit, direction) in self.quantity_patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                quantity = int(match.group(1))
                return self._calculate_quantity_range(quantity, unit, direction)
        
        return None
    
    def _calculate_relative_range(self, offset, pattern) -> Dict:
        """计算相对时间范围"""
        if offset == 0:  # 今天
            target_date = self.base_date
            expression = '今天'
        elif isinstance(offset, int):  # 具体天数偏移
            target_date = self.base_date + timedelta(days=offset)
            expressions = {
                -1: '昨天', -2: '前天', -3: '大前天',
                1: '明天', 2: '后天', 3: '大后天'
            }
            expression = expressions.get(offset, f'{abs(offset)}天前' if offset < 0 else f'{offset}天后')
        elif offset == 'last_week':  # 上周
            start_date = self.base_date - timedelta(days=self.base_date.weekday() + 7)
            end_date = start_date + timedelta(days=6)
            return {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'time_type': 'relative',
                'time_expression': '上周',
                'confidence': 0.9,
                'date_range_type': 'week'
            }
        elif offset == 'current_week':  # 本周
            start_date = self.base_date - timedelta(days=self.base_date.weekday())
            end_date = start_date + timedelta(days=6)
            return {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'time_type': 'relative',
                'time_expression': '本周',
                'confidence': 0.9,
                'date_range_type': 'week'
            }
        elif offset == 'last_month':  # 上月
            first_day = self.base_date.replace(day=1)
            last_month_last_day = first_day - timedelta(days=1)
            last_month_first_day = last_month_last_day.replace(day=1)
            return {
                'start_date': last_month_first_day.strftime('%Y-%m-%d'),
                'end_date': last_month_last_day.strftime('%Y-%m-%d'),
                'time_type': 'relative',
                'time_expression': '上月',
                'confidence': 0.8,
                'date_range_type': 'month'
            }
        else:
            return self._get_default_range()
        
        return {
            'start_date': target_date.strftime('%Y-%m-%d'),
            'end_date': target_date.strftime('%Y-%m-%d'),
            'time_type': 'relative',
            'time_expression': expression,
            'confidence': 0.9,
            'date_range_type': 'single_day'
        }
    
    def _calculate_quantity_range(self, quantity: int, unit: str, direction: int) -> Dict:
        """计算数量+时间单位范围"""
        if unit == 'days':
            delta = timedelta(days=quantity * direction)
        elif unit == 'weeks':
            delta = timedelta(weeks=quantity * direction)
        
        target_date = self.base_date + delta
        
        return {
            'start_date': target_date.strftime('%Y-%m-%d'),
            'end_date': target_date.strftime('%Y-%m-%d'),
            'time_type': 'relative',
            'time_expression': f'{quantity}{"天" if unit=="days" else "周"}{"前" if direction < 0 else "后"}',
            'confidence': 0.85,
            'date_range_type': 'single_day'
        }
    
    def _get_default_range(self) -> Dict:
        """获取默认时间范围（最近一周）"""
        end_date = self.base_date
        start_date = end_date - timedelta(days=7)
        
        return {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'time_type': 'default',
            'time_expression': '最近一周',
            'confidence': 0.5,
            'date_range_type': 'range'
        }

def time_parser_tool(inputs: dict) -> dict:
    """
    Dify自定义工具 - 时间表达式解析器
    输入: {
        "user_input": "用户输入文本", 
        "base_date": "2024-01-01(可选)"
    }
    输出: 时间范围信息
    """
    try:
        user_input = inputs.get("user_input", "")
        base_date_str = inputs.get("base_date", "")
        
        logger.info(f"🔧 时间解析工具被调用: user_input='{user_input}', base_date='{base_date_str}'")
        
        # 设置基准日期
        if base_date_str:
            try:
                base_date = datetime.strptime(base_date_str, "%Y-%m-%d")
                logger.info(f"使用指定的基准日期: {base_date.strftime('%Y-%m-%d')}")
            except ValueError as e:
                logger.warning(f"基准日期格式错误，使用当前日期: {e}")
                base_date = datetime.now()
        else:
            base_date = datetime.now()
            logger.info(f"使用默认基准日期(当前日期): {base_date.strftime('%Y-%m-%d')}")
        
        # 创建解析器并解析
        parser = TimeExpressionParser(base_date)
        time_result = parser.parse_time_expression(user_input)
        
        # 构建完整的返回结果
        result = {
            "success": True,
            "parsed_result": time_result,
            "debug_info": {
                "user_input": user_input,
                "base_date_used": base_date.strftime("%Y-%m-%d"),
                "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "tool_version": "1.0"
            }
        }
        
        logger.info(f"✅ 时间解析成功: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ 时间解析工具异常: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "parsed_result": {
                "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                "end_date": datetime.now().strftime("%Y-%m-%d"),
                "time_expression": "解析失败，使用默认范围",
                "time_type": "error",
                "confidence": 0.1
            }
        }

# 测试函数
def test_tool():
    """测试时间解析工具"""
    test_cases = [
        {"user_input": "帮我打开前天做的计算机网络的作业"},
        {"user_input": "昨天的文档在哪里"},
        {"user_input": "上周的会议记录"},
        {"user_input": "2026年1月5日的报告", "base_date": "2026-01-06"},
        {"user_input": "最近三天的文件"},
        {"user_input": "两个月前的项目资料"},
    ]
    
    print("=== 时间解析工具测试 ===")
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 测试用例 {i} ---")
        print(f"输入: {test_case}")
        result = time_parser_tool(test_case)
        print(f"输出: {result}")

if __name__ == "__main__":
    test_tool()