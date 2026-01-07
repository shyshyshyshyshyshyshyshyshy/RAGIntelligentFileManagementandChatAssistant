import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from knowledge_sync import test_dify_connection
from config import config

if __name__ == "__main__":
    print("测试Dify连接...")
    config.validate()
    test_dify_connection()