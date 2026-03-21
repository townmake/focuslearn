/**
 * Calendar 模块
 * 处理日历视图的渲染和交互
 */
window.Calendar = (function() {
    let currentDate = new Date();
    let tasks = [];
    let draggedTask = null;
    let dailySummaries = {}; // 存储每日总结数据
    
    // 工具函数
    const utils = {
        // 更新每日总结数据，暂时注释，实际应用中应从后端获取或更新，等下思中再写回来
        // updateDailySummaries: (summaries) => {
        //     dailySummaries = {};
        //     summaries.forEach(summary => {
        //         dailySummaries[summary.date] = summary;
        //     });
        // },
        // 时区转换工具 - 确保正确处理UTC和本地时间
        convertToLocalTime: (isoString) => {
            if (!isoString) return null;
            // 创建一个新的日期对象，确保正确解析ISO字符串
            const date = new Date(isoString);
            
            // 记录转换日志
            console.log(`时区转换 - UTC到本地: ${isoString} -> ${date.toString()}`);
            return date;
        },
        
        convertToUTC: (localDate) => {
            if (!localDate) return null;
            const utcString = new Date(localDate).toISOString();
            
            // 记录转换日志
            console.log(`时区转换 - 本地到UTC: ${localDate} -> ${utcString}`);
            return utcString;
        },
        // 格式化时间
        formatTime: (date) => {
            return date.toLocaleTimeString('zh-CN', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            });
        },
        
        // 格式化日期
        formatDate: (date) => {
            return date.toLocaleDateString('zh-CN', {
                month: 'long',
                day: 'numeric',
                weekday: 'long'
            });
        },
        
        // 获取一周的日期范围
        getWeekDates: (date) => {
            const start = new Date(date);
            start.setDate(start.getDate() - start.getDay());
            
            const dates = [];
            for (let i = 0; i < 7; i++) {
                const day = new Date(start);
                day.setDate(start.getDate() + i);
                dates.push(day);
            }
            return dates;
        },
        
        // 创建时间槽元素
        createTimeSlot: (date, hour) => {
            const slot = document.createElement('div');
            slot.className = 'time-slot';
            const dateStr = date.toISOString().split('T')[0];
            slot.dataset.date = dateStr;
            slot.dataset.hour = hour;

            // 添加点击事件处理（用于创建新任务）
            slot.addEventListener('click', (e) => {
                if (e.target === slot) { // 确保点击的是空白区域
                    const rect = slot.getBoundingClientRect();
                    const clickY = e.clientY - rect.top;
                    const startHour = hour + (clickY / 60); // 60px per hour
                    
                    const startTime = new Date(date);
                    startTime.setHours(Math.floor(startHour), Math.floor((startHour % 1) * 60));
                    
                    const endTime = new Date(startTime);
                    endTime.setHours(startTime.getHours() + 1);
                    
                    UI.showTaskForm({
                        isNew: true,
                        start_datetime: startTime.toISOString(),
                        end_datetime: endTime.toISOString()
                    });
                }
            });
            

            return slot;
        }
    };
    
    // 渲染函数
const render = {
    // 渲染日历头部
    renderHeader: function(){
        const header = document.createElement('div');
        header.className = 'calendar-header';
        
        const title = document.createElement('h2');
        title.className = 'calendar-title';
        title.textContent = `${currentDate.getFullYear()}年${currentDate.getMonth() + 1}月`;
        
        const controls = document.createElement('div');
        controls.className = 'calendar-controls';

        // 视图切换按钮组
        const viewControls = document.createElement('div');
        viewControls.className = 'view-controls';
        
        const viewButtons = [
            { text: '月', view: 'month', className: 'btn-view' },
            { text: '周', view: 'week', className: 'btn-view active' },
            { text: '日', view: 'day', className: 'btn-view' },
            { text: '列表', view: 'list', className: 'btn-view' }
        ];
        
        viewButtons.forEach(button => {
            const btn = document.createElement('button');
            btn.className = button.className;
            btn.textContent = button.text;
            btn.onclick = () => {
                // 移除其他按钮的active类
                viewControls.querySelectorAll('.btn-view').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                Calendar.changeView(button.view);
            };
            viewControls.appendChild(btn);
        });
            
            const prevButton = document.createElement('button');
            prevButton.className = 'btn btn-secondary';
            prevButton.textContent = '上一周';
            prevButton.onclick = () => {
                currentDate.setDate(currentDate.getDate() - 7);
                Calendar.render();
            };
            
            const nextButton = document.createElement('button');
            nextButton.className = 'btn btn-secondary';
            nextButton.textContent = '下一周';
            nextButton.onclick = () => {
                currentDate.setDate(currentDate.getDate() + 7);
                Calendar.render();
            };
            
            const todayButton = document.createElement('button');
            todayButton.className = 'btn btn-primary';
            todayButton.textContent = '今天';
            todayButton.onclick = () => {
                currentDate = new Date();
                Calendar.render();
            };
            
            controls.appendChild(viewControls);
            controls.appendChild(prevButton);
            controls.appendChild(todayButton);
            controls.appendChild(nextButton);
            
            header.appendChild(title);
            header.appendChild(controls);
            
            return header;
        },
        
        // 渲染月视图
    renderMonthView: function() {
        const monthContainer = document.createElement('div');
        monthContainer.className = 'month-container';
        
        // 获取当月第一天和最后一天
        const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
        const lastDay = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
        
        // 添加日历头部（周一到周日）
        const weekHeader = document.createElement('div');
        weekHeader.className = 'month-week-header';
        ['一', '二', '三', '四', '五', '六', '日'].forEach(day => {
            const cell = document.createElement('div');
            cell.className = 'month-week-header-cell';
            cell.textContent = day;
            weekHeader.appendChild(cell);
        });
        monthContainer.appendChild(weekHeader);
        
        // 创建日历网格
        const grid = document.createElement('div');
        grid.className = 'month-grid';
        
        // 获取当月第一天是星期几
        let firstDayOfWeek = firstDay.getDay() || 7; // 转换周日从0到7
        firstDayOfWeek--; // 调整为从0开始
        
        // 添加上月剩余日期
        for (let i = 0; i < firstDayOfWeek; i++) {
            const cell = document.createElement('div');
            cell.className = 'month-cell month-cell-disabled';
            const prevMonthDay = new Date(firstDay);
            prevMonthDay.setDate(prevMonthDay.getDate() - (firstDayOfWeek - i));
            cell.textContent = prevMonthDay.getDate();
            grid.appendChild(cell);
        }
        
        // 添加当月日期
        for (let date = 1; date <= lastDay.getDate(); date++) {
            const cell = document.createElement('div');
            cell.className = 'month-cell';
            
            const currentDateObj = new Date(currentDate.getFullYear(), currentDate.getMonth(), date);
            if (currentDateObj.toDateString() === new Date().toDateString()) {
                cell.classList.add('today');
            }
            
            cell.textContent = date;
            
            // 添加点击事件
            cell.addEventListener('click', () => {
                currentDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), date);
                Calendar.changeView('day');
            });
            
            grid.appendChild(cell);
        }
        
        // 添加下月开始日期
        const cellCount = grid.children.length;
        const remainingCells = 42 - cellCount; // 6行7列 = 42个格子
        
        for (let i = 1; i <= remainingCells; i++) {
            const cell = document.createElement('div');
            cell.className = 'month-cell month-cell-disabled';
            cell.textContent = i;
            grid.appendChild(cell);
        }
        
        monthContainer.appendChild(grid);
        return monthContainer;
    },
    
    // 渲染日视图头部
    renderDayHeader: function() {
        const header = document.createElement('div');
        header.className = 'day-header';
        
        const cell = document.createElement('div');
        cell.className = 'day-header-cell';
        cell.textContent = utils.formatDate(currentDate);
        header.appendChild(cell);
        
        return header;
    },
    
    // 渲染日视图内容
    renderDayGrid: function() {
        const grid = document.createElement('div');
        grid.className = 'day-grid';
        
        // 添加时间标签（8:00-24:00）
        for (let hour = 8; hour <= 24; hour++) {
            const timeSlot = document.createElement('div');
            timeSlot.className = 'time-slot';
            
            const timeLabel = document.createElement('div');
            timeLabel.className = 'time-label';
            timeLabel.textContent = `${hour}:00`;
            timeSlot.appendChild(timeLabel);
            
            const contentSlot = document.createElement('div');
            contentSlot.className = 'day-content-slot';
            contentSlot.dataset.hour = hour;
            contentSlot.dataset.date = currentDate.toISOString().split('T')[0];
            
            timeSlot.appendChild(contentSlot);
            grid.appendChild(timeSlot);
        }
        
        return grid;
    },
    
    // 渲染列表视图
    renderListView: function() {
        const listContainer = document.createElement('div');
        listContainer.className = 'list-container';
        
        // 如果没有任务，显示空状态
        if (!this.tasks || this.tasks.length === 0) {
            const emptyState = document.createElement('div');
            emptyState.className = 'empty-state';
            emptyState.textContent = '暂无任务';
            listContainer.appendChild(emptyState);
            return listContainer;
        }
        
        // 按日期分组显示任务
        const tasksByDate = {};
        this.tasks.forEach(task => {
            const date = task.start_datetime.split('T')[0];
            if (!tasksByDate[date]) {
                tasksByDate[date] = [];
            }
            tasksByDate[date].push(task);
        });
        
        // 按日期排序并显示任务
        Object.keys(tasksByDate).sort().forEach(date => {
            const dateGroup = document.createElement('div');
            dateGroup.className = 'list-date-group';
            
            const dateHeader = document.createElement('div');
            dateHeader.className = 'list-date-header';
            dateHeader.textContent = utils.formatDate(new Date(date));
            dateGroup.appendChild(dateHeader);
            
            tasksByDate[date].forEach(task => {
                const taskItem = document.createElement('div');
                taskItem.className = 'list-task-item';
                
                const taskTime = document.createElement('div');
                taskTime.className = 'list-task-time';
                taskTime.textContent = task.start_datetime.split('T')[1].substring(0, 5);
                
                const taskTitle = document.createElement('div');
                taskTitle.className = 'list-task-title';
                taskTitle.textContent = task.title;
                
                taskItem.appendChild(taskTime);
                taskItem.appendChild(taskTitle);
                
                // 添加点击事件
                taskItem.addEventListener('click', () => {
                    UI.showTaskForm(task);
                });
                
                dateGroup.appendChild(taskItem);
            });
            
            listContainer.appendChild(dateGroup);
        });
        
        return listContainer;
    },

    // 渲染周视图表头
    renderWeekHeader: function() {
            const header = document.createElement('div');
            header.className = 'week-header';
            
            // 添加时间列标题
            const timeHeader = document.createElement('div');
            timeHeader.className = 'week-header-cell';
            timeHeader.textContent = '时间';
            header.appendChild(timeHeader);
            
            // 添加每天的标题
            const weekDates = utils.getWeekDates(currentDate);
            weekDates.forEach(date => {
                const cell = document.createElement('div');
                cell.className = 'week-header-cell';
                cell.textContent = utils.formatDate(date);
                header.appendChild(cell);
            });
            
            return header;
        },
        
        // 渲染时间格子
        renderTimeGrid: function()  {
            const grid = document.createElement('div');
            grid.className = 'time-grid';
            
            // 生成时间标签（8:00-24:00）
            for (let hour = 8; hour <= 24; hour++) {
                // 添加时间标签
                const label = document.createElement('div');
                label.className = 'time-label';
                label.textContent = `${hour}:00`;
                grid.appendChild(label);
                
                // 为每天添加时间槽
                const weekDates = utils.getWeekDates(currentDate);
                weekDates.forEach(date => {
                    const slot = utils.createTimeSlot(date, hour);
                    grid.appendChild(slot);
                });
            }
            
            return grid;
        },
        
        // 渲染每日总结行
        renderSummaryRow: function(dailySummaries) {
            const summaryRow = document.createElement('div');
            summaryRow.className = 'summary-row';
            
            // 添加标题单元格
            const titleCell = document.createElement('div');
            titleCell.className = 'summary-cell summary-title';
            titleCell.textContent = '每日总结';
            summaryRow.appendChild(titleCell);
            
            // 为每天添加总结单元格
            const weekDates = utils.getWeekDates(currentDate);
            weekDates.forEach(date => {
                const dateStr = date.toISOString().split('T')[0];
                const cell = document.createElement('div');
                cell.className = 'summary-cell';
                
                // 如果有总结，显示总结内容
                if (dailySummaries[dateStr]) {
                    cell.textContent = dailySummaries[dateStr].description || '无内容';
                    cell.title = dailySummaries[dateStr].description || '';
                } else {
                    cell.textContent = '点击添加总结';
                }
                
                // 添加点击事件
                cell.addEventListener('click', () => {
                    UI.showDailySummaryForm(date, dailySummaries[dateStr]);
                });
                
                summaryRow.appendChild(cell);
            });
            
            return summaryRow;
        },
        
        // 渲染任务部分
        renderTasks:function(tasks){
            // 清除现有任务
            document.querySelectorAll('.task-item').forEach(el => el.remove());
            
            tasks.forEach(task => {
                // 确保正确处理时区
                const startDate = utils.convertToLocalTime(task.start_datetime);
                const endDate = utils.convertToLocalTime(task.end_datetime);

                 // 时区检查
                if (!startDate || !endDate) {
                    console.error('任务时间转换失败', task);
                    return;
                }
                
                console.log('任务时间信息:', {
                    任务标题: task.title,
                    原始开始时间: task.start_datetime,
                    转换后开始时间: startDate.toISOString(),
                    原始结束时间: task.end_datetime,
                    转换后结束时间: endDate.toISOString()
                });
                
                // 计算任务位置和高度
                const startHour = startDate.getHours() + startDate.getMinutes() / 60;
                const duration = (endDate - startDate) / (1000 * 60 * 60); // 小时
                
                // 输出更详细的日志，帮助调试时间问题
                console.log(`任务 "${task.title}" 详细时间信息:`, {
                    开始时间ISO: task.start_datetime,
                    开始时间本地: startDate.toString(),
                    开始小时: startHour,
                    结束时间ISO: task.end_datetime,
                    结束时间本地: endDate.toString(),
                    持续时间小时: duration,
                    时区偏移分钟: new Date().getTimezoneOffset()
                });
                
                if (startHour >= 8 && startHour <= 24) { // 只显示8:00-24:00之间的任务
                    const dayIndex = startDate.getDay() + 1; // 加1是因为第一列是时间标签
                    const rowStart = Math.floor((startHour - 8) * 60); // 减8是因为从8点开始
                    
                    const taskElement = document.createElement('div');
                    taskElement.className = 'task-item';
                    // 使用科目的颜色，如果没有则使用默认颜色
                    taskElement.style.backgroundColor = task.subject_color || '#3498db';
                    taskElement.style.top = `${rowStart}px`;
                    taskElement.style.height = `${duration * 60}px`; // 60px per hour
                    taskElement.textContent = task.title;
                    taskElement.dataset.taskId = task.id;
                    
                    // 添加拖拽功能
                    taskElement.draggable = true;
                    taskElement.addEventListener('dragstart', (e) => {
                        draggedTask = task;
                        e.dataTransfer.setData('text/plain', task.id);
                    });
                    
                    // 添加点击编辑功能
                    taskElement.addEventListener('click', () => {
                        UI.showTaskForm(task);
                    });
                    
                    // 找到对应的时间槽并添加任务
                    const dateStr = startDate.toISOString().split('T')[0];
                    const slot = document.querySelector(
                        `.time-slot[data-date="${dateStr}"][data-hour="${Math.floor(startHour)}"]`
                    );
                    if (slot) {
                        slot.appendChild(taskElement);
                    }
                }
            });
        },


        renderSummaryRow:function (dailySummaries) {
            const row = document.createElement('div');
            row.className = 'daily-summary-row';
            
            // 标题列
            const header = document.createElement('div');
            header.className = 'summary-header';
            header.textContent = '总结';
            row.appendChild(header);
            
            // 每天总结列
            const weekDates = utils.getWeekDates(currentDate);
            weekDates.forEach(date => {
                const dateStr = date.toISOString().split('T')[0];
              const cell = document.createElement('div');
              cell.className = 'summary-cell';
              cell.dataset.date = dateStr;
              
              const summary = dailySummaries[dateStr];
              

            //原先的内容显示逻辑被注释掉了
            //    if (summary && summary.description) {
            //     const content = document.createElement('div');
            //     content.className = 'summary-content';
            //     content.textContent = summary.description.length > 100 
            //       ? summary.description.substring(0, 100) + '...' 
            //       : summary.description;
            //     cell.appendChild(content);
            //   } else {
            //     const placeholder = document.createElement('div');
            //     placeholder.className = 'summary-placeholder';
            //     placeholder.textContent = '请填写';
            //     cell.appendChild(placeholder);
            //   }
            //下面是重构后的逻辑：
            cell.innerHTML = summary?.description 
            ? `<div class="summary-content">${formatSummaryText(summary.description)}</div>`
            : '<div class="summary-placeholder">请填写</div>';
              
              // 点击事件
            //   cell.addEventListener('click', () => {
            //     UI.showDailySummaryForm(date, summary || { description: '' });
            //   });
            //以下为重写的点击事件
            cell.addEventListener('click', (e) => {
                if (!e.target.closest('.edit-button')) { // 排除内部按钮的点击
                  const clickedDate = new Date(date);
                  UI.showDailySummaryForm(clickedDate, summary || { date: dateStr, description: '' });
                }
              });
              
              row.appendChild(cell);
            });
            
            return row;
          }
    };

        // 辅助函数：格式化总结文本
    function formatSummaryText(text) {
        return text.length > 100 
        ? text.substring(0, 100) + '...' 
        : text;
    }

        //renderTask 函数--渲染单个任务元素
        // 计算任务的开始时间和持续时间，并将其添加到对应的时间槽中
        

    
    // 初始化日历
    /**
     * 初始化函数，用于为页面添加拖拽事件处理
     */
    function init() {
        // 添加拖拽事件处理
        document.addEventListener('dragover', (e) => {
            e.preventDefault();
            const slot = e.target.closest('.time-slot');
            if (slot) {
                slot.style.backgroundColor = '#f0f9ff';
            }
        });
        
        document.addEventListener('dragleave', (e) => {
            const slot = e.target.closest('.time-slot');
            if (slot) {
                slot.style.backgroundColor = '';
            }
        });
        
        document.addEventListener('drop', async (e) => {
            e.preventDefault();
            const slot = e.target.closest('.time-slot');
            if (slot && draggedTask) {
                const date = new Date(slot.dataset.date);
                const hour = parseInt(slot.dataset.hour);
                date.setHours(hour);
                
                // 计算新的开始和结束时间
                const oldStart = new Date(draggedTask.start_datetime);
                const oldEnd = new Date(draggedTask.end_datetime);
                const duration = oldEnd - oldStart;
                
                const newStart = date;
                const newEnd = new Date(newStart.getTime() + duration);
                
                try {
                    await TaskAPI.tasks.move(draggedTask.id, {
                        start_datetime: newStart.toISOString(),
                        end_datetime: newEnd.toISOString()
                    });
                    
                    // 更新本地任务数据
                    await Calendar.fetchTasks();
                } catch (error) {
                    console.error('移动任务失败:', error);
                    UI.showError('移动任务失败');
                }
                
                slot.style.backgroundColor = '';
                draggedTask = null;
            }
        });
    }
    
    // 当前视图状态
    let currentView = 'week';
    
    // 公开API
    return {
        init: function() {
            init(); // 调用私有的init函数
        },
        
        // 切换视图
        changeView: function(viewName) {
            currentView = viewName;
            this.render({ tasks: this.tasks || [], dailySummaries: this.dailySummaries || {} });
        },
        
        render: function ({tasks, dailySummaries}) {
            const container = document.querySelector('.calendar-grid');
            if (!container) return;

            // 更新内部状态
            this.tasks = tasks;
            this.dailySummaries = dailySummaries;
            
            container.innerHTML = '';
            container.appendChild(render.renderHeader());
            
            // 根据当前视图渲染不同的内容
            switch (currentView) {
                case 'month':
                    container.classList.add('month-view');
                    container.classList.remove('week-view', 'day-view', 'list-view');
                    // 渲染月视图
                    container.appendChild(render.renderMonthView());
                    break;
                    
                case 'week':
                    container.classList.add('week-view');
                    container.classList.remove('month-view', 'day-view', 'list-view');
                    container.appendChild(render.renderWeekHeader());
                    container.appendChild(render.renderTimeGrid());
                    break;
                    
                case 'day':
                    container.classList.add('day-view');
                    container.classList.remove('month-view', 'week-view', 'list-view');
                    container.appendChild(render.renderDayHeader());
                    container.appendChild(render.renderDayGrid());
                    break;
                    
                case 'list':
                    container.classList.add('list-view');
                    container.classList.remove('month-view', 'week-view', 'day-view');
                    container.appendChild(render.renderListView());
                    break;
            }
            
            render.renderTasks(tasks); // 使用render对象的方法
            container.appendChild(render.renderSummaryRow(dailySummaries)); // 新增每日总结行渲染

        },
        
        setTasks: (newTasks) => {
            tasks = newTasks;
            render.tasks();
        },
        
        /**
         * 异步获取任务，4月10日21点15分注释拆分为任务和总结数据分开获取
         */
        // async fetchTasks() {
        //     try {
        //         const weekDates = utils.getWeekDates(currentDate); //获取当前日期所在周的日期范围，返回的是一个日期数组
        //         const startDate = weekDates[0];
        //         const endDate = weekDates[6]; //日期的起始确定
        //         endDate.setHours(23, 59, 59);
                
        //         // 并行获取任务和每日总结
        //         const [fetchedTasks, fetchedSummaries] = await Promise.all([
        //             TaskAPI.tasks.getByDateRange(startDate.toISOString(),endDate.toISOString()),
        //             Promise.all(weekDates.map(date =>TaskAPI.dailySummaries.getByDate(date)
        //                 .then(summaries => ({
        //                     date: date.toISOString().split('T')[0],
        //                     summary: summaries[0] || null
        //                 }))
        //                 .catch(() => ({
        //                     date: date.toISOString().split('T')[0],
        //                     summary: null
        //                 }))
        //             ))

        //         ]);

                
        //         // 更新每日总结数据
        //         dailySummaries = {};
        //         fetchedSummaries.forEach(({date, summary}) => {
        //             if (summary) {
        //                 dailySummaries[date] = summary;
        //             }
        //         });
                
        //         Calendar.setTasks(fetchedTasks);
        //     } catch (error) {
        //         console.error('获取任务失败:', error);
        //         UI.showError('获取任务失败');
        //     }
        // }
        async fetchTasks() {
            try {
              const weekDates = utils.getWeekDates(currentDate);
              const startDate = weekDates[0];
              const endDate = weekDates[6];
              endDate.setHours(23, 59, 59);
          
              // 并行获取任务和每日总结
              const [tasks, summaries] = await Promise.all([
                TaskAPI.tasks.getByDateRange(startDate.toISOString(),endDate.toISOString()),
                this.fetchDailySummaries(weekDates) // 新增专用方法
              ]);
          
              // 更新数据
              this.setData(tasks, summaries);
              // 触发重新渲染
              this.render({      
                    tasks,
                    dailySummaries: this.processSummaries(summaries)
                });
              
            } catch (error) {
              console.error('获取数据失败:', error);
              UI.showError('获取数据失败');
            }
          },
          
          // 新增方法：专门获取每日总结
          async fetchDailySummaries(weekDates) {
            const summaryPromises = weekDates.map(date => 
              TaskAPI.dailySummaries.getByDate(date)
                .then(res => ({
                  date: date.toISOString().split('T')[0],
                  data: res[0] || null // 假设API返回数组
                }))
                .catch(err => {
                  console.error(`获取${date}总结失败:`, err);
                  return { date: date.toISOString().split('T')[0], data: null };
                })
            );
            return await Promise.all(summaryPromises);
          },
          
          // 新增方法：统一更新数据
          setData(tasks, summaries) {
            this.tasks = tasks;
            
            // 转换总结数据格式 { date: summary }
            this.dailySummaries = this.processSummaries(summaries);
          },
          
          // 处理总结数据为合适的格式
          processSummaries(summaries) {
            return summaries.reduce((acc, {date, data}) => {
              if (data) acc[date] = data;
              return acc;
            }, {});
          }
    };
})();

