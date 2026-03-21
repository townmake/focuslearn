

// 从全局配置获取参数
const exercise_set_id = window.quizConfig.reviewSetId;
const exerciseSetUrl = window.quizConfig.reviewSetUrl;
const submitUrl = window.quizConfig.submitUrl;
const csrfToken = window.quizConfig.csrfToken;


// 初始化状态
let hidden = true; // 隐藏状态，默认为true
let currentExerciseIndex = 0;
let timeSpent;
let exercises = [];
let userAnswers = {}; //单放答案
// 存放答题记录 及其他更新数据
let answerRecords = {
    exercise_set_id: exercise_set_id,
    start_time: new Date().toISOString(),
    answers: {},     // 存放答题记录
    total_time: 0
};
let per_startTime = new Date();
let ratingStates = {};

// 添加防连续点击标志位
let isPrevButtonProcessing = false;
let isNextButtonProcessing = false;
let isShowButtonProcessing = false;
let isSubmitButtonProcessing = false;

const { Rate } = antd;

// 自定义开关组件
const ToggleSwitch = ({ value, onChange, label }) => {
    return (
        <label className="toggle-switch">
            <span className="toggle-switch-label">{label}</span>
            <input
                type="checkbox"
                checked={value}
                onChange={(e) => onChange(e.target.checked)}
            />
            <span className="slider"></span>
        </label>
    );
};
// 评分组件
const RatingComponent = ({ exerciseData , onUpdate }) => {
    const [answer, setAnswer] = React.useState(exerciseData.answer);
    const [difficulty, setDifficulty] = React.useState(exerciseData.difficulty || 3);
    const [memoryLevel, setMemoryLevel] = React.useState(exerciseData.memory_level || 3);
    const [masteryLevel, setMasteryLevel] = React.useState(exerciseData.mastery_level || 3);
    const [isCorrect, setCorrect] = React.useState(exerciseData.is_correct || false);


        // 统一更新逻辑
        const handleChange = (type, value) => {
            const updates = {
                answer: setAnswer,
                difficulty: setDifficulty,
                memory_level: setMemoryLevel,
                mastery_level: setMasteryLevel,
                is_correct: setCorrect,
                // 其他状态同理...
            };
            updates[type](value);
            onUpdate({ [type]: value }); // 触发父级更新
        };

    return (
        <div className="quiz-rating">
            <h3>参考答案</h3>
            <textarea 
                value={answer} 
                onChange={e => handleChange('answer', e.target.value)} 
            />

            <h3>习题评分</h3>
            <div>
                <span>难度：</span>
                <Rate 
                    value={difficulty} 
                    onChange={v => handleChange('difficulty', v)}
                />
            </div>
            <div>
                <span>记忆度：</span>
                <Rate 
                    value={memoryLevel} 
                    onChange={v => handleChange('memory_level', v)} 
                />
            </div>
            <div>
                <span>掌握度：</span>
                <Rate 
                    value={masteryLevel} 
                    onChange={v => handleChange('mastery_level', v)}
                />
            </div>
            <div>
                <ToggleSwitch
                    value={isCorrect}
                    onChange={(value) => handleChange('is_correct', value)}
                    label="是否正确："
                />
            </div>
        </div>
    );
};

// 初始化入口
function initializeApp() {
    if (!checkDependencies()) return;
    // 初始化事件监听
    setupEventListeners();
    // 开始初始化测验
    initQuiz();
}

// 确保依赖已加载
function checkDependencies() {
    if (!window.React || !window.ReactDOM || !window.antd || !window.quizConfig) {
        console.error('Missing required dependencies');
        document.getElementById('quiz-content').innerHTML = `
            <div class="error-message">系统初始化失败，请刷新页面</div>
        `;
        return false;
    }
    return true;
}

function setupEventListeners() {
    document.getElementById('prev-btn').addEventListener('click', handlePrevButtonClick);

    document.getElementById('show-btn').addEventListener('click', () => {
        if (isShowButtonProcessing) return;
        isShowButtonProcessing = true;
        showRate();
        setTimeout(() => {
            isShowButtonProcessing = false;
        }, 500);
    });

    document.getElementById('next-btn').addEventListener('click',handleNextButtonClick);

    document.getElementById('submit-btn').addEventListener('click', () => {
        if (isSubmitButtonProcessing) return;
        isSubmitButtonProcessing = true;
        saveCurrentAnswer(); 
        console.log("[Debug]存储的全局变量ratingStates", ratingStates);
        showConfirmation();
        // submitQuiz();
        setTimeout(() => {
            isSubmitButtonProcessing = false;
        }, 500);
    });
}

