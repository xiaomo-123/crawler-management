// 配额管理模块

// 初始化配额管理
function initQuotas() {
    // 初始化配额按钮
    document.getElementById('init-quotas-btn').addEventListener('click', function() {
        if (confirm('确定要初始化配额吗？这将清空现有配额数据。')) {
            initializeQuotas();
        }
    });

    // 添加配额按钮
    document.getElementById('add-quota-btn').addEventListener('click', function() {
        showQuotaModal();
    });

    // 初始加载数据
    loadQuotasData();
}

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

// 加载配额数据
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
