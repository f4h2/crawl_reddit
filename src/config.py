# config.py
# Thông tin cho API PRAW (thay bằng thực tế từ https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID = 'zOG_llD-bo0JAMCMISDbsA'
REDDIT_CLIENT_SECRET = 'nFkY932BAwL1YMrPsZzliMjSPqreOw'
REDDIT_USER_AGENT = 'MyRedditCrawler/1.0 by u/loc2002'

# cần crawl nội dung private thì điền
REDDIT_USERNAME = ''
REDDIT_PASSWORD = ''

# Thông tin cho Playwright
BROWSER_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Cấu hình chung
SUBREDDIT_NAME = 'python'  # Thay bằng subreddit bạn muốn (ví dụ: 'python')
SUBREDDIT_URL = f'https://www.reddit.com/r/{SUBREDDIT_NAME}/'  # URL cho Playwright
LIMIT = 10  # Số lượng post tối đa để crawl/test

# Thêm cho search
DEFAULT_QUERY = None  # Từ khóa mặc định (None nếu không dùng)
DEFAULT_USERNAME = None  # Tài khoản mặc định (None nếu không dùng)

# redirect uri: http://localhost:8080

# mongodb
MONGO_DB_HOST = "mongodb://localhost:27017/"