function handlePrevButtonClick() {
    if (isPrevButtonProcessing) return; // 如果正在处理，则直接返回
    isPrevButtonProcessing = true; // 设置标志位为真，表示正在处理

    saveCurrentAnswer();
    loadExercise(currentExerciseIndex - 1).finally(() => {
        isPrevButtonProcessing = false; // 处理完成后重置标志位
    });
}

function handleNextButtonClick() {
    if (isNextButtonProcessing) return; // 如果正在处理，则直接返回
    isNextButtonProcessing = true; // 设置标志位为真，表示正在处理
    console.log("[Debug]存储的全局变量ratingStates", ratingStates);

    saveCurrentAnswer();
    loadExercise(currentExerciseIndex + 1).finally(() => {
        isNextButtonProcessing = false; // 处理完成后重置标志位
    });
}



//（1） 初始化答题
async function initQuiz() {
    //设定答题开始时间
    const startTime = new Date();
    document.querySelector('body').dataset.startTime = startTime;
    try {
        // 通过练习集ID 获取练习集下的所有习题 及 习题数量 // 更新总题数显示
        const response = await fetch(exerciseSetUrl);
        exercises = await response.json();        
        document.getElementById('total-exercises').textContent = exercises.length;
        
        loadExercise(0); // 加载第一道题
    } catch (error) {
        document.getElementById('quiz-content').innerHTML = `
            <div class="error-message">加载失败: ${error.message}</div>
        `;
    }
}

// （2）加载指定索引的习题
/**

 */
async function loadExercise(index) {
    console.log("[Debug]loadExercise", index);
    if (index < 0 || index >= exercises.length) return;

    // 记录上一题答题时间，初始currentExerciseIndex = 0; 0->1 点击下一题时，还是会存0
    if (currentExerciseIndex >= 0 && exercises[currentExerciseIndex]) {

    }
    //延后赋值，使得能记录正确的第一题数据，但最后一题记不住
    const now = new Date();
    timeSpent = Math.floor((now - per_startTime) / 1000);
    currentExerciseIndex = index; 
  
    //设置正确的习题索引，并更新UI显示
    document.getElementById('current-exercise').textContent = index + 1;
    if (index === exercises.length - 1) {
        document.getElementById('next-btn').style.display = 'none';
        document.getElementById('submit-btn').style.display = 'inline-block';
    } else {
        document.getElementById('next-btn').style.display = 'inline-block';
        document.getElementById('submit-btn').style.display = 'none';
    }
    document.getElementById('prev-btn').disabled = index === 0;

    // 更新习题开始时间-每道题单独记录时间点
    per_startTime = new Date();

    // 加载习题内容
    try {
        let data = exercises[index]; // 习题数据对象，其实可以不用加载，完形和阅读理解不参与快答

        renderExercise_quiz(data);
    } catch (error) {
        document.getElementById('quiz-content').innerHTML = `
            <div class="error-message">加载习题失败: ${error.message}</div>
        `;
    };
}

// 渲染习题
function renderExercise_quiz(exerciseData) {
    //简化习题渲染逻辑，快答题模，不渲染子题
    const container = document.getElementById('quiz-content');
    container.innerHTML = renderQuestion(exerciseData);  
    // 评分组件清除—避免显示上一题答案，同时组件收起
    const rateContainer = document.getElementById('rate-container');
    ReactDOM.unmountComponentAtNode(rateContainer); 

    // 评分组件初始化
    ratingStates[exerciseData.id] = { 
        ...exerciseData, //创建对象，包含习题数据，和answer等参数
        answer: '',
        difficulty: 0,
        memoryLevel: 0,
        masteryLevel: 0,
        isCorrect:true, // 默认为正确，后续根据答案判断
    };

    ReactDOM.render(
        <RatingComponent // 评分组件传入习题数据对象和更新回调函数
            exerciseData={exerciseData}
            onUpdate={(updates) => {
                ratingStates[exerciseData.id] = {
                    ...ratingStates[exerciseData.id], // 回调函数，更新数据合并到 ratingStates[exerciseData.id] 
                    ...updates
                };
            }}
        />,
        rateContainer
    );
    rateContainer.classList.remove('visible');
    rateContainer.classList.add('hidden');
    hidden=true;
    console.warn('[DEBUG] 习题渲染完成：', exerciseData.id);
}

