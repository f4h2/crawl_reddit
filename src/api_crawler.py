# api_crawler.py
import praw
import time
from config import Config
from utils import handle_rate_limit


# def crawl_with_api(query=None, username=None):
#     # Khởi tạo Reddit instance
#     reddit = praw.Reddit(
#         client_id=Config.REDDIT_CLIENT_ID,
#         client_secret=Config.REDDIT_CLIENT_SECRET,
#         user_agent=Config.REDDIT_USER_AGENT
#         # username=REDDIT_USERNAME,
#         # password=REDDIT_PASSWORD
#     )
#
#     data = []
#
#     if username:  # Crawl theo tài khoản
#         redditor = handle_rate_limit(reddit.redditor, username)
#         submissions = handle_rate_limit(redditor.submissions.new, limit=Config.LIMIT)
#     elif query:  # Crawl theo từ khóa (toàn Reddit, sort by new)
#         subreddit = reddit.subreddit("all")
#         submissions = handle_rate_limit(subreddit.search, query, sort='new', limit=Config.LIMIT)        # Nếu muốn giới hạn trong subreddit: subreddit = reddit.subreddit(SUBREDDIT_NAME); submissions = subreddit.search(query, sort='new', limit=LIMIT)
#     else:  # Mặc định: subreddit new
#         subreddit = handle_rate_limit(reddit.subreddit, Config.SUBREDDIT_NAME)
#         submissions = handle_rate_limit(subreddit.new, limit=Config.LIMIT)
#
#     for submission in submissions:
#         post_data = {
#             'title': submission.title,
#             'content': submission.selftext,
#             'author': str(submission.author),
#             'score': submission.score,
#             'url': submission.url,
#             'created_utc': submission.created_utc,
#             'comments': []
#         }
#
#         # Crawl bình luận
#         submission.comments.replace_more(limit=None)
#         for comment in submission.comments.list():
#             post_data['comments'].append({
#                 'body': comment.body,
#                 'author': str(comment.author),
#                 'score': comment.score
#             })
#
#         data.append(post_data)
#         time.sleep(1)  # Độ trễ
#
#     return data


def crawl_with_api(query=None, username=None):
    # Khởi tạo Reddit instance
    reddit = praw.Reddit(
        client_id=Config.REDDIT_CLIENT_ID,
        client_secret=Config.REDDIT_CLIENT_SECRET,
        user_agent=Config.REDDIT_USER_AGENT
        # username=REDDIT_USERNAME,
        # password=REDDIT_PASSWORD
    )

    data = []

    if username and query:  # Crawl theo tài khoản và từ khóa
        redditor = handle_rate_limit(reddit.redditor, username)
        submissions = handle_rate_limit(redditor.submissions.new, limit=Config.LIMIT)
        # Lọc bài đăng theo từ khóa
        for submission in submissions:
            if query.lower() in submission.title.lower() or query.lower() in submission.selftext.lower():
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

    elif username:  # Crawl theo tài khoản
        redditor = handle_rate_limit(reddit.redditor, username)
        submissions = handle_rate_limit(redditor.submissions.new, limit=Config.LIMIT)
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

    elif query:  # Crawl theo từ khóa (toàn Reddit, sort by new)
        subreddit = reddit.subreddit("all")
        submissions = handle_rate_limit(subreddit.search, query, sort='new', limit=Config.LIMIT)
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

    else:  # Mặc định: subreddit new
        subreddit = handle_rate_limit(reddit.subreddit, Config.SUBREDDIT_NAME)
        submissions = handle_rate_limit(subreddit.new, limit=Config.LIMIT)
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