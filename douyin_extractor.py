"""
Browser-based video extractor using Playwright.

Extracts video stream URLs from Chinese short-video platforms by intercepting
network traffic in a headless Chromium browser. Used as a fallback when yt-dlp's
extractors fail (e.g. Douyin's a_bogus signature, Xiaohongshu anti-scraping, etc.).

Supported platforms:
  - 抖音 (Douyin)
  - 小红书 (Xiaohongshu / RED)
  - 快手 (Kuaishou)
  - 微博视频 (Weibo Video)
  - 西瓜视频 (Xigua Video)
  - 皮皮虾 (PiPiXia)
  - 知乎视频 (Zhihu Video)
  - 好看视频 (Haokan / Baidu Video)
"""

import logging
import re
import threading
import sys
from typing import Optional, Dict, Any, List, Callable
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Site configuration: URL patterns, CDN domains, and URL normalizers
# ---------------------------------------------------------------------------

def _normalize_douyin(url: str) -> str:
    """Normalize Douyin URLs to standard /video/ID format."""
    m = re.search(r'douyin\.com/video/(\d+)', url)
    if m:
        return f'https://www.douyin.com/video/{m.group(1)}'
    m = re.search(r'modal_id=(\d+)', url)
    if m:
        return f'https://www.douyin.com/video/{m.group(1)}'
    return url


def _normalize_xiaohongshu(url: str) -> str:
    """Normalize Xiaohongshu URLs."""
    # Already in standard format
    if '/explore/' in url or '/discovery/item/' in url:
        return url
    # Short URLs (xhslink.com) are resolved by the browser
    return url


def _normalize_kuaishou(url: str) -> str:
    """Normalize Kuaishou URLs."""
    # Standard format is already good
    return url


def _normalize_weibo(url: str) -> str:
    """Normalize Weibo video URLs."""
    return url


def _normalize_xigua(url: str) -> str:
    """Normalize Xigua (西瓜视频) URLs."""
    return url


def _normalize_pipixia(url: str) -> str:
    """Normalize PiPiXia (皮皮虾) URLs."""
    return url


def _normalize_zhihu(url: str) -> str:
    """Normalize Zhihu video URLs."""
    return url


def _normalize_haokan(url: str) -> str:
    """Normalize Haokan (好看视频) URLs."""
    return url


