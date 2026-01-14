from django.urls import path
from . import views

urlpatterns = [
    # Main views
    path('', views.index, name='index'),
    path('report/', views.report_issue, name='report_issue'),
    
    # API endpoints
    path('api/issues/', views.api_issues, name='api_issues'),
    path('api/issues/nearby/', views.api_issues_nearby, name='api_issues_nearby'),
    path('api/issues/<int:issue_id>/', views.api_issue_detail, name='api_issue_detail'),
    path('api/issues/<int:issue_id>/confirm/', views.confirm_issue, name='confirm_issue'),
    path('api/statistics/', views.api_statistics, name='api_statistics'),
    
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
