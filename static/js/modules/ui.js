/**
 * UI 模块
 * 处理用户界面元素和交互
 */
const UI = (function() {
    // 创建遮罩层
    function createOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'overlay';
        return overlay;
    }
    
    // 创建任务表单
    function createTaskForm(task = null) {
        const form = document.createElement('form');
        form.className = 'task-form';

        // 获取任务列表
        let taskLists = [];
        const fetchTaskLists = async () => {
            try {
                taskLists = await TaskAPI.taskLists.getAll();
                return taskLists;
            } catch (error) {
                console.error('获取任务列表失败:', error);
                UI.showError('获取任务列表失败');
                return [];
            }
        };

        // 获取科目和章节
        let subjects = [];
        const fetchSubjects = async () => {
            try {
                subjects = await TaskAPI.subjects.getAll();
                return subjects;
            } catch (error) {
                console.error('获取科目失败:', error);
                UI.showError('获取科目失败');
                return [];
            }
        };
        
        // 判断是否为新建任务
        const isNew = task && task.isNew;
        // 如果是新建任务，只保留时间信息
        if (isNew) {
            const { start_datetime, end_datetime } = task;
            task = {
                start_datetime,
                end_datetime
            };
        }
        
        // 标题输入
        const titleGroup = document.createElement('div');
        titleGroup.className = 'form-group horizontal';
        
        const titleLabel = document.createElement('label');
        titleLabel.textContent = '任务标题';
        
        const titleInput = document.createElement('input');
        titleInput.type = 'text';
        titleInput.name = 'title';
        titleInput.required = true;
        titleInput.value = task && !isNew ? task.title : '';
        
        titleGroup.appendChild(titleLabel);
        titleGroup.appendChild(titleInput);
        
        // 描述输入
        const descGroup = document.createElement('div');
        descGroup.className = 'form-group horizontal';
        
        const descLabel = document.createElement('label');
        descLabel.textContent = '任务描述';
        
        const descInput = document.createElement('textarea');
        descInput.name = 'description';
        descInput.rows = 3;
        descInput.style.cssText = `
            width: 100%;          /* 宽度由 Flex 布局控制 */
            min-height: 80px;     /* 设置最小高度 */
            resize: vertical;     /* 禁止水平拉伸 */
        `;
        descInput.value = task && !isNew ? task.description : '';
        descInput.required = false;
        
        descGroup.appendChild(descLabel);
        descGroup.appendChild(descInput);
        
        // 开始时间
const startGroup = document.createElement('div');
startGroup.className = 'form-group horizontal';

const startLabel = document.createElement('label');
startLabel.textContent = '开始时间';
startGroup.appendChild(startLabel);

// 创建时间选择容器
const startTimeContainer = document.createElement('div');
startTimeContainer.className = 'datetime-container';

// 日期选择
const startDateInput = document.createElement('input');
startDateInput.type = 'date';
startDateInput.name = 'start_date';
startDateInput.required = true;
startDateInput.style.width = '130px';

// 时间选择
const startTimeInput = document.createElement('input');
startTimeInput.type = 'time';
startTimeInput.name = 'start_time';
startTimeInput.required = true;
startTimeInput.style.width = '100px';

// 隐藏的datetime字段，用于表单提交
const startInput = document.createElement('input');
startInput.type = 'hidden';
startInput.name = 'start_datetime';

if (task) {
    const startDate = new Date(task.start_datetime);
    // 设置日期值 (YYYY-MM-DD)
    startDateInput.value = startDate.toISOString().split('T')[0];
    // 设置时间值 (HH:mm)
    startTimeInput.value = startDate.toTimeString().slice(0, 5);
    // 设置隐藏字段的完整值
    startInput.value = startDate.toISOString();
    console.log('设置开始时间:', startDateInput.value, startTimeInput.value, '原始值:', task.start_datetime);
}

// 监听日期和时间变化，更新隐藏的datetime字段
function updateStartDateTime() {
    if (startDateInput.value && startTimeInput.value) {
        const dateTime = new Date(`${startDateInput.value}T${startTimeInput.value}`);
        startInput.value = dateTime.toISOString();
    }
}

startDateInput.addEventListener('change', updateStartDateTime);
startTimeInput.addEventListener('change', updateStartDateTime);

startTimeContainer.appendChild(startDateInput);
startTimeContainer.appendChild(startTimeInput);
startTimeContainer.appendChild(startInput);
startGroup.appendChild(startTimeContainer);
        
        // 结束时间
const endGroup = document.createElement('div');
endGroup.className = 'form-group horizontal';

const endLabel = document.createElement('label');
endLabel.textContent = '结束时间';
endGroup.appendChild(endLabel);

// 创建时间选择容器
const endTimeContainer = document.createElement('div');
endTimeContainer.className = 'datetime-container';

// 日期选择
const endDateInput = document.createElement('input');
endDateInput.type = 'date';
endDateInput.name = 'end_date';
endDateInput.required = true;
endDateInput.style.width = '130px';

// 时间选择
const endTimeInput = document.createElement('input');
endTimeInput.type = 'time';
endTimeInput.name = 'end_time';
endTimeInput.required = true;
endTimeInput.style.width = '100px';

// 隐藏的datetime字段，用于表单提交
const endInput = document.createElement('input');
endInput.type = 'hidden';
endInput.name = 'end_datetime';

if (task) {
    const endDate = new Date(task.end_datetime);
    // 设置日期值 (YYYY-MM-DD)
    endDateInput.value = endDate.toISOString().split('T')[0];
    // 设置时间值 (HH:mm)
    endTimeInput.value = endDate.toTimeString().slice(0, 5);
    // 设置隐藏字段的完整值
    endInput.value = endDate.toISOString();
}

// 监听日期和时间变化，更新隐藏的datetime字段
function updateEndDateTime() {
    if (endDateInput.value && endTimeInput.value) {
        const dateTime = new Date(`${endDateInput.value}T${endTimeInput.value}`);
        endInput.value = dateTime.toISOString();
    }
}

endDateInput.addEventListener('change', updateEndDateTime);
endTimeInput.addEventListener('change', updateEndDateTime);

endTimeContainer.appendChild(endDateInput);
endTimeContainer.appendChild(endTimeInput);
endTimeContainer.appendChild(endInput);
endGroup.appendChild(endTimeContainer);
        
        // 重复类型
        const repeatGroup = document.createElement('div');
        repeatGroup.className = 'form-group horizontal';

        // 自定义重复选项容器
        const customRepeatGroup = document.createElement('div');
        customRepeatGroup.className = 'custom-repeat-group';
        customRepeatGroup.style.display = 'none';
        customRepeatGroup.id = 'repeatDaysGroup';

        const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
        weekDays.forEach((day, index) => {
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.name = 'repeat_days';
            checkbox.value = index + 1;
            checkbox.id = `repeat-day-${index + 1}`;

            // 如果是编辑已有任务，检查是否需要选中
            if (task && task.repeat_days) {
                const repeatDays = Array.isArray(task.repeat_days) ? 
                    task.repeat_days : 
                    (typeof task.repeat_days === 'string' ? task.repeat_days.split(',') : []);
                checkbox.checked = repeatDays.includes((index + 1).toString());
            }

            const label = document.createElement('label');
            label.htmlFor = `repeat-day-${index + 1}`;
            label.appendChild(checkbox);
            label.appendChild(document.createTextNode(day));

            customRepeatGroup.appendChild(label);
        });

        const repeatSelect = document.createElement('select');       
        repeatSelect.name = 'repeat_type';
        repeatSelect.id = 'repeatType';
        
        // 监听重复类型变化
        repeatSelect.addEventListener('change', (e) => {
            customRepeatGroup.style.display = e.target.value === 'custom' ? 'block' : 'none';
            
            // 重复结束日期容器
            const repeatEndsGroup = document.getElementById('repeatEndsGroup');
            if (repeatEndsGroup) {
                repeatEndsGroup.style.display = e.target.value === 'none' ? 'none' : 'flex';
            }
            
            // 当选择不重复时，隐藏结束日期行
            // 当选择重复时，显示结束日期行
            if (e.target.value === 'none') {
                // 不重复时，隐藏结束日期
                document.getElementById('repeatEndsInput').value = '';
            } else {
                // 重复时，默认设置30天后结束
                const startDate = new Date(document.querySelector('input[name="start_datetime"]').value);
                if (startDate) {
                    const endDate = new Date(startDate);
                    endDate.setDate(endDate.getDate() + 30);
                    document.getElementById('repeatEndsInput').value = endDate.toISOString().split('T')[0];
                }
            }
        });
        
        const repeatLabel = document.createElement('label');
        repeatLabel.textContent = '重复';
        

        
        const repeatOptions = [
            ['none', '不重复'],
            ['daily', '每天'],
            ['weekly', '每周'],
            ['monthly', '每月'],
            ['custom', '自定义']
        ];
        
        repeatOptions.forEach(([value, text]) => {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = text;
            if (task && task.repeat_type === value) {
                option.selected = true;
            }
            repeatSelect.appendChild(option);
        });
        
        repeatGroup.appendChild(repeatLabel);
        repeatGroup.appendChild(repeatSelect);
        
        // 添加重复结束日期
        const repeatEndsGroup = document.createElement('div');
        repeatEndsGroup.className = 'form-group horizontal';
        repeatEndsGroup.id = 'repeatEndsGroup';
        repeatEndsGroup.style.display = task && task.repeat_type !== 'none' ? 'flex' : 'none';
        
        const repeatEndsLabel = document.createElement('label');
        repeatEndsLabel.textContent = '重复结束';
        
        const repeatEndsInput = document.createElement('input');
        repeatEndsInput.type = 'date';
        repeatEndsInput.name = 'repeat_ends';
        repeatEndsInput.id = 'repeatEndsInput';
        
        // 如果是编辑已有任务，设置重复结束日期
        if (task && task.repeat_ends) {
            const repeatEnds = new Date(task.repeat_ends);
            repeatEndsInput.value = repeatEnds.toISOString().split('T')[0];
        } else if (task && task.repeat_type !== 'none') {
            // 默认设置30天后结束
            const endDate = new Date(task.start_datetime);
            endDate.setDate(endDate.getDate() + 30);
            repeatEndsInput.value = endDate.toISOString().split('T')[0];
        }
        
        repeatEndsGroup.appendChild(repeatEndsLabel);
        repeatEndsGroup.appendChild(repeatEndsInput);
        
        // 根据当前选择的重复类型显示或隐藏自定义重复选项
        customRepeatGroup.style.display = task && task.repeat_type === 'custom' ? 'block' : 'none';
        
        // 按钮组
        const actions = document.createElement('div');
        actions.className = 'form-actions';
        
        const cancelBtn = document.createElement('button');
        cancelBtn.type = 'button';
        cancelBtn.className = 'btn btn-secondary';
        cancelBtn.textContent = '取消';
        cancelBtn.onclick = UI.hideTaskForm;
        
        const submitBtn = document.createElement('button');
        submitBtn.type = 'submit';
        submitBtn.className = 'btn btn-primary';
        submitBtn.textContent = task && !isNew ? '更新' : '创建';
        
        // 只在编辑现有任务时显示删除按钮
        if (task && !isNew) {
            const deleteBtn = document.createElement('button');
            deleteBtn.type = 'button';
            deleteBtn.className = 'btn btn-secondary';
            deleteBtn.textContent = '删除';
            deleteBtn.onclick = async () => {
                if (confirm('确定要删除这个任务吗？')) {
                    try {
                        await TaskAPI.tasks.delete(task.id);
                        UI.hideTaskForm();
                        Calendar.fetchTasks();
                    } catch (error) {
                        console.error('删除任务失败:', error);
                        UI.showError('删除任务失败');
                    }
                }
            };
            actions.appendChild(deleteBtn);
        }
        
        actions.appendChild(cancelBtn);
        actions.appendChild(submitBtn);
        
        // 添加隐藏的任务ID字段
        if (task && !isNew) {
            const taskIdInput = document.createElement('input');
            taskIdInput.type = 'hidden';
            taskIdInput.name = 'task_id';
            taskIdInput.value = task.id;
            form.appendChild(taskIdInput);
        }

        // 组装表单
        form.appendChild(titleGroup);
        form.appendChild(descGroup);
        form.appendChild(startGroup);
        form.appendChild(endGroup);
        form.appendChild(repeatGroup);
        form.appendChild(customRepeatGroup);
        
        // 默认情况下，如果是不重复的任务，隐藏结束日期行
        if (repeatSelect.value === 'none') {
            endGroup.style.display = 'none';
        }

        // 移除任务列表选择

        // 科目选择
        const subjectGroup = document.createElement('div');
        subjectGroup.className = 'form-group horizontal';
        
        const subjectLabel = document.createElement('label');
        subjectLabel.textContent = '科目';
        
        const subjectSelect = document.createElement('select');
        subjectSelect.name = 'subject';
        
        // 章节选择
        const chapterGroup = document.createElement('div');
        chapterGroup.className = 'form-group horizontal';
        
        const chapterLabel = document.createElement('label');
        chapterLabel.textContent = '章节';
        
        const chapterSelect = document.createElement('select');
        chapterSelect.name = 'chapter';
        chapterSelect.disabled = true;
        
        // 异步加载科目和章节
        fetchSubjects().then(subjects => {
            // 添加空选项
            const emptyOption = document.createElement('option');
            emptyOption.value = '';
            emptyOption.textContent = '-- 选择科目 --';
            subjectSelect.appendChild(emptyOption);
            
            subjects.forEach(subject => {
                const option = document.createElement('option');
                option.value = subject.id;
                option.textContent = subject.name;
                if (task && !isNew && task.subject && task.subject.id === subject.id) {
                    option.selected = true;
                }
                subjectSelect.appendChild(option);
            });
        });

        // 监听科目选择变化
        subjectSelect.addEventListener('change', async (e) => {
            const subjectId = e.target.value;
            chapterSelect.innerHTML = '';
            chapterSelect.disabled = !subjectId;
            
            if (subjectId) {
                try {
                    const chapters = await TaskAPI.chapters.getBySubject(subjectId);
                    
                    // 添加空选项
                    const emptyOption = document.createElement('option');
                    emptyOption.value = '';
                    emptyOption.textContent = '-- 选择章节 --';
                    chapterSelect.appendChild(emptyOption);
                    
                    chapters.forEach(chapter => {
                        const option = document.createElement('option');
                        option.value = chapter.id;
                        option.textContent = chapter.title;  // 修改这里：从name改为title
                        if (task && !isNew && task.chapter && task.chapter.id === chapter.id) {
                            option.selected = true;
                        }
                        chapterSelect.appendChild(option);
                    });
                } catch (error) {
                    console.error('获取章节失败:', error);
                    UI.showError('获取章节失败');
                }
            }
        });
        
        subjectGroup.appendChild(subjectLabel);
        subjectGroup.appendChild(subjectSelect);
        form.appendChild(subjectGroup);
        
        chapterGroup.appendChild(chapterLabel);
        chapterGroup.appendChild(chapterSelect);
        form.appendChild(chapterGroup);
        
        // 专注力要求滑块
        const focusGroup = document.createElement('div');
        focusGroup.className = 'form-group horizontal';
        
        const focusLabel = document.createElement('label');
        focusLabel.textContent = '专注力要求';
        
        const focusContainer = document.createElement('div');
        focusContainer.className = 'slider-container';
        
        const focusValue = document.createElement('span');
        focusValue.className = 'slider-value';
        focusValue.textContent = task && !isNew ? task.focus_level : '50';
        
        const focusSlider = document.createElement('input');
        focusSlider.type = 'range';
        focusSlider.name = 'focus_level';
        focusSlider.min = '0';
        focusSlider.max = '100';
        focusSlider.step = '1';
        focusSlider.value = task && !isNew ? task.focus_level : '50';
        
        focusSlider.addEventListener('input', () => {
            focusValue.textContent = focusSlider.value;
        });
        
        focusContainer.appendChild(focusSlider);
        focusContainer.appendChild(focusValue);
        
        focusGroup.appendChild(focusLabel);
        focusGroup.appendChild(focusContainer);
        form.appendChild(focusGroup);
        
        // 体力要求滑块
        const energyGroup = document.createElement('div');
        energyGroup.className = 'form-group horizontal';
        
        const energyLabel = document.createElement('label');
        energyLabel.textContent = '体力要求';
        
        const energyContainer = document.createElement('div');
        energyContainer.className = 'slider-container';
        
        const energyValue = document.createElement('span');
        energyValue.className = 'slider-value';
        energyValue.textContent = task && !isNew ? task.energy_level : '50';
        
        const energySlider = document.createElement('input');
        energySlider.type = 'range';
        energySlider.name = 'energy_level';
        energySlider.min = '0';
        energySlider.max = '100';
        energySlider.step = '1';
        energySlider.value = task && !isNew ? task.energy_level : '50';
        
        energySlider.addEventListener('input', () => {
            energyValue.textContent = energySlider.value;
        });
        
        energyContainer.appendChild(energySlider);
        energyContainer.appendChild(energyValue);
        
        energyGroup.appendChild(energyLabel);
        energyGroup.appendChild(energyContainer);
        form.appendChild(energyGroup);

        // // 标签输入--先不实现
        // const tagGroup = document.createElement('div');
        // tagGroup.className = 'form-group horizontal';
        
        // const tagLabel = document.createElement('label');
        // tagLabel.textContent = '标签';
        
        // const tagInput = document.createElement('input');
        // tagInput.type = 'text';
        // tagInput.name = 'tags';
        // tagInput.placeholder = '多个标签用逗号分隔';
        // tagInput.value = task && !isNew && task.tags ? task.tags.join(',') : '';
        
        // tagGroup.appendChild(tagLabel);
        // tagGroup.appendChild(tagInput);
        // form.appendChild(tagGroup);

        form.appendChild(actions);
        
        // 表单提交处理
        form.onsubmit = async (e) => {
            e.preventDefault();
            
            const formData = new FormData(form);
            // 移除任务列表相关验证

            // 获取开始日期和时间
            let startDateTime, endDateTime;
            
            // 使用隐藏字段的值（已经在日期和时间变化时更新）
            const startDateTimeValue = formData.get('start_datetime');
            const endDateTimeValue = formData.get('end_datetime');
            
            if (startDateTimeValue) {
                startDateTime = startDateTimeValue;
            } else {
                // 备用方案：组合日期和时间字段
                const startDate = formData.get('start_date');
                const startTime = formData.get('start_time');
                startDateTime = new Date(`${startDate}T${startTime}`).toISOString();
            }
            
            if (endDateTimeValue) {
                endDateTime = endDateTimeValue;
            } else {
                // 备用方案：组合日期和时间字段
                const endDate = formData.get('end_date');
                const endTime = formData.get('end_time');
                endDateTime = new Date(`${endDate}T${endTime}`).toISOString();
            }
            
            const data = {
                title: formData.get('title'),
                description: formData.get('description'),
                start_datetime: startDateTime,
                end_datetime: endDateTime,
                repeat_type: formData.get('repeat_type'),
                subject: formData.get('subject'),
                chapter: formData.get('chapter'),
                focus_level: formData.get('focus_level'),
                energy_level: formData.get('energy_level'),
                // tags: formData.get('tags') ? formData.get('tags').split(',').filter(tag => tag.trim()) : []
            };
            
            console.log('提交的任务数据:', {
                表单开始时间: formData.get('start_datetime'),
                表单结束时间: formData.get('end_datetime'),
                转换后开始时间: data.start_datetime,
                转换后结束时间: data.end_datetime
            });
            
            try {
                // 获取表单中的任务ID
                const taskId = formData.get('task_id');
                
                // 根据是否有任务ID来判断是更新还是创建
                if (taskId) {
                    // 更新已有任务 - PUT请求
                    await TaskAPI.tasks.update(taskId, data);
                } else {
                    // 新建任务 - POST请求
                    await TaskAPI.tasks.create(data);
                }
                
                UI.hideTaskForm();
                Calendar.fetchTasks();
            } catch (error) {
                console.error('保存任务失败:', error);
                UI.showError('保存任务失败');
            }
        };
        
        return form;
    }
    
    // 创建每日总结表单
    function createDailySummaryForm(date) {
        const form = document.createElement('form');
        form.className = 'task-form daily-summary-form';

        // 标题
        const titleDiv = document.createElement('div');
        titleDiv.className = 'form-title';
        titleDiv.textContent = `${date.toLocaleDateString('zh-CN')} 每日总结`;
        form.appendChild(titleDiv);

        // 描述输入
        const descGroup = document.createElement('div');
        descGroup.className = 'form-group';
        
        const descInput = document.createElement('textarea');
        descInput.name = 'description';
        descInput.rows = 5;
        descInput.placeholder = '请输入今日总结...';
        descInput.required = true;
        descInput.style.cssText = `
            width: 100%;
            min-height: 120px;
            resize: vertical;
            margin-bottom: 15px;
        `;
        
        descGroup.appendChild(descInput);
        form.appendChild(descGroup);

        // 按钮组
        const actions = document.createElement('div');
        actions.className = 'form-actions';
        
        const cancelBtn = document.createElement('button');
        cancelBtn.type = 'button';
        cancelBtn.className = 'btn btn-secondary';
        cancelBtn.textContent = '取消';
        cancelBtn.onclick = UI.hideTaskForm;
        
        const submitBtn = document.createElement('button');
        submitBtn.type = 'submit';
        submitBtn.className = 'btn btn-primary';
        submitBtn.textContent = '保存';
        
        actions.appendChild(cancelBtn);
        actions.appendChild(submitBtn);
        form.appendChild(actions);

        // 加载已有的每日总结
        TaskAPI.dailySummaries.getByDate(date).then(summaries => {
            if (summaries && summaries.length > 0) {
                const summary = summaries[0];
                descInput.value = summary.description;
                form.existingSummary = summary;  // 存储现有总结对象到表单
               console.log("已存在的总结内容：", summary.description);

            }
        }).catch(error => {
            console.error('获取每日总结失败:', error);
        });

        // 表单提交处理
        form.onsubmit = async (e) => {
            e.preventDefault();
            const description = form.querySelector('textarea').value;
            const formData = new FormData(form);
            
            try {
                // 保存数据
                const result = await TaskAPI.dailySummaries.create({
                  date: date.toISOString().split('T')[0],
                  description
                });
            
                // 更新本地数据
                Calendar.dailySummaries[date.toISOString().split('T')[0]] = result;
                
                // 精准更新对应的总结单元格
                const dateStr = date.toISOString().split('T')[0];
                const cell = document.querySelector(`.summary-cell[data-date="${dateStr}"]`);
                if (cell) {
                  cell.innerHTML = result.description
                    ? `<div class="summary-content">${Calendar.formatSummary(result.description)}</div>`
                    : '<div class="summary-placeholder">请填写</div>';
                }
            
                UI.hideTaskForm();
              } catch (error) {
                console.error('保存失败:', error);
                UI.showError('保存失败');
              }
        };
        
        return form;
    }

    return {
        init: () => {
            // 初始化UI组件
        },

        showDailySummaryForm: (date,summary) => {
            const overlay = createOverlay();
            const dialog = document.createElement('div');
            dialog.className = 'task-dialog';
            
            const form = createDailySummaryForm(date, summary);
            dialog.appendChild(form);
            overlay.appendChild(dialog);
            document.body.appendChild(overlay);
            
            // 添加保存后的回调
            const saveButton = dialog.querySelector('button[type="submit"]');
            saveButton.addEventListener('click', async () => {
              const description = dialog.querySelector('textarea').value;
              try {
                await TaskAPI.dailySummaries.create({
                  date: date.toISOString().split('T')[0],
                  description
                });
                UI.hideTaskForm();
                Calendar.fetchTasks(); // 刷新数据
              } catch (error) {
                console.error('保存失败:', error);
                UI.showError('保存失败');
              }
            });
        },
        
        showTaskForm: (task = null) => {
            const overlay = createOverlay();
            const dialog = document.createElement('div');
            dialog.className = 'task-dialog';
            
            dialog.appendChild(createTaskForm(task));
            overlay.appendChild(dialog);
            document.body.appendChild(overlay);
        },
        
        hideTaskForm: () => {
            const overlay = document.querySelector('.overlay');
            if (overlay) {
                overlay.remove();
            }
        },
        
        showError: (message) => {
            // 创建一个更友好的错误提示
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background-color: #ff4444;
                color: white;
                padding: 15px 25px;
                border-radius: 4px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                z-index: 10000;
                animation: slideIn 0.3s ease-out;
            `;
            
            errorDiv.textContent = message;
            document.body.appendChild(errorDiv);

            // 3秒后自动消失
            setTimeout(() => {
                messageDiv.style.animation = 'slideOut 0.3s ease-in';
                setTimeout(() => messageDiv.remove(), 300);
            }, 3000);
        }
    };
})();