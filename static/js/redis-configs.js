// Redis配置管理模块

// 初始化Redis配置管理
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

// 加载Redis配置数据
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

// 显示添加Redis配置模态框
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

// 添加Redis配置
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

// 显示编辑Redis配置模态框
async function showEditRedisConfigModal(configId) {
    try {
        const response = await fetch('/api/redis-configs/');
        const configs = await response.json();
        const config = configs.find(c => c.id === configId);

        if (!config) {
            showNotification('Redis配置不存在', 'error');
            return;
        }

        let content = `
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

        createModal('编辑Redis配置', content, [
            {
                text: '取消',
                className: 'btn',
                onclick: closeModal
            }
        ]);

        // 等待模态框创建完成后再绑定表单事件
        setTimeout(() => {
            const form = document.getElementById('edit-redis-config-form');
            if (form) {
                form.addEventListener('submit', async function(e) {
                    e.preventDefault();
                    await updateRedisConfig(configId);
                });
            }
        }, 100);
    } catch (error) {
        console.error('获取Redis配置失败:', error);
        showNotification('获取Redis配置失败', 'error');
    }
}

// 更新Redis配置
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

// 删除Redis配置
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

// 测试Redis连接
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

// 测试当前Redis配置
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

// 重新加载Redis配置
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
