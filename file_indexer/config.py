import sys
import os
# 强制解决ModuleNotFoundError，无需修改
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# 加载.env配置，无需修改
load_dotenv()

class Config:
    # 读取.env中所有配置项，无需修改
    TARGET_DIR = os.getenv('TARGET_DIR')
    ALLOWED_EXTENSIONS = tuple(os.getenv('ALLOWED_EXTENSIONS', '.txt,.docx').split(','))
    PROCESS_INTERVAL = int(os.getenv('PROCESS_INTERVAL', 10))
    DIFY_BASE_URL = os.getenv('DIFY_BASE_URL')
    DIFY_KNOWLEDGE_BASE_ID = os.getenv('DIFY_KNOWLEDGE_BASE_ID')
    DIFY_KNOWLEDGE_API_KEY = os.getenv('DIFY_KNOWLEDGE_API_KEY')
    CONTENT_TRUNCATE_LENGTH = int(os.getenv('CONTENT_TRUNCATE_LENGTH', 2000))
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', 60))

    @classmethod
    def validate(cls):
        """验证配置是否有效，无需修改"""
        required = ['TARGET_DIR', 'DIFY_KNOWLEDGE_API_KEY', 'DIFY_BASE_URL', 'DIFY_KNOWLEDGE_BASE_ID']
        missing = [k for k in required if not getattr(cls, k)]
        if missing:
            raise ValueError(f"缺少必要配置项: {', '.join(missing)}")
        if not os.path.exists(cls.TARGET_DIR):
            raise NotADirectoryError(f"目标目录不存在: {cls.TARGET_DIR}")

# 实例化配置，供其他脚本调用，无需修改
config = Config()