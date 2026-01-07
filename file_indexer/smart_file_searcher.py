# smart_file_searcher.py
import os
import requests
import json
import re
from datetime import datetime, timedelta
from difflib import SequenceMatcher

class SmartFileSearcher:
    """智能文件搜索器 - 结合Dify知识库和本地文件系统"""
    
    def __init__(self):
        self.knowledge_base_id = "1f0cc924-cba1-4113-83eb-dca99b0a31f9"
        self.api_key = "dataset-zqGccO9VowfmI7bPG6opOh5C"
        self.base_url = "http://localhost"
        self.file_opener_url = "http://localhost:5002/open-file"
        self.allowed_dir = "D:/code/python/ALLOWED_FILE_DIR"
    
    def search_knowledge_base(self, query):
        """在Dify知识库中搜索文件"""
        url = f"{self.base_url}/v1/datasets/{self.knowledge_base_id}/documents"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        params = {
            "keyword": query,
            "limit": 10
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                return response.json().get('data', [])
            return []
        except Exception as e:
            print(f"知识库搜索异常: {e}")
            return []
    
    def search_local_files(self, query):
        """在本地目录中搜索文件"""
        matched_files = []
        
        for filename in os.listdir(self.allowed_dir):
            if self.is_text_file(filename):
                file_path = os.path.join(self.allowed_dir, filename)
                similarity = self.calculate_similarity(query, filename)
                
                if similarity > 0.3:  # 相似度阈值
                    matched_files.append({
                        'name': filename,
                        'path': file_path,
                        'similarity': similarity,
                        'type': 'filename_match'
                    })
        
        return matched_files
    
    def is_text_file(self, filename):
        """检查是否为文本文件"""
        text_extensions = {'.txt', '.docx', '.doc', '.pdf', '.md'}
        return any(filename.lower().endswith(ext) for ext in text_extensions)
    
    def calculate_similarity(self, text1, text2):
        """计算两个文本的相似度"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def parse_index_content(self, content):
        """解析索引文件内容"""
        info = {}
        lines = content.split('\n')
        
        for line in lines:
            if '：' in line:
                key, value = line.split('：', 1)
                info[key.strip()] = value.strip()
        
        return info
    
    def extract_file_info_from_kb(self, kb_document):
        """从知识库文档中提取文件信息"""
        content = kb_document.get('content', '')
        info = self.parse_index_content(content)
        
        # 从索引内容中提取文件路径
        file_path = info.get('文件路径') or info.get('完整路径') or info.get('本地路径')
        
        if file_path and os.path.exists(file_path):
            return {
                'name': os.path.basename(file_path),
                'path': file_path,
                'info': info,
                'source': 'knowledge_base'
            }
        
        # 如果路径不存在，尝试从文件名推断
        file_name = info.get('文件名')
        if file_name:
            inferred_path = os.path.join(self.allowed_dir, file_name)
            if os.path.exists(inferred_path):
                return {
                    'name': file_name,
                    'path': inferred_path,
                    'info': info,
                    'source': 'inferred_path'
                }
        
        return None
    
    def open_file_via_api(self, file_name):
        """通过API打开文件"""
        try:
            response = requests.get(
                self.file_opener_url,
                params={'file_name': file_name},
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {'code': 500, 'message': f'API调用失败: {str(e)}'}
    
    def understand_time_reference(self, query):
        """理解时间相关的查询"""
        now = datetime.now()
        
        if '昨天' in query or 'yesterday' in query.lower():
            target_date = now - timedelta(days=1)
            return target_date.strftime("%Y-%m-%d")
        elif '今天' in query or 'today' in query.lower():
            return now.strftime("%Y-%m-%d")
        elif '明天' in query or 'tomorrow' in query.lower():
            target_date = now + timedelta(days=1)
            return target_date.strftime("%Y-%m-%d")
        elif '上周' in query or 'last week' in query.lower():
            target_date = now - timedelta(weeks=1)
            return target_date.strftime("%Y-%m-%d")
        elif '最近' in query or 'recent' in query.lower():
            return 'recent'
        
        return None
    
    def filter_by_time(self, files, time_reference):
        """根据时间过滤文件"""
        if not time_reference:
            return files
        
        filtered_files = []
        for file_info in files:
            file_path = file_info['path']
            stat = os.stat(file_path)
            modify_time = datetime.fromtimestamp(stat.st_mtime)
            create_time = datetime.fromtimestamp(stat.st_ctime)
            
            if time_reference == 'recent':
                # 最近3天内修改的文件
                if modify_time > datetime.now() - timedelta(days=3):
                    filtered_files.append(file_info)
            else:
                # 匹配具体日期
                file_date = modify_time.strftime("%Y-%m-%d")
                if file_date == time_reference:
                    filtered_files.append(file_info)
        
        return filtered_files
    
    def rank_files(self, files, query):
        """根据查询对文件进行排序"""
        for file_info in files:
            # 计算文件名相似度
            name_similarity = self.calculate_similarity(query, file_info['name'])
            
            # 计算路径相似度
            path_similarity = self.calculate_similarity(query, file_info['path'])
            
            # 如果有索引信息，计算内容相似度
            content_similarity = 0
            if 'info' in file_info:
                summary = file_info['info'].get('文件内容摘要', '')
                content_similarity = self.calculate_similarity(query, summary)
            
            # 综合评分
            file_info['score'] = (
                name_similarity * 0.4 +
                path_similarity * 0.3 +
                content_similarity * 0.3
            )
        
        return sorted(files, key=lambda x: x['score'], reverse=True)
    
    def search_and_open(self, user_query):
        """智能搜索并打开文件"""
        print(f"🔍 搜索查询: {user_query}")
        
        # 理解时间引用
        time_reference = self.understand_time_reference(user_query)
        if time_reference:
            print(f"⏰ 识别到时间引用: {time_reference}")
        
        # 在知识库中搜索
        kb_results = self.search_knowledge_base(user_query)
        kb_files = []
        
        for doc in kb_results:
            file_info = self.extract_file_info_from_kb(doc)
            if file_info:
                kb_files.append(file_info)
        
        print(f"📚 知识库找到 {len(kb_files)} 个文件")
        
        # 在本地搜索
        local_files = self.search_local_files(user_query)
        print(f"💻 本地搜索找到 {len(local_files)} 个文件")
        
        # 合并结果
        all_files = kb_files + local_files
        
        # 去重
        unique_files = []
        seen_paths = set()
        
        for file_info in all_files:
            if file_info['path'] not in seen_paths:
                seen_paths.add(file_info['path'])
                unique_files.append(file_info)
        
        # 时间过滤
        if time_reference:
            filtered_files = self.filter_by_time(unique_files, time_reference)
            print(f"⏱️  时间过滤后剩余 {len(filtered_files)} 个文件")
        else:
            filtered_files = unique_files
        
        if not filtered_files:
            return "❌ 没有找到匹配的文件"
        
        # 排序
        ranked_files = self.rank_files(filtered_files, user_query)
        
        # 选择最佳匹配
        best_match = ranked_files[0]
        print(f"🎯 最佳匹配: {best_match['name']} (得分: {best_match['score']:.2f})")
        
        # 打开文件
        result = self.open_file_via_api(best_match['name'])
        
        if result.get('code') == 200:
            return f"✅ {result['message']}\n📁 文件: {best_match['name']}\n💡 来源: {best_match.get('source', '未知')}"
        else:
            return f"❌ 打开文件失败: {result.get('message', '未知错误')}"

# 创建搜索器实例
searcher = SmartFileSearcher()

def main():
    """测试智能文件搜索"""
    test_queries = [
        "帮我打开昨天还在完成的文档",
        "帮我打开我的移动应用开发期末大作业报告",
        "打开最近的数学作业",
        "我要看上周的项目报告",
        "4.4小数与单位换算",  # 直接匹配文件名
        "数学四年级下册",     # 部分匹配
    ]
    
    print("=== 智能文件搜索器测试 ===\n")
    
    for query in test_queries:
        print(f"查询: {query}")
        result = searcher.search_and_open(query)
        print(f"结果: {result}\n")
        print("-" * 60)

if __name__ == "__main__":
    main()