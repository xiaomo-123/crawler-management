
// 模态框相关功能

// 创建模态框
function createModal(title, content, footerButtons) {
    // 创建模态框元素
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'modal';

    // 创建模态框内容
    const modalContent = document.createElement('div');
    modalContent.className = 'modal-content';

    // 创建模态框头部
    const modalHeader = document.createElement('div');
    modalHeader.className = 'modal-header';

    const modalTitle = document.createElement('h3');
    modalTitle.className = 'modal-title';
    modalTitle.textContent = title;

    const closeButton = document.createElement('button');
    closeButton.className = 'close';
    closeButton.innerHTML = '&times;';
    closeButton.onclick = closeModal;

    modalHeader.appendChild(modalTitle);
    modalHeader.appendChild(closeButton);

    // 创建模态框主体
    const modalBody = document.createElement('div');
    modalBody.className = 'modal-body';
    modalBody.innerHTML = content;

    // 创建模态框底部
    const modalFooter = document.createElement('div');
    modalFooter.className = 'modal-footer';

    // 添加按钮
    if (footerButtons && footerButtons.length > 0) {
        footerButtons.forEach(button => {
            const btn = document.createElement('button');
            btn.className = button.className || 'btn';
            btn.textContent = button.text;
            btn.onclick = button.onclick;
            modalFooter.appendChild(btn);
        });
    } else {
        // 默认关闭按钮
        const closeBtn = document.createElement('button');
        closeBtn.className = 'btn';
        closeBtn.textContent = '关闭';
        closeBtn.onclick = closeModal;
        modalFooter.appendChild(closeBtn);
    }

    // 组装模态框
    modalContent.appendChild(modalHeader);
    modalContent.appendChild(modalBody);
    modalContent.appendChild(modalFooter);
    modal.appendChild(modalContent);

    // 添加到页面
    document.body.appendChild(modal);

    // 显示模态框
    modal.style.display = 'flex';

    return modal;
}

// 关闭模态框
function closeModal() {
    const modal = document.getElementById('modal');
    if (modal) {
        modal.remove();
    }
}

// 账号模态框
function showAccountModal(accountId = null) {
    let title = accountId ? '编辑账号' : '添加账号';
    let content = `
        <div class="form-group">
            <label for="account-name">账号Cookie</label>
            <textarea id="account-name" class="form-control" rows="5" placeholder="请输入账号Cookie"></textarea>
        </div>
        <div class="form-group">
            <label for="account-status">状态</label>
            <select id="account-status" class="form-control">
                <option value="1">正常</option>
                <option value="0">禁用</option>
            </select>
        </div>
    `;

    let footerButtons = [
        {
            text: '取消',
            className: 'btn',
            onclick: closeModal
        },
        {
            text: accountId ? '更新' : '创建',
            className: 'btn btn-primary',
            onclick: function() {
                saveAccount(accountId);
            }
        }
    ];

    createModal(title, content, footerButtons);

    // 如果是编辑模式，加载数据
    if (accountId) {
        loadAccountData(accountId);
    }
}

// 加载账号数据
async function loadAccountData(accountId) {
    try {
        const response = await fetch(`/api/accounts/${accountId}`);
        const account = await response.json();

        document.getElementById('account-name').value = account.account_name;
        document.getElementById('account-status').value = account.status;
    } catch (error) {
        console.error('加载账号数据失败:', error);
        showNotification('加载账号数据失败', 'error');
    }
}

// 保存账号
async function saveAccount(accountId = null) {
    const accountName = document.getElementById('account-name').value;
    const status = parseInt(document.getElementById('account-status').value);

    if (!accountName) {
        showNotification('请输入账号Cookie', 'error');
        return;
    }

    try {
        const url = accountId ? `/api/accounts/${accountId}` : '/api/accounts/';
        const method = accountId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                account_name: accountName,
                status: status
            })
        });

        if (response.ok) {
            showNotification(accountId ? '账号更新成功' : '账号创建成功', 'success');
            closeModal();
            loadAccountsData();
        } else {
            const error = await response.json();
            showNotification(error.detail || '操作失败', 'error');
        }
    } catch (error) {
        console.error('保存账号失败:', error);
        showNotification('保存账号失败', 'error');
    }
}

