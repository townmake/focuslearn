
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView
from .views import home, login_view, logout_view, generate_daily_review
from courses.views import chapter_detail
from django.views.generic import TemplateView


urlpatterns = [
    path('', home, name='home'),
    path('planner/', include('weekly_planner.urls')),
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('generate-review/', generate_daily_review, name='generate_review'),
    path('courses/', include('courses.urls')),
    re_path(r'^api-auth/', include('rest_framework.urls')),
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'images/favicon.ico')),
    path('debug/chapter/<int:pk>/', chapter_detail),
    path('test-editor/', TemplateView.as_view(template_name="components/test.html")),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
