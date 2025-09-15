import asyncio
import datetime
import logging
import time
import threading
from queue import Queue
from api_crawler import crawl_with_api
from browser_crawler import crawl_with_browser
from logger_config import setup_logging
from add_data import add_accounts_from_file, add_keywords_from_file
from utils import save_data, merge_data, get_accounts_and_keywords, push_to_kafka
from connection.mongoDB import MongoDBConnection
from config import Config

setup_logging()
logger = logging.getLogger("main")


def crawl_task(type_crawl, queries=None, username=None, mongo_conn=None, name_db=None, result_queue=None):
    try:
        data = []
        if type_crawl == 1:
            data = crawl_with_api(queries=queries, username=username, mongo_conn=mongo_conn, name_db=name_db)
        elif type_crawl == 2:
            data = asyncio.run(crawl_with_browser(query=queries, username=username))
        elif type_crawl == 3:
            api_data = crawl_with_api(queries=queries, username=username, mongo_conn=mongo_conn, name_db=name_db)
            browser_data = asyncio.run(crawl_with_browser(query=queries, username=username))
            data = merge_data(api_data, browser_data)
        else:
            logger.info(f"Phương thức không hợp lệ: {type_crawl}")
        if data:
            result_queue.put((data, name_db))
        logger.info(f"Đã crawl {len(data)} bài đăng cho username={username}, query={queries}, name_db={name_db}")
    except Exception as e:
        logger.error(f"Lỗi khi thu thập dữ liệu cho username={username}, query={queries}: {e}")


def fetch_by_accounts(mongo_conn, type_crawl, limit=10):
    page = 1
    while True:
        result_queue = Queue()
        threads = []
        accounts, _ = get_accounts_and_keywords(mongo_conn, page, limit)
        if not accounts:
            logger.info("Không còn tài khoản để crawl, thoát vòng lặp")
            break

        for username_document in accounts:
            username = username_document["username"]
            name_db = "username"
            thread = threading.Thread(
                target=crawl_task,
                args=(type_crawl, None, username, mongo_conn, name_db, result_queue)
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        while not result_queue.empty():
            data, name_db = result_queue.get()
            for post in data:
                post["filter"] = name_db
                save_data(post, mongo_conn, name_db)
            push_to_kafka(data)

        page += 1


def fetch_by_keywords(mongo_conn, type_crawl, limit=10):
    page = 1
    while True:
        result_queue = Queue()
        threads = []
        _, keywords = get_accounts_and_keywords(mongo_conn, page, limit)
        if not keywords:
            logger.info("Không còn từ khóa để crawl, thoát vòng lặp")
            break

        for query_document in keywords:
            query = query_document["keyword"]
            name_db = "keyword"
            thread = threading.Thread(
                target=crawl_task,
                args=(type_crawl, query, None, mongo_conn, name_db, result_queue)
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        while not result_queue.empty():
            data, name_db = result_queue.get()
            for post in data:
                post["filter"] = name_db
                save_data(post, mongo_conn, name_db)
            push_to_kafka(data)

        page += 1


def job_accounts():
    mongo_conn = MongoDBConnection()
    try:
        mongo_conn.connect()
        # Thêm accounts từ file trước khi crawl, chỉ thêm những account chưa có
        add_accounts_from_file(mongo_conn, "data_accounts_and_keywords/accounts.txt")
        type_crawl = Config.TYPE_CRAWL
        logger.info("Bắt đầu job crawl theo accounts")
        fetch_by_accounts(mongo_conn, type_crawl)
    except Exception as e:
        logger.error("Lỗi trong job crawl theo accounts: %s", str(e), exc_info=True)
    finally:
        mongo_conn.close()


def job_keywords():
    mongo_conn = MongoDBConnection()
    try:
        mongo_conn.connect()
        add_keywords_from_file(mongo_conn, "data_accounts_and_keywords/keywords.txt")
        type_crawl = Config.TYPE_CRAWL
        logger.info("Bắt đầu job crawl theo keywords")
        fetch_by_keywords(mongo_conn, type_crawl)
    except Exception as e:
        logger.error("Lỗi trong job crawl theo keywords: %s", str(e), exc_info=True)
    finally:
        mongo_conn.close()

#
# if __name__ == "__main__":
#     while True:
#         now = datetime.datetime.now()
#         if now.hour == 7 and now.minute == 0:
#             logger.info("Bắt đầu các job lúc 7h sáng...")
#             job_accounts()
#             job_keywords()
#             # Ngủ 61 giây để tránh chạy nhiều lần trong cùng phút
#             time.sleep(61)
#         else:
#             # Ngủ 30 giây để giảm tải CPU
#             time.sleep(30)

if __name__ == "__main__":
    logger.info("Bắt đầu các job...")
    job_accounts()
    job_keywords()