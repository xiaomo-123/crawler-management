// 任务管理模块

// 初始化任务管理
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

// 加载任务数据
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
