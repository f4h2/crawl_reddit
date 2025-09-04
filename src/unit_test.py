import unittest
from unittest.mock import patch, MagicMock
from api_crawler import crawl_with_api
from config import Config

class TestApiCrawler(unittest.TestCase):
    def setUp(self):
        # Mock Config values
        self.patcher_config = patch('api_crawler.Config', autospec=True)
        self.mock_config = self.patcher_config.start()
        self.mock_config.REDDIT_CLIENT_ID = "fake_client_id"
        self.mock_config.REDDIT_CLIENT_SECRET = "fake_client_secret"
        self.mock_config.REDDIT_USER_AGENT = "fake_user_agent"
        self.mock_config.SUBREDDIT_NAME = "testsubreddit"
        self.mock_config.LIMIT = 2

        # Mock time.sleep to avoid delays in tests
        self.patcher_time = patch('api_crawler.time.sleep', return_value=None)
        self.patcher_time.start()

    def tearDown(self):
        self.patcher_config.stop()
        self.patcher_time.stop()

    @patch('api_crawler.praw.Reddit')
    @patch('api_crawler.handle_rate_limit')
    def test_crawl_with_query(self, mock_handle_rate_limit, mock_reddit):
        # Mock Reddit instance and search results
        mock_reddit_instance = MagicMock()
        mock_reddit.return_value = mock_reddit_instance
        mock_subreddit = MagicMock()
        mock_reddit_instance.subreddit.return_value = mock_subreddit

        # Mock submission data
        mock_submission = MagicMock()
        mock_submission.title = "Test Post"
        mock_submission.selftext = "This is a test post"
        mock_submission.author = MagicMock(name="test_user")
        mock_submission.author.__str__.return_value = "test_user"
        mock_submission.score = 100
        mock_submission.url = "http://test.com"
        mock_submission.created_utc = 1630000000
        mock_submission.comments.replace_more.return_value = None
        mock_comment = MagicMock()
        mock_comment.body = "Test comment"
        mock_comment.author = MagicMock(name="commenter")
        mock_comment.author.__str__.return_value = "commenter"
        mock_comment.score = 10
        mock_submission.comments.list.return_value = [mock_comment]

        mock_subreddit.search.return_value = [mock_submission]
        mock_handle_rate_limit.side_effect = lambda func, *args, **kwargs: func(*args, **kwargs)

        # Call the function
        result = crawl_with_api(query="test query")

        # Expected output
        expected = [
            {
                'title': "Test Post",
                'content': "This is a test post",
                'author': "test_user",
                'score': 100,
                'url': "http://test.com",
                'created_utc': 1630000000,
                'comments': [{'body': "Test comment", 'author': "commenter", 'score': 10}]
            }
        ]

        # Assertions
        self.assertEqual(result, expected)
        mock_reddit_instance.subreddit.assert_called_with("all")
        mock_subreddit.search.assert_called_with("test query", sort='new', limit=self.mock_config.LIMIT)

    @patch('api_crawler.praw.Reddit')
    @patch('api_crawler.handle_rate_limit')
    def test_crawl_with_username(self, mock_handle_rate_limit, mock_reddit):
        # Mock Reddit instance and redditor submissions
        mock_reddit_instance = MagicMock()
        mock_reddit.return_value = mock_reddit_instance
        mock_redditor = MagicMock()
        mock_reddit_instance.redditor.return_value = mock_redditor

        # Mock submission data
        mock_submission = MagicMock()
        mock_submission.title = "User Post"
        mock_submission.selftext = "User post content"
        mock_submission.author = MagicMock(name="test_user")
        mock_submission.author.__str__.return_value = "test_user"
        mock_submission.score = 50
        mock_submission.url = "http://userpost.com"
        mock_submission.created_utc = 1630000000
        mock_submission.comments.replace_more.return_value = None
        mock_comment = MagicMock()
        mock_comment.body = "User comment"
        mock_comment.author = MagicMock(name="commenter2")
        mock_comment.author.__str__.return_value = "commenter2"
        mock_comment.score = 5
        mock_submission.comments.list.return_value = [mock_comment]

        mock_redditor.submissions.new.return_value = [mock_submission]
        mock_handle_rate_limit.side_effect = lambda func, *args, **kwargs: func(*args, **kwargs)

        # Call the function
        result = crawl_with_api(username="test_user")

        # Expected output
        expected = [
            {
                'title': "User Post",
                'content': "User post content",
                'author': "test_user",
                'score': 50,
                'url': "http://userpost.com",
                'created_utc': 1630000000,
                'comments': [{'body': "User comment", 'author': "commenter2", 'score': 5}]
            }
        ]

        # Assertions
        self.assertEqual(result, expected)
        mock_reddit_instance.redditor.assert_called_with("test_user")
        mock_redditor.submissions.new.assert_called_with(limit=self.mock_config.LIMIT)

    @patch('api_crawler.praw.Reddit')
    @patch('api_crawler.handle_rate_limit')
    def test_crawl_default_subreddit(self, mock_handle_rate_limit, mock_reddit):
        # Mock Reddit instance and subreddit new posts
        mock_reddit_instance = MagicMock()
        mock_reddit.return_value = mock_reddit_instance
        mock_subreddit = MagicMock()
        mock_reddit_instance.subreddit.return_value = mock_subreddit

        # Mock submission data
        mock_submission = MagicMock()
        mock_submission.title = "Subreddit Post"
        mock_submission.selftext = "Subreddit post content"
        mock_submission.author = MagicMock(name="subreddit_user")
        mock_submission.author.__str__.return_value = "subreddit_user"
        mock_submission.score = 75
        mock_submission.url = "http://subredditpost.com"
        mock_submission.created_utc = 1630000000
        mock_submission.comments.replace_more.return_value = None
        mock_comment = MagicMock()
        mock_comment.body = "Subreddit comment"
        mock_comment.author = MagicMock(name="commenter3")
        mock_comment.author.__str__.return_value = "commenter3"
        mock_comment.score = 15
        mock_submission.comments.list.return_value = [mock_comment]

        mock_subreddit.new.return_value = [mock_submission]
        mock_handle_rate_limit.side_effect = lambda func, *args, **kwargs: func(*args, **kwargs)

        # Call the function
        result = crawl_with_api()

        # Expected output
        expected = [
            {
                'title': "Subreddit Post",
                'content': "Subreddit post content",
                'author': "subreddit_user",
                'score': 75,
                'url': "http://subredditpost.com",
                'created_utc': 1630000000,
                'comments': [{'body': "Subreddit comment", 'author': "commenter3", 'score': 15}]
            }
        ]

        # Assertions
        self.assertEqual(result, expected)
        mock_reddit_instance.subreddit.assert_called_with(self.mock_config.SUBREDDIT_NAME)
        mock_subreddit.new.assert_called_with(limit=self.mock_config.LIMIT)

    @patch('api_crawler.praw.Reddit')
    @patch('api_crawler.handle_rate_limit')
    def test_crawl_with_query_no_results(self, mock_handle_rate_limit, mock_reddit):
        # Mock Reddit instance with no results
        mock_reddit_instance = MagicMock()
        mock_reddit.return_value = mock_reddit_instance
        mock_subreddit = MagicMock()
        mock_reddit_instance.subreddit.return_value = mock_subreddit
        mock_subreddit.search.return_value = []
        mock_handle_rate_limit.side_effect = lambda func, *args, **kwargs: func(*args, **kwargs)

        # Call the function
        result = crawl_with_api(query="no_results_query")

        # Expected output
        expected = []

        # Assertions
        self.assertEqual(result, expected)
        mock_reddit_instance.subreddit.assert_called_with("all")
        mock_subreddit.search.assert_called_with("no_results_query", sort='new', limit=self.mock_config.LIMIT)

if __name__ == '__main__':
    unittest.main()