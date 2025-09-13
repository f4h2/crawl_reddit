from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import asyncio
import random
import time
from config import Config
from utils import handle_browser_error


class Browser:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None

    async def initialize(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context(
            user_agent=Config.BROWSER_USER_AGENT,
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
            viewport={"width": 1280, "height": 720}
        )
        self.page = await self.context.new_page()

    async def goto_with_retry(self, url, max_retries=3):
        for attempt in range(max_retries):
            try:
                print(f"Đang thử tải trang {url}, lần {attempt + 1}/{max_retries}")
                await handle_browser_error(self.page, lambda: self.page.goto(url, wait_until='networkidle', timeout=90000))
                break
            except PlaywrightTimeoutError:
                if attempt < max_retries - 1:
                    print(f"Thử lại lần {attempt + 2}/{max_retries} sau 5 giây...")
                    await asyncio.sleep(5 + random.uniform(0, 2))
                else:
                    print(f"Không thể tải trang {url} sau {max_retries} lần thử.")
                    raise

    async def close(self):
        if self.browser:
            await self.browser.close()
            print("Đã đóng trình duyệt")

async def crawl_with_browser(query=None, username=None):
    data = []
    url = Config.SUBREDDIT_URL
    if username:
        url = f"https://www.reddit.com/user/{username}/submitted/?sort=new"
    elif query:
        url = f"https://www.reddit.com/r/space/search/?q={query}&sort=new"


    browser = Browser()
    await browser.initialize()

    try:
        await browser.goto_with_retry(url)

        loaded_posts = 0
        previous_height = 0
        while loaded_posts < Config.LIMIT:
            posts = await browser.page.query_selector_all('h2.m-0 a[data-testid="post-title"]')

            title_elem = await post_page.query_selector('h1[data-testid="post-title"]')
            title = await title_elem.inner_text() if title_elem else await post.get_attribute('aria-label') or 'N/A'

            for post in posts[loaded_posts:]:
                href = await post.get_attribute("href")
                full_url = f"https://www.reddit.com{href}" if href else 'N/A'

                post_page = await browser.context.new_page()
                await browser.goto_with_retry(full_url)

                # title_elem = await post_page.query_selector('h1[data-testid="post-title"]')
                # title = await title_elem.inner_text() if title_elem else await post.get_attribute('aria-label') or 'N/A'

                author_elem = await post_page.query_selector('a[href*="/user/"].author-name')
                author = await author_elem.inner_text() if author_elem else 'N/A'

                score_elem = await post_page.query_selector('faceplate-number')
                score = await score_elem.get_attribute('number') if score_elem else '0'

                content_elem = await post_page.query_selector('div.md')
                if content_elem:
                    paragraphs = await content_elem.query_selector_all('p')
                    content = "\n".join([await p.inner_text() for p in paragraphs])
                    links = await content_elem.query_selector_all('a')
                    link_urls = [await a.get_attribute('href') for a in links]
                    images = await content_elem.query_selector_all('img')
                    image_urls = [await img.get_attribute('src') for img in images]
                else:
                    content, link_urls, image_urls = 'N/A', [], []

                comments = []
                comment_elements = await post_page.query_selector_all('shreddit-comment')
                for comment in comment_elements:
                    comment_author_elem = await comment.query_selector('rpl-hovercard a.truncate.font-bold.text-neutral-content-strong.text-12')
                    comment_author = await comment_author_elem.inner_text() if comment_author_elem else 'N/A'

                    comment_score_elem = await comment.query_selector('faceplate-number')
                    comment_score = await comment_score_elem.get_attribute('number') if comment_score_elem else '0'

                    body_elem = await comment.query_selector('div[id$="-post-rtjson-content"]')
                    comment_body = await body_elem.inner_text() if body_elem else 'N/A'

                    comments.append({
                        'author': comment_author.strip(),
                        'score': int(comment_score) if comment_score.isdigit() else 0,
                        'body': comment_body.strip()
                    })

                data.append({
                    'title': title.strip(),
                    'author': author.strip(),
                    'score': int(score) if score.isdigit() else 0,
                    'content': content.strip(),
                    'url': full_url,
                    'comments': comments
                })

                await post_page.close()

            loaded_posts = len(data)
            if loaded_posts >= Config.LIMIT:
                break

            await browser.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await browser.page.wait_for_timeout(2000 + random.uniform(0, 1000))
            new_height = await browser.page.evaluate('document.body.scrollHeight')
            if new_height == previous_height:
                break
            previous_height = new_height

    finally:
        await browser.close()

    return data

if __name__ == "__main__":
    import asyncio
    asyncio.run(crawl_with_browser(query="dog"))