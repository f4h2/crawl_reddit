# utils.py
import datetime
import json
import re
import time
import asyncio
import unicodedata
from io import BytesIO
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from text_unidecode import unidecode
from config import Config

class MongoDBConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBConnection, cls).__new__(cls)
            cls._instance._client = None
        return cls._instance

    def connect(self):
        if self._client is None:
            try:
                self._client = MongoClient(Config.MONGO_DB_HOST)
                self._client.server_info()  # Kiểm tra kết nối
                print("Kết nối MongoDB thành công")
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                print(f"Lỗi khi kết nối MongoDB: {e}")
                raise
        return self._client

    def get_client(self):
        if self._client is None:
            self.connect()
        return self._client

    def close(self):
        if self._client:
            self._client.close()
            self._client = None
            print("Đã đóng kết nối MongoDB")

def normalize_string(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s)
    s = s.strip("_")
    return s.lower()

def save_data(data, mongo_conn, use_mongo=True):
    if not use_mongo:
        return

    try:
        client = mongo_conn.get_client()
        db = client["reddit_db"]
        collection = db["reddit_data"]

        title = data.get("title", "")
        if not title:
            raise ValueError("❌ Không tìm được title")

        clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', unidecode(title.lower())).replace(" ", "_")
        if not clean_title:
            raise ValueError("❌ Title làm sạch không hợp lệ")

        base_doc = {
            "title": data.get("title"),
            "content": data.get("content", ""),
            "author": data.get("author"),
            "score": data.get("score"),
            "url": data.get("url"),
            "created_utc": data.get("created_utc"),
            "saved_at": datetime.datetime.utcnow()
        }

        collection.update_one(
            {"_id": clean_title},
            {"$set": base_doc},
            upsert=True
        )

        for c in data.get("comments", []):
            collection.update_one(
                {"_id": clean_title, "comments": {"$not": {"$elemMatch": {"body": c["body"], "author": c["author"]}}}},
                {"$push": {"comments": c}}
            )

        print(f"✅ Đã lưu/ cập nhật post {clean_title} và comments vào MongoDB")

    except Exception as e:
        print(f"❌ Lỗi khi lưu MongoDB: {e}")

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
            print("Đạt giới hạn rate, chờ 60 giây...")
            time.sleep(60)
            return func(*args, **kwargs)
        else:
            raise e

async def handle_browser_error(page, action):
    try:
        await action()
    except Exception as e:
        print(f"Lỗi browser: {e}")
        await page.screenshot(path=f'error_screenshot_{int(time.time())}.png')
        raise