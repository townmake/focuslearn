



// 渲染树：带超时机制的渲染函数
function renderKnowledgeTree(treeData) {
    const treeContainer = document.getElementById('knowledge-points-tree');

    //优化体验部分
    if (!treeContainer) {
        console.error('知识点树容器未找到');
        return;
    }
    // 显示加载状态
    treeContainer.innerHTML = '<div class="loading-spinner"></div>';
    
    // 设置渲染超时(5秒)
    const renderTimeout = setTimeout(() => {
        if (treeContainer.querySelector('.loading-spinner')) {
            console.warn('渲染超时，强制显示错误状态');
            treeContainer.innerHTML = `
                <div class="error-message">
                    渲染超时，请<a href="javascript:window.location.reload()">刷新页面</a>
                </div>
            `;
        }
    }, 5000);


    try {
        // console.group('渲染知识点树');
        const formattedData = formatTreeData(treeData);

        // 验证数据有效性
        if (!formattedData || formattedData.length === 0) {
            throw new Error('无效的树形数据');
        }

        // node.key很重要，用于后续加载详情,这里用的是id作为key
        const treeElement = React.createElement(antd.Tree, {
            showLine: true,
            treeData: formattedData,
            onSelect: (selectedKeys, {node}) => {
                if (node?.key) {
                    // 加载知识点详情
                    loadKnowledgePointDetail(node.key);
                    loadKnowledgePointAnnotations(node.key);
                }
            },
            onExpand: (expandedKeys, { expanded: isExpanded, node }) => {
                // 立即同步高度
                syncHeights();
                // 动画完成后最终确认
                if (isExpanded) {
                    setTimeout(syncHeights, 500);
                }
                else {  // 收缩
                    setTimeout(syncHeights, 500);
                }
            }
        });
        
        // 渲染到DOM并强制验证状态
        ReactDOM.render(treeElement, treeContainer, () => {
            clearTimeout(renderTimeout);
            
            // 强制检查渲染结果
            setTimeout(() => {
                if (!treeContainer.querySelector('.ant-tree')) {
                    console.warn('React渲染结果未显示，尝试恢复');
                    treeContainer.innerHTML = '';
                    ReactDOM.render(treeElement, treeContainer);
                }
            }, 100);
        });
        // 同步高度，并记录此刻右侧栏高度

        
    } catch (error) {
        clearTimeout(renderTimeout);
        console.error('渲染知识点树失败:', error);
        treeContainer.innerHTML = `
            <div class="error-message">
                渲染失败: ${error.message}
                <button onclick="window.location.reload()">重试</button>
            </div>
        `;
    } finally {
        console.groupEnd();
    }
}


// 优化后的树形数据格式化
function formatTreeData(data) {
    if (!data || !Array.isArray(data) || data.length === 0) {
        return [];
    }
    
    return data.map(item => {
        const node = {
            key: item.id,
            title: item.title
        };
        // 只有当有子节点时才递归处理
        if (item.children && item.children.length > 0) {
            // 对子节点按brother_id排序
            node.children = formatTreeData(item.children.sort((a, b) => {
                // 按brother_id从小到大排序
                if (a.brother_id !== undefined && b.brother_id !== undefined) {
                    return a.brother_id - b.brother_id;
                }
                // 其次使用created_at排序
                if (a.created_at && b.created_at) {
                    return new Date(a.created_at) - new Date(b.created_at);
                }
                return 0;
            }));
        }
        return node;
    });
}


