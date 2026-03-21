/**
 * 主程序入口
 */
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // 创建日历容器
        const root = document.getElementById('task-manager-root');
        const calendarGrid = document.createElement('div');
        calendarGrid.className = 'calendar-grid';
        root.appendChild(calendarGrid);
        
        // 创建加载指示器
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'loading-indicator';
        loadingIndicator.innerHTML = '<div class="spinner"></div><div>加载中...</div>';
        root.appendChild(loadingIndicator);
        
        // 初始化各个模块
        UI.init();
        Calendar.init();
        
        // 先加载本周任务，再渲染日历
        await Calendar.fetchTasks();
        
        // 移除加载指示器
        if (loadingIndicator.parentNode) {
            loadingIndicator.parentNode.removeChild(loadingIndicator);
        }
        
        // 检查URL参数，设置初始视图
        const urlParams = new URLSearchParams(window.location.search);
        const view = urlParams.get('view');
        if (view && ['month', 'week', 'day', 'list'].includes(view)) {
            Calendar.changeView(view);
        }
        
    } catch (error) {
        console.error('初始化失败:', error);
        UI.showError('初始化失败，请刷新页面重试');
    }
});