// 表单处理模块
import TaskAPI from './task-api.js';

class FormHandler {
    constructor() {
        this.taskApi = new TaskAPI();
        this.initEventListeners();
    }

    initEventListeners() {
        // 监听任务表单提交
        document.addEventListener('submit', (event) => {
            if (event.target.matches('#taskForm')) {
                event.preventDefault();
                this.handleTaskFormSubmit(event.target);
            }
        });

        // 监听任务编辑按钮
        document.addEventListener('click', (event) => {
            if (event.target.matches('.edit-task-btn')) {
                event.preventDefault();
                const taskId = event.target.dataset.taskId;
                this.loadTaskForEdit(taskId);
            }
        });

        // 监听任务删除按钮
        document.addEventListener('click', (event) => {
            if (event.target.matches('.delete-task-btn')) {
                event.preventDefault();
                const taskId = event.target.dataset.taskId;
                const isRecurring = event.target.dataset.recurring === 'true';
                this.handleTaskDelete(taskId, isRecurring);
            }
        });
    }

    async handleTaskFormSubmit(form) {
        try {
            const formData = new FormData(form);
            const taskData = this.formDataToJson(formData);
            
            // 处理重复事件的特殊字段
            if (taskData.repeat_type === 'none') {
                taskData.repeat_days = '';
                taskData.repeat_ends = null;
            } else {
                // 处理重复结束日期
                if (!taskData.repeat_ends) {
                    // 默认设置为30天后
                    const endDate = new Date(taskData.start_datetime);
                    endDate.setDate(endDate.getDate() + 30);
                    taskData.repeat_ends = endDate.toISOString().split('T')[0];
                }
                
                // 处理自定义重复
                if (taskData.repeat_type === 'custom') {
                    if (!taskData.repeat_days || taskData.repeat_days.length === 0) {
                        throw new Error('自定义重复必须选择至少一天');
                    }
                }
            }
            
            // 检查是否为重复提交
            const isDuplicate = await this.checkDuplicateTask(taskData);
            
            if (isDuplicate) {
                const confirmDuplicate = await this.showDuplicateConfirmDialog();
                if (!confirmDuplicate) {
                    return; // 用户取消提交
                }
            }
            
            if (taskData.id) {
                // 更新任务
                const isRecurring = taskData.repeat_type !== 'none';
                await this.taskApi.updateTask(taskData.id, taskData);
            } else {
                // 创建任务
                await this.taskApi.createTask(taskData);
            }
            
            // 重置表单
            form.reset();
            
            // 刷新任务列表或日历
            this.refreshTaskView();
            
        } catch (error) {
            console.error('处理任务表单时出错:', error);
            alert(`处理任务时出错: ${error.message}`);
        }
    }

    async handleTaskDelete(taskId, isRecurring) {
        try {
            await this.taskApi.deleteTask(taskId, isRecurring);
            
            // 刷新任务列表或日历
            this.refreshTaskView();
            
        } catch (error) {
            if (error.message === '用户取消了操作') {
                return; // 用户取消删除，不做处理
            }
            
            console.error('删除任务时出错:', error);
            alert(`删除任务时出错: ${error.message}`);
        }
    }