// 异步获取树形数据
async function fetchTree(params = {}) {
    try {
        // 显示加载状态
        const treeContainer = document.getElementById('knowledge-points-tree');
        if (treeContainer) {
            treeContainer.innerHTML = '<div class="loading-state">加载中...</div>';
        }

        // 获取当前章节ID
        const chapterId = '{{chapter.id }}';
        if (!chapterId) {
            throw new Error('缺少章节ID参数');
        }

        // 构建查询参数
        const queryParams = new URLSearchParams(params).toString();
        const response = await fetch(`/courses/api/chapters/${chapterId}/knowledge-tree/?${queryParams}`, {
            headers: {
                'Accept': 'application/json',
                'X-CSRFToken': '{{ csrf_token }}'
            }
        });

        if (!response.ok) {
            throw new Error(`请求失败: ${response.status}`);
        }

        const responseData = await response.json();
        
        if (!responseData.tree_data || !Array.isArray(responseData.tree_data)) {
            throw new Error('无效的API响应格式');
        }

        return responseData.tree_data;
    } catch (error) {
        console.error('获取树数据失败:', error);
        throw error;
    }
}

// 增强版的知识点树加载———初始化清理完环境，就开始加载数据，加载数据后渲染树
async function loadKnowledgePoints() {
    const treeContainer = document.getElementById('knowledge-points-tree');
    if (!treeContainer) return;

    try {
        treeContainer.innerHTML = '<div class="loading-spinner"></div>';
        
        // 强制清除可能存在的旧数据
        if (treeContainer.querySelector('.ant-tree')) {
            ReactDOM.unmountComponentAtNode(treeContainer);
        }

        // 获取当前激活的筛选类型
        const activeType = document.querySelector('.icon-switcher .active')?.dataset.type;
        const params = activeType ? { type: activeType } : {};
        
        // 使用API获取数据
        const treeData = await fetchTree(params);
        
        if (!treeData || treeData.length === 0) {
            const treeContainer = document.getElementById('knowledge-points-tree');
            treeContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <img src="{% static 'images/empty-folder.png' %}" alt="空数据">
                    </div>
                    <h3>暂无知识点数据</h3>
                    <p>当前章节还没有添加任何知识点</p>
                    <button class="ant-btn ant-btn-primary" onclick="showAddModal_Knowledge(null)">
                        创建第一个知识点 
                    </button>
                </div>
            `;
            //按钮不显示
            const buttons = document.querySelectorAll('.action-buttons');
            buttons.forEach(btnGroup => {
                btnGroup.classList.add('hidden');  // 隐藏
                // btnGroup.classList.remove('hidden'); // 显示
                // btnGroup.classList.toggle('hidden'); // 切换
            });
            return;
        }

        // 渲染树
        renderKnowledgeTree(treeData);
        // 自动选中第一个知识点
        setTimeout(() => {
            const firstNode = document.querySelector('.ant-tree-node-content-wrapper');
            if (firstNode) {
                firstNode.click();
            }
        }, 300);
    } catch (error) {
        console.error('加载知识点失败:', error);
        
        const treeContainer = document.getElementById('knowledge-points-tree');
        if (treeContainer) {
            treeContainer.innerHTML = `<div class="error-state"> <h3>加载失败</h3> <p>${error.message}</p></div>`;
        }
    }
}

// 完整版的事件监听和初始化
let currentListeners = [];

function cleanupKnowledgePoints() {
    // 移除所有事件监听
    currentListeners.forEach(({element, type, handler}) => {
        element.removeEventListener(type, handler);
    });
    currentListeners = [];
    
    // 清理React组件
    const treeContainer = document.getElementById('knowledge-points-tree');
    if (treeContainer) {
        ReactDOM.unmountComponentAtNode(treeContainer);
        treeContainer.innerHTML = '';
    }
}

// 初始化知识点树加载逻辑——初始化后第一个调用，后续通过hash变化或tab点击触发重新加载
function initKnowledgePoints() {
    // 先清理现有状态
    cleanupKnowledgePoints();

    // 确保必要库已加载
    const checkDependencies = () => {
        if (!window.React || !window.ReactDOM || !window.antd) {
            console.warn('等待依赖库加载...');
            setTimeout(checkDependencies, 100);
            return false;
        }
        return true;
    };

    if (!checkDependencies()) return;

    // 添加tab点击监听
    document.querySelectorAll('[data-target="knowledge-points"]').forEach(tab => {
        const handler = () => {
            cleanupKnowledgePoints();
            loadKnowledgePoints();
        };
        tab.addEventListener('click', handler);
        currentListeners.push({element: tab, type: 'click', handler});
    });

    // 添加hash变化监听
    const hashHandler = () => {
        if (location.hash.includes('knowledge-points')) {
            cleanupKnowledgePoints();
            loadKnowledgePoints();
        }
    };
    window.addEventListener('hashchange', hashHandler);
    currentListeners.push({element: window, type: 'hashchange', handler: hashHandler});

    // 直接加载检查
    const shouldLoadDirectly = document.getElementById('knowledge-points')?.classList.contains('active') || location.hash.includes('knowledge-points');
    if (shouldLoadDirectly) {
        loadKnowledgePoints();
    }

    // 添加全局重载方法
    window.reloadKnowledgeTree = () => {
        cleanupKnowledgePoints();
        loadKnowledgePoints();
    };
    
    // 添加页面卸载时的清理
    window.addEventListener('beforeunload', cleanupKnowledgePoints);
    currentListeners.push({element: window, type: 'beforeunload', handler: cleanupKnowledgePoints});
}

// 根据评分类型获取容器ID
function getRatingContainerId(ratingType) {
    switch (ratingType) {
        case 'kp-difficulty':
            return 'kp-difficulty-container';
        case 'kp-memory-level':
            return 'kp-memory-level-container';
        case 'kp-mastery-level':
            return 'kp-mastery-level-container';
        default:
            console.error('未知评分类型:', ratingType);
            return '';
    }
}
// 转换数值为星星评级，知识点详情部分
function renderRating(value, max=5, containerId, firstRender=true) {
    const container = document.getElementById(containerId);
    if (!container) return;
    // 如果是非首次渲染，则移除之前的React组件
    if (!firstRender) {
        ReactDOM.unmountComponentAtNode(container);
    }
    // 清空容器内容
    container.innerHTML = '';
    
    // 创建Rate组件
    const Rate = antd.Rate;
    ReactDOM.render(
        React.createElement(Rate, {
            value: value,
            onChange: (newVal) => {
                saveRating(containerId.replace('-container', ''), newVal);
            }
        }),
        container
    );
}

// 保存评分到后台
function saveRating(ratingType, value) {
    const kpId = currentKnowledgePointId;
    if (!kpId) {
        console.error('知识点ID不存在');
        return;
    }
    
    const url = `/courses/api/knowledge-points/${kpId}/update-rating/`;
    const data = {
        rating_type: ratingType,
        value: value
    };
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token }}'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('保存失败');
        }
        return response.json();
    })
    .then(data => {
        antd.message.success('评分已保存'); 

       // 直接更新星星评分组件
        const containerId = getRatingContainerId(ratingType);
        renderRating(value, 5, containerId, false);
    })
    .catch(error => {
        console.error('保存评分失败:', error);
        antd.message.error('保存评分失败');
    });
}

// 可编辑字段配置
const editableFields = [
    {
        id: 'kp-title',
        field: 'title',
        type: 'text',
        validate: (value) => value.trim() !== ''
    },
    {
        id: 'kp-description',
        field: 'description',
        type: 'text',
        validate: (value) => true
    },
    {
        id: 'kp-brother_id',
        field: 'brother_id',
        type: 'number',
        validate: (value) => !isNaN(value) && value > 0
    }
];

// 加载知识点详情
function loadKnowledgePointDetail(kpId) {
    // 确保ID是字符串类型
    currentKnowledgePointId = String(kpId);
    document.getElementById('kp-id').value = currentKnowledgePointId;
    fetch(`/courses/knowledge-points/${kpId}/`)
        .then(response => response.json())
        .then(data => {
            // 更新右侧面板所有字段
            editableFields.forEach(fieldConfig => {
                const element = document.getElementById(fieldConfig.id);
                if (element) {
                    const value = data[fieldConfig.field];
                    element.textContent = value !== undefined ? value : fieldConfig.default || '';
                    element.setAttribute('data-original-value', element.textContent);
                    element.setAttribute('contenteditable', 'false');
                }
            });

            // 使用新的评分渲染方法
            renderRating(data.difficulty, 5, 'kp-difficulty-container',false);
            renderRating(data.memory_level, 5, 'kp-memory-level-container',false);
            renderRating(data.mastery_level, 5, 'kp-mastery-level-container',false);

            document.getElementById('kp-parent').textContent = 
                data.parent ? data.parent_title : "根节点";
            

            // 更新AiEditor编辑器内容,window.AiEditor_knowledge
            if (window.AiEditor_knowledge) {
                window.AiEditor_knowledge.setContent(data.content); // 设置编辑器内容
            } else {
                console.error('window.AiEditor_knowledge未初始化');
            }

            // 设置编辑/删除按钮的ID
            document.getElementById('tree-delete-btn').dataset.kpId = kpId;
            document.getElementById('add-child-btn').dataset.parentId = kpId;
            document.getElementById('add-root-btn').dataset.parentId = null;// 根节点的父ID设为null
        });
}

// 启用编辑模式
function startEdit(element) {
    const fieldConfig = editableFields.find(f => f.id === element.id);
    if (!fieldConfig) return;
    
    element.setAttribute('contenteditable', 'true');
    element.focus();
    // 保存原始内容以便比较
    if (!element.getAttribute('data-original-value')) {
        element.setAttribute('data-original-value', element.textContent);
    }
}

// 保存编辑内容
function saveEdit(element) {
    const fieldConfig = editableFields.find(f => f.id === element.id);
    if (!fieldConfig) return;
    
    element.setAttribute('contenteditable', 'false');
    const newValue = element.textContent.trim();
    const originalValue = element.getAttribute('data-original-value');
    
    if (newValue !== originalValue) {
        // 获取所有可编辑字段的值
        const allFields = editableFields.map(field => {
            const elem = document.getElementById(field.id);
            return {
                ...field,
                value: elem ? elem.textContent.trim() : ''
            };
        });
        
        currentKnowledgePointId = document.getElementById('kp-id').value;
        // 调用统一的保存函数
        saveMultipleFields(currentKnowledgePointId, allFields)
            .then(success => {
                if (success) {
                    // 更新所有字段的原始值
                    allFields.forEach(field => {
                        const elem = document.getElementById(field.id);
                        if (elem) {
                            elem.setAttribute('data-original-value', elem.textContent.trim());
                        }
                    });
                    //刷新页面
                    location.reload();
                }
            });
    }
}

// 保存多个字段
function saveMultipleFields(kpId, fields) {
    const fieldData = {};
    fields.forEach(field => {
        const element = document.getElementById(field.id);
        if (element) {
            const value = element.textContent.trim();
            if (field.validate(value)) {
                fieldData[field.field] = value;
            } else {
                antd.message.error(`${field.field}格式不正确`);
                return Promise.reject(`${field.field}格式不正确`);
            }
        }
    });

    return fetch(`/courses/knowledge-points/${kpId}/`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token }}'
        },
        body: JSON.stringify(fieldData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('保存失败');
        }
        return response.json();
    })
    .then(data => {
        antd.message.success('已保存');
        return true;
    })
    .catch(error => {
        console.error('保存失败:', error);
        antd.message.error('保存失败');
        return false;
    });
}


// 删除知识点
function deleteKnowledgePoint(kpId) {
    fetch(`/courses/knowledge-points/${kpId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': '{{ csrf_token }}'
        }
    })
    .then(response => {
        if (response.ok) {
            antd.message.success('删除成功');
            // 删除成功，重新加载知识点树
            initKnowledgePoints();
            setTimeout(() => {
                const firstNode = document.querySelector('.ant-tree-node-content-wrapper');
                if (firstNode) {
                    firstNode.click();
                }else{
                    // 树已空，重置当前选中知识点
                    currentKnowledgePointId = null;
                    // 清空右侧面板内容 
                    document.getElementById('kp-title').textContent = '';
                    document.getElementById('kp-description').textContent = '';
                    document.getElementById('kp-difficulty').textContent = '';
                    document.getElementById('kp-memory-level').textContent = '';
                    document.getElementById('kp-mastery-level').textContent = '';
                    document.getElementById('kp-parent').textContent = '';
                    document.getElementById('kp-brother_id').textContent = '';
                    // 清空编辑器内容
                    if(window.AiEditor_knowledge) {
                        window.AiEditor_knowledge.setContent(''); // 清空编辑器内容
                    }
                }
            }, 300);
        } else {
            throw new Error('删除失败');
        }
    })
    .catch(error => {
        antd.message.error(error.message);
    });
}

