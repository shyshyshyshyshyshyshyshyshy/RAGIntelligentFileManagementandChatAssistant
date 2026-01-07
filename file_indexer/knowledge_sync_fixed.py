# knowledge_sync_fixed.py
import os
import logging
import requests
import json
import time
from config import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DifySessionManager:
    """管理Dify会话状态"""
    
    def __init__(self):
        # 修复CSRF token格式
        self.cookies = {
            "locale": "zh-Hans",
            "csrf_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Njc1MzI2NzQsInN1YiI6Ijg3NTQ3NjE1LTcwNTQtNGIyYy04MGNjLWFjYWUyM2VhMjBiOSJ9.eO_FC22S7UiiZzElP4bYWghuOe61FEBX9p4yNthlzak",  # 已修复
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiODc1NDc2MTUtNzA1NC00YjJjLTgwY2MtYWNhZTIzZWEyMGI5IiwiZXhwIjoxNzY3NTMyNjc0LCJpc3MiOiJTRUxGX0hPU1RFRCIsInN1YiI6IkNvbnNvbGUgQVBJIFBhc3Nwb3J0In0.jUO1h1nJzMA-CR-dmB8mMP_JwItgJI4i3PGjXv6k9W8",
            "refresh_token": "5ccbc373640e10bb249a3996ed5cd0e19830a319a71d1d14560bb42562aed7f6e77c133e4c62c0ef056f2e05790527c246f965d16fbfbd343a5db312d9e227d5"
        }
        
        self.csrf_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Njc1MzI2NzQsInN1YiI6Ijg3NTQ3NjE1LTcwNTQtNGIyYy04MGNjLWFjYWUyM2VhMjBiOSJ9.eO_FC22S7UiiZzElP4bYWghuOe61FEBX9p4yNthlzak"
        
    def get_headers(self):
        """获取请求头"""
        return {
            "X-CSRF-Token": self.csrf_token,
            "X-App-Code": "create",
            "X-App-Passport": "",
            "Accept": "application/json",
            "Origin": "http://localhost",
            "Referer": f"http://localhost/datasets/{config.DIFY_KNOWLEDGE_BASE_ID}/documents/create",
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
                return False
        except Exception as e:
            logger.error(f"Dify会话测试异常: {str(e)}")
            return False

session_manager = DifySessionManager()

def sync_to_dify_knowledge(original_file_path, index_txt_path):
    """同步索引文件到Dify知识库 - 只上传索引文件"""
    
    # 只上传索引文件，不传原文件
    if not os.path.exists(index_txt_path) or os.path.getsize(index_txt_path) == 0:
        raise ValueError("索引文件不存在或为空")
    
    file_name = os.path.basename(index_txt_path)
    
    # 使用简单的上传API
    url = f"{config.DIFY_BASE_URL}/console/api/files/upload?source=datasets"
    
    headers = session_manager.get_headers()
    cookies = session_manager.cookies
    
    try:
        logger.info(f"开始上传索引文件到知识库: {file_name}")
        
        # 准备上传数据 - 只上传索引文件
        files = {
            "file": (file_name, open(index_txt_path, 'rb'), "text/plain")
        }
        
        data = {
            "dataset_id": config.DIFY_KNOWLEDGE_BASE_ID,
            "process_rule": json.dumps({"mode": "automatic"})
        }
        
        # 发送请求
        response = requests.post(
            url,
            headers=headers,
            cookies=cookies,
            files=files,
            data=data,
            timeout=config.API_TIMEOUT
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            logger.info(f"✅ 索引文件上传成功: {file_name}")
            logger.info(f"文件ID: {result.get('id')}")
            
            # 等待处理完成
            logger.info("等待Dify处理索引文件...")
            time.sleep(5)
            
            return result
        else:
            error_msg = f"索引文件上传失败，状态码: {response.status_code}"
            logger.error(error_msg)
            raise Exception(error_msg)
            
    except Exception as e:
        logger.error(f"索引文件上传失败: {str(e)}")
        raise
    finally:
        # 确保关闭文件
        if 'files' in locals():
            files['file'][1].close()

def test_simple_upload():
    """简化测试"""
    test_content = "简化测试文件内容"
    test_file = "test_simple.txt"
    
    try:
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        print("=== 简化上传测试 ===")
        
        if not session_manager.test_session():
            print("❌ 会话测试失败")
            return False
        
        result = sync_to_dify_knowledge(test_file, "")  # 第二个参数留空
        print(f"✅ 上传成功: {result}")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    test_simple_upload()