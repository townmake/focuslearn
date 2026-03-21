let editor;
    
class UploadAdapter {
  constructor(loader) {
    this.loader = loader;
  }
  
  upload() {
    return this.loader.file.then(file => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => {
          resolve({ default: reader.result });
        };
        reader.onerror = error => {
          reject(error);
        };
      });
    });
  }
  
  abort() {
    // 取消上传逻辑
  }
}

function UploadAdapterPlugin(editor) {
  editor.plugins.get('FileRepository').createUploadAdapter = (loader) => {
    return new UploadAdapter(loader);
  };
}

class PasteFromOffice {
  static get requires() {
    return ['Clipboard', 'FileRepository'];
  }
  
  constructor(editor) {
    this.editor = editor;
  }
  
  init() {
    const clipboard = this.editor.plugins.get('Clipboard');
    const fileRepository = this.editor.plugins.get('FileRepository');
    
    clipboard.on('inputTransformation', (evt, data) => {
      if (!data.dataTransfer.files) return;
      
      Array.from(data.dataTransfer.files)
        .filter(file => file.type.match('^image/'))
        .forEach(file => {
          const loader = fileRepository.createLoader(file);
          loader.upload()
            .then(url => {
              this.editor.model.change(writer => {
                const imageElement = writer.createElement('image', {
                  src: url.default
                });
                this.editor.model.insertContent(
                  imageElement,
                  this.editor.model.document.selection.getFirstPosition()
                );
              });
            })
            .catch(err => {
              console.error('图片上传失败:', err);
            });
        });
    });
  }
}


document.addEventListener('DOMContentLoaded', function() {
    // 获取表单content字段的初始值
    const contentField = document.querySelector('#content-container [name="content"]');
    const initialContent = contentField ? contentField.value : '';
    
    // 初始化CKEditor（如果已加载）
    if (typeof ClassicEditor !== 'undefined') {
        ClassicEditor
            .create(document.querySelector('#content-container'), {
                initialData: initialContent,
                language: 'zh-cn',
                extraPlugins: [UploadAdapterPlugin, PasteFromOffice],
                toolbar: {
                  items: [
                    'heading', '|',
                    'bold', 'italic', 'underline', 'strikethrough', 'code',
                    'subscript', 'superscript', 'highlight', '|',
                    'bulletedList', 'numberedList', 'todoList', '|',
                    'blockQuote', 'codeBlock', '|',
                    'alignment', '|',
                    'horizontalLine', '|',
                    'imageUpload', '|',
                    'fontSize', 'fontFamily', 'fontColor', 'fontBackgroundColor',
                    'mediaEmbed', 'removeFormat', 'insertTable', '|'
                  ],
                  shouldNotGroupWhenFull: true
                },
                image: {
                  toolbar: [
                    'imageTextAlternative',
                    'toggleImageCaption',
                    'imageStyle:inline',
                    'imageStyle:block',
                    'imageStyle:side'
                  ],
                  upload: {
                    types: ['jpeg', 'png', 'gif']
                  }
                },
                simpleUpload: {
                  // 禁用上传功能
                  uploadUrl: '',
                },
                fontFamily: {
                  options: [
                    '微软雅黑', '宋体', '黑体', '仿宋', '楷体', '隶书', '幼圆',
                    'Arial', 'Times New Roman', 'Verdana', 'Helvetica',
                    'Georgia', 'Courier New', 'Impact', 'Comic Sans MS', 'Trebuchet MS'
                  ],
                  supportAllValues: true
                },
                fontSize: {
                  options: [
                    { model:'20px', title: "小三", view: {styles: { "font-size": '14px' }}},
                    { model:'18.7px', title: "四号", view: {styles: { "font-size": '14px' }}},
                    { model:'16px', title: "小四", view: {styles: { "font-size": '14px' }}},
                    { model:'14px', title: "五号", view: {styles: { "font-size": '14px' }}},
                    { model:'12px', title: "小五", view: {styles: { "font-size": '14px' }}},
                    { model:'10px', title: "六号", view: {styles: { "font-size": '14px' }}},
                    { model:'8.7px', title: "小六", view: {styles: { "font-size": '14px' }}},
                    { model:'7.3px', title: "七号", view: {styles: { "font-size": '14px' }}},
                    { model:'6.7px', title: "八号", view: {styles: { "font-size": '14px' }}},
                    { model:'56px', title: "初号", view: {styles: { "font-size": '14px' }}},
                    { model:'48px', title: "小初", view: {styles: { "font-size": '14px' }}},
                    { model:'34.7px', title: "一号", view: {styles: { "font-size": '14px' }}},
                    { model:'32px', title: "小一", view: {styles: { "font-size": '14px' }}},
                    { model:'29.3px', title: "二号", view: {styles: { "font-size": '14px' }}},
                    { model:'24px', title: "小二", view: {styles: { "font-size": '14px' }}},
                    { model:'21.3px', title: "三号", view: {styles: { "font-size": '14px' }}}
                  ],
                  supportAllValues: true
                },
                licenseKey: 'GPL'
                // removePlugins: ['Markdown', 'Math']
              }).then(newEditor => {
                editor = newEditor;
                window.parent.postMessage({type: 'editor-ready'}, '*');
                
                const messageHandler = (event) => {
                  try {
                    if (!event.data || !event.data.type) return;
                    
                    switch(event.data.type) {
                      case 'init-content':
                        if (event.data.content) {
                          editor.setData(event.data.content);
                          editor.enableReadOnlyMode('lock');
                        }
                        break;
                        
                      case 'set-readonly-false':
                        editor.disableReadOnlyMode('lock');
                        break;
                        
                      case 'get-content':
                        const content = editor.getData();
                        editor.enableReadOnlyMode('lock');
                        window.parent.postMessage({
                          type: 'content-update',
                          content: content
                        }, '*');
                        break;
                    }
                  } catch (error) {
                    console.error('Message handling error:', error);
                  }
                };
                
                window.addEventListener('message', messageHandler);
              });
    }

    // 选项管理逻辑
    const optionsContainer = document.getElementById('options-container');
    const addOptionBtn = document.getElementById('add-option');
    let optionCount = 0;

    if (addOptionBtn) {
        addOptionBtn.addEventListener('click', function() {
            optionCount++;
            const optionDiv = document.createElement('div');
            optionDiv.className = 'option-item';
            optionDiv.innerHTML = `
                <input type="text" class="option-key form-control" placeholder="选项键(A/B/C)" maxlength="1">
                <input type="text" class="option-value form-control" placeholder="选项内容">
                <button type="button" class="btn btn-sm btn-danger remove-option">删除</button>
            `;
            optionsContainer.appendChild(optionDiv);
        });
    }

    // 删除选项
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-option')) {
            e.target.parentElement.remove();
        }
    });

    // 表单提交前处理选项
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const options = {};
            document.querySelectorAll('.option-item').forEach(item => {
                const key = item.querySelector('.option-key').value;
                const value = item.querySelector('.option-value').value;
                if (key && value) {
                    options[key] = value;
                }
            });
            
            // 如果有选项，添加到隐藏字段
            if (Object.keys(options).length > 0) {
                let optionsInput = document.querySelector('input[name="options"]');
                if (!optionsInput) {
                    optionsInput = document.createElement('input');
                    optionsInput.type = 'hidden';
                    optionsInput.name = 'options';
                    form.appendChild(optionsInput);
                }
                optionsInput.value = JSON.stringify(options);
            }
        });
    }
});