// 渲染问题部分
function renderQuestion(question) {
    console.log('[DEBUG] 习题编号:', question.id);
    
    // 根据题型返回不同的HTML
    let html;
    switch(question.question_type) {
        //单选和多选一样
        case 'single_choice':
            if (!question.options) {
                console.error('[ERROR] 单选题缺少options字段');
                return '<div class="error-message">题目数据不完整</div>';
            }
            // 普通单选题
            html = `<div class="question">
                <h3>${question.content}</h3>
                <div class="options">
                    ${Object.entries(question.options).map(([key, value]) => `
                        <label>
                            <input type="radio" name="answer" value="${key}">
                            ${key}. ${value}
                        </label>
                    `).join('')}
                </div>
            </div>`;
            break;
        case 'multiple_choice':
            if (!question.options) {
                console.error('[ERROR] 多选题缺少options字段');
                return '<div class="error-message">题目数据不完整</div>';
            }
            html = `
                <div class="question">
                    <h3>${question.content}</h3>
                    <div class="options">
                        ${Object.entries(question.options).map(([key, value]) => `
                            <label>
                                <input type="checkbox" name="answer" value="${key}">
                                ${key}. ${value}
                            </label>
                        `).join('')}
                    </div>
                </div>
            `;
            break;
        case 'fill_blank':
            html = `
                <div class="question">
                    <h3>${question.content.replace('___', '<input type="text" name="answer">')}</h3>
                </div>
            `;
            break;
        case 'cloze_test':
            html = `
                <div class="question">
                    <span>完形填空不参与快答</span><br/>
                    <h3>${question.content}</h3>
                </div>
            `;
            break;
        case 'reading_answer':
            html = `
                <div class="question">
                    <span>阅读理解不参与快答</span><br/>
                    <h3>${question.content}</h3>
                </div>
            `;
            break;
        default:
            html = `
                <div class="question">
                    <h3>${question.content}</h3>
                    <textarea name="answer" rows="5"></textarea>
                </div>
            `;
    }

    // 添加历史答案提示
    if (userAnswers[question.id]) {
        let historyAnswer = '';
        if (typeof userAnswers[question.id] === 'object') {
            // 处理子题历史答案
            historyAnswer = Object.values(userAnswers[question.id])
                .map(a => `小题${a.order}: ${a.answer}`)
                .join('; ');
        } else {
            // 处理普通题历史答案
            historyAnswer = userAnswers[question.id];
        }
        html += `<div class="history-answer">您之前的答案为: ${historyAnswer}</div>`;
    }
    return html;
}

function showRate() {
    console.log('点击了评分组件',new Date());
    console.log('当前hidden值:', hidden);
    const rateContainer = document.getElementById('rate-container');
    if (!rateContainer) {
        console.error('未找到评分容器元素');
        return;
    }

    // 获取当前习题
    const currentExercise = exercises[currentExerciseIndex];
    if (!currentExercise) return;

    // 更新评分组件中的答案
    if (ratingStates[currentExercise.id]) {
        ratingStates[currentExercise.id].answer = currentExercise.answer;
    }

    // 重新渲染评分组件以显示正确答案
    ReactDOM.render(
        <RatingComponent
            exerciseData={{
                ...currentExercise,
                answer: currentExercise.answer // 确保显示正确答案
            }}
            onUpdate={(updates) => {
                ratingStates[currentExercise.id] = {
                    ...ratingStates[currentExercise.id],
                    ...updates
                };
            }}
        />,
        rateContainer
    );

    // 切换显示状态
    if (hidden === true) {
        rateContainer.classList.add('visible');
        rateContainer.classList.remove('hidden');
        hidden = false;

    } else {
        rateContainer.classList.remove('visible');
        rateContainer.classList.add('hidden');
        hidden = true;
    }
}


// 保存答案和评分
function saveCurrentAnswer() {

    const exercise = exercises[currentExerciseIndex]; // 获取当前习题数据对象
    const answerInputs = document.querySelectorAll(`[name="answer"]`);// 获取答案输入元素数组
    if (!answerInputs.length) {
        console.error('未找到答案输入元素');
        return;
    }
    try {
        if (exercise.question_type === 'multiple_choice') {
            const answersInput = Array.from(answerInputs)
                .filter(input => input.checked)
                .map(input => input.value);
            userAnswers[exercise.id] = answersInput.join(',');
        } else if (exercise.question_type === 'single_choice') {
            const selected = Array.from(answerInputs).find(input => input.checked);
            userAnswers[exercise.id] = selected?.value || '';
        } else {
            userAnswers[exercise.id] = answerInputs[0]?.value || '';
        }
        // 找到答案
        console.warn("rating",ratingStates);
        console.log("exercise-id", ratingStates[exercise.id]);
        //获取评分
        const currentRating = ratingStates[exercise.id] || {};
        answerRecords.answers[exercise.id] = {
            ...answerRecords.answers[exercise.id],
            difficulty: currentRating.difficulty || exercise.difficulty ||3,
            memory_level: currentRating.memory_level || exercise.memory_level ||3,
            mastery_level: currentRating.mastery_level || exercise.mastery_level ||3,
            answer: userAnswers[exercise.id],
            is_correct: currentRating.is_correct||null,
            time_spent: timeSpent,
            order: exercise.order,
            title: exercise.title
        };
        answerRecords.total_time += timeSpent;


        console.log('[DEBUG] 保存的数据:', answerRecords.answers[exercise.id]);
    // 移除缓存保存逻辑
    } catch (error) {
        console.error('保存答案时出错:', error);
    }
}

