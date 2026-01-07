# test_upload_mode.py
import os
import sys
import time
import json
import requests
import hashlib
from datetime import datetime
from dotenv import load_dotenv
import logging

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('upload_test.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class Config:
    """配置类"""
    DIFY_BASE_URL = os.getenv('DIFY_BASE_URL', 'http://localhost').rstrip('/')
    DATASET_API_KEY = os.getenv('DIFY_API_KEY', 'dataset-zqGccO9VowfmI7bPG6opOh5C')
    
    # 知识库配置
    PARENT_CHILD_KB_ID = os.getenv('PARENT_CHILD_KB_ID', '1388750e-551b-4084-b699-17091a5b8364')
    TXT_KNOWLEDGE_BASE_ID = os.getenv('DIFY_KNOWLEDGE_BASE_ID', '1f0cc924-cba1-4113-83eb-dca99b0a31f9')
    
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', '60'))

config = Config()

class UploadTester:
    """上传测试器"""
    
    def __init__(self):
        self.base_url = config.DIFY_BASE_URL
        self.api_key = config.DATASET_API_KEY
    
    def test_upload_modes(self, file_path):
        """测试不同的上传模式"""
        file_name = os.path.basename(file_path)
        logger.info(f"🧪 开始测试文件上传模式: {file_name}")
        
        # 定义不同的上传策略
        strategies = [
            {
                "name": "完全空配置（最小配置）",
                "data": {"name": file_name},
                "description": "不指定任何处理规则，让Dify使用知识库默认设置"
            },
            {
                "name": "仅自动模式",
                "data": {
                    "name": file_name,
                    "process_rule": json.dumps({"mode": "automatic"})
                },
                "description": "只指定自动模式，不设置具体规则"
            },
            {
                "name": "自动模式+空规则",
                "data": {
                    "name": file_name,
                    "process_rule": json.dumps({"mode": "automatic", "rules": {}})
                },
                "description": "自动模式+空规则，让Dify自动选择"
            },
            {
                "name": "高质量索引",
                "data": {
                    "name": file_name,
                    "indexing_technique": "high_quality"
                },
                "description": "只指定高质量索引"
            },
            {
                "name": "完整配置（自动+高质量）",
                "data": {
                    "name": file_name,
                    "process_rule": json.dumps({"mode": "automatic", "rules": {}}),
                    "indexing_technique": "high_quality"
                },
                "description": "完整配置：自动模式+高质量索引"
            },
            {
                "name": "显式指定段落模式",
                "data": {
                    "name": file_name,
                    "process_rule": json.dumps({
                        "mode": "custom", 
                        "rules": {
                            "segmentation": {
                                "separator": "\\n\\n",
                                "max_tokens": 1000
                            }
                        }
                    })
                },
                "description": "显式指定段落分割模式"
            }
        ]
        
        results = []
        
        for i, strategy in enumerate(strategies):
            logger.info(f"\n🔧 测试策略 {i+1}/{len(strategies)}: {strategy['name']}")
            logger.info(f"📋 描述: {strategy['description']}")
            logger.info(f"⚙️ 配置: {json.dumps(strategy['data'], ensure_ascii=False)}")
            
            success, result = self._test_single_upload(file_path, config.PARENT_CHILD_KB_ID, strategy)
            results.append({
                "strategy": strategy['name'],
                "success": success,
                "result": result
            })
            
            if success:
                logger.info(f"✅ 策略成功: {strategy['name']}")
            else:
                logger.info(f"❌ 策略失败: {strategy['name']}")
            
            # 策略间短暂延迟
            time.sleep(2)
        
        # 输出测试总结
        self._print_test_summary(results, file_name)
        
        return results
    
    def _test_single_upload(self, file_path, knowledge_base_id, strategy):
        """测试单个上传策略"""
        try:
            file_name = os.path.basename(file_path)
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size > 100 * 1024 * 1024:
                logger.warning(f"📦 文件过大({file_size}字节)，跳过测试")
                return False, "文件过大"
            
            # 读取文件内容
            with open(file_path, 'rb') as file:
                file_content = file.read()
            
            # 使用BytesIO
            from io import BytesIO
            file_stream = BytesIO(file_content)
            
            # 获取MIME类型
            file_ext = os.path.splitext(file_name)[1].lower()
            mime_type = self._get_mime_type(file_ext)
            
            url = f"{config.DIFY_BASE_URL}/v1/datasets/{knowledge_base_id}/document/create-by-file"
            
            files = {'file': (file_name, file_stream, mime_type)}
            data = strategy['data']
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "UploadTester/1.0"
            }
            
            logger.debug(f"🌐 请求URL: {url}")
            logger.debug(f"📤 请求数据: {data}")
            
            response = requests.post(
                url, 
                headers=headers, 
                files=files, 
                data=data, 
                timeout=config.API_TIMEOUT
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"✅ 上传成功 - 文档ID: {result.get('id', '未知')}")
                
                # 尝试获取文档详情
                doc_info = self._get_document_info(knowledge_base_id, result.get('id'))
                
                return True, {
                    "document_id": result.get('id'),
                    "response": result,
                    "document_info": doc_info
                }
            else:
                error_msg = f"❌ 上传失败: {response.status_code} - {response.text}"
                logger.error(error_msg)
                
                # 分析错误类型
                error_analysis = self._analyze_upload_error(response)
                
                return False, {
                    "error_code": response.status_code,
                    "error_message": response.text,
                    "analysis": error_analysis
                }
                
        except requests.exceptions.Timeout:
            error_msg = "⏰ 请求超时"
            logger.error(error_msg)
            return False, {"error": "请求超时"}
        except requests.exceptions.ConnectionError:
            error_msg = "🌐 连接错误"
            logger.error(error_msg)
            return False, {"error": "连接错误"}
        except Exception as e:
            error_msg = f"💥 上传异常: {str(e)}"
            logger.error(error_msg)
            return False, {"error": str(e)}
    
    def _get_mime_type(self, file_ext):
        """获取MIME类型"""
        mime_types = {
            '.txt': 'text/plain',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.pdf': 'application/pdf',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.csv': 'text/csv',
            '.md': 'text/markdown'
        }
        return mime_types.get(file_ext, 'application/octet-stream')
    
    def _analyze_upload_error(self, response):
        """分析上传错误"""
        error_text = response.text.lower()
        analysis = []
        
        if "doc_form" in error_text:
            analysis.append("📋 文档格式错误：上传配置与知识库的分段模式不匹配")
            analysis.append("💡 可能原因：知识库设置为段落模式，但上传配置尝试使用全文模式，或反之")
        
        if "indexing_technique" in error_text:
            analysis.append("⚙️ 索引技术错误")
            analysis.append("💡 可能原因：父子模式知识库必须使用高质量索引")
        
        if "not found" in error_text:
            analysis.append("🔍 知识库不存在或API密钥无权限")
        
        if "unauthorized" in error_text:
            analysis.append("🔐 认证失败：请检查API密钥")
        
        if "segmentation" in error_text:
            analysis.append("📊 分段规则错误")
            analysis.append("💡 可能原因：分段参数与知识库设置冲突")
        
        if not analysis:
            analysis.append("🔧 未知错误类型，请检查Dify API文档")
        
        return analysis
    
    def _get_document_info(self, knowledge_base_id, document_id):
        """获取文档详细信息"""
        if not document_id:
            return None
        
        try:
            url = f"{config.DIFY_BASE_URL}/v1/datasets/{knowledge_base_id}/documents/{document_id}"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"获取文档信息失败: {response.status_code}")
                return None
        except Exception as e:
            logger.warning(f"获取文档信息异常: {str(e)}")
            return None
    
    def _print_test_summary(self, results, file_name):
        """打印测试总结"""
        logger.info("\n" + "="*80)
        logger.info("📊 上传测试总结")
        logger.info("="*80)
        
        successful_strategies = [r for r in results if r['success']]
        failed_strategies = [r for r in results if not r['success']]
        
        logger.info(f"📁 测试文件: {file_name}")
        logger.info(f"✅ 成功策略: {len(successful_strategies)}/{len(results)}")
        logger.info(f"❌ 失败策略: {len(failed_strategies)}/{len(results)}")
        
        if successful_strategies:
            logger.info("\n🎯 成功的上传策略:")
            for result in successful_strategies:
                logger.info(f"  ✓ {result['strategy']}")
                if 'document_id' in result['result']:
                    logger.info(f"    文档ID: {result['result']['document_id']}")
        
        if failed_strategies:
            logger.info("\n⚠️ 失败的上传策略及错误分析:")
            for result in failed_strategies:
                logger.info(f"  ✗ {result['strategy']}")
                if 'analysis' in result['result']:
                    for analysis_line in result['result']['analysis']:
                        logger.info(f"    {analysis_line}")
        
        # 给出建议
        logger.info("\n💡 建议:")
        if successful_strategies:
            best_strategy = successful_strategies[0]
            logger.info(f"推荐使用策略: '{best_strategy['strategy']}'")
            logger.info("在file_monitor_final.py中使用此策略的配置")
        else:
            logger.info("❌ 所有策略都失败，需要检查知识库设置")
            logger.info("💡 建议检查:")
            logger.info("  1. 知识库ID是否正确")
            logger.info("  2. API密钥是否有权限")
            logger.info("  3. Dify服务是否正常运行")
            logger.info("  4. 知识库的分段模式设置")
        
        logger.info("="*80)
    
    def get_knowledge_base_info(self, knowledge_base_id):
        """获取知识库信息"""
        try:
            url = f"{config.DIFY_BASE_URL}/v1/datasets/{knowledge_base_id}"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                kb_info = response.json()
                logger.info("📋 知识库信息:")
                logger.info(f"  名称: {kb_info.get('name', '未知')}")
                logger.info(f"  描述: {kb_info.get('description', '无描述')}")
                logger.info(f"  文档数量: {kb_info.get('document_count', 0)}")
                logger.info(f"  索引技术: {kb_info.get('indexing_technique', '未知')}")
                logger.info(f"  创建时间: {kb_info.get('created_at', '未知')}")
                return kb_info
            else:
                logger.error(f"获取知识库信息失败: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"获取知识库信息异常: {str(e)}")
            return None

def main():
    """主函数"""
    print("🧪 Dify知识库上传模式测试工具")
    print("="*50)
    
    # 检查必要配置
    if not all([config.DIFY_BASE_URL, config.DATASET_API_KEY, config.PARENT_CHILD_KB_ID]):
        print("❌ 环境变量配置不完整")
        print("请检查以下环境变量:")
        print(f"  DIFY_BASE_URL: {config.DIFY_BASE_URL}")
        print(f"  DIFY_API_KEY: {config.DATASET_API_KEY}")
        print(f"  PARENT_CHILD_KB_ID: {config.PARENT_CHILD_KB_ID}")
        return
    
    tester = UploadTester()
    
    # 显示知识库信息
    print("\n🔍 检查知识库信息...")
    kb_info = tester.get_knowledge_base_info(config.PARENT_CHILD_KB_ID)
    
    if not kb_info:
        print("❌ 无法获取知识库信息，请检查配置")
        return
    
    # 获取测试文件路径
    test_file = input("\n📁 请输入要测试的文件路径（或直接回车使用默认测试文件）: ").strip()
    
    if not test_file:
        # 使用当前目录下的测试文件
        default_files = ['test.docx', 'test.pdf', 'test.txt', '1.docx']
        for file in default_files:
            if os.path.exists(file):
                test_file = file
                break
        
        if not test_file:
            print("❌ 未找到默认测试文件，请手动指定文件路径")
            return
    
    if not os.path.exists(test_file):
        print(f"❌ 文件不存在: {test_file}")
        return
    
    print(f"📂 使用测试文件: {test_file}")
    print(f"📊 文件大小: {os.path.getsize(test_file)} 字节")
    
    # 开始测试
    print("\n🚀 开始上传测试...")
    results = tester.test_upload_modes(test_file)
    
    # 保存测试结果到文件
    result_file = f"upload_test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_time": datetime.now().isoformat(),
            "test_file": test_file,
            "knowledge_base_id": config.PARENT_CHILD_KB_ID,
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 测试结果已保存到: {result_file}")
    print("🎯 测试完成！")

if __name__ == "__main__":
    main()