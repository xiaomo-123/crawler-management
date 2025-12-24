
// 辅助函数

// 显示通知
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;

    // 添加到页面
    document.body.appendChild(notification);

    // 3秒后移除
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// 获取状态文本
function getStatusText(status) {
    const statusMap = {
        0: "等待",
        1: "运行",
        2: "暂停",
        3: "失败",
        4: "完成"
    };
    return statusMap[status] || "未知";
}

// 获取状态样式类
function getStatusClass(status) {
    const statusMap = {
        0: "status-waiting",
        1: "status-running",
        2: "status-paused",
        3: "status-failed",
        4: "status-completed"
    };
    return statusMap[status] || "";
}

// 格式化日期时间
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

// 格式化文件大小
function formatFileSize(sizeBytes) {
    if (sizeBytes === 0) return "0 B";

    const sizeNames = ["B", "KB", "MB", "GB", "TB"];
    let i = 0;
    let size = sizeBytes;

    while (size >= 1024 && i < sizeNames.length - 1) {
        size /= 1024.0;
        i++;
    }

    return `${size.toFixed(2)} ${sizeNames[i]}`;
}

// 绘制任务状态图表
function drawTaskStatusChart(tasks) {
    const ctx = document.getElementById('task-status-chart').getContext('2d');

    // 统计各状态任务数量
    const statusCounts = {
        0: 0,  // 等待
        1: 0,  // 运行
        2: 0,  // 暂停
        3: 0,  // 失败
        4: 0   // 完成
    };

    tasks.forEach(task => {
        statusCounts[task.status]++;
    });

    // 销毁现有图表
    if (window.taskStatusChart) {
        window.taskStatusChart.destroy();
    }

    // 创建新图表
    window.taskStatusChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['等待', '运行', '暂停', '失败', '完成'],
            datasets: [{
                data: [
                    statusCounts[0],
                    statusCounts[1],
                    statusCounts[2],
                    statusCounts[3],
                    statusCounts[4]
                ],
                backgroundColor: [
                    '#6c757d',  // 等待 - 灰色
                    '#28a745',  // 运行 - 绿色
                    '#ffc107',  // 暂停 - 黄色
                    '#dc3545',  // 失败 - 红色
                    '#17a2b8'   // 完成 - 青色
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

// 绘制数据年份分布图表
function drawDataYearChart(rawDataStats, sampleDataStats) {
    const ctx = document.getElementById('data-year-chart').getContext('2d');

    // 准备年份标签
    const years = [];
    for (let year = 2018; year <= 2025; year++) {
        years.push(year.toString());
    }

    // 准备原始数据和抽样数据
    const rawData = years.map(year => rawDataStats[year] || 0);
    const sampleData = years.map(year => sampleDataStats[year] || 0);

    // 销毁现有图表
    if (window.dataYearChart) {
        window.dataYearChart.destroy();
    }

    // 创建新图表
    window.dataYearChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: years,
            datasets: [
                {
                    label: '原始数据',
                    data: rawData,
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                },
                {
                    label: '抽样数据',
                    data: sampleData,
                    backgroundColor: 'rgba(255, 99, 132, 0.5)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}