// 任务模态框
function showTaskModal(taskId = null) {
    let title = taskId ? '编辑任务' : '创建任务';
    let content = `
        <div class="form-group">
            <label for="task-name">任务名称</label>
            <input type="text" id="task-name" class="form-control" placeholder="请输入任务名称">
        </div>
        <div class="form-group">
            <label for="task-account">账号</label>
            <select id="task-account" class="form-control">
                <option value="">请选择账号</option>
            </select>
        </div>
        <div class="form-group">
            <label for="task-type">任务类型</label>
            <select id="task-type" class="form-control">
                <option value="crawler">爬虫</option>
                <option value="export">导出</option>
            </select>
        </div>
        <div class="form-group">
            <label for="task-status">状态</label>
            <select id="task-status" class="form-control">
                <option value="0">等待</option>
                <option value="1">运行</option>
                <option value="2">暂停</option>
                <option value="3">失败</option>
                <option value="4">完成</option>
                <option value="5">已停止</option>
            </select>
        </div>
        <div class="form-group">
            <label for="task-progress">进度 (%)</label>
            <input type="number" id="task-progress" class="form-control" min="0" max="100" placeholder="0-100">
        </div>
        <div class="form-group">
            <label for="task-error">错误信息</label>
            <textarea id="task-error" class="form-control" rows="3" placeholder="错误信息（如有）"></textarea>
        </div>
    `;

    let footerButtons = [
        {
            text: '取消',
            className: 'btn',
            onclick: closeModal
        },
        {
            text: taskId ? '更新' : '创建',
            className: 'btn btn-primary',
            onclick: function() {
                saveTask(taskId);
            }
        }
    ];

    createModal(title, content, footerButtons);

    // 加载账号列表
    loadAccountsForTask();

    // 如果是编辑模式，加载数据
    if (taskId) {
        loadTaskData(taskId);
    }
}

// 加载账号列表到任务选择框
async function loadAccountsForTask() {
    try {
        const response = await fetch('/api/accounts/');
        const accounts = await response.json();

        const select = document.getElementById('task-account');
        accounts.forEach(account => {
            const option = document.createElement('option');
            option.value = account.account_name;
            option.textContent = account.account_name.substring(0, 20) + '...';
            select.appendChild(option);
        });
    } catch (error) {
        console.error('加载账号列表失败:', error);
    }
}