SITES: Dict[str, Dict[str, Any]] = {
    'douyin': {
        'name': '抖音',
        'url_patterns': [
            re.compile(r'https?://(?:www\.)?(?:douyin\.com|iesdouyin\.com)'),
            re.compile(r'https?://v\.douyin\.com/[\w-]+'),
        ],
        'cdn_domains': ['douyinvod.com', 'douyinpic.com', 'bytedance.com',
                        'byteimg.com', 'bytecdn.cn', 'bdurl.net'],
        'cdn_path_hint': '/video/',
        'referer': 'https://www.douyin.com/',
        'normalize': _normalize_douyin,
        'title_suffix': ' - 抖音',
        'skip_ytdlp': True,
    },
    'xiaohongshu': {
        'name': '小红书',
        'url_patterns': [
            re.compile(r'https?://(?:www\.)?(?:xiaohongshu\.com|xiaohongshu\.cn)'),
            re.compile(r'https?://xhslink\.com/[\w-]+'),
        ],
        'cdn_domains': ['xhscdn.com', 'sns-video', 'ci.xiaohongshu.com'],
        'cdn_path_hint': '/video/',
        'referer': 'https://www.xiaohongshu.com/',
        'normalize': _normalize_xiaohongshu,
        'title_suffix': ' - 小红书',
        'skip_ytdlp': False,
    },
    'kuaishou': {
        'name': '快手',
        'url_patterns': [
            re.compile(r'https?://(?:www\.)?(?:kuaishou\.com|gifshow\.com|kwai\.com)'),
            re.compile(r'https?://(?:www\.)?v\.kuaishou\.com/[\w-]+'),
            re.compile(r'https?://(?:www\.)?ch\.kuaishou\.com/'),
        ],
        'cdn_domains': ['kuaishou.com', 'ksyun.com', 'kscpcdn.cn', 'ks-livecdn',
                        'yximgs.com', 'gifshow.com'],
        'cdn_path_hint': '/video/',
        'referer': 'https://www.kuaishou.com/',
        'normalize': _normalize_kuaishou,
        'title_suffix': ' - 快手',
        'skip_ytdlp': False,
    },
    'weibo': {
        'name': '微博',
        'url_patterns': [
            re.compile(r'https?://(?:www\.)?(?:weibo\.com|weibo\.cn)'),
            re.compile(r'https?://video\.weibo\.com/'),
        ],
        'cdn_domains': ['video.weibo.com', 'f.video.weibocdn.com',
                        'wb-video', 'sinacdn.com'],
        'cdn_path_hint': '/video/',
        'referer': 'https://weibo.com/',
        'normalize': _normalize_weibo,
        'title_suffix': ' - 微博',
    },
    'xigua': {
        'name': '西瓜视频',
        'url_patterns': [
            re.compile(r'https?://(?:www\.)?(?:ixigua\.com)'),
            re.compile(r'https?://(?:www\.)?(?:toutiao\.com)/(?:video|group)'),
        ],
        'cdn_domains': ['ixigua.com', 'toutiao.com', 'bytedance.com',
                        'bdurl.net', 'bytecdn.cn'],
        'cdn_path_hint': '/video/',
        'referer': 'https://www.ixigua.com/',
        'normalize': _normalize_xigua,
        'title_suffix': ' - 西瓜视频',
        'skip_ytdlp': False,
    },
    'pipixia': {
        'name': '皮皮虾',
        'url_patterns': [
            re.compile(r'https?://(?:www\.)?(?:pipix\.com|pipixia\.com)'),
            re.compile(r'https?://(?:www\.)?isnip\.com/'),
        ],
        'cdn_domains': ['pipix.com', 'bytedance.com', 'bytecdn.cn', 'bdurl.net'],
        'cdn_path_hint': '/video/',
        'referer': 'https://www.pipix.com/',
        'normalize': _normalize_pipixia,
        'title_suffix': ' - 皮皮虾',
        'skip_ytdlp': False,
    },
    'zhihu': {
        'name': '知乎',
        'url_patterns': [
            re.compile(r'https?://(?:www\.)?zhihu\.com/'),
            re.compile(r'https?://zhuanlan\.zhihu\.com/'),
            re.compile(r'https?://video\.zhihu\.com/'),
        ],
        'cdn_domains': ['zhimg.com', 'vdn.vzuu.com', 'zhihu-video',
                        'zhihu.com/video'],
        'cdn_path_hint': '/video/',
        'referer': 'https://www.zhihu.com/',
        'normalize': _normalize_zhihu,
        'title_suffix': ' - 知乎',
        'skip_ytdlp': False,
    },
    'haokan': {
        'name': '好看视频',
        'url_patterns': [
            re.compile(r'https?://(?:www\.)?haokan\.baidu\.com/'),
            re.compile(r'https?://haokan\.baidu\.com/v'),
        ],
        'cdn_domains': ['haokan.baidu.com', 'bcebos.com', 'bcecdn.com',
                        'baidu.com/video'],
        'cdn_path_hint': '/video/',
        'referer': 'https://haokan.baidu.com/',
        'normalize': _normalize_haokan,
        'title_suffix': ' - 好看视频',
        'skip_ytdlp': True,
    },
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def is_browser_extraction_url(url: str) -> bool:
    """Check if a URL should use browser-based extraction instead of yt-dlp.

    Returns True for any URL matching a configured site that is known to have
    broken yt-dlp support (primarily Chinese short-video platforms).
    """
    for site_id, site_config in SITES.items():
        for pattern in site_config['url_patterns']:
            if pattern.search(url):
                return True
    return False


def get_site_id(url: str) -> Optional[str]:
    """Return the site identifier for a URL, or None if not recognized."""
    for site_id, site_config in SITES.items():
        for pattern in site_config['url_patterns']:
            if pattern.search(url):
                return site_id
    return None


def normalize_url(url: str, site_id: Optional[str] = None) -> str:
    """Normalize a URL using the site-specific normalizer."""
    if site_id is None:
        site_id = get_site_id(url)
    if site_id and site_id in SITES:
        return SITES[site_id]['normalize'](url)
    return url


def should_skip_ytdlp(url: str) -> bool:
    """Return True if yt-dlp should be skipped for this URL.

    Sites with skip_ytdlp=True have yt-dlp extractors that are known to be
    fundamentally broken (e.g. Douyin's a_bogus signature). For these sites,
    we go directly to browser extraction instead of wasting time with yt-dlp.
    """
    site_id = get_site_id(url)
    if site_id and site_id in SITES:
        return SITES[site_id].get('skip_ytdlp', False)
    return False


# Backward-compatible aliases
is_douyin_url = is_browser_extraction_url
normalize_douyin_url = normalize_url


class BrowserExtractionError(Exception):
    """Raised when browser-based video extraction fails."""
    pass


# Backward-compatible alias
DouyinExtractionError = BrowserExtractionError


# ---------------------------------------------------------------------------
# Browser extractor
# ---------------------------------------------------------------------------

class BrowserExtractor:
    """Extract video stream URLs from supported sites using headless Playwright.

    Works by launching a headless Chromium browser, navigating to the target URL,
    and intercepting video stream responses from CDN domains.
    """

    # Minimum content-length to consider a response as actual video (bytes)
    MIN_VIDEO_SIZE = 50000

    def __init__(self, cookie_browser: str = '', timeout: int = 30):
        """
        Args:
            cookie_browser: Browser to load cookies from ('chrome', 'edge', 'firefox').
                           Empty string means no cookies.
            timeout: Maximum seconds to wait for page load.
        """
        self.cookie_browser = cookie_browser
        self.timeout = timeout

    def extract_video_url(self, url: str) -> Dict[str, Any]:
        """
        Open a headless browser, navigate to the URL, and intercept the
        video stream URL from network traffic.

        Args:
            url: Video page URL on a supported platform.

        Returns:
            Dict with keys:
                - 'video_url': str, direct video stream URL
                - 'title': str, video title (may be empty)

        Raises:
            BrowserExtractionError: If extraction fails
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise BrowserExtractionError(
                "Playwright is not installed. Install it with:\n"
                "  pip install playwright\n"
                "  playwright install chromium"
            )

        site_id = get_site_id(url)
        site_config = SITES.get(site_id, {}) if site_id else {}
        site_name = site_config.get('name', 'Unknown')
        referer = site_config.get('referer', '')
        title_suffix = site_config.get('title_suffix', '')
        cdn_domains = site_config.get('cdn_domains', [])

        # Normalize the URL
        resolved_url = normalize_url(url, site_id)
        logger.info(f"Normalized URL: {url} -> {resolved_url}")

        video_urls: List[str] = []
        dom_video_urls: List[str] = []
        page_title = ''
        page_closed = threading.Event()

        # Video file extensions to match in URLs
        VIDEO_EXTENSIONS = ('.mp4', '.m3u8', '.flv', '.mov', '.webm', '.ts')

        with sync_playwright() as p:
            browser = None
            context = None
            try:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=(
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/120.0.0.0 Safari/537.36'
                    ),
                    viewport={'width': 1920, 'height': 1080},
                )

                # Load cookies from browser if configured
                if self.cookie_browser:
                    self._load_cookies(context, self.cookie_browser)

                page = context.new_page()

                def on_response(response):
                    if page_closed.is_set():
                        return
                    resp_url = response.url
                    content_type = response.headers.get('content-type', '')

                    # Skip known non-video types early
                    non_video_types = ('text/', 'image/', 'application/javascript',
                                       'application/json', 'font/', 'css')
                    if any(content_type.startswith(t) for t in non_video_types):
                        return

                    # Check if this looks like a video response
                    is_video_type = 'video/' in content_type
                    is_cdn_match = cdn_domains and any(
                        domain in resp_url for domain in cdn_domains)
                    has_video_ext = any(resp_url.split('?')[0].endswith(ext)
                                       for ext in VIDEO_EXTENSIONS)

                    if is_video_type:
                        # Confirmed video by content-type — trust it
                        content_length = response.headers.get('content-length')
                        if content_length and int(content_length) < self.MIN_VIDEO_SIZE:
                            return
                        video_urls.append(resp_url)
                        logger.info(f"Intercepted video URL: {resp_url[:120]}...")
                    elif is_cdn_match and (has_video_ext or '/video/' in resp_url):
                        # CDN domain match + video-like path or extension
                        content_length = response.headers.get('content-length')
                        if content_length and int(content_length) < self.MIN_VIDEO_SIZE:
                            return
                        video_urls.append(resp_url)
                        logger.info(f"Intercepted video URL: {resp_url[:120]}...")

                page.on('response', on_response)

                # Navigate to the video page
                logger.info(f"Navigating to: {resolved_url}")
                page.goto(resolved_url, wait_until='domcontentloaded',
                          timeout=self.timeout * 1000)

                # Wait for the video element and try to trigger playback
                video_found = False
                try:
                    page.wait_for_selector('video', timeout=15000)
                    page_title = page.title()
                    video_found = True
                    # Scroll to trigger lazy-loaded video
                    page.evaluate('window.scrollTo(0, 500)')
                    # Try clicking the video to trigger playback
                    try:
                        page.click('video', timeout=2000)
                    except Exception:
                        pass
                except Exception:
                    logger.warning("Video element not found within timeout")
                    page_title = page.title()

                # Give extra time for network interception
                page.wait_for_timeout(3000)

                # DOM fallback: extract video src from <video> and <source> elements
                if not video_urls and video_found:
                    try:
                        srcs = page.evaluate('''() => {
                            const urls = [];
                            document.querySelectorAll('video source, video').forEach(el => {
                                const src = el.src || el.getAttribute('src');
                                if (src) urls.push(src);
                            });
                            return urls;
                        }''')
                        for src in srcs:
                            if src and src.startswith('http'):
                                dom_video_urls.append(src)
                                logger.info(f"DOM video src: {src[:120]}...")
                    except Exception as e:
                        logger.warning(f"Failed to extract video src from DOM: {e}")

            except Exception as e:
                error_text = str(e)
                if ('Executable doesn\'t exist' in error_text or
                        'Executable does not exist' in error_text):
                    if getattr(sys, '_MEIPASS', None):
                        raise BrowserExtractionError(
                            f"Browser extraction failed for {site_name}: this EXE was built "
                            f"without the bundled Playwright Chromium browser. Please download "
                            f"a newer release."
                        )
                    raise BrowserExtractionError(
                        f"Browser extraction failed for {site_name}: Playwright Chromium is not installed. "
                        f"Run `python -m playwright install chromium`."
                    )
                raise BrowserExtractionError(
                    f"Browser extraction failed for {site_name}: {e}"
                )
            finally:
                page_closed.set()
                if context:
                    try:
                        context.close()
                    except Exception:
                        pass
                if browser:
                    try:
                        browser.close()
                    except Exception:
                        pass

        all_urls = video_urls + dom_video_urls
        if not all_urls:
            raise BrowserExtractionError(
                f"No video stream URL was intercepted from {site_name}. "
                f"The video may be private, deleted, or region-blocked. "
                f"Try enabling cookies from your browser in Advanced Options."
            )

        # Pick the best URL:
        # 1. Prefer URLs from known CDN domains (actual video streams)
        # 2. Among CDN URLs, prefer the last one (typically the full video)
        # 3. Fall back to non-CDN URLs, skipping known static asset domains
        static_domains = ('douyinstatic.com', 'staticcdn', 'fe-static')

        cdn_urls = [u for u in video_urls
                    if cdn_domains and any(d in u for d in cdn_domains)
                    and not any(s in u for s in static_domains)]
        non_static = [u for u in all_urls
                      if not any(s in u for s in static_domains)]

        if cdn_urls:
            best_url = cdn_urls[-1]
        elif non_static:
            best_url = non_static[-1]
        else:
            best_url = all_urls[-1]

        # Clean up title
        if title_suffix and title_suffix in page_title:
            page_title = page_title.replace(title_suffix, '').strip()

        return {
            'video_url': best_url,
            'title': page_title or f'{site_name} Video',
        }

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


# Backward-compatible alias
DouyinBrowserExtractor = BrowserExtractor
