
// 全局变量
let currentPage = {
    accounts: 1,
    tasks: 1,
    proxies: 1,
    redis_configs: 1,
    raw_data: 1,
    sample_data: 1
};

let totalPages = {
    accounts: 1,
    tasks: 1,
    proxies: 1,
    redis_configs: 1,
    raw_data: 1,
    sample_data: 1
};

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化导航
    initNavigation();

    // 初始化仪表盘
    initDashboard();

    // 初始化账号管理
    initAccounts();

    // 初始化任务管理
    initTasks();

    // 初始化代理管理
    initProxies();

    // 初始化配额管理
    initQuotas();

    // 初始化Redis配置管理
    initRedisConfigs();

    // 初始化数据管理
    initData();
});

// 导航功能
function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const pages = document.querySelectorAll('.page');

    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();

            // 移除所有活动状态
            navLinks.forEach(l => l.classList.remove('active'));
            pages.forEach(p => p.classList.remove('active'));

            // 添加活动状态
            this.classList.add('active');
            const targetId = this.getAttribute('href').substring(1);
            document.getElementById(targetId).classList.add('active');

            // 刷新对应页面数据
            switch(targetId) {
                case 'dashboard':
                    loadDashboardData();
                    break;
                case 'accounts':
                    loadAccountsData();
                    break;
                case 'tasks':
                    loadTasksData();
                    break;
                case 'proxies':
                    loadProxiesData();
                    break;
                case 'quotas':
                    loadQuotasData();
                    break;
                case 'redis-configs':
                    loadRedisConfigsData();
                    break;
                case 'data':
                    // 默认显示原始数据标签页
                    document.querySelector('[data-tab="raw-data"]').click();
                    break;
            }
        });
    });
}

// 仪表盘功能
function initDashboard() {
    loadDashboardData();
}

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

// 账号管理功能
function initAccounts() {
    // 添加账号按钮
    document.getElementById('add-account-btn').addEventListener('click', function() {
        showAccountModal();
    });

    // 分页按钮
    document.getElementById('prev-accounts-page').addEventListener('click', function() {
        if (currentPage.accounts > 1) {
            currentPage.accounts--;
            loadAccountsData();
        }
    });

    document.getElementById('next-accounts-page').addEventListener('click', function() {
        if (currentPage.accounts < totalPages.accounts) {
            currentPage.accounts++;
            loadAccountsData();
        }
    });

    // 初始加载数据
    loadAccountsData();
}