// 加载任务数据
async function loadTaskData(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}`);
        const task = await response.json();

        document.getElementById('task-name').value = task.task_name || '';
        document.getElementById('task-account').value = task.account_name || '';
        document.getElementById('task-type').value = task.task_type || 'crawler';
        document.getElementById('task-status').value = task.status !== undefined ? task.status : '0';
        document.getElementById('task-progress').value = task.progress !== undefined ? task.progress : '0';
        document.getElementById('task-error').value = task.error_message || '';
    } catch (error) {
        console.error('加载任务数据失败:', error);
        showNotification('加载任务数据失败', 'error');
    }
}

// 保存任务
async function saveTask(taskId = null) {
    const taskName = document.getElementById('task-name').value;
    const accountName = document.getElementById('task-account').value;
    const taskType = document.getElementById('task-type').value;
    const taskStatus = document.getElementById('task-status').value;
    const taskProgress = document.getElementById('task-progress').value;
    const taskError = document.getElementById('task-error').value;

    if (!taskName || !accountName) {
        showNotification('请填写完整信息', 'error');
        return;
    }

    try {
        const url = taskId ? `/api/tasks/${taskId}` : '/api/tasks/';
        const method = taskId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                task_name: taskName,
                account_name: accountName,
                task_type: taskType,
                status: parseInt(taskStatus),
                progress: parseInt(taskProgress),
                error_message: taskError
            })
        });

        if (response.ok) {
            showNotification(taskId ? '任务更新成功' : '任务创建成功', 'success');
            closeModal();
            loadTasksData();
        } else {
            const error = await response.json();
            showNotification(error.detail || '操作失败', 'error');
        }
    } catch (error) {
        console.error('保存任务失败:', error);
        showNotification('保存任务失败', 'error');
    }
}

// 代理模态框
function showProxyModal(proxyId = null) {
    let title = proxyId ? '编辑代理' : '添加代理';
    let content = `
        <div class="form-group">
            <label for="proxy-type">代理类型</label>
            <select id="proxy-type" class="form-control">
                <option value="HTTP">HTTP</option>
                <option value="HTTPS">HTTPS</option>
                <option value="SOCKS">SOCKS</option>
            </select>
        </div>
        <div class="form-group">
            <label for="proxy-addr">代理地址</label>
            <input type="text" id="proxy-addr" class="form-control" placeholder="例如: 127.0.0.1:8080">
        </div>
        <div class="form-group">
            <label for="proxy-status">状态</label>
            <select id="proxy-status" class="form-control">
                <option value="1">正常</option>
                <option value="0">禁用</option>
            </select>
        </div>
        <div class="form-group">
            <label for="proxy-strategy">策略</label>
            <select id="proxy-strategy" class="form-control">
                <option value="轮询">轮询</option>
                <option value="随机">随机</option>
                <option value="失败切换">失败切换</option>
            </select>
        </div>
    `;

    let footerButtons = [
        {
            text: '取消',
            className: 'btn',
            onclick: closeModal
        },
        {
            text: proxyId ? '更新' : '创建',
            className: 'btn btn-primary',
            onclick: function() {
                saveProxy(proxyId);
            }
        }
    ];

    createModal(title, content, footerButtons);

    // 如果是编辑模式，加载数据
    if (proxyId) {
        loadProxyData(proxyId);
    }
}

// 加载代理数据
async function loadProxyData(proxyId) {
    try {
        const response = await fetch(`/api/proxies/${proxyId}`);
        const proxy = await response.json();

        document.getElementById('proxy-type').value = proxy.proxy_type;
        document.getElementById('proxy-addr').value = proxy.proxy_addr;
        document.getElementById('proxy-status').value = proxy.status;
        document.getElementById('proxy-strategy').value = proxy.strategy;
    } catch (error) {
        console.error('加载代理数据失败:', error);
        showNotification('加载代理数据失败', 'error');
    }
}

// 保存代理
async function saveProxy(proxyId = null) {
    const proxyType = document.getElementById('proxy-type').value;
    const proxyAddr = document.getElementById('proxy-addr').value;
    const status = parseInt(document.getElementById('proxy-status').value);
    const strategy = document.getElementById('proxy-strategy').value;

    if (!proxyAddr) {
        showNotification('请输入代理地址', 'error');
        return;
    }

    try {
        const url = proxyId ? `/api/proxies/${proxyId}` : '/api/proxies/';
        const method = proxyId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                proxy_type: proxyType,
                proxy_addr: proxyAddr,
                status: status,
                strategy: strategy
            })
        });

        if (response.ok) {
            showNotification(proxyId ? '代理更新成功' : '代理创建成功', 'success');
            closeModal();
            loadProxiesData();
        } else {
            const error = await response.json();
            showNotification(error.detail || '操作失败', 'error');
        }
    } catch (error) {
        console.error('保存代理失败:', error);
        showNotification('保存代理失败', 'error');
    }
}

// 配额模态框
function showQuotaModal(quotaId = null) {
    const isEdit = quotaId !== null;
    let title = isEdit ? '编辑配额' : '添加配额';
    
    // 根据是否是编辑模式设置默认值
    const defaultStartYear = isEdit ? '' : '2018';
    const defaultEndYear = isEdit ? '' : '2025';
    const defaultRatio = isEdit ? '' : '0.1';
    const defaultNum = isEdit ? '' : '1000';
    
    let content = `
        <div class="form-group">
            <label for="quota-start-year">开始年份</label>
            <input type="number" id="quota-start-year" class="form-control" placeholder="例如: 2018" value="${defaultStartYear}" ${isEdit ? 'readonly' : ''}>
            ${isEdit ? '<small class="form-text text-muted">编辑模式下不能修改开始年份</small>' : ''}
        </div>
        <div class="form-group">
            <label for="quota-end-year">结束年份</label>
            <input type="number" id="quota-end-year" class="form-control" placeholder="例如: 2025" value="${defaultEndYear}">
        </div>
        <div class="form-group">
            <label for="quota-ratio">存量占比</label>
            <input type="number" id="quota-ratio" class="form-control" min="0" max="1" step="0.01" placeholder="例如: 0.8" value="${defaultRatio}">
        </div>
        <div class="form-group">
            <label for="quota-num">抽样条数</label>
            <input type="number" id="quota-num" class="form-control" min="1" placeholder="例如: 1000" value="${defaultNum}">
        </div>
    `;

    let footerButtons = [
        {
            text: '取消',
            className: 'btn',
            onclick: closeModal
        },
        {
            text: quotaId ? '更新' : '创建',
            className: 'btn btn-primary',
            onclick: function() {
                saveQuota(quotaId);
            }
        }
    ];

    createModal(title, content, footerButtons);

    // 如果是编辑模式，加载数据
    if (quotaId) {
        loadQuotaData(quotaId);
    }
}

// 加载配额数据
async function loadQuotaData(quotaId) {
    try {
        const response = await fetch(`/api/quotas/${quotaId}`);
        const quota = await response.json();

        // 设置表单值
        document.getElementById('quota-start-year').value = quota.start_year;
        document.getElementById('quota-end-year').value = quota.end_year;
        document.getElementById('quota-ratio').value = quota.stock_ratio;
        document.getElementById('quota-num').value = quota.sample_num;
        
        // 显示当前配额信息
        const quotaInfo = document.createElement('div');
        quotaInfo.className = 'alert alert-info mb-3';
        quotaInfo.innerHTML = `
            <strong>当前配额信息：</strong><br>
            年份范围: ${quota.start_year} - ${quota.end_year}<br>
            存量占比: ${quota.stock_ratio}<br>
            抽样条数: ${quota.sample_num}
        `;
        
        // 将信息插入到表单前面
        const formGroups = document.querySelectorAll('.form-group');
        if (formGroups.length > 0) {
            formGroups[0].parentNode.insertBefore(quotaInfo, formGroups[0]);
        }
    } catch (error) {
        console.error('加载配额数据失败:', error);
        showNotification('加载配额数据失败', 'error');
    }
}

// 保存配额
async function saveQuota(quotaId = null) {
    const startYear = parseInt(document.getElementById('quota-start-year').value);
    const endYear = parseInt(document.getElementById('quota-end-year').value);
    const stockRatio = parseFloat(document.getElementById('quota-ratio').value);
    const sampleNum = parseInt(document.getElementById('quota-num').value);

    // 验证输入
    if (!startYear || !endYear || stockRatio === null || sampleNum === null) {
        showNotification('请填写完整信息', 'error');
        return;
    }
    
    if (isNaN(startYear) || isNaN(endYear) || isNaN(stockRatio) || isNaN(sampleNum)) {
        showNotification('请输入有效的数字', 'error');
        return;
    }
    
    if (startYear > endYear) {
        showNotification('开始年份不能大于结束年份', 'error');
        return;
    }
    
    if (stockRatio < 0 || stockRatio > 1) {
        showNotification('存量占比必须在0-1之间', 'error');
        return;
    }
    
    if (sampleNum <= 0) {
        showNotification('抽样条数必须为正数', 'error');
        return;
    }

    try {
        const isEdit = quotaId !== null;
        const url = isEdit ? `/api/quotas/${quotaId}` : '/api/quotas/';
        const method = isEdit ? 'PUT' : 'POST';
        
        // 构建请求体，编辑模式下只包含需要更新的字段
        const requestBody = isEdit ? {
            end_year: endYear,
            stock_ratio: stockRatio,
            sample_num: sampleNum
        } : {
            start_year: startYear,
            end_year: endYear,
            stock_ratio: stockRatio,
            sample_num: sampleNum
        };

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        if (response.ok) {
            showNotification(isEdit ? `配额 ${startYear}-${endYear} 更新成功` : `配额 ${startYear}-${endYear} 创建成功`, 'success');
            closeModal();
            loadQuotasData();
        } else {
            const error = await response.json();
            showNotification(error.detail || '操作失败', 'error');
        }
    } catch (error) {
        console.error('保存配额失败:', error);
        showNotification('保存配额失败', 'error');
    }
}
