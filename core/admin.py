from django.contrib import admin
from .models import Authority, Category, Issue, IssueConfirmation, UserProfile


@admin.register(Authority)
class AuthorityAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color']
    search_fields = ['name']


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
    readonly_fields = ['days_since_report', 'urgency_level']


@admin.register(IssueConfirmation)
class IssueConfirmationAdmin(admin.ModelAdmin):
    list_display = ['issue', 'user', 'confirmed_at']
    list_filter = ['confirmed_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'area', 'reports_count', 'confirmations_count']
    search_fields = ['user__username', 'area']
