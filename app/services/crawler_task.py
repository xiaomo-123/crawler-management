import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

class ControlledSpider:
    def __init__(
        self,
        interval: int = 5,
        restart_interval: int = 3600,
        time_range: tuple = (0, 24),
        max_exception: int = 3,  # 最大允许异常次数，超过则停止
        headless: bool = False,
        proxy: str = None,
        user_agent: str = None,
        storage_state_path: str = None,
        api_request: str = None,
        task_type: str = "crawler"
    ):
        self.interval = interval
        self.restart_interval = restart_interval
        self.time_range = time_range
        self.max_exception = max_exception
        self.headless = headless
        self.proxy = proxy
        self.user_agent = user_agent
        self.storage_state_path = storage_state_path
        self.api_request = api_request
        self.task_type = task_type
        self.stop_event = asyncio.Event()
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        self.start_time = None
        self.exception_count = 0  # 异常计数器
        self.task = None  # 存储异步任务

    async def _init_browser(self):        
        try:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始初始化浏览器...")
            
            # 关闭旧的浏览器实例
            await self._close_browser()
            
            # 启动新的浏览器实例
            self.playwright = await async_playwright().start()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Playwright 已启动")
            
            # 启动浏览器
            browser_args = {
                'headless': self.headless,
                'slow_mo': 50
            }
            
            # if self.proxy:
            #     browser_args['proxy'] = {'server': self.proxy}
            #     print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 使用代理: {self.proxy}")
            
            self.browser = await self.playwright.chromium.launch(**browser_args)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 浏览器已启动")
            
            # 创建浏览器上下文
            context_args = {}
            if self.storage_state_path:
                context_args['storage_state'] = self.storage_state_path
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 使用存储状态: {self.storage_state_path}")
            
            self.context = await self.browser.new_context(**context_args)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 浏览器上下文已创建")
            
            # 创建新页面
            self.page = await self.context.new_page()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 新页面已创建")
            
            if self.user_agent:
                await self.page.set_extra_http_headers({"User-Agent": self.user_agent})
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] User-Agent 已设置: {self.user_agent}")
            
            self.start_time = datetime.now()
            self.exception_count = 0  # 重启浏览器后重置异常计数
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 浏览器初始化完成")
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
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 当前时间不在运行时间范围内，跳过本次爬取")
            await asyncio.sleep(self.interval)
            return
        # 检查浏览器是否需要初始化
        if self.page is None:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 浏览器未初始化，开始初始化...")
            await self._init_browser()
        
        # 定期重启浏览器
        if self.start_time and (datetime.now() - self.start_time).total_seconds() >= self.restart_interval:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 达到重启间隔，重启浏览器...")
            await self._init_browser()
        
        # 使用已初始化的浏览器实例
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=self.headless,
                    slow_mo=50
                   
                )
                self.page = await browser.new_page()
                if self.user_agent:
                    await self.page.set_extra_http_headers({"User-Agent": self.user_agent})
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始爬取链接: {url}")
                await self.page.goto(url, timeout=3000)
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 页面加载成功")
                
                # 获取页面标题
                # title = await self.page.title()
                # print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 页面标题: {title}")
                # await asyncio.sleep(10000000)
        except asyncio.CancelledError:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 爬取任务被取消")
            raise  # 重新抛出CancelledError以便上层处理
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
        try:
            while not self.stop_event.is_set():
                await self.crawl(url)
        except asyncio.CancelledError:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 爬虫任务被取消")
            raise

    async def stop(self):
        self.stop_event.set()
        await self._close_browser()
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                print(f"停止爬虫任务时出错: {str(e)}")
        print("爬虫已停止运行")
    
    def stop_sync(self):
        """同步停止方法，用于在非异步上下文中停止爬虫"""
        self.stop_event.set()

    def is_running(self):
        """判断爬虫是否正在运行"""
        return not self.stop_event.is_set() and self.task is not None and not self.task.done()