async function loadAccountsData() {
    try {
        const skip = (currentPage.accounts - 1) * 20;
        const response = await fetch(`/api/accounts/?skip=${skip}&limit=20`);
        const accounts = await response.json();

        const tbody = document.querySelector('#accounts-table tbody');
        tbody.innerHTML = '';

        accounts.forEach(account => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${account.id}</td>
                <td>${account.account_name.substring(0, 20)}...</td>
                <td>${account.status === 1 ? '正常' : '禁用'}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="editAccount(${account.id})">编辑</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteAccount(${account.id})">删除</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        // 更新分页信息
        document.getElementById('accounts-page-info').textContent = `第${currentPage.accounts}页，共${totalPages.accounts}页`;

    } catch (error) {
        console.error('加载账号数据失败:', error);
        showNotification('加载账号数据失败', 'error');
    }
}

// 任务管理功能
function initTasks() {
    // 添加任务按钮
    document.getElementById('add-task-btn').addEventListener('click', function() {
        showTaskModal();
    });

    // 分页按钮
    document.getElementById('prev-tasks-page').addEventListener('click', function() {
        if (currentPage.tasks > 1) {
            currentPage.tasks--;
            loadTasksData();
        }
    });

    document.getElementById('next-tasks-page').addEventListener('click', function() {
        if (currentPage.tasks < totalPages.tasks) {
            currentPage.tasks++;
            loadTasksData();
        }
    });

    // 初始加载数据
    loadTasksData();
}

async function loadTasksData() {
    try {
        const skip = (currentPage.tasks - 1) * 20;
        const response = await fetch(`/api/tasks/?skip=${skip}&limit=20`);
        const tasks = await response.json();

        const tbody = document.querySelector('#tasks-table tbody');
        tbody.innerHTML = '';

        tasks.forEach(task => {
            const tr = document.createElement('tr');
            const statusClass = getStatusClass(task.status);
            const statusText = getStatusText(task.status);

            tr.innerHTML = `
                <td>${task.id}</td>
                <td>${task.task_name}</td>
                <td>${task.account_name.substring(0, 20)}...</td>
                <td>${task.task_type === 'crawler' ? '爬虫' : '导出'}</td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                <td>
                    <div class="progress">
                        <div class="progress-bar" style="width: ${task.progress}%"></div>
                    </div>
                    ${task.progress}%
                </td>
                <td>${new Date(task.start_time).toLocaleString()}</td>
                <td>
                    <div class="action-buttons">
                        ${getTaskActionButtons(task)}
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });

        // 更新分页信息
        document.getElementById('tasks-page-info').textContent = `第${currentPage.tasks}页，共${totalPages.tasks}页`;

    } catch (error) {
        console.error('加载任务数据失败:', error);
        showNotification('加载任务数据失败', 'error');
    }
}

// 代理管理功能
function initProxies() {
    // 添加代理按钮
    document.getElementById('add-proxy-btn').addEventListener('click', function() {
        showProxyModal();
    });

    // 分页按钮
    document.getElementById('prev-proxies-page').addEventListener('click', function() {
        if (currentPage.proxies > 1) {
            currentPage.proxies--;
            loadProxiesData();
        }
    });

    document.getElementById('next-proxies-page').addEventListener('click', function() {
        if (currentPage.proxies < totalPages.proxies) {
            currentPage.proxies++;
            loadProxiesData();
        }
    });

    // 初始加载数据
    loadProxiesData();
}

async function loadProxiesData() {
    try {
        const skip = (currentPage.proxies - 1) * 20;
        const response = await fetch(`/api/proxies/?skip=${skip}&limit=20`);
        const proxies = await response.json();

        const tbody = document.querySelector('#proxies-table tbody');
        tbody.innerHTML = '';

        proxies.forEach(proxy => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${proxy.id}</td>
                <td>${proxy.proxy_type}</td>
                <td>${proxy.proxy_addr}</td>
                <td>${proxy.status === 1 ? '正常' : '禁用'}</td>
                <td>${proxy.strategy}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="editProxy(${proxy.id})">编辑</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteProxy(${proxy.id})">删除</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        // 更新分页信息
        document.getElementById('proxies-page-info').textContent = `第${currentPage.proxies}页，共${totalPages.proxies}页`;

    } catch (error) {
        console.error('加载代理数据失败:', error);
        showNotification('加载代理数据失败', 'error');
    }
}

// 配额管理功能
function initQuotas() {
    // 初始化配额按钮
    document.getElementById('init-quotas-btn').addEventListener('click', function() {
        if (confirm('确定要初始化配额吗？这将清空现有配额数据。')) {
            initializeQuotas();
        }
    });
    
    // 初始化配额数据
    async function initializeQuotas() {
        try {
            const response = await fetch('/api/quotas/init', {
                method: 'POST'
            });
            
            if (response.ok) {
                showNotification('配额初始化成功', 'success');
                loadQuotasData();
            } else {
                const error = await response.json();
                showNotification(error.detail || '初始化配额失败', 'error');
            }
        } catch (error) {
            console.error('初始化配额失败:', error);
            showNotification('初始化配额失败', 'error');
        }
    }

    // 添加配额按钮
    document.getElementById('add-quota-btn').addEventListener('click', function() {
        showQuotaModal();
    });

    // 初始加载数据
    loadQuotasData();
}

async function loadQuotasData() {
    try {
        const response = await fetch('/api/quotas/');
        const quotas = await response.json();

        const tbody = document.querySelector('#quotas-table tbody');
        tbody.innerHTML = '';

        quotas.forEach(quota => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${quota.start_year} - ${quota.end_year}</td>
                <td>${quota.stock_ratio}</td>
                <td>${quota.sample_num}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="editQuota(${quota.id})">编辑</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteQuota(${quota.id})">删除</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

    } catch (error) {
        console.error('加载配额数据失败:', error);
        showNotification('加载配额数据失败', 'error');
    }
}

// 数据管理功能
function initData() {
    // 初始化选项卡
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // 移除所有活动状态
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            // 添加活动状态
            this.classList.add('active');
            const tabId = this.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');

            // 加载对应数据
            if (tabId === 'raw-data') {
                loadRawData();
                loadTaskOptions('raw-data-task-filter');
            } else if (tabId === 'sample-data') {
                loadSampleData();
                loadTaskOptions('sample-data-task-filter');
            } else if (tabId === 'exports') {
                loadExports();
            }
        });
    });
    
    // 初始加载任务选项
    loadTaskOptions('raw-data-task-filter');
    loadTaskOptions('sample-data-task-filter');

    // 导出抽样数据按钮
    document.getElementById('export-sample-data-btn').addEventListener('click', function() {
        exportSampleData();
    });

    // 导出原始数据按钮
    document.getElementById('export-raw-data-btn').addEventListener('click', function() {
        exportRawData();
    });

    // 抽样数据按钮
    document.getElementById('sample-data-btn').addEventListener('click', function() {
        if (confirm('确定要按配额抽样数据吗？这将清空现有抽样数据。')) {
            sampleData();
        }
    });

    // 清空抽样数据按钮
    document.getElementById('clear-sample-data-btn').addEventListener('click', function() {
        if (confirm('确定要清空抽样数据吗？')) {
            clearSampleData();
        }
    });

    // 导入JSON数据按钮
    document.getElementById('import-json-btn').addEventListener('click', function() {
        showImportJsonModal();
    });

    // 全部删除原始数据按钮
    document.getElementById('delete-all-raw-data-btn').addEventListener('click', function() {
        deleteAllRawData();
    });

    // 原始数据分页按钮
    document.getElementById('prev-raw-data-page').addEventListener('click', function() {
        if (currentPage.raw_data > 1) {
            currentPage.raw_data--;
            loadRawData();
        }
    });

    document.getElementById('next-raw-data-page').addEventListener('click', function() {
        if (currentPage.raw_data < totalPages.raw_data) {
            currentPage.raw_data++;
            loadRawData();
        }
    });

    // 抽样数据分页按钮
    document.getElementById('prev-sample-data-page').addEventListener('click', function() {
        if (currentPage.sample_data > 1) {
            currentPage.sample_data--;
            loadSampleData();
        }
    });

    document.getElementById('next-sample-data-page').addEventListener('click', function() {
        if (currentPage.sample_data < totalPages.sample_data) {
            currentPage.sample_data++;
            loadSampleData();
        }
    });

    // 初始加载原始数据
    loadRawData();
}

// 导出抽样数据
async function exportSampleData() {
    try {
        const response = await fetch('/api/exports/export-sample-data', {
            method: 'POST'
        });

        if (response.ok) {
            showNotification('导出任务已启动', 'success');
            // 定期检查导出状态
            const checkInterval = setInterval(async () => {
                const exportsResponse = await fetch('/api/exports/');
                const exports = await exportsResponse.json();
                
                // 检查是否有新的导出文件
                if (exports.length > 0) {
                    clearInterval(checkInterval);
                    showNotification('导出完成', 'success');
                    loadExports();
                }
            }, 5000);
        } else {
            const error = await response.json();
            showNotification(error.detail || '导出失败', 'error');
        }
    } catch (error) {
        console.error('导出失败:', error);
        showNotification('导出失败', 'error');
    }
}

// 导出原始数据
async function exportRawData() {
    console.log('导出原始数据按钮被点击');
    try {
        console.log('开始发送API请求');
        const response = await fetch('/api/exports/export-raw-data', {
            method: 'POST'
        });
        console.log('API请求已发送，响应状态:', response.status);

        if (response.ok) {
            showNotification('导出任务已启动', 'success');
            // 定期检查导出状态
            const checkInterval = setInterval(async () => {
                const exportsResponse = await fetch('/api/exports/');
                const exports = await exportsResponse.json();

                // 检查是否有新的导出文件
                if (exports.length > 0) {
                    clearInterval(checkInterval);
                    showNotification('导出完成', 'success');
                    loadExports();
                }
            }, 5000);
        } else {
            const error = await response.json();
            showNotification(error.detail || '导出失败', 'error');
        }
    } catch (error) {
        console.error('导出失败:', error);
        showNotification('导出失败', 'error');
    }
}

// 导出抽样数据
async function exportSampleData() {
    try {
        const response = await fetch('/api/exports/export-sample-data', {
            method: 'POST'
        });

        if (response.ok) {
            showNotification('导出任务已启动', 'success');
            // 定期检查导出状态
            const checkInterval = setInterval(async () => {
                const exportsResponse = await fetch('/api/exports/');
                const exports = await exportsResponse.json();
                
                // 检查是否有新的导出文件
                if (exports.length > 0) {
                    clearInterval(checkInterval);
                    showNotification('导出完成', 'success');
                    loadExports();
                }
            }, 5000);
        } else {
            const error = await response.json();
            showNotification(error.detail || '导出失败', 'error');
        }
    } catch (error) {
        console.error('导出失败:', error);
        showNotification('导出失败', 'error');
    }
}

// 加载任务选项
async function loadTaskOptions(selectId) {
    try {
        const response = await fetch('/api/tasks/');
        const tasks = await response.json();
        
        const select = document.getElementById(selectId);
        select.innerHTML = '<option value="">所有任务</option>';
        
        tasks.forEach(task => {
            const option = document.createElement('option');
            option.value = task.id;
            option.textContent = `${task.id} - ${task.task_name}`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('加载任务选项失败:', error);
    }
}

// 删除原始数据
async function deleteRawData(dataId) {
    if (!confirm('确定要删除这条原始数据吗？')) {
        return;
    }

    try {
        const response = await fetch(`/api/raw-data/${dataId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showNotification('原始数据删除成功', 'success');
            loadRawData();
        } else {
            const error = await response.json();
            showNotification(error.detail || '删除原始数据失败', 'error');
        }
    } catch (error) {
        console.error('删除原始数据失败:', error);
        showNotification('删除原始数据失败', 'error');
    }
}

// 删除所有原始数据
async function deleteAllRawData() {
    if (!confirm('确定要删除所有原始数据吗？此操作不可恢复！')) {
        return;
    }

    try {
        console.log('发送删除所有原始数据请求...');
        const response = await fetch('/api/raw-data/clear-all', {
            method: 'DELETE',
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({})
        });
        console.log('响应状态:', response.status);

        if (response.ok) {
            const result = await response.json();
            showNotification(result.message || '所有原始数据已删除', 'success');
            loadRawData();
        } else {
            const error = await response.json();
            console.error('删除所有原始数据失败，错误详情:', error);
            showNotification(error.detail || '删除所有原始数据失败', 'error');
        }
    } catch (error) {
        console.error('删除所有原始数据失败:', error);
        showNotification('删除所有原始数据失败', 'error');
    }
}

// 查看原始数据
async function viewRawData(dataId) {
    try {
        const response = await fetch(`/api/raw-data/${dataId}`);
        const data = await response.json();
        
        let content = `
            <div class="data-view">
                <h3>原始数据详情</h3>
                <div class="data-field">
                    <label>ID:</label>
                    <span>${data.id}</span>
                </div>
                <div class="data-field">
                    <label>标题:</label>
                    <span>${data.title || '无'}</span>
                </div>
                <div class="data-field">
                    <label>作者:</label>
                    <span>${data.author || '无'}</span>
                </div>
                <div class="data-field">
                    <label>发布时间:</label>
                    <span>${data.publish_time || '无'}</span>
                </div>
                <div class="data-field">
                    <label>年份:</label>
                    <span>${data.year}</span>
                </div>
                <div class="data-field">
                    <label>任务ID:</label>
                    <span>${data.task_id}</span>
                </div>
                <div class="data-field">
                    <label>回答链接:</label>
                    <a href="${data.answer_url}" target="_blank">${data.answer_url}</a>
                </div>
                <div class="data-field">
                    <label>内容:</label>
                    <div class="data-content">${data.content ? data.content.substring(0, 500) + (data.content.length > 500 ? '...' : '') : '无'}</div>
                </div>
            </div>
        `;
        
        createModal('查看原始数据', content, [
            {
                text: '关闭',
                className: 'btn',
                onclick: closeModal
            }
        ]);
    } catch (error) {
        console.error('查看原始数据失败:', error);
        showNotification('查看原始数据失败', 'error');
    }
}

// 查看抽样数据
async function viewSampleData(dataId) {
    try {
        const response = await fetch(`/api/sample-data/${dataId}`);
        const data = await response.json();
        
        let content = `
            <div class="data-view">
                <h3>抽样数据详情</h3>
                <div class="data-field">
                    <label>ID:</label>
                    <span>${data.id}</span>
                </div>
                <div class="data-field">
                    <label>标题:</label>
                    <span>${data.title || '无'}</span>
                </div>
                <div class="data-field">
                    <label>作者:</label>
                    <span>${data.author || '无'}</span>
                </div>
                <div class="data-field">
                    <label>发布时间:</label>
                    <span>${data.publish_time || '无'}</span>
                </div>
                <div class="data-field">
                    <label>年份:</label>
                    <span>${data.year}</span>
                </div>
                <div class="data-field">
                    <label>任务ID:</label>
                    <span>${data.task_id}</span>
                </div>
                <div class="data-field">
                    <label>回答链接:</label>
                    <a href="${data.answer_url}" target="_blank">${data.answer_url}</a>
                </div>
                <div class="data-field">
                    <label>内容:</label>
                    <div class="data-content">${data.content ? data.content.substring(0, 500) + (data.content.length > 500 ? '...' : '') : '无'}</div>
                </div>
            </div>
        `;
        
        createModal('查看抽样数据', content, [
            {
                text: '关闭',
                className: 'btn',
                onclick: closeModal
            }
        ]);
    } catch (error) {
        console.error('查看抽样数据失败:', error);
        showNotification('查看抽样数据失败', 'error');
    }
}

async function loadRawData() {
    try {
        const yearFilter = document.getElementById('raw-data-year-filter').value;
        const taskFilter = document.getElementById('raw-data-task-filter').value;

        let url = `/api/raw-data/?skip=${(currentPage.raw_data - 1) * 20}&limit=20`;
        if (yearFilter) url += `&year=${yearFilter}`;
        if (taskFilter) url += `&task_id=${taskFilter}`;

        const response = await fetch(url);
        const rawData = await response.json();

        const tbody = document.querySelector('#raw-data-table tbody');
        tbody.innerHTML = '';

        rawData.forEach(data => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${data.id}</td>
                <td>${data.title ? data.title.substring(0, 50) + '...' : ''}</td>
                <td>${data.author || ''}</td>
                <td>${data.publish_time || ''}</td>
                <td>${data.year}</td>
                <td>${data.task_id}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="viewRawData(${data.id})">查看</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteRawData(${data.id})">删除</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        // 更新分页信息
        document.getElementById('raw-data-page-info').textContent = `第${currentPage.raw_data}页，共${totalPages.raw_data}页`;

    } catch (error) {
        console.error('加载原始数据失败:', error);
        showNotification('加载原始数据失败', 'error');
    }
}

async function loadSampleData() {
    try {
        const yearFilter = document.getElementById('sample-data-year-filter').value;
        const taskFilter = document.getElementById('sample-data-task-filter').value;

        let url = `/api/sample-data/?skip=${(currentPage.sample_data - 1) * 20}&limit=20`;
        if (yearFilter) url += `&year=${yearFilter}`;
        if (taskFilter) url += `&task_id=${taskFilter}`;

        const response = await fetch(url);
        const sampleData = await response.json();

        const tbody = document.querySelector('#sample-data-table tbody');
        tbody.innerHTML = '';

        sampleData.forEach(data => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${data.id}</td>
                <td>${data.title ? data.title.substring(0, 50) + '...' : ''}</td>
                <td>${data.author || ''}</td>
                <td>${data.publish_time || ''}</td>
                <td>${data.year}</td>
                <td>${data.task_id}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="viewSampleData(${data.id})">查看</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteSampleData(${data.id})">删除</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        // 更新分页信息
        document.getElementById('sample-data-page-info').textContent = `第${currentPage.sample_data}页，共${totalPages.sample_data}页`;

    } catch (error) {
        console.error('加载抽样数据失败:', error);
        showNotification('加载抽样数据失败', 'error');
    }
}

async function loadExports() {
    try {
        const response = await fetch('/api/exports/');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const exports = await response.json();
        
        // 确保exports是一个数组
        if (!Array.isArray(exports)) {
            console.error('导出文件数据不是数组格式:', exports);
            showNotification('导出文件数据格式错误', 'error');
            return;
        }

        const tbody = document.querySelector('#exports-table tbody');
        tbody.innerHTML = '';

        exports.forEach(exportFile => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${exportFile.filename}</td>
                <td>${formatFileSize(exportFile.size)}</td>
                <td>${exportFile.created_time}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="downloadExport('${exportFile.filename}')">下载</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteExport('${exportFile.filename}')">删除</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

    } catch (error) {
        console.error('加载导出文件失败:', error);
        showNotification('加载导出文件失败', 'error');
    }
}

// 下载导出文件
async function downloadExport(filename) {
    try {
        window.open(`/api/exports/download/${filename}`, '_blank');
    } catch (error) {
        console.error('下载文件失败:', error);
        showNotification('下载文件失败', 'error');
    }
}

// 删除导出文件
async function deleteExport(filename) {
    if (!confirm(`确定要删除文件 ${filename} 吗？`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/exports/delete/${filename}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('文件删除成功', 'success');
            loadExports();
        } else {
            const error = await response.json();
            showNotification(error.detail || '删除失败', 'error');
        }
    } catch (error) {
        console.error('删除文件失败:', error);
        showNotification('删除文件失败', 'error');
    }
}

// 编辑任务
function editTask(taskId) {
    showTaskModal(taskId);
}

// 删除任务
async function deleteTask(taskId) {
    if (!confirm('确定要删除这个任务吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/tasks/${taskId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('任务删除成功', 'success');
            loadTasksData();
        } else {
            const error = await response.json();
            showNotification(error.detail || '删除任务失败', 'error');
        }
    } catch (error) {
        console.error('删除任务失败:', error);
        showNotification('删除任务失败', 'error');
    }
}

// 编辑代理
function editProxy(proxyId) {
    showProxyModal(proxyId);
}

// 删除代理
async function deleteProxy(proxyId) {
    if (!confirm('确定要删除这个代理吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/proxies/${proxyId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('代理删除成功', 'success');
            loadProxiesData();
        } else {
            const error = await response.json();
            showNotification(error.detail || '删除代理失败', 'error');
        }
    } catch (error) {
        console.error('删除代理失败:', error);
        showNotification('删除代理失败', 'error');
    }
}

// 编辑配额
function editQuota(quotaId) {
    showQuotaModal(quotaId);
}

// 删除配额
async function deleteQuota(quotaId) {
  try {
    // 获取配额信息
    const getResponse = await fetch(`/api/quotas/${quotaId}`);
    if (!getResponse.ok) throw new Error('获取配额信息失败');
    
    const quota = await getResponse.json();
    // 确认删除
    const confirmMessage = `确定要删除以下配额吗？\n\n` +
      `年份范围: ${quota.start_year} - ${quota.end_year}\n` +
      `存量占比: ${quota.stock_ratio}\n` +
      `抽样条数: ${quota.sample_num}`;
    if (!confirm(confirmMessage)) return;

    // 执行删除
    const delResponse = await fetch(`/api/quotas/${quotaId}`, { method: 'DELETE' });
    if (delResponse.ok) {
      showNotification(`配额 ${quota.start_year}-${quota.end_year} 删除成功`, 'success');
      loadQuotasData();
    } else {
      const error = await delResponse.json().catch(() => ({ detail: '删除配额失败' }));
      showNotification(error.detail || '删除配额失败', 'error');
    }
  } catch (error) {
    console.error('操作失败:', error);
    showNotification(error.message || '操作失败', 'error');
  }
}
// 编辑账号
function editAccount(accountId) {
    showAccountModal(accountId);
}

// 删除账号
async function deleteAccount(accountId) {
    if (!confirm('确定要删除这个账号吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/accounts/${accountId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('账号删除成功', 'success');
            loadAccountsData();
        } else {
            const error = await response.json();
            showNotification(error.detail || '删除账号失败', 'error');
        }
    } catch (error) {
        console.error('删除账号失败:', error);
        showNotification('删除账号失败', 'error');
    }
}

// 根据状态文本获取状态值
function getStatusValue(statusText) {
    switch(statusText) {
        case '未开始': return 0;
        case '运行中': return 1;
        case '已暂停': return 2;
        case '已完成': return 3;
        case '已停止': return 4;
        case '失败': return 5;
        default: return 0;
    }
}

// 获取任务操作按钮
function getTaskActionButtons(task) {
    let buttons = '';
    
    // 兜底方案：始终显示启动、停止、编辑和删除按钮
    buttons += `<button class="btn btn-sm btn-success" onclick="startTask(${task.id})">启动</button>`;
    buttons += `<button class="btn btn-sm btn-danger" onclick="stopTask(${task.id})">停止</button>`;
    buttons += `<button class="btn btn-sm btn-primary" onclick="editTask(${task.id})">编辑</button>`;
    buttons += `<button class="btn btn-sm btn-danger" onclick="deleteTask(${task.id})">删除</button>`;
    
    return buttons;
}

// 工具函数
function getStatusClass(status) {
    switch(status) {
        case 0: return 'status-waiting';
        case 1: return 'status-running';
        case 2: return 'status-paused';
        case 3: return 'status-failed';
        case 4: return 'status-completed';
        default: return '';
    }
}

function getStatusText(status) {
    switch(status) {
        case 0: return '等待';
        case 1: return '运行中';
        case 2: return '暂停';
        case 3: return '失败';
        case 4: return '完成';
        default: return '';
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    // 添加到页面
    document.body.appendChild(notification);

    // 显示动画
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);

    // 自动隐藏
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// 任务操作函数
async function startTask(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            showNotification('任务启动成功', 'success');
            loadTasksData();
        } else {
            const error = await response.json();
            showNotification(error.detail || '任务启动失败', 'error');
        }
    } catch (error) {
        console.error('启动任务失败:', error);
        showNotification('启动任务失败', 'error');
    }
}

async function pauseTask(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/pause`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            showNotification('任务暂停成功', 'success');
            loadTasksData();
        } else {
            const error = await response.json();
            showNotification(error.detail || '任务暂停失败', 'error');
        }
    } catch (error) {
        console.error('暂停任务失败:', error);
        showNotification('暂停任务失败', 'error');
    }
}

async function resumeTask(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/resume`, {
            method: 'POST'
        });

        if (response.ok) {
            showNotification('任务恢复成功', 'success');
            loadTasksData();
        } else {
            const error = await response.json();
            showNotification(error.detail || '任务恢复失败', 'error');
        }
    } catch (error) {
        console.error('恢复任务失败:', error);
        showNotification('恢复任务失败', 'error');
    }
}

async function stopTask(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/stop`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            showNotification('任务停止成功', 'success');
            loadTasksData();
        } else {
            const error = await response.json();
            showNotification(error.detail || '任务停止失败', 'error');
        }
    } catch (error) {
        console.error('停止任务失败:', error);
        showNotification('停止任务失败', 'error');
    }
}

// 抽样数据操作函数
async function sampleData() {
    try {
        const response = await fetch('/api/sample-data/sample', {
            method: 'POST'
        });

        if (response.ok) {
            showNotification('抽样任务已启动', 'success');
            // 定期检查抽样状态
            const checkInterval = setInterval(async () => {
                const statsResponse = await fetch('/api/sample-data/stats/by-year');
                const stats = await statsResponse.json();
                const total = Object.values(stats).reduce((sum, count) => sum + count, 0);

                if (total > 0) {
                    clearInterval(checkInterval);
                    showNotification('抽样完成', 'success');
                    loadSampleData();
                }
            }, 5000);
        } else {
            const error = await response.json();
            showNotification(error.detail || '抽样失败', 'error');
        }
    } catch (error) {
        console.error('抽样失败:', error);
        showNotification('抽样失败', 'error');
    }
}

async function deleteSampleData(id) {
    if (!confirm('确定要删除这条抽样数据吗？此操作不可恢复！')) {
        return;
    }

    try {
        const response = await fetch(`/api/sample-data/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showNotification('抽样数据删除成功', 'success');
            loadSampleData();
        } else {
            const error = await response.json();
            showNotification(error.detail || '删除抽样数据失败', 'error');
        }
    } catch (error) {
        console.error('删除抽样数据失败:', error);
        showNotification('删除抽样数据失败', 'error');
    }
}

async function clearSampleData() {
    try {
        console.log('发送清空抽样数据请求...');
        const response = await fetch('/api/sample-data/clear-all', {
            method: 'DELETE',
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({})
        });
        console.log('响应状态:', response.status);

        if (response.ok) {
            const result = await response.json();
            showNotification(result.message || '抽样数据已清空', 'success');
            loadSampleData();
        } else {
            const error = await response.json();
            console.error('删除所有抽样数据失败，错误详情:', error);
            showNotification(error.detail || '清空抽样数据失败', 'error');
        }
    } catch (error) {
        console.error('清空抽样数据失败:', error);
        showNotification('清空抽样数据失败', 'error');
    }
}

// 图表绘制函数
function drawTaskStatusChart(tasks) {
    const canvas = document.getElementById('task-status-chart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // 统计各状态任务数量
    const statusCounts = {
        0: 0, // 等待
        1: 0, // 运行中
        2: 0, // 暂停
        3: 0, // 失败
        4: 0  // 完成
    };

    tasks.forEach(task => {
        statusCounts[task.status]++;
    });

    // 准备图表数据
    const data = [
        { label: '等待', value: statusCounts[0], color: '#6c757d' },
        { label: '运行中', value: statusCounts[1], color: '#28a745' },
        { label: '暂停', value: statusCounts[2], color: '#ffc107' },
        { label: '失败', value: statusCounts[3], color: '#dc3545' },
        { label: '完成', value: statusCounts[4], color: '#17a2b8' }
    ];

    // 绘制饼图
    drawPieChart(ctx, canvas.width, canvas.height, data);
}

function drawDataYearChart(rawDataStats, sampleDataStats) {
    const canvas = document.getElementById('data-year-chart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // 准备数据
    const years = [];
    const rawDataCounts = [];
    const sampleDataCounts = [];

    // 获取所有年份
    const allYears = new Set([
        ...Object.keys(rawDataStats),
        ...Object.keys(sampleDataStats)
    ]);

    // 排序年份
    Array.from(allYears).sort().forEach(year => {
        years.push(year);
        rawDataCounts.push(rawDataStats[year] || 0);
        sampleDataCounts.push(sampleDataStats[year] || 0);
    });

    // 绘制柱状图
    drawBarChart(ctx, canvas.width, canvas.height, years, rawDataCounts, sampleDataCounts);
}

function drawPieChart(ctx, width, height, data) {
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 2 - 20;

    let total = data.reduce((sum, item) => sum + item.value, 0);
    let currentAngle = -Math.PI / 2;

    // 绘制扇形
    data.forEach(item => {
        if (item.value === 0) return;

        const sliceAngle = (item.value / total) * 2 * Math.PI;

        // 绘制扇形
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
        ctx.lineTo(centerX, centerY);
        ctx.fillStyle = item.color;
        ctx.fill();

        // 绘制标签
        const labelAngle = currentAngle + sliceAngle / 2;
        const labelX = centerX + Math.cos(labelAngle) * (radius * 0.7);
        const labelY = centerY + Math.sin(labelAngle) * (radius * 0.7);

        ctx.fillStyle = '#fff';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        if (item.value > 0) {
            ctx.fillText(`${item.label}: ${item.value}`, labelX, labelY);
        }

        currentAngle += sliceAngle;
    });

    // 绘制图例
    let legendY = 20;
    data.forEach(item => {
        ctx.fillStyle = item.color;
        ctx.fillRect(10, legendY, 15, 15);

        ctx.fillStyle = '#333';
        ctx.font = '12px Arial';
        ctx.textAlign = 'left';
        ctx.fillText(`${item.label}: ${item.value}`, 30, legendY + 12);

        legendY += 25;
    });
}

function drawBarChart(ctx, width, height, labels, data1, data2) {
    const padding = 40;
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;

    const barWidth = chartWidth / (labels.length * 2 + labels.length + 1);
    const maxValue = Math.max(...data1, ...data2);

    // 绘制坐标轴
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, height - padding);
    ctx.lineTo(width - padding, height - padding);
    ctx.strokeStyle = '#333';
    ctx.stroke();

    // 绘制Y轴刻度
    const ySteps = 5;
    for (let i = 0; i <= ySteps; i++) {
        const y = padding + (chartHeight / ySteps) * i;
        const value = Math.round(maxValue * (1 - i / ySteps));

        ctx.beginPath();
        ctx.moveTo(padding - 5, y);
        ctx.lineTo(padding, y);
        ctx.strokeStyle = '#333';
        ctx.stroke();

        ctx.fillStyle = '#333';
        ctx.font = '12px Arial';
        ctx.textAlign = 'right';
        ctx.textBaseline = 'middle';
        ctx.fillText(value, padding - 10, y);
    }

    // 绘制柱状图
    labels.forEach((label, index) => {
        const x = padding + barWidth + index * (barWidth * 2 + barWidth);

        // 原始数据柱
        const height1 = (data1[index] / maxValue) * chartHeight;
        ctx.fillStyle = '#3498db';
        ctx.fillRect(x, height - padding - height1, barWidth, height1);

        // 抽样数据柱
        const height2 = (data2[index] / maxValue) * chartHeight;
        ctx.fillStyle = '#2ecc71';
        ctx.fillRect(x + barWidth, height - padding - height2, barWidth, height2);

        // X轴标签
        ctx.fillStyle = '#333';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText(label, x + barWidth, height - padding + 5);
    });

    // 绘制图例
    ctx.fillStyle = '#3498db';
    ctx.fillRect(width - 150, 20, 15, 15);
    ctx.fillStyle = '#333';
    ctx.font = '12px Arial';
    ctx.textAlign = 'left';
    ctx.fillText('原始数据', width - 130, 32);

    ctx.fillStyle = '#2ecc71';
    ctx.fillRect(width - 150, 45, 15, 15);
    ctx.fillStyle = '#333';
    ctx.fillText('抽样数据', width - 130, 57);
}

// Redis配置管理功能
function initRedisConfigs() {
    loadRedisConfigsData();
    
    // 添加配置按钮
    document.getElementById('add-redis-config-btn').addEventListener('click', showAddRedisConfigModal);
    
    // 重新加载配置按钮
    document.getElementById('reload-redis-btn').addEventListener('click', reloadRedisConfig);
    
    // 分页按钮
    document.getElementById('prev-redis-configs-page').addEventListener('click', () => {
        if (currentPage.redis_configs > 1) {
            currentPage.redis_configs--;
            loadRedisConfigsData();
        }
    });
    
    document.getElementById('next-redis-configs-page').addEventListener('click', () => {
        if (currentPage.redis_configs < totalPages.redis_configs) {
            currentPage.redis_configs++;
            loadRedisConfigsData();
        }
    });
}

async function loadRedisConfigsData() {
    try {
        const response = await fetch('/api/redis-configs/');
        const configs = await response.json();
        
        // 更新分页信息
        totalPages.redis_configs = Math.ceil(configs.length / 10) || 1;
        document.getElementById('redis-configs-page-info').textContent = 
            `第${currentPage.redis_configs}页，共${totalPages.redis_configs}页`;
        
        // 计算当前页的数据
        const startIndex = (currentPage.redis_configs - 1) * 10;
        const endIndex = startIndex + 10;
        const pageData = configs.slice(startIndex, endIndex);
        
        // 渲染表格
        const tbody = document.querySelector('#redis-configs-table tbody');
        tbody.innerHTML = '';
        
        pageData.forEach(config => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${config.id}</td>
                <td>${config.name}</td>
                <td>${config.host}</td>
                <td>${config.port}</td>
                <td>${config.db}</td>
                <td>${config.password ? '******' : '无'}</td>
                <td>${config.is_default ? '是' : '否'}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="testRedisConnection(${config.id})">测试</button>
                    <button class="btn btn-sm btn-secondary" onclick="showEditRedisConfigModal(${config.id})">编辑</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteRedisConfig(${config.id})">删除</button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('加载Redis配置失败:', error);
        showNotification('加载Redis配置失败', 'error');
    }
}

function showAddRedisConfigModal() {
    const modalBody = document.getElementById('modal-body');
    modalBody.innerHTML = `
        <h3>添加Redis配置</h3>
        <form id="add-redis-config-form">
            <div class="form-group">
                <label for="name">配置名称</label>
                <input type="text" id="name" name="name" required>
            </div>
            <div class="form-group">
                <label for="host">主机地址</label>
                <input type="text" id="host" name="host" value="127.0.0.1" required>
            </div>
            <div class="form-group">
                <label for="port">端口</label>
                <input type="number" id="port" name="port" value="6379" required>
            </div>
            <div class="form-group">
                <label for="db">数据库</label>
                <input type="number" id="db" name="db" value="0" required>
            </div>
            <div class="form-group">
                <label for="password">密码</label>
                <input type="password" id="password" name="password">
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="is_default" name="is_default"> 设为默认配置
                </label>
            </div>
            <div class="form-actions">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">取消</button>
                <button type="button" class="btn btn-info" onclick="testCurrentRedisConfig()">测试连接</button>
                <button type="submit" class="btn btn-primary">保存</button>
            </div>
        </form>
    `;
    
    // 绑定表单提交事件
    document.getElementById('add-redis-config-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        await addRedisConfig();
    });
    
    // 显示模态框
    document.getElementById('modal').style.display = 'block';
}

async function addRedisConfig() {
    const form = document.getElementById('add-redis-config-form');
    const formData = new FormData(form);
    
    const config = {
        name: formData.get('name'),
        host: formData.get('host'),
        port: parseInt(formData.get('port')),
        db: parseInt(formData.get('db')),
        password: formData.get('password') || null,
        is_default: formData.get('is_default') === 'on'
    };
    
    try {
        const response = await fetch('/api/redis-configs/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        if (response.ok) {
            showNotification('Redis配置添加成功', 'success');
            closeModal();
            loadRedisConfigsData();
        } else {
            const error = await response.json();
            showNotification(`添加失败: ${error.detail || '未知错误'}`, 'error');
        }
    } catch (error) {
        console.error('添加Redis配置失败:', error);
        showNotification('添加Redis配置失败', 'error');
    }
}

async function showEditRedisConfigModal(configId) {
    try {
        const response = await fetch(`/api/redis-configs/`);
        const configs = await response.json();
        const config = configs.find(c => c.id === configId);
        
        if (!config) {
            showNotification('Redis配置不存在', 'error');
            return;
        }
        
        const modalBody = document.getElementById('modal-body');
        modalBody.innerHTML = `
            <h3>编辑Redis配置</h3>
            <form id="edit-redis-config-form">
                <div class="form-group">
                    <label for="name">配置名称</label>
                    <input type="text" id="name" name="name" value="${config.name}" required>
                </div>
                <div class="form-group">
                    <label for="host">主机地址</label>
                    <input type="text" id="host" name="host" value="${config.host}" required>
                </div>
                <div class="form-group">
                    <label for="port">端口</label>
                    <input type="number" id="port" name="port" value="${config.port}" required>
                </div>
                <div class="form-group">
                    <label for="db">数据库</label>
                    <input type="number" id="db" name="db" value="${config.db}" required>
                </div>
                <div class="form-group">
                    <label for="password">密码</label>
                    <input type="password" id="password" name="password" placeholder="留空表示不修改">
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="is_default" name="is_default" ${config.is_default ? 'checked' : ''}> 设为默认配置
                    </label>
                </div>
                <div class="form-actions">
                    <button type="button" class="btn btn-secondary" onclick="closeModal()">取消</button>
                    <button type="button" class="btn btn-info" onclick="testCurrentRedisConfig()">测试连接</button>
                    <button type="submit" class="btn btn-primary">保存</button>
                </div>
            </form>
        `;
        
        // 绑定表单提交事件
        document.getElementById('edit-redis-config-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            await updateRedisConfig(configId);
        });
        
        // 显示模态框
        document.getElementById('modal').style.display = 'block';
    } catch (error) {
        console.error('获取Redis配置失败:', error);
        showNotification('获取Redis配置失败', 'error');
    }
}

async function updateRedisConfig(configId) {
    const form = document.getElementById('edit-redis-config-form');
    const formData = new FormData(form);
    
    const config = {};
    
    // 只包含修改的字段
    if (formData.get('name')) config.name = formData.get('name');
    if (formData.get('host')) config.host = formData.get('host');
    if (formData.get('port')) config.port = parseInt(formData.get('port'));
    if (formData.get('db')) config.db = parseInt(formData.get('db'));
    if (formData.get('password')) config.password = formData.get('password');
    config.is_default = formData.get('is_default') === 'on';
    
    try {
        const response = await fetch(`/api/redis-configs/${configId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        if (response.ok) {
            showNotification('Redis配置更新成功', 'success');
            closeModal();
            loadRedisConfigsData();
        } else {
            const error = await response.json();
            showNotification(`更新失败: ${error.detail || '未知错误'}`, 'error');
        }
    } catch (error) {
        console.error('更新Redis配置失败:', error);
        showNotification('更新Redis配置失败', 'error');
    }
}

async function deleteRedisConfig(configId) {
    if (!confirm('确定要删除此Redis配置吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/redis-configs/${configId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('Redis配置删除成功', 'success');
            loadRedisConfigsData();
        } else {
            const error = await response.json();
            showNotification(`删除失败: ${error.detail || '未知错误'}`, 'error');
        }
    } catch (error) {
        console.error('删除Redis配置失败:', error);
        showNotification('删除Redis配置失败', 'error');
    }
}

async function testRedisConnection(configId) {
    try {
        const response = await fetch('/api/redis-configs/');
        const configs = await response.json();
        const config = configs.find(c => c.id === configId);
        
        if (!config) {
            showNotification('Redis配置不存在', 'error');
            return;
        }
        
        const testResponse = await fetch('/api/redis-configs/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                host: config.host,
                port: config.port,
                db: config.db,
                password: config.password
            })
        });
        
        const result = await testResponse.json();
        
        if (result.success) {
            showNotification('Redis连接测试成功', 'success');
        } else {
            showNotification(`Redis连接测试失败: ${result.message}`, 'error');
        }
    } catch (error) {
        console.error('测试Redis连接失败:', error);
        showNotification('测试Redis连接失败', 'error');
    }
}

async function testCurrentRedisConfig() {
    const form = document.querySelector('#modal-body form');
    const formData = new FormData(form);
    
    const config = {
        host: formData.get('host'),
        port: parseInt(formData.get('port')),
        db: parseInt(formData.get('db')),
        password: formData.get('password') || null
    };
    
    try {
        const response = await fetch('/api/redis-configs/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Redis连接测试成功', 'success');
        } else {
            showNotification(`Redis连接测试失败: ${result.message}`, 'error');
        }
    } catch (error) {
        console.error('测试Redis连接失败:', error);
        showNotification('测试Redis连接失败', 'error');
    }
}

async function reloadRedisConfig() {
    try {
        const response = await fetch('/api/system/reload-redis', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Redis配置重新加载成功', 'success');
            loadRedisConfigsData();
        } else {
            showNotification(`Redis配置重新加载失败: ${result.message}`, 'error');
        }
    } catch (error) {
        console.error('重新加载Redis配置失败:', error);
        showNotification('重新加载Redis配置失败', 'error');
    }
}