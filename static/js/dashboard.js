// 仪表盘模块

// 初始化仪表盘
function initDashboard() {
    loadDashboardData();
}

// 加载仪表盘数据
async function loadDashboardData() {
    try {
        // 加载统计数据
        const accountsResponse = await fetch('/api/accounts/');
        const accounts = await accountsResponse.json();
        document.getElementById('total-accounts').textContent = accounts.length;

        const tasksResponse = await fetch('/api/tasks/');
        const tasks = await tasksResponse.json();
        const runningTasks = tasks.filter(task => task.status === 1);
        document.getElementById('running-tasks').textContent = runningTasks.length;

        const proxiesResponse = await fetch('/api/proxies/');
        const proxies = await proxiesResponse.json();
        const availableProxies = proxies.filter(proxy => proxy.status === 1);
        document.getElementById('available-proxies').textContent = availableProxies.length;

        const rawDataResponse = await fetch('/api/raw-data/stats/by-year');
        const rawDataStats = await rawDataResponse.json();
        const totalRawData = Object.values(rawDataStats).reduce((sum, count) => sum + count, 0);
        document.getElementById('total-raw-data').textContent = totalRawData;

        const sampleDataResponse = await fetch('/api/sample-data/stats/by-year');
        const sampleDataStats = await sampleDataResponse.json();
        const totalSampleData = Object.values(sampleDataStats).reduce((sum, count) => sum + count, 0);
        document.getElementById('total-sample-data').textContent = totalSampleData;

        // 绘制任务状态图表
        drawTaskStatusChart(tasks);

        // 绘制数据年份分布图表
        drawDataYearChart(rawDataStats, sampleDataStats);

    } catch (error) {
        console.error('加载仪表盘数据失败:', error);
        showNotification('加载仪表盘数据失败', 'error');
    }
}
