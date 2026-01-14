from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Authority(models.Model):
    """Government body responsible for handling specific types of issues"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fa-building')  # FontAwesome icon
    color = models.CharField(max_length=7, default='#4d9fff')  # Hex color for markers
    
    class Meta:
        verbose_name_plural = "Authorities"
        ordering = ['name']
    
    def __str__(self):
        return self.name


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
    resolved_at = models.DateTimeField(null=True, blank=True)
    
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
