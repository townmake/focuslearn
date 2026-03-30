
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from .api_views import (
    KnowledgePointDetailAPI,
    KnowledgePointListAPI,
    KnowledgePointAPI,
    KnowledgeTreeAPI,
    knowledge_points_list,
    update_knowledge_point_content,
    knowledge_point_resources,
    search_knowledge_points,
    KnowledgePointAnnotationListAPI,
    KnowledgePointAnnotationDetailAPI
    )
from .exercise_views import (
    ExerciseListView, ExerciseCreateView,
    ExerciseUpdateView, ExerciseDetailView,
    ExerciseImportView,ExerciseSetStartAPI,ExerciseSetStartQuickAPI,
    ExerciseSetNextAPI, ExerciseSetSubmitAPI,
    ExerciseViewView,
    submit_answer, delete_exercise,
    exercise_set_exercise_delete,
    exercise_set_exercise_add,
    get_exercise_edit,
    update_exercise_edit,
    get_exercise_parentid,
    ExerciseNeighborAPI
)
from .review_views import (
    ReviewSetCreateView,
    ReviewSetListCreateAPI,
    ReviewSetDetailAPI,
    ReviewSetCompletionListCreateAPI,
    ExerciseFilterView,
    ReviewSetCreateView,
    ReviewSetExercisesView,
    review_set_exercise_delete,
    review_set_exercise_add,
    ReviewSetStartQuickAPI,ReviewSetNextAPI, ReviewSetSubmitAPI,
    review_set_result
)
from .views import (
    VideoCommentView,
    VideoCommentActionView,
    VideoListCreateAPIView,
    VideoRetrieveUpdateDestroyAPIView,
    VideoPlayerView,
    KnowledgePointListView,
    KnowledgePointDetailView,
    subject_chapter_options,
    chapter_detail,
    subjectListView,
    subject_detail,
    subject_methods,
    subject_create,
    subject_data,
    subject_update,
    subject_delete,
    subject_refresh,
    chapter_create,
    chapter_update,
    chapter_delete,
    chapter_nextMethods,
    chapter_nextChapter,
    ChapterDetailView,
    ChapterExerciseView,
    ChapterBasicView,
    ChapterListAPI,
    StudyRecordCreateAPI,
    StudyRecordDetailAPI,
    BaseStudyRecordListView,
    StudyRecordListView,
    StudyRecordsAPIView,
    ExerciseSetListCreateAPI,
    ExerciseSetDetailAPI,
    ExerciseSetExercisesAPI,
    ExerciseSetCompletionListCreateAPI,
    exercise_set_result,
    MethodSummaryListView,
    MethodSummarySubjectListView,
    MethodSummaryDetailView,
    MethodSummaryListCreateAPI,
    MethodSummaryUpdateAPIView,
    MethodSummaryDeleteView,
    MethodSummaryAddDeleteView,
    MethodSummaryAddKPDeleteView,
    method_exercises,
    daily_review_sets
)
from .document_views import (
    DocumentCreateAPI,
    DocumentUpdateAPI,
    DocumentDeleteAPI,
    DocumentListAPI
)
from .comment_views import get_comments, submit_comment
from .document_views import document_detail, document_file_view
from .editor_upload_views import aieditor_image_upload

app_name = 'courses'


