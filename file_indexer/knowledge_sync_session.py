# knowledge_sync_session.py
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
        # 从您的请求头中提取的cookie和CSRF令牌
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
                return False
        except Exception as e:
            logger.error(f"Dify会话测试异常: {str(e)}")
            return False

session_manager = DifySessionManager()

def sync_to_dify_knowledge(original_file_path, index_txt_path):
    """使用会话认证同步文件到Dify知识库"""
    
    # 使用控制台API端点
    url = f"{config.DIFY_BASE_URL}/console/api/files/upload?source=datasets"
    
    # 获取会话管理器
    global session_manager
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

    # 请求参数 - 使用表单数据格式
    data = {
        "dataset_id": config.DIFY_KNOWLEDGE_BASE_ID,
        "process_rule": json.dumps({"mode": "automatic"})
    }

    try:
        logger.info(f"开始同步文件到知识库: {os.path.basename(original_file_path)}")
        
        # 发送POST请求 - 使用会话认证
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
            logger.debug(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
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

def test_session_upload():
    """测试会话上传功能"""
    # 创建测试文件
    test_content = "测试使用会话认证上传文件到Dify知识库"
    test_filename = "test_session_upload.txt"
    
    try:
        with open(test_filename, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        # 创建一个虚拟的索引文件
        index_content = """文件名：test_session_upload.txt
文件路径：/tmp/test_session_upload.txt
创建时间：2026-01-04 20:25:00
更新时间：2026-01-04 20:25:00
内容总结：这是一个测试文件，用于验证Dify知识库同步功能。
关键词：测试,会话,上传,Dify,知识库"""
        
        index_filename = "test_session_upload_index.txt"
        with open(index_filename, "w", encoding="utf-8") as f:
            f.write(index_content)
        
        print("=== 测试会话上传功能 ===")
        
        # 测试会话
        if not session_manager.test_session():
            print("❌ 会话测试失败")
            return False
        
        print("✅ 会话测试成功")
        
        # 测试上传
        result = sync_to_dify_knowledge(test_filename, index_filename)
        print(f"✅ 上传测试成功: {result}")
        return True
        
    except Exception as e:
        print(f"❌ 上传测试失败: {str(e)}")
        return False
    finally:
        # 清理测试文件
        for filename in [test_filename, index_filename]:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"清理文件: {filename}")

if __name__ == "__main__":
    test_session_upload()