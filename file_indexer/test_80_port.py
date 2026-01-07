import requests
import os
from dotenv import load_dotenv

load_dotenv()

def check_api_key():
    """验证Dify API密钥"""
    
    DIFY_BASE_URL = os.getenv('DIFY_BASE_URL', 'http://localhost')
    DIFY_API_KEY = os.getenv('DIFY_API_KEY')
    DIFY_KNOWLEDGE_BASE_ID = os.getenv('DIFY_KNOWLEDGE_BASE_ID')
    
    print("=== API密钥验证 ===")
    print(f"知识库ID: {DIFY_KNOWLEDGE_BASE_ID}")
    print(f"API密钥: {DIFY_API_KEY}")
    
    if not DIFY_API_KEY:
        print("❌ 未找到DIFY_API_KEY环境变量")
        return
    
    # 测试API密钥有效性
    url = f"{DIFY_BASE_URL}/v1/datasets"
    headers = {"Authorization": f"Bearer {DIFY_API_KEY}"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"\nAPI测试结果:")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API密钥有效！")
            datasets = response.json()
            if 'data' in datasets:
                print("\n可用知识库:")
                for ds in datasets['data']:
                    print(f"  - {ds.get('name')} (ID: {ds.get('id')})")
                    if ds.get('id') == DIFY_KNOWLEDGE_BASE_ID:
                        print("    ✅ 这是您配置的知识库ID")
        elif response.status_code == 401:
            print("❌ API密钥无效或已过期")
            print("请在Dify后台重新生成API密钥")
        else:
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

if __name__ == "__main__":
    check_api_key()