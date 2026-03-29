

document.addEventListener('DOMContentLoaded', function() {
    // 获取元素
    const timerWidget = document.getElementById('timer-widget');
    const notesWidget = document.getElementById('notes-widget');
    const timerTrigger = document.getElementById('timer-trigger');
    const notesTrigger = document.getElementById('notes-trigger');
    const backToTopTrigger = document.getElementById('back-to-top');

    // 回到顶部功能
    backToTopTrigger.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });


    // 存储radioGroup实例和当前选中值
    let radioGroupInstance = null;
    let currentSelectedValue = 'thinking';
    let currentSelectedLabel = '思考';

    // 初始化radioGroup
    if (window.antd && window.React && window.ReactDOM) {
        const options = [
            { label: '调研', value: 'research' },
            { label: '思考', value: 'thinking' },
            { label: '沟通', value: 'communication' },
            { label: '实施', value: 'implementation' },
            { label: '复盘', value: 'retrospective' },
            { label: '流程步骤', value: 'process_step' },
            { label: '其他', value: 'other' }
        ];
        
        const handleChange = (e) => {
            currentSelectedValue = e.target.value;
            currentSelectedLabel = options.find(
                opt => opt.value === currentSelectedValue
            )?.label || '思考';
            console.log('当前选择的任务类型:', currentSelectedValue);
            console.log('当前选择的任务类型标签:', currentSelectedLabel);
        };

        const radioGroup = React.createElement(antd.Radio.Group, {
            defaultValue: 'thinking',
            name: "study-type",
            optionType: "button",
            buttonStyle: "solid",
            size: "small",
            options: options,
            onChange: handleChange
        });
        
        radioGroupInstance = ReactDOM.render(
            radioGroup,
            document.getElementById('study-type-radios')
        );
        
        // 初始化默认值
        currentSelectedValue = 'thinking';
        currentSelectedLabel = '思考';
    }
    
    // 初始化状态
    let currentOpenWidget = null;
    
    // 设置初始样式
    timerWidget.style.display = 'none';
    notesWidget.style.display = 'none';
    
    // 计时器功能
    const timerDisplay = timerWidget.querySelector('.timer-display');
    let timerInterval;
    // 初始化计时器状态
    let seconds = localStorage.getItem('timerSeconds') ? parseInt(localStorage.getItem('timerSeconds')) : 0;
    let startTime;
    
    function updateDisplay() {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        timerDisplay.textContent = 
            `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        localStorage.setItem('timerSeconds', seconds);
    }
    
    // 自动开始计时器(延迟3秒)
    setTimeout(() => {
        if (!timerInterval) {
            console.log('自动开始计时器');
            startTime = new Date();
            timerInterval = setInterval(() => {
                seconds++;
                updateDisplay();
            }, 1000);
            // 触发呼吸动画
            timerTrigger.classList.add('timer-active');
            // 显示计时器面板
            // timerWidget.style.display = 'block';
            currentOpenWidget = timerWidget;
        }
    }, 3000);
    
    // 切换浮窗函数
    function toggleWidget(widget) {
        if (currentOpenWidget === widget) {
            // 点击当前打开的浮窗，关闭它
            widget.style.display = 'none';
            currentOpenWidget = null;
        } else {
            // 关闭当前浮窗（如果有）
            if (currentOpenWidget) {
                currentOpenWidget.style.display = 'none';
            }
            // 打开新浮窗
            widget.style.display = 'block';
            currentOpenWidget = widget;
        }
    }
    
    // 绑定事件
    timerTrigger.addEventListener('click', () => toggleWidget(timerWidget));
    notesTrigger.addEventListener('click', () => toggleWidget(notesWidget));
    
    // 计时器控制
    timerWidget.querySelector('.timer-control.start').addEventListener('click', () => {
        if (!timerInterval) {
            startTime = new Date();
            timerInterval = setInterval(() => {
                seconds++;
                updateDisplay();
            }, 1000);
            // 添加呼吸动效
            timerTrigger.classList.add('timer-active');
            // 隐藏计时器面板
            timerWidget.style.display = 'none';
        }
    });
    
    timerWidget.querySelector('.timer-control.stop').addEventListener('click', () => {
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
            // 移除呼吸动效
            timerTrigger.classList.remove('timer-active');
            // 显示计时器面板
            timerWidget.style.display = 'block';
        }
    });
    
    timerWidget.querySelector('.timer-control.reset').addEventListener('click', () => {
        clearInterval(timerInterval);
        timerInterval = null;
        seconds = 0;
        localStorage.removeItem('timerSeconds');
        updateDisplay();
        timerWidget.querySelector('.description-input').value = '';
        // 移除呼吸动效
        timerTrigger.classList.remove('timer-active');
        // 显示计时器面板
        timerWidget.style.display = 'block';
    });

    timerWidget.querySelector('.timer-control.change').addEventListener('click', () => {
        // 创建自定义弹窗
        const modal = document.createElement('div');
        modal.style.position = 'fixed';
        modal.style.top = '0';
        modal.style.left = '0';
        modal.style.width = '100%';
        modal.style.height = '100%';
        modal.style.backgroundColor = 'rgba(38, 35, 35, 0.5)';
        modal.style.display = 'flex';
        modal.style.justifyContent = 'center';
        modal.style.alignItems = 'center';
        modal.style.zIndex = '1000';
        
        // 弹窗内容
        const modalContent = document.createElement('div');
        modalContent.style.backgroundColor = 'white';
        modalContent.style.padding = '20px';
        modalContent.style.borderRadius = '8px';
        modalContent.style.width = '300px';
        
        // 计算当前时分秒
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        // 创建输入框
        modalContent.innerHTML = `
            <h3 style="margin-top: 0">修改计时器时间</h3>
            <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                <div>
                    <label>小时</label>
                    <input type="number" id="edit-hours" min="0" value="${hours}" style="width: 60px; padding: 5px;border: 2px solid #3199eeff; border-radius: 6px; transition: all 0.3s ease;">
                </div>
                <div>
                    <label>分钟</label>
                    <input type="number" id="edit-minutes" min="0" max="59" value="${minutes}" style="width: 60px; padding: 5px;border: 2px solid #cbb244ff; border-radius: 6px; transition: all 0.3s ease;">
                </div>
                <div>
                    <label>秒</label>
                    <input type="number" id="edit-seconds" min="0" max="59" value="${secs}" style="width: 60px; padding: 5px; border: 2px solid #72767aff; border-radius: 6px; transition: all 0.3s ease;">
                </div>
            </div>
            <div style="display: flex; justify-content: flex-end; gap: 10px;">
                <button id="cancel-edit" style="padding: 5px 10px;">取消</button>
                <button id="confirm-edit" style="padding: 5px 10px; background: #1890ff; color: white; border: 2px;">确定</button>
            </div>
        `;
        
        modal.appendChild(modalContent);
        document.body.appendChild(modal);
        
        // 绑定事件
        document.getElementById('cancel-edit').addEventListener('click', () => {
            document.body.removeChild(modal);
        });
        
        document.getElementById('confirm-edit').addEventListener('click', () => {
            const hoursInput = parseInt(document.getElementById('edit-hours').value) || 0;
            const minutesInput = parseInt(document.getElementById('edit-minutes').value) || 0;
            const secondsInput = parseInt(document.getElementById('edit-seconds').value) || 0;
            
            if (minutesInput >= 60 || secondsInput >= 60) {
                alert('分钟和秒数必须小于60');
                return;
            }
            
            if (hoursInput < 0 || minutesInput < 0 || secondsInput < 0) {
                alert('时间值不能为负数');
                return;
            }
            
            // 计算总秒数
            seconds = hoursInput * 3600 + minutesInput * 60 + secondsInput;
            updateDisplay();
            localStorage.setItem('timerSeconds', seconds);
            document.body.removeChild(modal);
        });
    });

    // 保存记录功能
    timerWidget.querySelector('.timer-save').addEventListener('click', () => {
        const description = timerWidget.querySelector('.description-input').value;
        if (!description.trim()) {
            alert('请填写任务内容');
            return;
        }
        // 组装数据
        // 获取当前时间戳作为created_date
        const now = new Date();
        const currentDate = now.toISOString().split('T')[0]; // YYYY-MM-DD格式的日期字符串
        const endTime = startTime ? 
            new Date(startTime.getTime() + seconds * 1000).toISOString() : 
            new Date().toISOString();
        
        
        // 使用状态变量获取选中项
        const selectedValue = currentSelectedValue;
        const selectedLabel = currentSelectedLabel;
        console.log('当前选择的任务类型:', selectedValue);
        console.log('当前选择的任务类型标签:', selectedLabel);

        
        const data = {
            user: document.body.dataset.userId || null,
            start_time: startTime ? startTime.toISOString() : new Date().toISOString(),
            end_time: endTime,
            duration: seconds,
            page_type: selectedValue,
            chapter: document.body.dataset.chapterId,
            learning_content: description,
            description: description,
            created_date: currentDate,  // 必填字段
            subject_name: document.querySelector('[data-subject-name]')?.dataset.subjectName || '未命名科目',
            chapter_name: document.querySelector('[data-chapter-name]')?.dataset.chapterName || '未命名章节'
        };
        console.log('提交数据:', data);
        // 数据提交函数
        fetch('/courses/api/study-records/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        })
        .then(res => {
            if (!res.ok) throw new Error('Network response was not ok');
            return res.json();
        })
        .then(() => {
            // 使用antd的message提示
            if (typeof antd !== 'undefined' && antd.message) {
                antd.message.success({
                    content: '记录已保存!',
                    duration: 2,
                    className: 'custom-message-notice'
                });
            } else {
                // 回退方案
                const toast = document.createElement('div');
                toast.textContent = '记录已保存!';
                toast.style.position = 'fixed';
                toast.style.bottom = '20px';
                toast.style.left = '50%';
                toast.style.transform = 'translateX(-50%)';
                toast.style.backgroundColor = '#4CAF50';
                toast.style.color = 'white';
                toast.style.padding = '12px 24px';
                toast.style.borderRadius = '4px';
                toast.style.zIndex = '1000';
                toast.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
                document.body.appendChild(toast);
                setTimeout(() => {
                    document.body.removeChild(toast);
                }, 2000);
            }
            
            // 重置计时器状态
            clearInterval(timerInterval);
            timerInterval = null;
            seconds = 0;
            updateDisplay();
            timerWidget.querySelector('.description-input').value = '';
            timerTrigger.classList.remove('timer-active');
            timerWidget.style.display = 'none';
            currentOpenWidget = null;
        })
        .catch(err => {
            console.error('提交失败 - 完整错误:', err);
            throw err;
        });
    })
    
    // 笔记功能
    const notesInput = notesWidget.querySelector('.notes-input');
    notesInput.value = localStorage.getItem('learningNotes') || '';
    
    notesWidget.querySelector('.notes-save').addEventListener('click', () => {
        const content = notesInput.value.trim();
        if (content) {
            localStorage.setItem('learningNotes', content);
            alert('笔记已保存!');
        }
    });
    
    
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }
    updateDisplay(); 

})
