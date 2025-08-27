import os
from dotenv import load_dotenv

load_dotenv("../.env")

class Config:
    # Thông tin cho API PRAW
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "zOG_llD-bo0JAMCMISDbsA")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "nFkY932BAwL1YMrPsZzliMjSPqreOw")
    REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "MyRedditCrawler/1.0 by u/loc2002")
    REDDIT_USERNAME = os.getenv("REDDIT_USERNAME", "")
    REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD", "")

    # Thông tin cho Playwright
    BROWSER_USER_AGENT = os.getenv("BROWSER_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    # Cấu hình chung
    SUBREDDIT_NAME = os.getenv("SUBREDDIT_NAME", "python")
    SUBREDDIT_URL = f"https://www.reddit.com/r/{SUBREDDIT_NAME}/"
    LIMIT = int(os.getenv("LIMIT", 10))

    # Thêm cho search
    DEFAULT_QUERY = os.getenv("DEFAULT_QUERY", None)
    DEFAULT_USERNAME = os.getenv("DEFAULT_USERNAME", None)

    # MongoDB
    MONGO_DB_HOST = os.getenv("MONGO_DB_HOST", "mongodb://localhost:27017/")