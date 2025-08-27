# api_crawler.py
import praw
import time
from config import (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET,
                    REDDIT_USER_AGENT, REDDIT_USERNAME, REDDIT_PASSWORD,
                    SUBREDDIT_NAME, LIMIT, DEFAULT_QUERY, DEFAULT_USERNAME)
from utils import handle_rate_limit


def crawl_with_api(query=None, username=None):
    # Khởi tạo Reddit instance
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
        # username=REDDIT_USERNAME,
        # password=REDDIT_PASSWORD
    )

    data = []

    if username:  # Crawl theo tài khoản
        redditor = handle_rate_limit(reddit.redditor, username)
        submissions = handle_rate_limit(redditor.submissions.new, limit=LIMIT)
    elif query:  # Crawl theo từ khóa (toàn Reddit, sort by new)
        subreddit = reddit.subreddit("all")
        submissions = handle_rate_limit(subreddit.search, query, sort='new', limit=LIMIT)        # Nếu muốn giới hạn trong subreddit: subreddit = reddit.subreddit(SUBREDDIT_NAME); submissions = subreddit.search(query, sort='new', limit=LIMIT)
    else:  # Mặc định: subreddit new
        subreddit = handle_rate_limit(reddit.subreddit, SUBREDDIT_NAME)
        submissions = handle_rate_limit(subreddit.new, limit=LIMIT)

    for submission in submissions:
        post_data = {
            'title': submission.title,
            'content': submission.selftext,
            'author': str(submission.author),
            'score': submission.score,
            'url': submission.url,
            'created_utc': submission.created_utc,
            'comments': []
        }

        # Crawl bình luận
        submission.comments.replace_more(limit=None)
        for comment in submission.comments.list():
            post_data['comments'].append({
                'body': comment.body,
                'author': str(comment.author),
                'score': comment.score
            })

        data.append(post_data)
        time.sleep(1)  # Độ trễ

    return data