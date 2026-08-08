
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
from .views import (
    KnowledgePointListView,
    KnowledgePointDetailView,
    subject_chapter_options,
    chapter_detail,
    subjectListView,
    subjectClosedListView,
    subject_detail,
    subject_create,
    subject_data,
    subject_update,
    subject_delete,
    subject_refresh,
    chapter_create,
    chapter_update,
    chapter_update_progress_status,
    chapter_transfer,
    chapter_delete,
    ChapterDetailView,
    ChapterListAPI,
    StudyRecordCreateAPI,
    StudyRecordDetailAPI,
    BaseStudyRecordListView,
    StudyRecordListView,
    StudyRecordsAPIView,
    study_record_export,
    SubjectPlanSummaryListCreateAPI,
    SubjectPlanSummaryDetailAPI,
    subject_plan_review,
    chapter_plan_review,
    plan_review_records_embed,
    subject_plan_summary_edit,
)
from .knowledge_point_export import knowledge_point_export
from .document_views import (
    DocumentCreateAPI,
    DocumentUpdateAPI,
    DocumentDeleteAPI,
    DocumentListAPI
)
from .comment_views import get_comments, submit_comment
from .document_views import document_detail, document_file_view
from .editor_upload_views import aieditor_image_upload
from learning_system.weekly_ai_summary_views import subject_weekly_ai_summary_start

app_name = 'courses'


urlpatterns = [
    path('knowledgepoints/', KnowledgePointListView.as_view(), name='knowledgepoint_list'),
    path('knowledgepoints/<int:pk>/', KnowledgePointDetailView.as_view(), name='knowledgepoint_detail'),
    path('knowledgepoints/view/<int:pk>/', KnowledgePointDetailView.as_view(), name='knowledgepoint_view'),
    path('knowledge-points/<int:pk>/export/', knowledge_point_export, name='knowledge_point_export'),
    path('knowledge-points/<int:pk>/', KnowledgePointDetailAPI.as_view(), name='knowledgepoint-detail'),
    path('knowledge-points/', KnowledgePointListAPI.as_view(), name='knowledgepoint-list'),
    path('api/knowledge-points-list/', knowledge_points_list, name='knowledge-points-list'),
    path('api/knowledge-points/', KnowledgePointAPI.as_view(), name='knowledge-point-api'),
    path('api/knowledge-points/<int:pk>/content/', update_knowledge_point_content, name='knowledge-point-content'),
    path('api/chapters/<int:chapter_id>/search-knowledge-points/', search_knowledge_points, name='search_knowledge_points'),
    path('api/knowledge-points/<int:pk>/resources/', knowledge_point_resources, name='knowledge-point-resources'),
    path('api/chapters/<int:chapter_id>/knowledge-tree/', KnowledgeTreeAPI.as_view(), name='knowledge-tree-api'),

    path('api/editor/upload/image/', aieditor_image_upload, name='aieditor_image_upload'),

    path('api/knowledge_points/<int:pk>/annotations/', KnowledgePointAnnotationListAPI.as_view(), name='annotation-list'),
    path('api/knowledge_points/annotations/<int:pk>/', KnowledgePointAnnotationDetailAPI.as_view(), name='annotation-detail'),

    path('study-records/', StudyRecordListView.as_view(), name='study_records'),
    path('study-records/list/', StudyRecordsAPIView.as_view(), name='study_record_list'),
    path('study-records/export/', study_record_export, name='study_record_export'),
    path('base_study_record/', BaseStudyRecordListView.as_view(), name='base_study_record'),
    path('subject-chapter-options/', subject_chapter_options, name='subject_chapter_options'),

    path('api/study-records/list/', StudyRecordsAPIView.as_view(), name='study-records-list'),
    path('api/chapters/', ChapterListAPI.as_view(), name='chapter-list'),
    path('api/study-records/<int:pk>/', StudyRecordDetailAPI.as_view(), name='study-records-detail'),
    path('api/study-records/', StudyRecordCreateAPI.as_view(), name='study-records-create'),

    path('subjects/', subjectListView, name='subject_list'),
    path('subjects/closed/', subjectClosedListView, name='subject_closed_list'),
    path('subject/<int:pk>/data/', subject_data, name='subject_data'),
    path('subject_create/', subject_create, name='subject_create'),
    path('subject_update/<int:pk>/', subject_update, name='subject_update'),
    path('subject/<int:pk>/refresh/', subject_refresh, name='subject_refresh'),
    path('subject/<int:pk>/plan-review/', subject_plan_review, name='subject_plan_review'),
    path(
        'subject/<int:subject_pk>/weekly-ai-summary/start/',
        subject_weekly_ai_summary_start,
        name='subject_weekly_ai_summary_start',
    ),
    path(
        'subject/<int:subject_pk>/plan-review/records/',
        plan_review_records_embed,
        name='plan_review_records_embed',
    ),
    path(
        'subject/<int:subject_pk>/plan-summaries/new/',
        subject_plan_summary_edit,
        name='subject_plan_summary_create',
    ),
    path(
        'subject/<int:subject_pk>/plan-summaries/<int:summary_pk>/edit/',
        subject_plan_summary_edit,
        name='subject_plan_summary_edit',
    ),
    path('subject/<int:pk>/', subject_detail, name='subject_detail'),
    path('subject/<int:pk>/delete/', subject_delete, name='subject_delete'),
    path(
        'api/subject/<int:subject_pk>/plan-summaries/',
        SubjectPlanSummaryListCreateAPI.as_view(),
        name='subject_plan_summaries_api',
    ),
    path(
        'api/plan-summaries/<int:pk>/',
        SubjectPlanSummaryDetailAPI.as_view(),
        name='subject_plan_summary_detail_api',
    ),

    path('chapter/<int:pk>/plan-review/', chapter_plan_review, name='chapter_plan_review'),
    path('chapter/<int:pk>/', chapter_detail, name='chapter_detail'),
    path('chapter/<int:pk>/detail/', ChapterDetailView.as_view(), name='chapter_detail_page'),
    path('chapter/create/', chapter_create, name='chapter_create'),
    path('chapter/<int:pk>/update/', chapter_update, name='chapter_update'),
    path(
        'chapter/<int:pk>/progress-status/',
        chapter_update_progress_status,
        name='chapter_progress_status',
    ),
    path(
        'chapter/<int:pk>/transfer/',
        chapter_transfer,
        name='chapter_transfer',
    ),
    path('chapter/<int:pk>/delete/', chapter_delete, name='chapter_delete'),

    path('document_list/', DocumentListAPI.as_view(), name='document_list'),
    path('document/create/', DocumentCreateAPI.as_view(), name='document_create'),
    path('document/<int:pk>/', document_detail, name='document_detail'),
    path('document/<int:pk>/update/', DocumentUpdateAPI.as_view(), name='document_update'),
    path('document/<int:pk>/delete/', DocumentDeleteAPI.as_view(), name='document_delete'),

    path('comments/', get_comments, name='get_comments'),
    path('comments/submit/', submit_comment, name='submit_comment'),

    path('chapter/<int:chapter_id>/detail/<str:filename>/', document_file_view, name='document_file_view'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
