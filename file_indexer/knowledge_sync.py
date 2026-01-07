# knowledge_sync.py
import os
import logging
import requests
import json
from config import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DifySessionManager:
    """管理Dify会话状态"""
    
    def __init__(self):
        # 从您的浏览器请求头中提取的有效cookie和CSRF令牌
        self.cookies = {
            "locale": "zh-Hans",
            "csrf_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Njc1MzI2NzQsInN1YiI6Ijg3NTQ3NjE1LTcwNTQtNGIyYy04MGNjLWFjYWUyM2VhMjBiOSJ9.eO_FC22S7UiiZzElP4bYWghuOe61FEBX9p4yNthlzak",
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiODc1NDc2MTUtNzA1NC00YjJjLTgwY2MtYWNhZTIzZWEyMGI5IiwiZXhwIjoxNzY3NTMyNjc0LCJpc3MiOiJTRUxGX0hPU1RFRCIsInN1YiI6IkNvbnNvbGUgQVBJIFBhc3Nwb3J0In0.jUO1h1nJzMA-CR-dmB8mMP_JwItgJI4i3PGjXv6k9W8",
            "refresh_token": "5ccbc373640e10bb249a3996ed5cd0e19830a319a71d1d14560bb42562aed7f6e77c133e4c62c0ef056f2e05790527c246f965d16fbfbd343a5db312d9e227d5"
        }
        
        self.csrf_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Njc1MzI2NzQsInN1YiI6Ijg3NTQ3NjE1LTcwNTQtNGIyYy04MGNjLWFjYWUyM2VhMjBiOSJ9.eO_FC22S7UiiZzElP4bYWghuOe61FEBX9p4yNthlzak"
        
        # 从配置中获取知识库ID
        self.knowledge_base_id = config.DIFY_KNOWLEDGE_BASE_ID
        
    def get_headers(self):
        """获取请求头"""
        return {
            "X-CSRF-Token": self.csrf_token,
            "X-App-Code": "create",
            "X-App-Passport": "",
            "Accept": "application/json",
            "Origin": "http://localhost",
            "Referer": f"http://localhost/datasets/{self.knowledge_base_id}/documents/create",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    def test_session(self):
        """测试会话是否有效"""
        url = f"{config.DIFY_BASE_URL}/console/api/datasets"
        
        try:
            response = requests.get(
                url,
                headers=self.get_headers(),
                cookies=self.cookies,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ Dify会话测试成功")
                return True
            else:
                logger.warning(f"Dify会话测试失败，状态码: {response.status_code}")
                logger.debug(f"响应: {response.text[:200]}")
                return False
        except Exception as e:
            logger.error(f"Dify会话测试异常: {str(e)}")
            return False

# 全局会话管理器
session_manager = DifySessionManager()

def sync_to_dify_knowledge(original_file_path, index_txt_path):
    """同步原文件和索引文件到Dify知识库"""
    
    # 使用控制台API端点
    url = f"{config.DIFY_BASE_URL}/console/api/files/upload?source=datasets"
    
    headers = session_manager.get_headers()
    cookies = session_manager.cookies
    
    # 首先测试会话
    if not session_manager.test_session():
        logger.error("❌ Dify会话无效，无法同步文件")
        raise Exception("Dify会话无效")
    
    # 准备要上传的文件
    files = []
    
    # 上传原文件
    if os.path.exists(original_file_path) and os.path.getsize(original_file_path) > 0:
        file_name = os.path.basename(original_file_path)
        # 根据文件类型设置正确的MIME类型
        if file_name.lower().endswith('.docx'):
            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif file_name.lower().endswith('.txt'):
            mime_type = "text/plain"
        else:
            mime_type = "application/octet-stream"
        
        files.append(("file", (file_name, open(original_file_path, 'rb'), mime_type)))
    
    # 上传索引文件
    if os.path.exists(index_txt_path) and os.path.getsize(index_txt_path) > 0:
        index_name = os.path.basename(index_txt_path)
        files.append(("file", (index_name, open(index_txt_path, 'rb'), "text/plain")))
    
    if not files:
        raise ValueError("没有可上传的有效文件")

    # 请求参数
    data = {
        "dataset_id": config.DIFY_KNOWLEDGE_BASE_ID,
        "process_rule": json.dumps({"mode": "automatic"})
    }

    try:
        logger.info(f"开始同步文件到知识库: {os.path.basename(original_file_path)}")
        
        # 发送POST请求
        response = requests.post(
            url,
            headers=headers,
            cookies=cookies,
            files=files,
            data=data,
            timeout=config.API_TIMEOUT
        )
        
        # 检查响应状态
        if response.status_code in [200, 201]:
            result = response.json()
            logger.info(f"✅ 文件同步成功: {os.path.basename(original_file_path)}")
            logger.info(f"📄 响应详情:")
            logger.info(f"   文件ID: {result.get('id', '未知')}")
            logger.info(f"   文件名: {result.get('name', '未知')}")
            logger.info(f"   文件大小: {result.get('size', '未知')}")
            logger.info(f"   MIME类型: {result.get('mime_type', '未知')}")
            logger.info(f"   创建时间: {result.get('created_at', '未知')}")
            return result
        else:
            error_msg = f"文件同步失败，状态码: {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f"\n错误详情: {error_detail}"
            except:
                error_msg += f"\n响应内容: {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
    except requests.exceptions.RequestException as e:
        error_msg = f"知识库同步失败: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                error_msg += f"\n错误详情: {error_detail}"
            except:
                error_msg += f"\n响应内容: {e.response.text}"
        logger.error(error_msg)
        raise Exception(error_msg)
    finally:
        # 确保关闭所有文件句柄
        for _, (_, file_handle, _) in files:
            file_handle.close()

def get_session_status():
    """获取会话状态"""
    return session_manager.test_session()