// 代理管理模块

// 初始化代理管理
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

// 加载代理数据
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
