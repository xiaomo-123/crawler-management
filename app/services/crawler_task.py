import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

class ControlledSpider:
    def __init__(
        self,
        interval: int = 5,
        restart_interval: int = 3600,
        time_range: tuple = (0, 24),
        browser_type: str = "chromium",
        max_exception: int = 3,  # 最大允许异常次数，超过则停止
        headless: bool = True,
        proxy: str = None,
        user_agent: str = None,
        storage_state_path: str = None
    ):
        self.interval = interval
        self.restart_interval = restart_interval
        self.time_range = time_range
        self.browser_type = browser_type
        self.max_exception = max_exception
        self.headless = headless
        self.proxy = proxy
        self.user_agent = user_agent
        self.storage_state_path = storage_state_path
        self.stop_event = asyncio.Event()
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        self.start_time = None
        self.exception_count = 0  # 异常计数器
        self.task = None  # 存储异步任务

    async def _init_browser(self):
        await self._close_browser()
        try:
            self.playwright = await async_playwright().start()
            browser_cls = getattr(self.playwright, self.browser_type)

            # 构建启动参数
            launch_kwargs = {
                "headless": self.headless,
                "args": ["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            }
            if self.proxy:
                launch_kwargs["proxy"] = {"server": self.proxy}

            self.browser = await browser_cls.launch(**launch_kwargs)

            # 构建上下文参数
            ctx_kwargs = {
                "viewport": {"width": 1280, "height": 800},
            }
            if self.storage_state_path:
                ctx_kwargs["storage_state"] = self.storage_state_path
            if self.user_agent:
                ctx_kwargs["user_agent"] = self.user_agent
            else:
                ctx_kwargs["user_agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

            self.context = await self.browser.new_context(**ctx_kwargs)
            self.page = await self.context.new_page()
            self.start_time = datetime.now()
            self.exception_count = 0  # 重启浏览器后重置异常计数
        except Exception as e:
            print(f"浏览器初始化失败: {e}")
            await self.stop()  # 初始化失败直接停止

    async def _close_browser(self):
        if self.page:
            await self.page.close()
            self.page = None
        if self.context:
            await self.context.close()
            self.context = None
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

    def _is_in_time_range(self):
        current_hour = datetime.now().hour
        return self.time_range[0] <= current_hour < self.time_range[1]

    async def crawl(self, url: str):
        if self.stop_event.is_set():
            return
        if not self._is_in_time_range():
            await asyncio.sleep(self.interval)
            return
        # 定期重启浏览器
        if self.start_time and (datetime.now() - self.start_time).total_seconds() >= self.restart_interval:
            await self._init_browser()
        try:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 爬取链接: {url}")
            await self.page.goto(url, timeout=3000)
            title = await self.page.title()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 爬取结果: {title}")
        except Exception as e:
            self.exception_count += 1
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 爬取失败: {str(e)} | 异常次数: {self.exception_count}/{self.max_exception}")
            # 异常次数超过阈值，停止任务
            if self.exception_count >= self.max_exception:
                print(f"异常次数达到上限 {self.max_exception}，自动停止爬虫")
                await self.stop()
                return
        await asyncio.sleep(self.interval)

    async def start(self, url: str):
        await self._init_browser()
        self.task = asyncio.create_task(self._run(url))

    async def _run(self, url: str):
        while not self.stop_event.is_set():
            await self.crawl(url)

    async def stop(self):
        self.stop_event.set()
        await self._close_browser()
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        print("爬虫已停止运行")

    def is_running(self):
        """判断爬虫是否正在运行"""
        return not self.stop_event.is_set() and self.task is not None and not self.task.done()
