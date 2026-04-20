"""
Browser-based Douyin video extractor using Playwright.

Falls back on headless Chromium when yt-dlp's Douyin extractor fails
(due to missing a_bogus signature support).
"""

import logging
import re
import threading
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Regex to match Douyin video URLs
DOUYIN_URL_PATTERN = re.compile(
    r'https?://(?:www\.)?(?:douyin\.com/video/(\d+)|v\.douyin\.com/\w+)'
)


def is_douyin_url(url: str) -> bool:
    """Check if a URL is a Douyin video link."""
    return bool(DOUYIN_URL_PATTERN.match(url))


class DouyinExtractionError(Exception):
    """Raised when browser-based Douyin extraction fails."""
    pass


class DouyinBrowserExtractor:
    """Extract video stream URLs from Douyin using headless Playwright browser."""

    def __init__(self, cookie_browser: str = '', timeout: int = 30):
        """
        Args:
            cookie_browser: Browser to load cookies from ('chrome', 'edge', 'firefox').
                           Empty string means no cookies.
            timeout: Maximum seconds to wait for video URL interception.
        """
        self.cookie_browser = cookie_browser
        self.timeout = timeout

    def extract_video_url(self, url: str) -> Dict[str, Any]:
        """
        Open a headless browser, navigate to the Douyin URL,
        and intercept the video stream URL from network traffic.

        Args:
            url: Douyin video URL (e.g. https://www.douyin.com/video/7493...)

        Returns:
            Dict with keys:
                - 'video_url': str, direct video stream URL
                - 'title': str, video title (may be empty)
                - 'duration': Optional[int], duration in seconds

        Raises:
            DouyinExtractionError: If extraction fails
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise DouyinExtractionError(
                "Playwright is not installed. Install it with:\n"
                "  pip install playwright\n"
                "  playwright install chromium"
            )

        # Resolve short URLs first (v.douyin.com -> www.douyin.com/video/xxx)
        resolved_url = self._resolve_url(url)

        video_urls = []
        page_title = ''
        page_closed = threading.Event()

        with sync_playwright() as p:
            browser = None
            try:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                )

                # Load cookies from browser if configured
                if self.cookie_browser:
                    self._load_cookies(context, self.cookie_browser)

                page = context.new_page()

                # Intercept video stream responses
                def on_response(response):
                    if page_closed.is_set():
                        return
                    content_type = response.headers.get('content-type', '')
                    resp_url = response.url
                    if ('video/' in content_type or
                            ('douyinvod.com' in resp_url and '/video/' in resp_url)):
                        # Filter out tiny responses (thumbnails, ads)
                        content_length = response.headers.get('content-length')
                        if content_length and int(content_length) < 10000:
                            return
                        video_urls.append(resp_url)
                        logger.info(f"Intercepted video URL: {resp_url[:100]}...")

                page.on('response', on_response)

                # Navigate to the video page
                logger.info(f"Navigating to: {resolved_url}")
                page.goto(resolved_url, wait_until='domcontentloaded',
                          timeout=self.timeout * 1000)

                # Wait for the video element to appear and start playing
                try:
                    page.wait_for_selector('video', timeout=15000)
                    page_title = page.title()
                    # Try to trigger video load by scrolling
                    page.evaluate('window.scrollTo(0, 500)')
                except Exception:
                    logger.warning("Video element not found within timeout")

                # Give extra time for network interception
                page.wait_for_timeout(3000)

                page_closed.set()
                browser.close()
            except Exception as e:
                page_closed.set()
                if browser:
                    try:
                        browser.close()
                    except Exception:
                        pass
                raise DouyinExtractionError(f"Browser extraction failed: {e}")

        if not video_urls:
            raise DouyinExtractionError(
                "No video stream URL was intercepted. "
                "The video may be private, deleted, or region-blocked."
            )

        # Pick the best URL (prefer larger content-length or last URL which is
        # typically the actual video rather than a preview)
        best_url = video_urls[-1]

        # Clean up title
        if ' - 抖音' in page_title:
            page_title = page_title.replace(' - 抖音', '').strip()
        elif ' - 抖音精选' in page_title:
            page_title = page_title.replace(' - 抖音精选', '').strip()

        return {
            'video_url': best_url,
            'title': page_title or 'Douyin Video',
        }

    def _resolve_url(self, url: str) -> str:
        """Resolve v.douyin.com short URLs to full video URLs.

        For short URLs, we let the browser handle the redirect automatically
        by navigating to the short URL directly.
        """
        return url

    def _load_cookies(self, context, browser_name: str):
        """Load cookies from the user's browser into the Playwright context.

        Uses yt-dlp's cookies_from_browser to extract cookies, then adds
        them to the Playwright context.
        """
        try:
            from yt_dlp import YoutubeDL

            ydl_opts = {
                'cookiesfrombrowser': (browser_name,),
                'quiet': True,
            }

            with YoutubeDL(ydl_opts) as ydl:
                cookie_jar = ydl.cookiejar
                if cookie_jar:
                    cookies = []
                    for cookie in cookie_jar:
                        if 'douyin.com' in cookie.domain:
                            cookies.append({
                                'name': cookie.name,
                                'value': cookie.value,
                                'domain': cookie.domain,
                                'path': cookie.path,
                            })
                    if cookies:
                        context.add_cookies(cookies)
                        logger.info(f"Loaded {len(cookies)} cookies from {browser_name}")
        except Exception as e:
            logger.warning(f"Failed to load cookies from {browser_name}: {e}")
            # Non-fatal: continue without cookies
