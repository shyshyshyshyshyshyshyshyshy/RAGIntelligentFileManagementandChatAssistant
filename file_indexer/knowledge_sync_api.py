# knowledge_sync_api.py
import os
import logging
import requests
import json
import time
from config import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DifyAPIManager:
    """使用API密钥管理Dify连接"""
    
    def __init__(self):
        self.api_key = config.DIFY_KNOWLEDGE_API_KEY
        self.base_url = config.DIFY_BASE_URL.rstrip('/')  # 确保没有尾随斜杠
        self.knowledge_base_id = config.DIFY_KNOWLEDGE_BASE_ID
        
    def get_headers(self):
        """获取API密钥认证的请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def test_connection(self):
        """测试API连接是否有效"""
        url = f"{self.base_url}/v1/datasets"
        
        try:
            response = requests.get(
                url,
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ API连接测试成功")
                # 打印可用的知识库信息
                data = response.json()
                if 'data' in data:
                    for dataset in data['data']:
                        if dataset.get('id') == self.knowledge_base_id:
                            logger.info(f"✅ 找到配置的知识库: {dataset.get('name')}")
                return True
            else:
                logger.warning(f"API连接测试失败，状态码: {response.status_code}")
                logger.debug(f"响应: {response.text}")
                return False
        except Exception as e:
            logger.error(f"API连接测试异常: {str(e)}")
            return False
    
    def upload_file(self, file_path):
        """上传文件到Dify"""
        # 使用Dify的文件上传API
        url = f"{self.base_url}/v1/files/upload"
        
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            raise ValueError(f"文件不存在或为空: {file_path}")
        
        file_name = os.path.basename(file_path)
        
        try:
            # 读取文件内容
            with open(file_path, 'rb') as file:
                file_content = file.read()
            
            # 准备请求数据
            files = {
                'file': (file_name, file_content, 'application/octet-stream')
            }
            
            data = {
                'user': 'file_indexer_system',
                'knowledge_base_id': self.knowledge_base_id
            }
            
            # 使用API密钥认证
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            logger.info(f"开始上传文件: {file_name}")
            
            response = requests.post(
                url,
                headers=headers,
                files=files,
                data=data,
                timeout=config.API_TIMEOUT
            )
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"✅ 文件上传成功: {file_name}")
                logger.info(f"文件ID: {result.get('id')}")
                return result
            elif response.status_code == 200:
                result = response.json()
                logger.info(f"✅ 文件上传成功: {file_name}")
                logger.info(f"文件ID: {result.get('id')}")
                return result
            else:
                error_msg = f"文件上传失败，状态码: {response.status_code}"
                logger.error(f"{error_msg}\n响应: {response.text}")
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"上传过程异常: {str(e)}")
            raise
    
    def create_document(self, file_id, file_name):
        """从上传的文件创建文档"""
        # 根据Dify API文档调整端点
        url = f"{self.base_url}/v1/datasets/{self.knowledge_base_id}/documents"
        
        data = {
            "name": file_name,
            "file_id": file_id,
            "indexing_technique": "high_quality",
            "process_rule": {
                "mode": "automatic",
                "rules": {}
            }
        }
        
        try:
            response = requests.post(
                url,
                headers=self.get_headers(),
                json=data,
                timeout=config.API_TIMEOUT
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"✅ 文档创建成功: {file_name}")
                logger.info(f"文档ID: {result.get('id', '未知')}")
                return result
            else:
                error_msg = f"文档创建失败，状态码: {response.status_code}"
                logger.error(f"{error_msg}\n响应: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"文档创建异常: {str(e)}")
            return None
    
    def check_document_status(self, document_id):
        """检查文档处理状态"""
        url = f"{self.base_url}/v1/datasets/{self.knowledge_base_id}/documents/{document_id}"
        
        try:
            response = requests.get(
                url,
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status', 'unknown')
                logger.info(f"文档状态: {status}")
                return status
            else:
                logger.warning(f"获取文档状态失败: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"检查文档状态异常: {str(e)}")
            return None

# 全局API管理器
api_manager = DifyAPIManager()

def sync_to_dify_knowledge(original_file_path, index_txt_path):
    """使用API密钥同步文件到Dify知识库"""
    
    try:
        # 只上传原文件（索引文件作为本地参考，不上传到Dify）
        if not os.path.exists(original_file_path):
            raise ValueError(f"原文件不存在: {original_file_path}")
        
        logger.info("=== 开始知识库同步 ===")
        
        # 测试API连接
        if not api_manager.test_connection():
            raise Exception("API连接测试失败，无法继续")
        
        # 上传文件
        logger.info("步骤1: 上传文件")
        upload_result = api_manager.upload_file(original_file_path)
        
        if not upload_result or 'id' not in upload_result:
            raise Exception("文件上传失败，未返回文件ID")
        
        file_id = upload_result['id']
        file_name = os.path.basename(original_file_path)
        
        # 等待文件处理
        logger.info("步骤2: 等待文件处理完成...")
        time.sleep(5)
        
        # 创建文档
        logger.info("步骤3: 创建文档")
        doc_result = api_manager.create_document(file_id, file_name)
        
        if doc_result:
            document_id = doc_result.get('id')
            if document_id:
                # 检查文档状态
                logger.info("步骤4: 检查文档处理状态")
                time.sleep(3)
                status = api_manager.check_document_status(document_id)
                
                if status == 'completed':
                    logger.info(f"✅ 知识库同步完成: {file_name}")
                else:
                    logger.info(f"⚠️  文档处理中，当前状态: {status}")
            
            return {
                'success': True,
                'file_name': file_name,
                'file_id': file_id,
                'document_id': document_id,
                'status': status if 'status' in locals() else 'unknown'
            }
        else:
            logger.warning("文档创建可能失败，但文件已上传")
            return {
                'success': False,
                'file_name': file_name,
                'file_id': file_id,
                'error': '文档创建失败'
            }
            
    except Exception as e:
        logger.error(f"❌ 知识库同步失败: {str(e)}")
        raise

def test_api_upload():
    """测试API密钥上传功能"""
    # 创建测试文件
    test_content = "测试使用API密钥上传文件到Dify知识库。这是一个测试文件内容。"
    test_file = "test_api_upload.txt"
    
    try:
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        # 创建索引文件（本地使用，不上传到Dify）
        index_content = f"""文件名：{test_file}
文件路径：{os.path.abspath(test_file)}
创建时间：{time.strftime('%Y-%m-%d %H:%M:%S')}
更新时间：{time.strftime('%Y-%m-%d %H:%M:%S')}
内容总结：这是一个测试文件，用于验证Dify API密钥上传功能。
关键词：测试,API密钥,上传,Dify,知识库"""
        
        index_file = "test_api_upload_index.txt"
        with open(index_file, "w", encoding="utf-8") as f:
            f.write(index_content)
        
        print("=== 测试API密钥上传功能 ===")
        
        result = sync_to_dify_knowledge(test_file, index_file)
        
        if result.get('success'):
            print(f"✅ 上传测试成功!")
            print(f"文件: {result['file_name']}")
            print(f"文件ID: {result['file_id']}")
            if 'document_id' in result:
                print(f"文档ID: {result['document_id']}")
            print(f"状态: {result.get('status', '未知')}")
        else:
            print(f"⚠️  上传测试部分成功")
            print(f"详情: {result}")
            
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ 上传测试失败: {str(e)}")
        return False
    finally:
        # 清理测试文件
        for filename in [test_file, index_file]:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"清理文件: {filename}")

if __name__ == "__main__":
    test_api_upload()