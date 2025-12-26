// 账号管理模块

// 初始化账号管理
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

// 加载账号数据
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