// 点击每日总结行时，显示每日总结表单
UI.showDailySummaryForm = async (date, existingSummary) => {
    // 创建模态框
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>${date.toLocaleDateString('zh-CN')} 每日总结</h3>
                <button class="close-button">&times;</button>
            </div>
            <div class="modal-body">
                <textarea id="summary-description" 
                    placeholder="请输入今日总结..."
                    rows="5"
                    style="width: 100%; padding: 8px;"
                >${existingSummary?.description || ''}</textarea>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" id="cancel-summary-button">取消</button>
                <button class="btn btn-primary" id="save-summary-button">保存</button>
            </div>
        </div>
    `;

    // 添加模态框样式
    const style = document.createElement('style');
    style.textContent = `
        .modal {
            display: block;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.4);
        }
        .modal-content {
            background-color: #fefefe;
            margin: 15% auto;
            padding: 20px;
            border: 1px solid #888;
            width: 50%;
            border-radius: 5px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .close-button {
            background: none;
            border: none;
            font-size: 1.5em;
            cursor: pointer;
        }
        .modal-footer {
            margin-top: 15px;
            display: flex;
            justify-content: flex-end;
            gap: 10px;
        }
        #summary-description {
            resize: vertical;
            min-height: 100px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
    `;
    document.head.appendChild(style);
    document.body.appendChild(modal);

    // 事件处理
    const closeModal = () => {
        document.body.removeChild(modal);
        document.head.removeChild(style);
    };

    // 关闭按钮事件
    modal.querySelector('.close-button').addEventListener('click', closeModal);
    modal.querySelector('#cancel-summary-button').addEventListener('click', closeModal);

    // 点击模态框外部关闭
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    // 保存按钮事件
    modal.querySelector('#save-summary-button').addEventListener('click', async () => {
        const description = document.querySelector('#summary-description').value;
        try {
            await TaskAPI.dailySummaries.create({
                date: date.toISOString().split('T')[0],
                description,
                id: existingSummary?.id // 如果是更新，传入ID
            });
            
            // 保存成功后刷新日历内容
            await Calendar.fetchTasks();
            closeModal();
            
            // 显示成功提示
            UI.showMessage('保存成功', 'success');
        } catch (error) {
            console.error('保存每日总结失败:', error);
            UI.showError('保存每日总结失败');
        }
    });
};