
document.addEventListener('DOMContentLoaded', function() {
    // 初始化章节链接点击事件
    const chapterLinks = document.querySelectorAll('.chapter-link');
    chapterLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const chapterId = this.dataset.chapterId;
            // 这里可以添加跳转到章节详情页的逻辑
            console.log('跳转到章节详情页:', chapterId);
        });
    });

    // 如果有Ant Design组件，可以在这里初始化
    if (typeof antd !== 'undefined') {
        console.log('Ant Design组件已加载');
    }
});
