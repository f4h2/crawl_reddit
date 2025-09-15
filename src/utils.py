import hashlib
from datetime import datetime
import logging
import re
import time
import unicodedata
from logger_config import setup_logging

from connection.kafkaConnection import KafkaConnection

setup_logging()
logger = logging.getLogger("utils")


def normalize_string(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s)
    s = s.strip("_")
    return s.lower()


def get_accounts_and_keywords(mongo_conn, page, limit: int = 10):
    try:
        client = mongo_conn.get_client()
        db = client["reddit_db"]
        skip = (page - 1) * limit
        # lấy dữ liệu từ collection account
        accounts_cursor = db.account.find().skip(skip).limit(limit)
        accounts = list(accounts_cursor)

        # lấy dữ liệu từ collection key_word
        keywords_cursor = db.key_word.find().skip(skip).limit(limit)
        keywords = list(keywords_cursor)

        return accounts, keywords

    except Exception as e:
        logger.error(
            "Error in get_accounts_and_keywords | page=%s, limit=%s | error=%s",
            page, limit, str(e),
            exc_info=True
        )
        return [], []

# def save_data(data, mongo_conn, use_mongo=True):
#     if not use_mongo:
#         return
#
#     try:
#         client = mongo_conn.get_client()
#         db = client["reddit_db"]
#         collection = db["reddit_data"]
#
#         title = data.get("title", "")
#         if not title:
#             raise ValueError("❌ Không tìm được title")
#
#         clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', unidecode(title.lower())).replace(" ", "_")
#         if not clean_title:
#             raise ValueError("❌ Title làm sạch không hợp lệ")
#
#         base_doc = {
#             "title": data.get("title"),
#             "content": data.get("content", ""),
#             "author": data.get("author"),
#             "score": data.get("score"),
#             "url": data.get("url"),
#             "created_utc": data.get("created_utc"),
#             "saved_at": datetime.datetime.utcnow()
#         }
#
#         collection.update_one(
#             {"_id": clean_title},
#             {"$set": base_doc},
#             upsert=True
#         )
#
#         for c in data.get("comments", []):
#             collection.update_one(
#                 {"_id": clean_title, "comments": {"$not": {"$elemMatch": {"body": c["body"], "author": c["author"]}}}},
#                 {"$push": {"comments": c}}
#             )
#
#         logger.info(f"✅ Đã lưu/ cập nhật post {clean_title} và comments vào MongoDB")
#
#     except Exception as e:
#         logger.error(f"❌ Lỗi khi lưu MongoDB: {e}")

def save_data(post, mongo_conn,name_db):
    try:
        name_db = f"posts_{name_db}"
        db = mongo_conn.get_client()["reddit_db"]
        collection = db[name_db]
        # Đảm bảo post là một dictionary
        if isinstance(post, dict):
            # Kiểm tra xem bài đăng đã tồn tại chưa dựa trên submission_id
            if not collection.find_one({"submission_id": post.get("submission_id")}):
                collection.insert_one(post)
                logger.info(f"Đã lưu bài đăng {post.get('submission_id')} vào MongoDB")
            else:
                logger.info(f"Bài đăng {post.get('submission_id')} đã tồn tại, bỏ qua")
        else:
            logger.error(f"Dữ liệu không phải dictionary: {post}")
    except Exception as e:
        logger.error(f"Lỗi khi lưu MongoDB: {e}")


def merge_data(api_data, browser_data):
    merged = api_data[:]
    for b_post in browser_data:
        if not any(m['title'] == b_post['title'] for m in merged):
            merged.append(b_post)
    return merged

def handle_rate_limit(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if 'ratelimit' in str(e).lower():
            logger.info("Đạt giới hạn rate, chờ 60 giây...")
            time.sleep(60)
            return func(*args, **kwargs)
        else:
            raise e

async def handle_browser_error(page, action):
    try:
        await action()
    except Exception as e:
        logger.info(f"Lỗi browser: {e}")
        await page.screenshot(path=f'error_screenshot_{int(time.time())}.png')
        raise


def push_to_kafka(data,batch_size=10):
    try:
        kafka = KafkaConnection()
        producer = kafka.get_producer()

        list_comment = []
        for doc in data:
            doc_to_send = {
                "source": "reddit",
                "docType": "forum",
                "type": "forum",
                "userId": doc.get("user_id"),
                "userName": doc.get("author"),
                "sourceId": "reddit",
                "sourceName": "reddit",
                "collectDate": datetime.utcnow().isoformat() + "Z",  # thời gian crawl
                "createDate": datetime.utcfromtimestamp(doc["created_utc"]).isoformat() + "Z",  # ngày đăng
                "postLink": doc.get("submission_url"),
                "domain": "reddit.com",
                "pictures": doc.get("images", []),
                "title": doc.get("title") or doc.get("content", ""),
                "description": "",
                "tags": "",
                "content": doc.get("content"),
                "logoLink": "",
                "provinces": [],
                "categories": [],
                "link": doc.get("url"),
                "numLikes": doc.get("like", 0),
                "numDislikes": doc.get("dislike", 0),
                "numComments": doc.get("num_comments", 0),
                "numShares": 0,
                "numViews": 0,
                "reactions": {},
                "docId": hashlib.md5(doc["submission_id"].encode()).hexdigest().upper(),
                "postId": "",   # rỗng vì đây là bài gốc
                "fromCrawler": "reddit_crawler"
            }

            # send vào Kafka
            producer.send("vnsocial_indexing_crawl_forum", value=doc_to_send)

            for c in doc.get("comments",[]):
                c["postId"]=hashlib.md5(doc["submission_id"].encode()).hexdigest().upper()
                list_comment.append(c)

        # flush phần còn lại
        if list_comment:
            for doc in list_comment:
                doc_to_send = {
                    "source": "reddit",
                    "docType": "forum",
                    "type": "forum_comment",
                    "userId": doc.get("user_id"),
                    "userName": doc.get("author"),
                    "sourceId": "reddit",
                    "sourceName": "reddit",
                    "collectDate": datetime.utcnow().isoformat() + "Z",  # thời gian crawl
                    "createDate": datetime.utcfromtimestamp(doc["created_utc"]).isoformat() + "Z",  # ngày đăng
                    "postLink": doc.get("comment_url"),
                    "domain": "reddit.com",
                    "pictures": doc.get("images", []),
                    "title": "",
                    "description": "",
                    "tags": "",
                    "content": doc.get("body"),
                    "logoLink": "",
                    "provinces": [],
                    "categories": [],
                    "link": doc.get("url",""),
                    "numLikes": doc.get("like", 0),
                    "numDislikes": doc.get("dislike", 0),
                    "numComments": doc.get("num_replies", 0),
                    "numShares": 0,
                    "numViews": 0,
                    "reactions": {},
                    "docId": "",
                    "postId": doc.get("postId",""),
                    "fromCrawler": "reddit_crawler"
                }
                producer.send("vnsocial_indexing_crawl_forum_comment", value=doc_to_send)
            list_comment.clear()

        producer.flush()

    except Exception as e:
        logger.error(f"Kafka push error: {e}")