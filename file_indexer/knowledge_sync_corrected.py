# knowledge_sync_corrected.py
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
        # 从您的请求头中提取的cookie和CSRF令牌
        self.cookies = {
            "locale": "zh-Hans",
            "csrf_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Njc1MzI2NzQsInN1YiI6Ijg3NTQ3NjE1LTcwNTQtNGIyYz04MGNjLWFjYWUyM2VhMjBiOSJ9.eO_FC22S7UiiZzElP4bYWghuOe61FEBX9p4yNthlzak",
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
    """同步原文件和索引文件到Dify知识库 - 修正版本"""
    
    # 第一步：上传文件
    upload_url = f"{config.DIFY_BASE_URL}/console/api/files/upload?source=datasets"
    
    headers = session_manager.get_headers()
    cookies = session_manager.cookies
    
    # 准备要上传的文件
    files = []
    
    # 上传原文件
    if os.path.exists(original_file_path) and os.path.getsize(original_file_path) > 0:
        file_name = os.path.basename(original_file_path)
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

    # 上传参数
    upload_data = {
        "dataset_id": config.DIFY_KNOWLEDGE_BASE_ID,
        "process_rule": json.dumps({"mode": "automatic"})
    }

    uploaded_file_ids = []
    
    try:
        for file_info in files:
            file_name = file_info[1][0]  # 获取文件名
            
            logger.info(f"开始上传文件: {file_name}")
            
            # 重新打开文件（因为之前可能已关闭）
            file_path = original_file_path if file_name == os.path.basename(original_file_path) else index_txt_path
            file_handle = open(file_path, 'rb')
            
            # 准备单个文件上传
            single_file = {"file": (file_name, file_handle, file_info[1][2])}
            
            # 发送上传请求
            response = requests.post(
                upload_url,
                headers=headers,
                cookies=cookies,
                files=single_file,
                data=upload_data,
                timeout=config.API_TIMEOUT
            )
            
            file_handle.close()
            
            if response.status_code in [200, 201]:
                result = response.json()
                file_id = result.get('id')
                
                if file_id:
                    uploaded_file_ids.append({
                        'id': file_id,
                        'name': file_name,
                        'result': result
                    })
                    logger.info(f"✅ 文件上传成功: {file_name} (ID: {file_id})")
                else:
                    logger.error(f"❌ 文件上传成功但未返回文件ID: {file_name}")
            else:
                error_msg = f"文件上传失败: {file_name}, 状态码: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f"\n错误详情: {error_detail}"
                except:
                    error_msg += f"\n响应内容: {response.text}"
                logger.error(error_msg)
        
        if not uploaded_file_ids:
            raise Exception("没有文件上传成功")
        
        # 第二步：为每个上传的文件创建文档记录
        logger.info(f"开始为 {len(uploaded_file_ids)} 个文件创建文档记录...")
        
        created_docs = []
        
        for file_info in uploaded_file_ids:
            file_id = file_info['id']
            file_name = file_info['name']
            
            # 创建文档的API端点
            create_doc_url = f"{config.DIFY_BASE_URL}/console/api/datasets/{config.DIFY_KNOWLEDGE_BASE_ID}/document/create"
            
            # 准备创建文档的数据
            doc_data = {
                "data_source": {
                    "type": "upload_file",
                    "info_list": [
                        {
                            "file_id": file_id,
                            "file_name": file_name
                        }
                    ]
                },
                "process_rule": {
                    "mode": "automatic"
                },
                "indexing_technique": "high_quality"
            }
            
            # 发送创建文档请求
            response = requests.post(
                create_doc_url,
                headers=headers,
                cookies=cookies,
                json=doc_data,
                timeout=config.API_TIMEOUT
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                doc_id = result.get('id')
                logger.info(f"✅ 文档创建成功: {file_name} (文档ID: {doc_id})")
                created_docs.append({
                    'file_name': file_name,
                    'file_id': file_id,
                    'doc_id': doc_id
                })
            else:
                error_msg = f"文档创建失败: {file_name}, 状态码: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f"\n错误详情: {error_detail}"
                except:
                    error_msg += f"\n响应内容: {response.text}"
                logger.warning(f"⚠️  {error_msg}")
        
        if created_docs:
            logger.info(f"✅ 知识库同步完成，成功创建 {len(created_docs)} 个文档")
            return created_docs
        else:
            raise Exception("文档创建全部失败")
            
    except Exception as e:
        error_msg = f"知识库同步失败: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)

def test_complete_upload():
    """测试完整的文件上传+文档创建流程"""
    # 创建测试文件
    test_content = "测试完整的文件上传和文档创建流程"
    test_file = "test_complete_upload.txt"
    
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(test_content)
    
    # 创建测试索引文件
    index_content = """文件名：test_complete_upload.txt
文件路径：/tmp/test_complete_upload.txt
创建时间：2026-01-04 20:30:00
更新时间：2026-01-04 20:30:00
内容总结：这是一个测试文件，用于验证完整的Dify知识库同步流程。
关键词：测试,完整流程,Dify,知识库"""
    
    index_file = "test_complete_upload_index.txt"
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(index_content)
    
    print("=== 测试完整的上传流程 ===")
    
    try:
        # 测试会话
        if not session_manager.test_session():
            print("❌ 会话测试失败")
            return False
        
        print("✅ 会话测试成功")
        
        # 执行完整上传
        result = sync_to_dify_knowledge(test_file, index_file)
        print(f"✅ 完整上传测试成功: {result}")
        
        # 等待几秒
        print("等待5秒...")
        time.sleep(5)
        
        # 检查知识库文档列表
        print("检查知识库文档列表...")
        docs_url = f"{config.DIFY_BASE_URL}/console/api/datasets/{config.DIFY_KNOWLEDGE_BASE_ID}/documents"
        headers = session_manager.get_headers()
        cookies = session_manager.cookies
        
        response = requests.get(docs_url, headers=headers, cookies=cookies, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and 'data' in data:
                all_docs = data['data']
                print(f"知识库文档总数: {len(all_docs)}")
                
                # 查找刚上传的文件
                found = False
                for doc in all_docs:
                    if doc.get('name') == test_file:
                        print(f"✅ 找到新创建的文档!")
                        print(f"文档ID: {doc.get('id')}")
                        print(f"状态: {doc.get('status', '未知')}")
                        found = True
                        break
                
                if not found:
                    print("⚠️  在知识库中未找到新创建的文档（可能在处理中）")
        
        return True
        
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
    test_complete_upload()