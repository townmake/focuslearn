// Task API 处理模块
class TaskAPI {
    constructor(baseUrl = '/api') {
        this.baseUrl = baseUrl;
    }

    // 获取CSRF Token
    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    // 基础请求方法
    async request(url, options = {}) {
        const defaultOptions = {
            credentials: 'same-origin',
            headers: {
                'X-CSRFToken': this.getCsrfToken(),
                'Content-Type': 'application/json',
            },
        };

        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return response;
    }

    // 获取任务列表
    async getTasks() {
        const response = await this.request(`${this.baseUrl}/tasks/`);
        return response.json();
    }

    // 创建任务,重复任务在api.py中处理
    async createTask(taskData) {
        const response = await this.request(`${this.baseUrl}/tasks/`, {
            method: 'POST',
            body: JSON.stringify(taskData)
        });
        return response.json();
    }

    // 更新任务,重复任务在api.py中处理
    async updateTask(taskId, taskData) {

        const response = await this.request(`${this.baseUrl}/tasks/${taskId}/`, {
            method: 'PATCH',
            body: JSON.stringify(taskData)
        });
        return response.json();
    }

    // 删除任务，重复任务在api.py中处理
    async deleteTask(taskId) {
        await this.request(`${this.baseUrl}/tasks/${taskId}/`, {
            method: 'DELETE'
        });
    }


}
export default TaskAPI;