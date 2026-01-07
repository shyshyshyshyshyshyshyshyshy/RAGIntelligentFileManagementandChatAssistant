import sys
import os
# 强制解决ModuleNotFoundError，无需修改
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
import logging
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from llm_summarize import generate_file_index
from knowledge_sync_api import sync_to_dify_knowledge
from config import config

# 配置日志，清晰记录运行状态，无需修改
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 缓存文件最后处理时间，避免重复处理，无需修改
last_processed = {}

class FileChangeHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            self._handle_file_event(event.src_path)
    
    def on_modified(self, event):
        if not event.is_directory:
            self._handle_file_event(event.src_path)
    
    def _handle_file_event(self, file_path):
        # 过滤无效文件，避免重复处理，无需修改
        file_name = os.path.basename(file_path)
        if (file_name.startswith('~$') or
            file_name.endswith('_index.txt') or
            not file_path.lower().endswith(config.ALLOWED_EXTENSIONS)):
            return

        # 避免短时间重复处理，无需修改
        current_time = time.time()
        if (file_path in last_processed and 
            current_time - last_processed[file_path] < config.PROCESS_INTERVAL):
            logger.debug(f"文件{file_path}短时间内已处理，跳过")
            return
        last_processed[file_path] = current_time

        try:
            # 校验文件是否存在，避免报错，无需修改
            if not os.path.exists(file_path):
                logger.warning(f"文件不存在，跳过处理: {file_path}")
                return
            
            # 提取文件元数据，无需修改
            file_stat = os.stat(file_path)
            create_time = datetime.fromtimestamp(file_stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
            update_time = datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

            # 等待文件完全写入，无需修改
            time.sleep(1)
            if not os.path.exists(file_path):
                logger.warning(f"文件不存在，跳过处理: {file_path}")
                return
            initial_size = os.path.getsize(file_path)
            time.sleep(1)
            if os.path.getsize(file_path) != initial_size:
                logger.info(f"文件{file_name}仍在写入，等待完成后再处理")
                return

            # 核心流程：生成索引 + 全自动同步知识库，无需修改
            index_txt_path = generate_file_index(file_path, file_name, create_time, update_time)
            sync_to_dify_knowledge(file_path, index_txt_path)
            logger.info(f"✅ 索引生成+知识库同步完成，文件：{file_name}")

        except Exception as e:
            logger.error(f"文件{file_name}处理失败: {str(e)}", exc_info=True)

def start_file_monitor():
    try:
        # 验证配置，无需修改
        config.validate()
        event_handler = FileChangeHandler()
        observer = Observer()
        observer.schedule(event_handler, path=config.TARGET_DIR, recursive=False)
        observer.start()
        logger.info(f"✅ 目录监控已启动，监控路径: {config.TARGET_DIR}")
        logger.info(f"✅ 支持文件格式: {config.ALLOWED_EXTENSIONS}")

        # 保持监控运行，无需修改
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("✅ 监控已手动停止")
    except Exception as e:
        logger.error(f"❌ 监控启动失败: {str(e)}", exc_info=True)
    finally:
        if 'observer' in locals():
            observer.join()

if __name__ == "__main__":
    start_file_monitor()