urlpatterns = [
    # 知识点相关路由，新增KnowledgePointListView和KnowledgePointDetailView
    path('knowledgepoints/', KnowledgePointListView.as_view(), name='knowledgepoint_list'),
    path('knowledgepoints/<int:pk>/', KnowledgePointDetailView.as_view(), name='knowledgepoint_detail'),
    path('knowledgepoints/view/<int:pk>/', KnowledgePointDetailView.as_view(), name='knowledgepoint_view'),
    path('knowledge-points/<int:pk>/', KnowledgePointDetailAPI.as_view(), name='knowledgepoint-detail'),
    path('knowledge-points/', KnowledgePointListAPI.as_view(), name='knowledgepoint-list'),
    # 知识点API路由
    path('api/knowledge-points-list/', knowledge_points_list, name='knowledge-points-list'),
    path('api/knowledge-points/', KnowledgePointAPI.as_view(), name='knowledge-point-api'),
    path('api/knowledge-points/<int:pk>/content/', update_knowledge_point_content, name='knowledge-point-content'),
        #模糊查询知识点-自动补全
    path('api/chapters/<int:chapter_id>/search-knowledge-points/', search_knowledge_points, name='search_knowledge_points'),
    path('api/knowledge-points/<int:pk>/resources/', knowledge_point_resources, name='knowledge-point-resources'),
    path('api/chapters/<int:chapter_id>/knowledge-tree/', KnowledgeTreeAPI.as_view(), name='knowledge-tree-api'),

    # AiEditor 图片上传（字段名默认为 image）
    path('api/editor/upload/image/', aieditor_image_upload, name='aieditor_image_upload'),

    #知识点 注释相关
    path('api/knowledge_points/<int:pk>/annotations/', KnowledgePointAnnotationListAPI.as_view(), name='annotation-list'),
    path('api/knowledge_points/annotations/<int:pk>/', KnowledgePointAnnotationDetailAPI.as_view(), name='annotation-detail'),


    # 记录路由
    path('study-records/', StudyRecordListView.as_view(), name='study_records'),
    path('study-records/list/', StudyRecordsAPIView.as_view(), name='study_record_list'),
    path('base_study_record/', BaseStudyRecordListView.as_view(), name='base_study_record'),
    #  科目章节级联查询
    path('subject-chapter-options/', subject_chapter_options, name='subject_chapter_options'),
    
    # API路由--待更改
    path('api/study-records/list/', StudyRecordsAPIView.as_view(), name='study-records-list'),
    path('api/chapters/', ChapterListAPI.as_view(), name='chapter-list'),
    path('api/study-records/<int:pk>/', StudyRecordDetailAPI.as_view(), name='study-records-detail'),
    path('api/study-records/', StudyRecordCreateAPI.as_view(), name='study-records-create'),
    # 练习集相关API
    path('api/exercise-sets/', ExerciseSetListCreateAPI.as_view(), name='exercise-set-list'),
    path('api/exercise-sets/create/', ExerciseSetListCreateAPI.as_view(), name='create_exercise_set'),
    path('api/exercise-sets/<int:id>/', ExerciseSetDetailAPI.as_view(), name='exercise-set-detail'),
    path('api/exercise-set-completions/', ExerciseSetCompletionListCreateAPI.as_view(), name='exercise-set-completion'),
    # 练习集相关API-获取习题
    path('api/exercise-sets/<int:exercise_set_id>/exercises/', ExerciseSetExercisesAPI.as_view(), name='exercise-set-exercises'),
    path('api/exercise-sets/<int:exercise_set_id>/start/', ExerciseSetStartAPI.as_view(), name='exercise-set-start'),
    path('api/exercise-sets/<int:exercise_set_id>/start-quick/', ExerciseSetStartQuickAPI.as_view(), name='exercise-set-start-quick'),
    path('api/exercise-sets/<int:exercise_set_id>/next/<int:current_exercise_id>/', ExerciseSetNextAPI.as_view(), name='exercise-set-next'),
    path('api/exercise-sets/<int:exercise_set_id>/submit/', ExerciseSetSubmitAPI.as_view(), name='exercise-set-submit'),

    # 科目相关路由
    path('subjects/', subjectListView, name='subject_list'),
    path('subject/<int:pk>/data/', subject_data, name='subject_data'),
    path('subject_create/', subject_create, name='subject_create'),
    path('subject_update/<int:pk>/', subject_update, name='subject_update'),
    path('subject/<int:pk>/refresh/', subject_refresh, name='subject_refresh'),
    path('subject/<int:pk>/', subject_detail, name='subject_detail'),
    path('subject/<int:pk>/delete/', subject_delete, name='subject_delete'),
    path('subject/<int:pk>/methods/', subject_methods, name='subject_methods'), # 科目方法列表


    # 章节相关路由
    path('chapter/<int:pk>/', chapter_detail, name='chapter_detail'),
    path('chapter/exercise/<int:pk>/', ChapterExerciseView.as_view(), name='chapter_exercise'),
    path('chapter/basic/<int:pk>/', ChapterBasicView.as_view(), name='chapter_basic'),
    path('chapter/<int:pk>/detail/', ChapterDetailView.as_view(), name='chapter_detail'),
    path('chapter/create/', chapter_create, name='chapter_create'),
    path('chapter/<int:pk>/update/', chapter_update, name='chapter_update'),
    path('chapter/<int:pk>/delete/', chapter_delete, name='chapter_delete'),
    path('chapter/<int:pk>/methods/', chapter_nextMethods, name='chapter_nextMethods'), # 章节方法列表
    path('chapter/<int:pk>/next/', chapter_nextChapter, name='chapter_nextChapter'), # 章节方法列表



    # 文档相关路由
    path('document_list/', DocumentListAPI.as_view(), name='document_list'),
    path('document/create/', DocumentCreateAPI.as_view(), name='document_create'),
    path('document/<int:pk>/', document_detail, name='document_detail'),
    path('document/<int:pk>/update/', DocumentUpdateAPI.as_view(), name='document_update'),
    path('document/<int:pk>/delete/', DocumentDeleteAPI.as_view(), name='document_delete'),

    # 视频相关路由
    path('video_list/', VideoListCreateAPIView.as_view(), name='video_list'),
    path('video/create/', VideoListCreateAPIView.as_view(), name='video_create'),
    path('video/<int:id>/update/', VideoRetrieveUpdateDestroyAPIView.as_view(), name='video_update'),
    path('video/<int:id>/description/', VideoRetrieveUpdateDestroyAPIView.as_view(), name='update_video_description'),
    path('video/<int:id>/delete/', VideoRetrieveUpdateDestroyAPIView.as_view(), name='video_delete'),
    #path('video/<int:pk>/', video_detail, name='video_detail'),
    path('video/player/', VideoPlayerView.as_view(), name='video_player'),
    path('video/comment/', VideoCommentView.as_view(), name='video_comment'),
    path('video/comment/add/', VideoCommentView.as_view(), name='add_video_comment'),
    path('video/comment/<int:comment_id>/action/', VideoCommentActionView.as_view(), name='video_comment_action'),
    
    # 评论组件路由
    path('comments/', get_comments, name='get_comments'),
    path('comments/submit/',submit_comment, name='submit_comment'),
    
    # 习题相关路由
    path('api/exercises/<int:exercise_id>/neighbor/', ExerciseNeighborAPI.as_view(), name='exercise-neighbor'),
    path('exercises_list/', ExerciseListView.as_view(), name='exercises_list'),
    path('exercises/create/', ExerciseCreateView.as_view(), name='exercise_create'),
    path('exercises/import/', ExerciseImportView.as_view(), name='exercise_import'),
    path('exercises/<int:pk>/', ExerciseDetailView.as_view(), name='exercise_detail'),
    path('exercises/<int:pk>/edit/', ExerciseUpdateView.as_view(), name='exercise_update'),
    path('exercises/<int:pk>/view/', ExerciseViewView.as_view(), name='exercise_view'),
    # 方法总结相关URL
    path('methods/', MethodSummaryListView.as_view(), name='method_list'),
    path('methods/subject/<int:subject_id>/', MethodSummarySubjectListView.as_view(), name='method_list_subject'),
    path('methods/create/', MethodSummaryListCreateAPI.as_view(), name='method_create'),
    path('methods/<int:pk>/', MethodSummaryDetailView.as_view(), name='method_detail'),
    path('methods/<int:pk>/update/', MethodSummaryUpdateAPIView.as_view(), name='method_update'),
    path('methods/<int:pk>/delete/', MethodSummaryDeleteView.as_view(), name='method_delete'),
    path('methods/<int:method_id>/add/', MethodSummaryAddDeleteView.as_view(), name='method_add_exercise'),
    path('methods/<int:method_id>/addkp/', MethodSummaryAddKPDeleteView.as_view(), name='method_add_knowledgepoint'),
    path('methods/<int:method_id>/delete/<int:exercise_id>/', MethodSummaryAddDeleteView.as_view(), name='method_delete_exercise'),
    path('methods/<int:method_id>/deletekp/<int:knowledge_id>/', MethodSummaryAddKPDeleteView.as_view(), name='method_delete_knowledgepoint'),
    path('methods/<int:pk>/exercises/', method_exercises, name='method_exercises'),
    path('exercises/<int:pk>/delete/', delete_exercise, name='exercise_delete'),
    path('exercises/<int:pk>/submit/', submit_answer, name='exercise_submit_answer'),
    # 习题集相关路由
    path('api/exercise-sets/<int:exercise_set_id>/exercises/<int:exercise_id>/delete/', 
        exercise_set_exercise_delete, name='exercise-set-exercise-delete'),
    path('api/exercise-sets/<int:exercise_set_id>/exercises/add/', 
        exercise_set_exercise_add, name='exercise-set-exercise-add'),
    path('api/exercises/<int:pk>/', get_exercise_edit, name='exercise_detail_edit'),
    path('api/exercises/<int:pk>/update/', update_exercise_edit, name='exercise_update_api'),
    path('api/exercises/<int:pk>/submit/', submit_answer, name='exercise_submit_answer'),
    path('api/exercises/<int:pk>/parentid/', get_exercise_parentid, name='exercise_parentid_byid'),
    path('exercise-set/<int:exercise_set_id>/result/<int:completion_id>/', 
         exercise_set_result, name='exercise-set-result'),

    # 复习集相关路由
    path('api/review-sets/', ReviewSetListCreateAPI.as_view(), name='review-set-list'),
    path('review-sets/daily/', daily_review_sets, name='daily_review_sets'),
    path('api/review-sets/<int:id>/', ReviewSetDetailAPI.as_view(), name='review-set-detail'),
    path('api/review-sets-exercises/<int:id>/', ReviewSetExercisesView.as_view(), name='review-set-exercises'),
    path('api/review-sets/<int:review_set_id>/exercises/<int:exercise_id>/delete/', 
        review_set_exercise_delete, name='review-set-exercise-delete'),
    path('api/review-sets/<int:review_set_id>/exercises/add/', 
        review_set_exercise_add, name='review-set-exercise-add'),
    path('api/review-sets/<int:review_set_id>/start-quick/', ReviewSetStartQuickAPI.as_view(), name='review-set-start-quick'),
    path('api/review-sets/<int:review_set_id>/next/<int:current_exercise_id>/', ReviewSetNextAPI.as_view(), name='review-set-next'),
    path('api/review-sets/<int:review_set_id>/submit/', ReviewSetSubmitAPI.as_view(), name='exercise-set-submit'),
    path('api/review-set-completions/', ReviewSetCompletionListCreateAPI.as_view(), name='review-set-completion'),
    path('api/review-sets/<int:review_set_id>/submit/', ReviewSetSubmitAPI.as_view(), name='review-set-submit'),
    path('review-set/<int:review_set_id>/result/<int:completion_id>/', 
         review_set_result, name='review-set-result'),
    
    # 配置页面相关路由
    path('api/filter-exercises/', ExerciseFilterView.as_view(), name='filter-exercises'),
    path('api/create-review-set/', ReviewSetCreateView.as_view(), name='create-review-set'),

    # 文档文件访问路由
    path('chapter/<int:chapter_id>/detail/<str:filename>/', document_file_view, name='document_file_view'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)