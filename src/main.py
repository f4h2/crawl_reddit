import argparse
import asyncio
import datetime
import logging
import time

from api_crawler import crawl_with_api
from browser_crawler import crawl_with_browser
from src.logger_config import setup_logging
from utils import save_data, merge_data, get_accounts_and_keywords, push_to_kafka
from  connection.mongoDB import MongoDBConnection
from config import Config
setup_logging()
logger = logging.getLogger("main")


def fetch_all(mongo_conn,type_crawl, limit=10):
    page = 1

    while True:
        data = []

        accounts, keywords = get_accounts_and_keywords(mongo_conn, page, limit)
        if not accounts and not keywords:  # Hết data
            break

        # lọc theo tài khoản và keyword
        if accounts and keywords:
            # Ghép cặp username và query theo thứ tự
            for username_document in accounts:
                username = username_document["username"]
                for query_document in keywords:
                    query = query_document["keyword"]
                    try:
                        name_db = "username_keyword"
                        if type_crawl == 1:
                            data = crawl_with_api(queries=query, username=username,mongo_conn=mongo_conn,name_db=name_db)
                            print(f"data {data}")
                        elif type_crawl == 2:
                            data = asyncio.run(crawl_with_browser(query=query, username=username))
                        elif type_crawl == 3:
                            api_data = crawl_with_api(queries=query, username=username)
                            browser_data = asyncio.run(crawl_with_browser(query=query, username=username))
                            data = merge_data(api_data, browser_data)
                        else:
                            logger.info(f"Phương thức không hợp lệ: {type_crawl}")
                            continue
                        for post in data:
                            post["filter"] = name_db
                            save_data(post, mongo_conn,name_db)
                            push_to_kafka(data, Config.TOPIC)

                    except Exception as e:
                        logger.error(f"Lỗi khi thu thập dữ liệu cho username={username}, query={query}: {e}")

        # lọc theo accounts
        if accounts:
            for username_document in accounts:
                username = username_document["username"]

                try:
                    name_db = "username"
                    if type_crawl == 1:
                        data = crawl_with_api(username=username,mongo_conn=mongo_conn,name_db=name_db)
                    elif type_crawl == 2:
                        data = asyncio.run(crawl_with_browser(username=username))
                    elif type_crawl == 3:
                        api_data = crawl_with_api(username=username)
                        browser_data = asyncio.run(crawl_with_browser(username=username))
                        data = merge_data(api_data, browser_data)
                    else:
                        logger.info(f"Phương thức không hợp lệ: {type_crawl}")
                        continue

                    for post in data:
                        post["filter"] = name_db
                        save_data(post, mongo_conn,name_db)
                        push_to_kafka(data, Config.TOPIC)

                except Exception as e:
                    logger.error(f"Lỗi khi thu thập dữ liệu cho username={username}: {e}")

        # lọc theo key word
        if keywords:
            for query_document in keywords:
                query = query_document["keyword"]
                try:
                    name_db = "keyword"
                    if type_crawl == 1:
                        data = crawl_with_api(queries=query, mongo_conn=mongo_conn, name_db=name_db)
                    elif type_crawl == 2:
                        data = asyncio.run(crawl_with_browser(query=query))
                    elif type_crawl == 3:
                        api_data = crawl_with_api(queries=query)
                        browser_data = asyncio.run(crawl_with_browser(query=query))
                        data = merge_data(api_data, browser_data)
                    else:
                        logger.info(f"Phương thức không hợp lệ: {type_crawl}")
                        continue

                    for post in data:
                        post["filter"] = name_db
                        save_data(post, mongo_conn,name_db)
                        push_to_kafka(data, Config.TOPIC)

                except Exception as e:
                    logger.error(f"Lỗi khi thu thập dữ liệu cho query={query}: {e}")

        page += 1


def job():
    mongo_conn = MongoDBConnection()
    try:
        mongo_conn.connect()
        type_crawl = Config.TYPE_CRAWL
        fetch_all(mongo_conn,type_crawl)
    except Exception as e:
        logger.error("Lỗi trong quá trình chạy job: %s", str(e), exc_info=True)
    finally:
        mongo_conn.close()


if __name__ == "__main__":
    # while True:
    #     now = datetime.datetime.now()
    #     if now.hour == 7 and now.minute == 0:
    #         logger.info("Bắt đầu job lúc 7h sáng...")
    #         job()
    #         # ngủ 61 giây để tránh chạy nhiều lần trong cùng phút
    #         time.sleep(61)
    #     else:
    #         # ngủ 30 giây để giảm tải CPU
    #         time.sleep(30)

    job()