// 显示添加知识点模态框
function showAddModal_Knowledge(parentId) {
    let difficulty = 3;
    let memoryLevel = 3;
    let masteryLevel = 3;
    const parent_null = parentId===null;
    
    const setDifficulty = (value) => difficulty = value;
    const setMemoryLevel = (value) => memoryLevel = value;
    const setMasteryLevel = (value) => masteryLevel = value;

    const modalContent = React.createElement('div', { style: { padding: '20px 0' } }, [
        React.createElement('div', { 
            key: 'type',
            className: 'modal-header-title' 
        }, 
            `添加${parent_null ? '章节根节点' : '子节点'}`),
        React.createElement('div', { key: 'title', style: { marginTop: '10px' } }, '知识点标题:'),
        React.createElement(antd.Input, {
            key: 'title-input',
            id: 'new-kp-title',
            placeholder: '输入知识点标题',
            style: { marginBottom: '15px', width: '100%' }
        }),
        React.createElement('div', { key: 'desc' }, '知识点描述:'),
        React.createElement(antd.Input.TextArea, {
            key: 'textarea',
            id: 'new-kp-desc',
            placeholder: '输入知识点描述',
            rows: 4,
            style: { marginBottom: '15px', width: '100%' }
        }),
        React.createElement('div', { key: 'brother_id', style: { marginTop: '10px' } }, '顺序:'),
        React.createElement(antd.InputNumber, {
            key: 'brother_id-input',
            id: 'new-kp-brother_id',
            min: 1,
            defaultValue: 1,
            style: { marginBottom: '15px', width: '100%' }
        }),
        React.createElement('div', { key: 'difficulty' }, '难度:'),
        React.createElement(antd.Radio.Group, {
            key: 'difficulty-group',
            name: 'difficulty',
            options: [
                { label: '非常简单', value: 1 },
                { label: '简单', value: 2 },
                { label: '中等', value: 3 },
                { label: '困难', value: 4 },
                { label: '非常困难', value: 5 }
            ],
            defaultValue:3,
            onChange: e => setDifficulty(e.target.value),
            optionType: 'button',
            buttonStyle: 'solid',
            style: { marginBottom: '15px' }
        }),
        React.createElement('div', { key: 'memory' }, '记忆度:'),
        React.createElement(antd.Radio.Group, {
            key: 'memory-group',
            name: 'memory_level',
            options: [
                { label: '完全陌生', value: 1 },
                { label: '有些印象', value: 2 },
                { label: '一般熟悉', value: 3 },
                { label: '比较熟悉', value: 4 },
                { label: '完全掌握', value: 5 }
            ],
            defaultValue:3,
            onChange: e => setMemoryLevel(e.target.value),
            optionType: 'button',
            buttonStyle: 'solid',
            style: { marginBottom: '15px' }
        }),
        React.createElement('div', { key: 'mastery' }, '掌握度:'),
        React.createElement(antd.Radio.Group, {
            key: 'mastery-group',
            name: 'mastery_level',
            options: [
                { label: '完全不懂', value: 1 },
                { label: '初步了解', value: 2 },
                { label: '基本掌握', value: 3 },
                { label: '熟练运用', value: 4 },
                { label: '精通', value: 5 }
            ],
            defaultValue:3,
            onChange: e => {
                setMasteryLevel(e.target.value);
                // 强制更新组件
                const event = new Event('input', { bubbles: true });
                document.querySelector('[name="mastery_level"]').dispatchEvent(event);
            },
            optionType: 'button',
            buttonStyle: 'solid'
        })
    ]);

    const modal = antd.Modal.confirm({
        title: null,
        icon: null,
        content: modalContent,
        width: 650,
        okText: '保存',
        cancelText: '取消',
        onOk: () => {
            const title = document.getElementById('new-kp-title').value;
            const description = document.getElementById('new-kp-desc').value;
            const brother_id = document.getElementById('new-kp-brother_id').value;
            // 精确获取各单选按钮组的值
            const difficulty = document.querySelector('input[name="difficulty"]:checked').value;
            const memoryLevel = document.querySelector('input[name="memory_level"]:checked').value;
            const masteryLevel = document.querySelector('input[name="mastery_level"]:checked').value;
            if (!title) {
                antd.message.error('请输入知识点标题');
                return Promise.reject();
            }
            if (!description) {
                antd.message.error('请输入知识点描述');
                return Promise.reject();
            }
            submitAddKnowledgePoint(parentId, title, description, difficulty, memoryLevel, masteryLevel, brother_id);
            return Promise.resolve();
        },
        onCancel: () => {}
    });
}