    async loadTaskForEdit(taskId) {
        try {
            const response = await fetch(`/api/tasks/${taskId}/`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const task = await response.json();
            
            // 填充表单
            const form = document.getElementById('taskForm');
            
            // 设置隐藏字段
            form.querySelector('#taskId').value = task.id;
            
            // 填充基本字段
            form.querySelector('#title').value = task.title;
            form.querySelector('#description').value = task.description;
            form.querySelector('#subject').value = task.subject;
            
            if (task.chapter) {
                form.querySelector('#chapter').value = task.chapter;
            }
            
            // 设置日期时间
            const startDateTime = new Date(task.start_datetime);
            form.querySelector('#startDate').value = startDateTime.toISOString().split('T')[0];
            form.querySelector('#startTime').value = startDateTime.toTimeString().substring(0, 5);
            
            const endDateTime = new Date(task.end_datetime);
            form.querySelector('#endDate').value = endDateTime.toISOString().split('T')[0];
            form.querySelector('#endTime').value = endDateTime.toTimeString().substring(0, 5);
            
            // 设置重复类型
            form.querySelector('#repeatType').value = task.repeat_type;
            
            // 根据重复类型显示/隐藏相关字段
            this.toggleRepeatFields(task.repeat_type);
            
            if (task.repeat_ends) {
                const repeatEnds = new Date(task.repeat_ends);
                form.querySelector('#repeatEnds').value = repeatEnds.toISOString().split('T')[0];
            }
            
            if (task.repeat_days) {
                const repeatDays = task.repeat_days.split(',');
                const checkboxes = form.querySelectorAll('input[name="repeat_days"]');
                checkboxes.forEach(checkbox => {
                    checkbox.checked = repeatDays.includes(checkbox.value);
                });
            }
            
            // 设置完成状态
            form.querySelector('#isCompleted').checked = task.is_completed;
            
            // 设置焦点和能量级别
            if (form.querySelector('#focusLevel')) {
                form.querySelector('#focusLevel').value = task.focus_level;
            }
            
            if (form.querySelector('#energyLevel')) {
                form.querySelector('#energyLevel').value = task.energy_level;
            }
            
            // 更新表单标题
            const formTitle = document.querySelector('#taskFormTitle');
            if (formTitle) {
                formTitle.textContent = '编辑任务';
            }
            
            // 显示表单（如果是模态框）
            const taskModal = document.getElementById('taskModal');
            if (taskModal) {
                const modal = new bootstrap.Modal(taskModal);
                modal.show();
            }
            
        } catch (error) {
            console.error('加载任务进行编辑时出错:', error);
            alert(`加载任务时出错: ${error.message}`);
        }
    }

    formDataToJson(formData) {
        const data = {};
        
        for (const [key, value] of formData.entries()) {
            // 处理特殊字段
            if (key === 'repeat_days') {
                if (!data[key]) {
                    data[key] = [];
                }
                data[key].push(value);
            } else {
                data[key] = value;
            }
        }
        
        // 合并日期和时间字段
        if (data.startDate && data.startTime) {
            data.start_datetime = `${data.startDate}T${data.startTime}:00`;
            delete data.startDate;
            delete data.startTime;
        }
        
        if (data.endDate && data.endTime) {
            data.end_datetime = `${data.endDate}T${data.endTime}:00`;
            delete data.endDate;
            delete data.endTime;
        }
        
        // 处理布尔值
        data.is_completed = !!data.is_completed;
        
        // 处理重复天数数组
        if (Array.isArray(data.repeat_days)) {
            data.repeat_days = data.repeat_days.join(',');
        }
        
        return data;
    }

    toggleRepeatFields(repeatType) {
        const repeatEndsGroup = document.getElementById('repeatEndsGroup');
        const repeatDaysGroup = document.getElementById('repeatDaysGroup');
        
        if (repeatType === 'none') {
            repeatEndsGroup.style.display = 'none';
            repeatDaysGroup.style.display = 'none';
        } else if (repeatType === 'custom') {
            repeatEndsGroup.style.display = 'block';
            repeatDaysGroup.style.display = 'block';
            
            // 确保至少选中一天
            const checkboxes = document.querySelectorAll('input[name="repeat_days"]');
            const atLeastOneChecked = Array.from(checkboxes).some(cb => cb.checked);
            if (!atLeastOneChecked) {
                checkboxes[0].checked = true;
            }
        } else {
            repeatEndsGroup.style.display = 'block';
            repeatDaysGroup.style.display = 'none';
            
            // 清除自定义重复的选择
            document.querySelectorAll('input[name="repeat_days"]').forEach(cb => {
                cb.checked = false;
            });
        }
        
        // 如果显示结束日期，确保有默认值
        if (repeatEndsGroup.style.display === 'block') {
            const repeatEndsInput = document.getElementById('repeatEnds');
            if (!repeatEndsInput.value) {
                const defaultEnd = new Date();
                defaultEnd.setDate(defaultEnd.getDate() + 30);
                repeatEndsInput.value = defaultEnd.toISOString().split('T')[0];
            }
        }
    }

    refreshTaskView() {
        // 刷新任务视图（日历或列表）
        if (window.calendar) {
            window.calendar.refetchEvents();
        }
        
        // 如果有任务列表视图，也刷新它
        const taskListEvent = new CustomEvent('refresh-tasks');
        document.dispatchEvent(taskListEvent);
    }

    async checkDuplicateTask(taskData) {
        // 获取当天的所有任务
        const tasks = await this.taskApi.getTasks();
        
        // 提取当天的任务
        const taskDate = new Date(taskData.start_datetime).toISOString().split('T')[0];
        const sameDayTasks = tasks.filter(task => {
            const taskStartDate = new Date(task.start_datetime).toISOString().split('T')[0];
            return taskStartDate === taskDate && task.id !== taskData.id;
        });
        
        // 检查是否有标题相同的任务
        return sameDayTasks.some(task => task.title === taskData.title);
    }

    async showDuplicateConfirmDialog() {
        return new Promise((resolve) => {
            const dialog = document.createElement('div');
            dialog.innerHTML = `
                <div class="modal fade" id="duplicateTaskModal" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">发现重复任务</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <p>当天已存在相同标题的任务，确定要继续创建吗？</p>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                                <button type="button" class="btn btn-primary" id="confirmDuplicate">继续创建</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(dialog);
            
            const modal = new bootstrap.Modal(document.getElementById('duplicateTaskModal'));
            modal.show();
            
            document.getElementById('confirmDuplicate').addEventListener('click', () => {
                modal.hide();
                resolve(true);
            });
            
            document.getElementById('duplicateTaskModal').addEventListener('hidden.bs.modal', () => {
                document.body.removeChild(dialog);
                resolve(false);
            });
        });
    }
}

export default FormHandler;