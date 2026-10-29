from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_choice, name='register_choice'),
    path('register/candidate/', views.register_candidate, name='register_candidate'),
    path('register/recruiter/', views.register_recruiter, name='register_recruiter'),
    path('login/', views.SmartRecruitLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('platform-dashboard/', views.platform_admin_dashboard, name='platform_admin_dashboard'),
]