// 提交添加知识点
function submitAddKnowledgePoint(parentId, title, description, difficulty = 3, memoryLevel = 3, masteryLevel = 3,brother_id = 1) {
    chapterId = '{{chapter.id}}';
    const requestData = {
        title: title,
        description: description,
        difficulty: difficulty,
        memory_level: memoryLevel,
        mastery_level: masteryLevel,
        parent: parentId,
        chapter: chapterId,
        brother_id: brother_id
    };
    
    fetch('/courses/api/knowledge-points/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token }}'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        antd.message.success('添加成功');
        initKnowledgePoints(); // 初始化树
    })
    .catch(error => {
        antd.message.error('添加失败: ' + error.message);
    });
}


// 添加按钮事件处理
// 删除知识点
document.getElementById('tree-delete-btn').addEventListener('click', function() {
    const kpId = this.dataset.kpId;
    if (kpId && confirm('确定要删除这个知识点，及其所有子节点吗？')) {
        deleteKnowledgePoint(kpId);
    }
});

// 添加子节点按钮事件处理
document.getElementById('add-child-btn').addEventListener('click', function() {
    const parentId = this.dataset.parentId;
    if (parentId) {
        showAddModal_Knowledge(parentId);
    } else {
        antd.message.warning('添加根节点请点击添加根节点按钮');
    }
});

