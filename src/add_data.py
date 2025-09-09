import logging
from connection.mongoDB import MongoDBConnection

# Logging cơ bản
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("add_data")

def add_accounts_from_file(mongo_conn, file_path):
    try:
        with open(file_path, "r") as f:
            accounts = [{"username": line.strip()} for line in f if line.strip()]
        if not accounts:
            logger.info("File accounts trống.")
            return
        client = mongo_conn.get_client()
        db = client["reddit_db"]
        result = db.account.insert_many(accounts)
        logger.info("Đã thêm %d account.", len(result.inserted_ids))
    except Exception as e:
        logger.error("Lỗi khi thêm accounts: %s", str(e), exc_info=True)

def add_keywords_from_file(mongo_conn, file_path):
    try:
        with open(file_path, "r") as f:
            keywords = [{"keyword": line.strip()} for line in f if line.strip()]
        if not keywords:
            logger.info("File keywords trống.")
            return
        client = mongo_conn.get_client()
        db = client["reddit_db"]
        result = db.key_word.insert_many(keywords)
        logger.info("Đã thêm %d keywords.", len(result.inserted_ids))
    except Exception as e:
        logger.error("Lỗi khi thêm keywords: %s", str(e), exc_info=True)

if __name__ == "__main__":
    mongo_conn = MongoDBConnection()
    try:
        mongo_conn.connect()
        add_accounts_from_file(mongo_conn, "accounts.txt")   # file chỉ chứa username
        add_keywords_from_file(mongo_conn, "keywords.txt")  # file chỉ chứa từ khóa
    finally:
        mongo_conn.close()
