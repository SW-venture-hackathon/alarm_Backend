from django.urls import path
from . import views

urlpatterns = [
    # path('', views.main, name='main'),  # 메인 화면
    path('login/', views.google_login, name='google_login'),  # Google 계정 로그인
    path('redirect/', views.google_redirect, name='google_redirect'),  # Google OAuth 리디렉션
    path('calendar/', views.calendar_view, name='calendar'),  # 캘린더 화면
    path("", views.public_calendar_view, name="public_calendar"),
]