from django.contrib import admin
from .models import Authority, Category, Issue, IssueConfirmation, UserProfile, NotificationLog


@admin.register(Authority)
class AuthorityAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'icon', 'color', 'get_silence_score']
    search_fields = ['name', 'email']
    readonly_fields = ['get_silence_score']
    
    @admin.display(description='Silence Score')
    def get_silence_score(self, obj):
        """Display the computed silence score"""
        score = obj.get_silence_score()
        return f"{score:.1f} days"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'authority', 'default_severity']
    list_filter = ['authority']
    search_fields = ['name']


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'status', 'severity', 'days_since_report', 'reported_at']
    list_filter = ['status', 'severity', 'category__authority']
    search_fields = ['title', 'address', 'description']
    date_hierarchy = 'reported_at'
    readonly_fields = ['days_since_report', 'urgency_level', 'escalation_label']


@admin.register(IssueConfirmation)
class IssueConfirmationAdmin(admin.ModelAdmin):
    list_display = ['issue', 'user', 'confirmed_at']
    list_filter = ['confirmed_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'area', 'reports_count', 'confirmations_count']
    search_fields = ['user__username', 'area']


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['issue', 'authority', 'email_address', 'status', 'sent_at']
    list_filter = ['status', 'authority', 'sent_at']
    search_fields = ['issue__title', 'authority__name', 'email_address']
    date_hierarchy = 'sent_at'
    readonly_fields = ['issue', 'authority', 'email_address', 'sent_at', 'status', 'error_message']
    
    def has_add_permission(self, request):
        return False  # Logs are created automatically, not manually
