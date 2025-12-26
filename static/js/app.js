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
    try {
        const response = await fetch('/api/exports/export-raw-data', {
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
        const response = await fetch('/api/raw-data/clear-all', {
            method: 'DELETE',
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({})
        });

        if (response.ok) {
            const result = await response.json();
            showNotification(result.message || '所有原始数据已删除', 'success');
            loadRawData();
        } else {
            const error = await response.json();
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
function downloadExport(filename) {
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

// 编辑任务和删除任务函数已在tasks.js中定义

// 编辑账号和删除账号函数已在accounts.js中定义

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
        const response = await fetch('/api/sample-data/clear-all', {
            method: 'DELETE',
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({})
        });

        if (response.ok) {
            const result = await response.json();
            showNotification(result.message || '抽样数据已清空', 'success');
            loadSampleData();
        } else {
            const error = await response.json();
            showNotification(error.detail || '清空抽样数据失败', 'error');
        }
    } catch (error) {
        console.error('清空抽样数据失败:', error);
        showNotification('清空抽样数据失败', 'error');
    }
}
