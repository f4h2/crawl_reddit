import unittest
from unittest.mock import MagicMock, patch
from api_crawler import crawl_with_api
from config import Config

class TestApiCrawler(unittest.TestCase):
    def setUp(self):
        # Mock the Config attributes
        self.patcher_config = patch('api_crawler.Config', autospec=True)
        self.mock_config = self.patcher_config.start()
        self.mock_config.REDDIT_CLIENT_ID = "test_client_id"
        self.mock_config.REDDIT_CLIENT_SECRET = "test_client_secret"
        self.mock_config.REDDIT_USER_AGENT = "test_user_agent"
        self.mock_config.SUBREDDIT_NAME = "testsubreddit"
        self.mock_config.LIMIT = 2

        # Mock the PRAW Reddit instance
        self.patcher_reddit = patch('api_crawler.praw.Reddit', autospec=True)
        self.mock_reddit = self.patcher_reddit.start()

        # Mock handle_rate_limit
        self.patcher_handle_rate_limit = patch('api_crawler.handle_rate_limit', side_effect=lambda func, *args, **kwargs: func(*args, **kwargs))
        self.mock_handle_rate_limit = self.patcher_handle_rate_limit.start()

    def tearDown(self):
        self.patcher_config.stop()
        self.patcher_reddit.stop()
        self.patcher_handle_rate_limit.stop()

    def test_crawl_with_username(self):
        # Setup mock Redditor and submissions
        mock_redditor = MagicMock()
        mock_submission1 = MagicMock()
        mock_submission1.title = "Test Post 1"
        mock_submission1.selftext = "Content 1"
        mock_submission1.author = MagicMock(__str__=lambda x: "user1")
        mock_submission1.score = 10
        mock_submission1.url = "http://test1.com"
        mock_submission1.created_utc = 1234567890
        mock_submission1.comments = MagicMock()
        mock_submission1.comments.replace_more = MagicMock()
        mock_submission1.comments.list.return_value = [
            MagicMock(body="Comment 1", author=MagicMock(__str__=lambda x: "commenter1"), score=5)
        ]

        mock_submission2 = MagicMock()
        mock_submission2.title = "Test Post 2"
        mock_submission2.selftext = "Content 2"
        mock_submission2.author = MagicMock(__str__=lambda x: "user1")
        mock_submission2.score = 20
        mock_submission2.url = "http://test2.com"
        mock_submission2.created_utc = 1234567891
        mock_submission2.comments = MagicMock()
        mock_submission2.comments.replace_more = MagicMock()
        mock_submission2.comments.list.return_value = []

        mock_redditor.submissions.new.return_value = [mock_submission1, mock_submission2]
        self.mock_reddit.return_value.redditor.return_value = mock_redditor

        # Call the function
        result = crawl_with_api(username="testuser")

        # Expected output
        expected = [
            {
                'title': "Test Post 1",
                'content': "Content 1",
                'author': "user1",
                'score': 10,
                'url': "http://test1.com",
                'created_utc': 1234567890,
                'comments': [{'body': "Comment 1", 'author': "commenter1", 'score': 5}]
            },
            {
                'title': "Test Post 2",
                'content': "Content 2",
                'author': "user1",
                'score': 20,
                'url': "http://test2.com",
                'created_utc': 1234567891,
                'comments': []
            }
        ]

        self.assertEqual(result, expected)
        self.mock_reddit.return_value.redditor.assert_called_with("testuser")
        mock_redditor.submissions.new.assert_called_with(limit=self.mock_config.LIMIT)

    def test_crawl_with_query(self):
        # Setup mock subreddit and submissions
        mock_subreddit = MagicMock()
        mock_submission = MagicMock()
        mock_submission.title = "Test Query Post"
        mock_submission.selftext = "Query Content"
        mock_submission.author = MagicMock(__str__=lambda x: "user2")
        mock_submission.score = 15
        mock_submission.url = "http://query.com"
        mock_submission.created_utc = 1234567892
        mock_submission.comments = MagicMock()
        mock_submission.comments.replace_more = MagicMock()
        mock_submission.comments.list.return_value = [
            MagicMock(body="Query Comment", author=MagicMock(__str__=lambda x: "commenter2"), score=3)
        ]

        mock_subreddit.search.return_value = [mock_submission]
        self.mock_reddit.return_value.subreddit = MagicMock(return_value=mock_subreddit)  # Sửa ở đây

        # Call the function
        result = crawl_with_api(query="test query")

        # Expected output
        expected = [
            {
                'title': "Test Query Post",
                'content': "Query Content",
                'author': "user2",
                'score': 15,
                'url': "http://query.com",
                'created_utc': 1234567892,
                'comments': [{'body': "Query Comment", 'author': "commenter2", 'score': 3}]
            }
        ]

        self.assertEqual(result, expected)
        self.mock_reddit.return_value.subreddit.assert_called_with("all")
        mock_subreddit.search.assert_called_with("test query", sort='new', limit=self.mock_config.LIMIT)

    def test_crawl_with_username_and_query(self):
        # Setup mock Redditor and submissions
        mock_redditor = MagicMock()
        mock_submission = MagicMock()
        mock_submission.title = "Test Post with Query"
        mock_submission.selftext = "Content with test query"
        mock_submission.author = MagicMock(__str__=lambda x: "user3")
        mock_submission.score = 25
        mock_submission.url = "http://testquery.com"
        mock_submission.created_utc = 1234567893
        mock_submission.comments = MagicMock()
        mock_submission.comments.replace_more = MagicMock()
        mock_submission.comments.list.return_value = []

        mock_redditor.submissions.new.return_value = [mock_submission]
        self.mock_reddit.return_value.redditor.return_value = mock_redditor

        # Call the function
        result = crawl_with_api(username="testuser", query="test query")

        # Expected output
        expected = [
            {
                'title': "Test Post with Query",
                'content': "Content with test query",
                'author': "user3",
                'score': 25,
                'url': "http://testquery.com",
                'created_utc': 1234567893,
                'comments': []
            }
        ]

        self.assertEqual(result, expected)
        self.mock_reddit.return_value.redditor.assert_called_with("testuser")
        mock_redditor.submissions.new.assert_called_with(limit=self.mock_config.LIMIT)

    def test_crawl_default_subreddit(self):
        # Setup mock subreddit and submissions
        mock_subreddit = MagicMock()
        mock_submission = MagicMock()
        mock_submission.title = "Default Post"
        mock_submission.selftext = "Default Content"
        mock_submission.author = MagicMock(__str__=lambda x: "user4")
        mock_submission.score = 30
        mock_submission.url = "http://default.com"
        mock_submission.created_utc = 1234567894
        mock_submission.comments = MagicMock()
        mock_submission.comments.replace_more = MagicMock()
        mock_submission.comments.list.return_value = []

        mock_subreddit.new.return_value = [mock_submission]
        self.mock_reddit.return_value.subreddit = MagicMock(return_value=mock_subreddit)  # Sửa ở đây

        # Call the function
        result = crawl_with_api()

        # Expected output
        expected = [
            {
                'title': "Default Post",
                'content': "Default Content",
                'author': "user4",
                'score': 30,
                'url': "http://default.com",
                'created_utc': 1234567894,
                'comments': []
            }
        ]

        self.assertEqual(result, expected)
        self.mock_reddit.return_value.subreddit.assert_called_with(self.mock_config.SUBREDDIT_NAME)
        mock_subreddit.new.assert_called_with(limit=self.mock_config.LIMIT)

if __name__ == '__main__':
    unittest.main()