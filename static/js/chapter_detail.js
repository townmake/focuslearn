
document.addEventListener('DOMContentLoaded', function() {
    // 页面切换功能
    const menuItems = document.querySelectorAll('.ant-menu-item');
    menuItems.forEach(item => {
        item.addEventListener('click', function() {
            // 更新菜单激活状态
            menuItems.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            
            // 切换内容页
            const targetId = this.dataset.target;
            document.querySelectorAll('.content-page').forEach(page => {
                page.classList.remove('active');
            });
            document.getElementById(targetId).classList.add('active');
        });
    });

    // 编辑弹窗功能
    window.showEditModal = function() {
        document.getElementById('editModalMask').style.display = 'block';
        document.getElementById('editModalWrap').style.display = 'block';
    };

    window.hideEditModal = function() {
        document.getElementById('editModalMask').style.display = 'none';
        document.getElementById('editModalWrap').style.display = 'none';
    };

    window.submitEditForm = function() {
        const form = document.getElementById('editForm');
        const submitBtn = document.querySelector('#editModalWrap .ant-btn-primary');
        
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="anticon anticon-loading"></i> 保存中...';
        
        fetch(form.action, {
            method: 'POST',
            body: new FormData(form),
            headers: {
                'X-CSRFToken': '{{ csrf_token }}'
            }
        })
        .then(response => response.json())
        .then(data => {
            if(data.status === 'success') {
                location.reload();
            } else {
                alert('更新失败: ' + JSON.stringify(data.errors));
            }
        })
        .catch(error => {
            alert('请求出错: ' + error);
        })
        .finally(() => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '保存';
        });
    };
});
