from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Authority(models.Model):
    """Government body responsible for handling specific types of issues"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fa-building')  # FontAwesome icon
    color = models.CharField(max_length=7, default='#4d9fff')  # Hex color for markers
    email = models.EmailField(blank=True, help_text="Official email address for notifications")
    
    class Meta:
        verbose_name_plural = "Authorities"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_silence_score(self):
        """
        Calculate the Silence Score for this authority.
        Formula: total_unresolved_days / total_issues
        
        Returns the average days of inaction per issue.
        Computed dynamically to reflect live conditions.
        """
        # Get all unresolved issues under this authority
        unresolved_issues = self.categories.all().values_list('issues', flat=True)
        from django.db.models import Q
        issues = Issue.objects.filter(
            category__authority=self,
            status__in=['ignored', 'acknowledged', 'in_progress']
        )
        
        total_issues = issues.count()
        if total_issues == 0:
            return 0.0
        
        # Sum days since report for all unresolved issues
        total_unresolved_days = sum(issue.days_since_report for issue in issues)
        
        return round(total_unresolved_days / total_issues, 1)


class Category(models.Model):
    """Type of civic issue (linked to an authority)"""
    authority = models.ForeignKey(Authority, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fa-exclamation-triangle')
    default_severity = models.IntegerField(default=3, choices=[(i, i) for i in range(1, 6)])
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['authority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.authority.name})"


class Issue(models.Model):
    """A reported civic problem at a specific location"""
    STATUS_CHOICES = [
        ('ignored', 'Ignored'),
        ('acknowledged', 'Acknowledged'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]
    
    SEVERITY_CHOICES = [(i, i) for i in range(1, 6)]
    
    # Basic info
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='issues')
    
    # Location
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    address = models.CharField(max_length=300, blank=True)
    
    # Status & severity
    severity = models.IntegerField(choices=SEVERITY_CHOICES, default=3)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ignored')
    
    # Timestamps
    reported_at = models.DateTimeField(default=timezone.now)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    in_progress_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    status_updated_at = models.DateTimeField(null=True, blank=True, help_text="Last status change timestamp")
    
    # User tracking
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reported_issues')
    
    # Image (optional)
    image = models.ImageField(upload_to='issues/', blank=True, null=True)
    
    class Meta:
        ordering = ['-reported_at']
    
    def __str__(self):
        return f"{self.title} - {self.status}"
    
    @property
    def days_since_report(self):
        """Calculate days since the issue was first reported"""
        delta = timezone.now() - self.reported_at
        return delta.days
    
    @property
    def days_ignored(self):
        """Days the issue has been in 'ignored' status"""
        if self.status == 'ignored':
            return self.days_since_report
        elif self.acknowledged_at:
            delta = self.acknowledged_at - self.reported_at
            return delta.days
        return 0
    
    @property
    def urgency_level(self):
        """Calculate urgency based on severity and days ignored"""
        days = self.days_ignored
        if days >= 40 or self.severity >= 5:
            return 'critical'
        elif days >= 20 or self.severity >= 4:
            return 'serious'
        elif days >= 7 or self.severity >= 3:
            return 'moderate'
        return 'recent'
    
    @property
    def urgency_color(self):
        """Get color based on urgency level"""
        colors = {
            'critical': '#ff4d4d',
            'serious': '#ff8c00',
            'moderate': '#ffd700',
            'recent': '#4ade80'
        }
        return colors.get(self.urgency_level, '#4d9fff')
    
    @property
    def escalation_label(self):
        """Get escalation label based on days ignored (passive accountability)"""
        if self.status == 'resolved':
            return None
        days = self.days_ignored
        if days >= 30:
            return 'systemic_neglect'
        elif days >= 14:
            return 'unacknowledged'
        return None
    
    @property
    def escalation_display(self):
        """Human-readable escalation label for UI"""
        labels = {
            'systemic_neglect': 'Systemic Neglect',
            'unacknowledged': 'Unacknowledged'
        }
        return labels.get(self.escalation_label)


class IssueConfirmation(models.Model):
    """Community confirmation of an issue's existence"""
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='confirmations')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    confirmed_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['issue', 'user']
    
    def __str__(self):
        return f"{self.user.username} confirmed {self.issue.title}"


class UserProfile(models.Model):
    """Extended user profile for civic engagement tracking"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    area = models.CharField(max_length=100, blank=True)
    reports_count = models.IntegerField(default=0)
    confirmations_count = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username}'s profile"


<<<<<<< HEAD
class NotificationLog(models.Model):
    """Log of all authority notification emails sent"""
    DELIVERY_STATUS = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='notifications')
    authority = models.ForeignKey(Authority, on_delete=models.CASCADE)
    email_address = models.EmailField()
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=DELIVERY_STATUS, default='pending')
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = "Notification Log"
        verbose_name_plural = "Notification Logs"
    
    def __str__(self):
        return f"Notification to {self.authority.name} for Issue #{self.issue.id} - {self.status}"


class AuthorityUser(models.Model):
    """
    Links a Django User account to an Authority for login access.
    Allows authority representatives to manage issues assigned to them.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='authority_profile')
    authority = models.OneToOneField(Authority, on_delete=models.CASCADE, related_name='user_account')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Authority User"
        verbose_name_plural = "Authority Users"
    
    def __str__(self):
        return f"{self.user.username} - {self.authority.name}"


class IssueStatusLog(models.Model):
    """
    Audit log for tracking all status changes made by authorities.
    Read-only record for accountability and transparency.
    """
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='status_logs')
    authority_user = models.ForeignKey(AuthorityUser, on_delete=models.SET_NULL, null=True, related_name='status_changes')
    previous_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, help_text="Optional notes about the status change")
    
    class Meta:
        ordering = ['-changed_at']
        verbose_name = "Issue Status Log"
        verbose_name_plural = "Issue Status Logs"
    
    def __str__(self):
        return f"Issue #{self.issue.id}: {self.previous_status} → {self.new_status}"
=======
class IssueComment(models.Model):
    """User comments on unaddressed issues to add public pressure"""
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.issue.title}"
