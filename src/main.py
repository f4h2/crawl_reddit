# main.py
import argparse
import asyncio
from api_crawler import crawl_with_api
from browser_crawler import crawl_with_browser
from utils import save_data, merge_data, MongoDBConnection
from config import Config

# Parser cho command-line
parser = argparse.ArgumentParser(description='Reddit Crawler Project')
parser.add_argument('--method', type=str, default='api',
                    choices=['api', 'browser', 'both'],
                    help='Chọn phương pháp: api (PRAW), browser (Playwright), both (merge cả hai)')
parser.add_argument('--query', type=str, default=Config.DEFAULT_QUERY,
                    help='Từ khóa để search (ví dụ: "python tutorial")')
parser.add_argument('--username', type=str, default=Config.DEFAULT_USERNAME,
                    help='Tài khoản người dùng để crawl submissions (ví dụ: "spez")')
args = parser.parse_args()

# Chạy dựa trên method
if __name__ == "__main__":
    mongo_conn = MongoDBConnection()

    try:
        mongo_client = mongo_conn.connect()

        query = args.query
        username = args.username
        if query and username:
            print("Lỗi: Chỉ chọn một trong --query hoặc --username.")
            exit(1)

        if args.method == 'api':
            data = crawl_with_api(query=query, username=username)
        elif args.method == 'browser':
            data = asyncio.run(crawl_with_browser(query=query, username=username))
        elif args.method == 'both':
            api_data = crawl_with_api(query=query, username=username)
            browser_data = asyncio.run(crawl_with_browser(query=query, username=username))
            data = merge_data(api_data, browser_data)

        for post in data:
            save_data(post, mongo_conn)

    except Exception as e:
        print(f"Lỗi trong quá trình chạy: {e}")
    finally:
        mongo_conn.close()