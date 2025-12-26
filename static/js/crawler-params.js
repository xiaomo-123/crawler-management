// 爬虫参数管理模块

// 初始化爬虫参数管理
function initCrawlerParams() {
    // 添加爬虫参数按钮
    document.getElementById('add-crawler-param-btn').addEventListener('click', function() {
        showCrawlerParamModal();
    });

    // 分页按钮
    document.getElementById('prev-crawler-params-page').addEventListener('click', function() {
        if (currentPage.crawler_params > 1) {
            currentPage.crawler_params--;
            loadCrawlerParamsData();
        }
    });

    document.getElementById('next-crawler-params-page').addEventListener('click', function() {
        if (currentPage.crawler_params < totalPages.crawler_params) {
            currentPage.crawler_params++;
            loadCrawlerParamsData();
        }
    });

    // 初始加载数据
    loadCrawlerParamsData();
}

// 加载爬虫参数数据
async function loadCrawlerParamsData() {
    try {
        const skip = (currentPage.crawler_params - 1) * 20;
        const response = await fetch(`/api/crawler-params/?skip=${skip}&limit=20`);
        const params = await response.json();

        const tbody = document.querySelector('#crawler-params-table tbody');
        tbody.innerHTML = '';

        params.forEach(param => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${param.id}</td>
                <td>${param.url.substring(0, 50)}...</td>
                <td>${param.task_type}</td>
                <td>${param.start_time || '不限'}</td>
                <td>${param.end_time || '不限'}</td>
                <td>${param.interval_time}小时</td>
                <td>${param.error_count}次</td>
                <td>${param.restart_browser_time}小时</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="editCrawlerParam(${param.id})">编辑</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteCrawlerParam(${param.id})">删除</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        // 更新分页信息
        document.getElementById('crawler-params-page-info').textContent = `第${currentPage.crawler_params}页，共${totalPages.crawler_params}页`;

    } catch (error) {
        console.error('加载爬虫参数数据失败:', error);
        showNotification('加载爬虫参数数据失败', 'error');
    }
}

// 编辑爬虫参数
function editCrawlerParam(paramId) {
    showCrawlerParamModal(paramId);
}

// 删除爬虫参数
async function deleteCrawlerParam(paramId) {
    if (!confirm('确定要删除这个爬虫参数吗？')) {
        return;
    }

    try {
        const response = await fetch(`/api/crawler-params/${paramId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showNotification('爬虫参数删除成功', 'success');
            loadCrawlerParamsData();
        } else {
            const error = await response.json();
            showNotification(error.detail || '删除爬虫参数失败', 'error');
        }
    } catch (error) {
        console.error('删除爬虫参数失败:', error);
        showNotification('删除爬虫参数失败', 'error');
    }
}