// 最后一题时提交，会显示弹窗确认提交
// async function submitQuiz() {
//     // 记录最后一道题
//     const now = new Date();
//     const currentExercise = exercises[currentExerciseIndex];
//     timeSpent = Math.floor((now - per_startTime) / 1000);
//     console.warn('最后一道题前保存数据：', answerRecords.answers);
//     answerRecords.answers[currentExercise.id].answer = userAnswers[currentExercise.id];
//     answerRecords.total_time += timeSpent;
//     console.warn('最后一道题赋值后保存数据：', answerRecords.answers);

    
//     // 显示确认弹窗
//     showConfirmation();
// }
// 显示确认弹窗
function showConfirmation() {
    const modal = document.createElement('div');
    modal.style.position = 'fixed';
    modal.style.top = '0';
    modal.style.left = '0';
    modal.style.width = '100%';
    modal.style.height = '100%';
    modal.style.backgroundColor = 'rgba(0,0,0,0.5)';
    modal.style.display = 'flex';
    modal.style.justifyContent = 'center';
    modal.style.alignItems = 'center';
    modal.style.zIndex = '1000';
    
    const modalContent = document.createElement('div');
    modalContent.style.backgroundColor = 'white';
    modalContent.style.padding = '20px';
    modalContent.style.borderRadius = '8px';
    modalContent.style.maxWidth = '600px';
    modalContent.style.width = '80%';
    modalContent.style.maxHeight = '80vh';
    modalContent.style.overflowY = 'auto';
    
    modalContent.innerHTML = `
        <h3 style="margin-bottom: 20px;">请确认您的答案</h3>
        <div class="answer-list" style="margin-bottom: 20px;">
            ${Object.values(answerRecords.answers).map(item => {
                let answerDisplay = item.answer || '未作答';
                return `
                <div class="answer-item" style="margin-bottom: 15px; padding: 10px; border-bottom: 1px solid #eee;">
                    <div style="font-weight: bold;">#${item.id} ${item.title}</div>
                    <div style="margin-top: 5px;">答案: ${answerDisplay}</div>
                    <div style="margin-top: 5px;">耗时: ${item.time_spent}秒</div>
                    <div style="margin-top: 5px;">难度: ${item.difficulty}</div>
                    <div style="margin-top: 5px;">记忆水平: ${item.memory_level}</div>
                    <div style="margin-top: 5px;">掌握水平: ${item.mastery_level}</div>
                    <div style="margin-top: 5px;">是否答对: ${item.is_correct}</div>
                </div>`;
            }).join('')}
        </div>
        <div style="display: flex; justify-content: space-between;">
            <button id="cancel-submit" class="ant-btn" style="margin-right: 10px;">返回修改</button>
            <button id="confirm-submit" class="ant-btn ant-btn-primary">确认提交</button>
        </div>
    `;
    
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // 返回修改按钮
    modalContent.querySelector('#cancel-submit').addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    // 确认提交按钮
    modalContent.querySelector('#confirm-submit').addEventListener('click', async () => {
        await doSubmit();
        document.body.removeChild(modal);
    });
}

// 实际提交函数
async function doSubmit() {
    console.log('[DEBUG] 提交答案:', userAnswers);
    try {
        const response = await fetch(submitUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                exercise_set_id: exercise_set_id,
                answers: answerRecords.answers,
                total_time: answerRecords.total_time
            })
        });
        
        const result = await response.json();
        if (response.ok) {
            if (result.redirect_url) {
                window.location.href = result.redirect_url;
            } else {
                alert(result.message || '提交成功');
            }
        } else {
            alert(result.message || '提交失败');
        }
    } catch (error) {
        alert('提交失败: ' + error.message);
    }
}


// 全局初始化函数
window.initializeQuizApp = function() {
    // 严格检查React是否可用
    const checkReact = () => {
        if (!window.React || !window.React.useState) {
            console.log('React not fully loaded, waiting...');
            setTimeout(checkReact, 100);
            return;
        }
        initializeApp();
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', checkReact);
    } else {
        checkReact();
    }
};

// 确保React完全加载后再初始化
if (typeof window.React !== 'undefined' && typeof window.quizConfig !== 'undefined') {
    // 额外检查React Hooks是否可用
    if (window.React.useState) {
        window.initializeQuizApp();
    } else {
        const reactObserver = new MutationObserver(() => {
            if (window.React.useState) {
                reactObserver.disconnect();
                window.initializeQuizApp();
            }
        });
        reactObserver.observe(document, { 
            childList: true, 
            subtree: true 
        });
    }
}
