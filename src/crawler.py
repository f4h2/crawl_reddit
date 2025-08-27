# crawler.py
import praw
import time

from config import (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET,
                    REDDIT_USER_AGENT, REDDIT_USERNAME, REDDIT_PASSWORD)
from utils import save_data, handle_rate_limit

# Khởi tạo Reddit instance
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
    username=REDDIT_USERNAME,  # Nếu cần crawl nội dung private
    password=REDDIT_PASSWORD
)


# Hàm crawl subreddit
def crawl_subreddit(subreddit_name, limit=10):
    data = []
    subreddit = handle_rate_limit(reddit.subreddit, subreddit_name)

    # Crawl bài đăng mới nhất
    for submission in handle_rate_limit(subreddit.new, limit=limit):
        post_data = {
            'title': submission.title,
            'content': submission.selftext,
            'author': str(submission.author),
            'score': submission.score,
            'url': submission.url,
            'created_utc': submission.created_utc,
            'comments': []
        }

        # Crawl bình luận (lấy tất cả, loại bỏ "More Comments")
        submission.comments.replace_more(limit=None)
        for comment in submission.comments.list():
            post_data['comments'].append({
                'body': comment.body,
                'author': str(comment.author),
                'score': comment.score
            })

        data.append(post_data)
        time.sleep(1)  # Độ trễ để tránh rate limit

    return data


# Chạy crawl
if __name__ == "__main__":
    subreddit_to_crawl = 'python'  # Thay bằng subreddit bạn muốn
    crawled_data = crawl_subreddit(subreddit_to_crawl, limit=5)  # Giới hạn 5 để test
    save_data(crawled_data)