// 添加根节点按钮事件处理
document.getElementById('add-root-btn').addEventListener('click', function() {
    const chapterId = '{{chapter.id}}';
    if (chapterId) {
        showAddModal_Knowledge(null);
    } else {
        antd.message.error('无法获取章节信息');
    }
});

// 添加根节点按钮事件处理
document.getElementById('import-root-btn').addEventListener('click', function() {
    try {
        const chapterId = '{{chapter.id}}';
        const knowledgePoints_id = document.getElementById('kp-id').value;
        // 检查URL格式
        const importUrl = `/courses/knowledge-points/${chapterId}/import/${knowledgePoints_id}/`;

        // 打开新窗口
        const newWindow = window.open(importUrl, '_blank');
        
        if (!newWindow || newWindow.closed) {
            throw new Error('无法打开导入页面，请检查弹出窗口是否被阻止');
        }
        
        // 恢复按钮状态
        setTimeout(() => {
            this.textContent = originalText;
            this.disabled = false;
        }, 1000);
        
    } catch (error) {
        console.error('打开导入页面失败:', error);
        alert('打开导入页面失败: ' + error.message);
        
        // 恢复按钮状态
        this.textContent = '导入';
        this.disabled = false;
    }
});

// 初始化
document.addEventListener('DOMContentLoaded', initKnowledgePoints);
// 额外确保SPA路由变化也能触发
document.addEventListener('turbolinks:load', initKnowledgePoints);

