import praw
import time
from config import Config
from utils import handle_rate_limit


def crawl_with_api(queries=None, username=None, mongo_conn=None,name_db=None):
    # queries có thể là string hoặc list
    if isinstance(queries, str):
        queries = [queries]

    reddit = praw.Reddit(
        client_id=Config.REDDIT_CLIENT_ID,
        client_secret=Config.REDDIT_CLIENT_SECRET,
        user_agent=Config.REDDIT_USER_AGENT
    )

    name_db = f"crawled_posts_{name_db}"
    data = []
    # Kết nối tới collection lưu trữ ID bài đăng đã crawl
    crawled_collection = mongo_conn.get_client()["reddit_db"][name_db]

    def match_keywords(text):
        """Kiểm tra text có chứa ít nhất 1 keyword"""
        if not queries:
            return True
        text_lower = text.lower()
        return any(q.lower() in text_lower for q in queries)

    def is_post_crawled(submission_id):
        """Kiểm tra xem bài đăng đã được crawl chưa"""
        return crawled_collection.find_one({"submission_id": submission_id}) is not None

    def mark_post_as_crawled(submission_id):
        """Đánh dấu bài đăng là đã crawl"""
        crawled_collection.insert_one({"submission_id": submission_id, "crawled_at": time.time()})

    # if username and queries:  # Crawl theo tài khoản và từ khóa
    #     redditor = handle_rate_limit(reddit.redditor, username)
    #     submissions = handle_rate_limit(redditor.submissions.new, limit=Config.LIMIT)
    #     for submission in submissions:
    #         if not is_post_crawled(submission.id):
    #             if match_keywords(submission.title) or match_keywords(submission.selftext):
    #                 data.append(parse_submission(submission))
    #                 mark_post_as_crawled(submission.id)
    #                 time.sleep(1)

    if username:  # Crawl theo tài khoản
        redditor = handle_rate_limit(reddit.redditor, username)
        submissions = handle_rate_limit(redditor.submissions.new, limit=Config.LIMIT)
        for submission in submissions:
            if not is_post_crawled(submission.id):
                data.append(parse_submission(submission))
                mark_post_as_crawled(submission.id)
                time.sleep(1)

    elif queries:  # Crawl theo nhiều từ khóa (search all Reddit)
        subreddit = reddit.subreddit("all")
        for q in queries:
            submissions = handle_rate_limit(subreddit.search, q, sort='new', limit=Config.LIMIT)
            for submission in submissions:
                if not is_post_crawled(submission.id):
                    data.append(parse_submission(submission))
                    mark_post_as_crawled(submission.id)
                    time.sleep(1)

    else:  # Mặc định: crawl subreddit new
        subreddit = handle_rate_limit(reddit.subreddit, Config.SUBREDDIT_NAME)
        submissions = handle_rate_limit(subreddit.new, limit=Config.LIMIT)
        for submission in submissions:
            if not is_post_crawled(submission.id):
                data.append(parse_submission(submission))
                mark_post_as_crawled(submission.id)
                time.sleep(1)

    return data


def parse_submission(submission):
    """Parse bài viết + comment"""
    post_data = {
        'submission_id': submission.id,
        'user_id':submission.author.id,
        'title': submission.title,
        'content': submission.selftext,
        'author': str(submission.author),
        'submission_url' : "https://www.reddit.com" + submission.permalink,
        'url': submission.url,
        'created_utc': submission.created_utc,
        'score': submission.score,                  # like - dislike
        'like':submission.ups,
        'dislike':submission.downs,
        'num_comments': submission.num_comments,    # tổng comment trực tiếp và lồng nhau
        'comments': []
    }

    images = []
    if hasattr(submission,"preview"):
        try:
            for img in submission.preview.get("image",[]):
                images.append(img["source"]["url"])
        except Exception:
            pass

    video = submission.media if submission.media else None

    post_data["images"] = images
    post_data["video"] = video

    submission.comments.replace_more(limit=None)                # lấy comment ở mọi cấp độ
    for comment in submission.comments.list():                  # flatten tất cả comment thành 1 list
        post_data['comments'].append({
            'comment_id': comment.id,           # ID comment
            'user_id' : comment.author.id,
            'comment_url' :"https://www.reddit.com" + comment.permalink ,
            'body': comment.body,
            'author': str(comment.author),
            'score': comment.score,                 # Điểm (up - down)
            'like': comment.ups,                     # Số upvote
            'dislike': comment.downs,                 # Số downvote (thường = 0)
            'created_utc': comment.created_utc,     # Ngày đăng (timestamp UTC)
            'num_replies': len(comment.replies)    # Số comment con trực tiếp
        })

    return post_data