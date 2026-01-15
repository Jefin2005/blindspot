from django.urls import path
from . import views

urlpatterns = [
    # Main views
    path('', views.landing_page, name='landing'),
    path('dashboard/', views.index, name='index'),
    path('report/', views.report_issue, name='report_issue'),
    
    # API endpoints
    path('api/issues/', views.api_issues, name='api_issues'),
    path('api/issues/nearby/', views.api_issues_nearby, name='api_issues_nearby'),
<<<<<<< HEAD
    path('api/issues/radius/', views.api_issues_radius, name='api_issues_radius'),
=======
    path('api/issues/unaddressed/', views.api_unaddressed_issues, name='api_unaddressed_issues'),
>>>>>>> 2df7404 (11th commit)
    path('api/issues/<int:issue_id>/', views.api_issue_detail, name='api_issue_detail'),
    path('api/issues/<int:issue_id>/confirm/', views.confirm_issue, name='confirm_issue'),
    path('api/issues/<int:issue_id>/comments/', views.api_issue_comments, name='api_issue_comments'),
    path('api/issues/<int:issue_id>/comment/', views.api_add_comment, name='api_add_comment'),
    path('api/statistics/', views.api_statistics, name='api_statistics'),
    path('api/authorities/silence-scores/', views.api_authority_silence_scores, name='api_authority_silence_scores'),
    
    # Citizen Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Authority Authentication & Dashboard
    path('authority/login/', views.authority_login, name='authority_login'),
    path('authority/logout/', views.authority_logout, name='authority_logout'),
    path('authority/dashboard/', views.authority_dashboard, name='authority_dashboard'),
    path('authority/issues/<int:issue_id>/accept/', views.authority_accept_issue, name='authority_accept_issue'),
    path('authority/issues/<int:issue_id>/progress/', views.authority_start_progress, name='authority_start_progress'),
    path('authority/issues/<int:issue_id>/complete/', views.authority_complete_issue, name='authority_complete_issue'),
]

