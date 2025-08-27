# utils.py
import datetime
import json
import re
import time
import asyncio
import unicodedata
from io import BytesIO

from minio import S3Error
from pymongo import MongoClient
from text_unidecode import unidecode


def normalize_string(s: str) -> str:
    # Chuyển về unicode chuẩn (NFD tách dấu)
    s = unicodedata.normalize("NFD", s)
    # Loại bỏ dấu
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    # Giữ lại chữ, số, và thay khoảng trắng bằng "_"
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s)
    # Bỏ ký tự "_" dư thừa ở đầu/cuối
    s = s.strip("_")
    return s.lower()


def save_data(data, mongo_client, use_mongo=True):
    if not use_mongo:
        return

    try:
        db = mongo_client["reddit_db"]
        collection = db["reddit_data"]

        # Lấy và làm sạch title để dùng làm _id
        title = data.get("title", "")
        if not title:
            raise ValueError("❌ Không tìm được title")

        # Loại bỏ dấu và ký tự đặc biệt, thay thế khoảng trắng bằng dấu gạch dưới
        clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', unidecode(title.lower())).replace(" ", "_")

        if not clean_title:
            raise ValueError("❌ Title làm sạch không hợp lệ")

        # Tạo document cơ bản
        base_doc = {
            "title": data.get("title"),
            "content": data.get("content", ""),
            "author": data.get("author"),
            "score": data.get("score"),
            "url": data.get("url"),
            "created_utc": data.get("created_utc"),
            "saved_at": datetime.datetime.utcnow()
        }

        # Update các field cơ bản
        collection.update_one(
            {"_id": clean_title},
            {"$set": base_doc},
            upsert=True
        )

        # Thêm comment mới (so sánh theo body + author)
        for c in data.get("comments", []):
            collection.update_one(
                {"_id": clean_title, "comments": {"$not": {"$elemMatch": {"body": c["body"], "author": c["author"]}}}},
                {"$push": {"comments": c}}
            )

        print(f"✅ Đã lưu/ cập nhật post {clean_title} và comments vào MongoDB")

    except Exception as e:
        print(f"❌ Lỗi khi lưu MongoDB: {e}")

def merge_data(api_data, browser_data):
    """Merge dữ liệu từ hai phương pháp (đơn giản: ưu tiên API, bổ sung từ browser nếu title trùng)."""
    merged = api_data[:]  # Copy từ API
    for b_post in browser_data:
        if not any(m['title'] == b_post['title'] for m in merged):
            merged.append(b_post)
    return merged


def handle_rate_limit(func, *args, **kwargs):
    """Xử lý rate limit cho API."""
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
    """Xử lý lỗi cho Playwright."""
    try:
        await action()
    except Exception as e:
        print(f"Lỗi browser: {e}")
        await page.screenshot(path='error_screenshot.png')  # Debug