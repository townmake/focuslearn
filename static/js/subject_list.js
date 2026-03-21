
document.addEventListener('DOMContentLoaded', function() {
    // 搜索功能
    const searchInput = document.querySelector('.search-input');
    const searchBtn = document.querySelector('.search-btn');
    const tableRows = document.querySelectorAll('.ant-table tbody tr');
    
    if (searchBtn && searchInput) {
        searchBtn.addEventListener('click', function() {
            const searchTerm = searchInput.value.toLowerCase();
            
            tableRows.forEach(row => {
                const textContent = row.textContent.toLowerCase();
                if (textContent.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
        
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchBtn.click();
            }
        });
    }

    // 初始化Ant Design组件
    if (typeof antd !== 'undefined') {
        // 可以在这里初始化Ant Design表格组件
        console.log('Ant Design已加载');
    }
});
