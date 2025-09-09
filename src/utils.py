import datetime
import logging
import re
import time
import unicodedata
from logger_config import setup_logging
from text_unidecode import unidecode

from src.connection.kafkaConnection import KafkaConnection

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


def push_to_kafka(data, topic, batch_size=10):

    try:

        kafka = KafkaConnection()
        producer = kafka.get_producer()


        for doc in data:
            # Loại bỏ _id vì Kafka message không cần
            doc_to_send = {k: v for k, v in doc.items() if k != "_id"}

            # Gửi vào Kafka
            producer.send(topic, value=doc_to_send)
            logger.info(f" Sent post '{doc.get('title', '')}' to Kafka topic={topic}")

        producer.flush()  # Đảm bảo tất cả message đã được gửi
        logger.info("Hoàn tất đẩy dữ liệu  sang Kafka")

    except Exception as e:
        logger.error(f"Lỗi khi đẩy  -> Kafka: {e}")