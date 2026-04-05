from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api, views
from .important_date_api import (
    important_dates_api,
    important_date_detail_api,
    subject_category_options_api,
)
from .calendar_study_records_api import calendar_study_records
from .views import (
    QuickAccessListView,
    QuickAccessDetailView,
    QuickAccessCreateView,
    QuickAccessUpdateView,
    QuickAccessDeleteView
)

# Web views
app_name = 'weekly_planner'
urlpatterns = [
    path('', views.home_tasks_view, name='home'),
    path('planner/', views.planner_view, name='planner'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('update-task-status/', views.update_task_status, name='update_task_status'),
    path('quick-access/', QuickAccessListView.as_view(), name='quick_access_list'),
    path('quick-access/<int:pk>/', QuickAccessDetailView.as_view(), name='quick_access_detail'),
    path('quick-access/create/', QuickAccessCreateView.as_view(), name='quick_access_create'),
    path('quick-access/<int:pk>/edit/', QuickAccessUpdateView.as_view(), name='quick_access_edit'),
    path('quick-access/<int:pk>/delete/', QuickAccessDeleteView.as_view(), name='quick_access_delete'),
    path('word-view/', views.word_view, name='word_view'),
    path('api/important-dates/', important_dates_api, name='important_dates_api'),
    path(
        'api/subject-category-options/',
        subject_category_options_api,
        name='subject_category_options_api',
    ),
    path(
        'api/important-dates/<int:pk>/',
        important_date_detail_api,
        name='important_date_detail_api',
    ),
    path(
        'api/calendar-study-records/',
        calendar_study_records,
        name='calendar_study_records',
    ),
]

# API endpoints (单独包含)
api_router = DefaultRouter()
api_router.register(r'tasks', api.TaskViewSet, basename='task')
api_router.register(r'subjects', api.SubjectViewSet, basename='subject')
api_router.register(r'chapters', api.ChapterViewSet, basename='chapter')
api_router.register(r'daily-summaries', api.DailySummaryViewSet, basename='daily-summary')
api_router.register(r'task-lists', api.TaskListViewSet, basename='task-lists')
api_router.register(r'words', api.WordsViewSet, basename='words')

urlpatterns += [
    path('api/', include(api_router.urls)),
]