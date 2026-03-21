
from django.urls import path
from ..views.study_records import StudyRecordListView, ChapterStudyRecordListView

urlpatterns = [
    path('study-records/', StudyRecordListView.as_view(), name='study_records'),
    path('chapters/<int:chapter_id>/study-records/', ChapterStudyRecordListView.as_view(), name='chapter_study_records'),
]
