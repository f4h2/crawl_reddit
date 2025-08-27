from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from config import BROWSER_USER_AGENT, SUBREDDIT_URL, LIMIT, DEFAULT_QUERY, DEFAULT_USERNAME
from utils import handle_browser_error
import asyncio
import random
import time

async def crawl_with_browser(query=None, username=None):
    data = []
    url = SUBREDDIT_URL
    if username:  # URL cho tài khoản, sort by new
        url = f'https://www.reddit.com/user/{username}/submitted/?sort=new'
    elif query:  # URL cho search trong subreddit, sort by new
        url = f'https://www.reddit.com/r/space/search/?q={query}&sort=new'

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent=BROWSER_USER_AGENT,
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
            viewport={"width": 1280, "height": 720}  # Đặt viewport cố định
        )
        page = await context.new_page()

        # Đi đến trang với retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Đang thử tải trang {url}, lần {attempt + 1}/{max_retries}")
                await handle_browser_error(page, lambda: page.goto(url, wait_until='networkidle', timeout=90000))  # Tăng timeout lên 90 giây
                break
            except PlaywrightTimeoutError:
                if attempt < max_retries - 1:
                    print(f"Thử lại lần {attempt + 2}/{max_retries} sau 5 giây...")
                    await asyncio.sleep(5 + random.uniform(0, 2))  # Thêm ngẫu nhiên để tránh bị chặn
                else:
                    print(f"Không thể tải trang {url} sau {max_retries} lần thử.")
                    await browser.close()
                    return data

        # Scroll và scrape
        loaded_posts = 0
        previous_height = 0
        while loaded_posts < LIMIT:
            posts = await page.query_selector_all('h2.m-0 a[data-testid="post-title"]')

            for post in posts[loaded_posts:]:
                href = await post.get_attribute("href")
                full_url = f"https://www.reddit.com{href}" if href else 'N/A'

                # Mở trang full_url để lấy tất cả thông tin
                post_page = await context.new_page()
                for attempt in range(max_retries):
                    try:
                        print(f"Đang tải {full_url}, lần {attempt + 1}/{max_retries}")
                        start_time = time.time()
                        await handle_browser_error(post_page, lambda: post_page.goto(full_url, wait_until='networkidle', timeout=90000))
                        load_time = time.time() - start_time
                        print(f"Đã tải {full_url} trong {load_time:.2f} giây")
                        break
                    except PlaywrightTimeoutError:
                        if attempt < max_retries - 1:
                            print(f"Thử lại lần {attempt + 2}/{max_retries} cho {full_url} sau 5 giây...")
                            await asyncio.sleep(5 + random.uniform(0, 2))
                        else:
                            print(f"Không thể tải trang {full_url} sau {max_retries} lần thử.")
                            await post_page.close()
                            continue

                # Lấy title
                title_elem = await post_page.query_selector('h1[data-testid="post-title"]')
                title = await title_elem.inner_text() if title_elem else await post.get_attribute('aria-label') or 'N/A'

                # Lấy author của bài viết
                author_elem = await post_page.query_selector('a[href*="/user/"].author-name')
                author = await author_elem.inner_text() if author_elem else 'N/A'

                # Lấy score của bài viết
                score_elem = await post_page.query_selector('faceplate-number')
                score = await score_elem.get_attribute('number') if score_elem else '0'

                # Lấy content
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

                # Lấy danh sách comment
                comments = []
                comment_elements = await post_page.query_selector_all('shreddit-comment')
                for comment in comment_elements:
                    # Lấy author của comment
                    comment_author_elem = await comment.query_selector('rpl-hovercard a.truncate.font-bold.text-neutral-content-strong.text-12')
                    comment_author = await comment_author_elem.inner_text() if comment_author_elem else 'N/A'

                    # Lấy score của comment
                    comment_score_elem = await comment.query_selector('faceplate-number')
                    comment_score = await comment_score_elem.get_attribute('number') if comment_score_elem else '0'

                    # Lấy body
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
            if loaded_posts >= LIMIT:
                break

            # Scroll với delay ngẫu nhiên
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(2000 + random.uniform(0, 1000))  # Delay từ 2-3 giây
            new_height = await page.evaluate('document.body.scrollHeight')
            if new_height == previous_height:
                break
            previous_height = new_height

        await browser.close()

    return data

# Chạy hàm (ví dụ)
if __name__ == "__main__":
    import asyncio
    asyncio.run(crawl_with_browser(query="dog"))