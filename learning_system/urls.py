
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.views.generic.base import RedirectView
from .views import (
    home,
    login_view,
    logout_view,
    random_welcome_quote,
    refresh_weekly_dashboard,
)
from .weekly_ai_summary_views import (
    home_weekly_ai_summary_start,
    weekly_ai_summary_status,
    weekly_ai_summary_update_body,
)
from courses.views import chapter_detail
from django.views.generic import TemplateView


urlpatterns = [
    path("", home, name="home"),
    path(
        "home/welcome-quote/",
        random_welcome_quote,
        name="random_welcome_quote",
    ),
    path(
        "home/refresh-weekly-stats/",
        refresh_weekly_dashboard,
        name="refresh_weekly_dashboard",
    ),
    path(
        "home/weekly-ai-summary/start/",
        home_weekly_ai_summary_start,
        name="home_weekly_ai_summary_start",
    ),
    path(
        "home/weekly-ai-summary/status/<int:pk>/",
        weekly_ai_summary_status,
        name="weekly_ai_summary_status",
    ),
    path(
        "home/weekly-ai-summary/<int:pk>/body/",
        weekly_ai_summary_update_body,
        name="weekly_ai_summary_update_body",
    ),
    path('planner/', include('weekly_planner.urls')),
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('courses/', include('courses.urls')),
    re_path(r'^api-auth/', include('rest_framework.urls')),
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'images/favicon.ico')),
    path('debug/chapter/<int:pk>/', chapter_detail),
    path(
        'test-editor/',
        login_required(
            TemplateView.as_view(template_name="components/test.html"),
        ),
    ),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
