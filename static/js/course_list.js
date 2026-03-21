
document.addEventListener('DOMContentLoaded', function() {
    // 搜索表单提交
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const params = new URLSearchParams(formData).toString();
            window.location.search = params;
        });
    }

    // 初始化Ant Design组件
    if (typeof antd !== 'undefined') {
        // 可以在这里初始化Ant Design表格组件
        console.log('Ant Design已加载');
    }
});
