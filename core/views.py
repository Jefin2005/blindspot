from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
import json

from .models import Authority, Category, Issue, IssueConfirmation, UserProfile


def index(request):
    """Main map view"""
    authorities = Authority.objects.prefetch_related('categories').all()
    categories = Category.objects.select_related('authority').all()
    
    # Statistics for the dashboard
    stats = {
        'total_issues': Issue.objects.count(),
        'ignored_issues': Issue.objects.filter(status='ignored').count(),
        'resolved_issues': Issue.objects.filter(status='resolved').count(),
        'critical_issues': Issue.objects.filter(severity__gte=4, status='ignored').count(),
    }
    
    context = {
        'authorities': authorities,
        'categories': categories,
        'stats': stats,
    }
    return render(request, 'core/index.html', context)


def api_issues(request):
    """Return all issues as GeoJSON for the map"""
    issues = Issue.objects.select_related('category', 'category__authority').annotate(
        confirmation_count=Count('confirmations')
    )
    
    # Filter by authority if specified
    authority_id = request.GET.get('authority')
    if authority_id:
        issues = issues.filter(category__authority_id=authority_id)
    
    # Filter by category if specified
    category_id = request.GET.get('category')
    if category_id:
        issues = issues.filter(category_id=category_id)
    
    # Filter by status if specified
    status = request.GET.get('status')
    if status:
        issues = issues.filter(status=status)
    
    features = []
    for issue in issues:
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [float(issue.longitude), float(issue.latitude)]
            },
            'properties': {
                'id': issue.id,
                'title': issue.title,
                'description': issue.description,
                'category': issue.category.name,
                'authority': issue.category.authority.name,
                'authority_color': issue.category.authority.color,
                'severity': issue.severity,
                'status': issue.status,
                'status_display': issue.get_status_display(),
                'address': issue.address,
                'reported_at': issue.reported_at.isoformat(),
                'days_since_report': issue.days_since_report,
                'days_ignored': issue.days_ignored,
                'urgency_level': issue.urgency_level,
                'urgency_color': issue.urgency_color,
                'confirmation_count': issue.confirmation_count,
                'icon': issue.category.icon,
            }
        })
    
    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }
    
    return JsonResponse(geojson)


def api_issues_nearby(request):
    """Return issues near a specific location"""
    try:
        lat = float(request.GET.get('lat', 0))
        lng = float(request.GET.get('lng', 0))
        radius = float(request.GET.get('radius', 0.01))  # ~1km default
    except ValueError:
        return JsonResponse({'error': 'Invalid coordinates'}, status=400)
    
    # Simple bounding box filter (good enough for local demo)
    issues = Issue.objects.filter(
        latitude__gte=lat - radius,
        latitude__lte=lat + radius,
        longitude__gte=lng - radius,
        longitude__lte=lng + radius,
    ).select_related('category', 'category__authority').annotate(
        confirmation_count=Count('confirmations')
    )
    
    features = []
    for issue in issues:
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [float(issue.longitude), float(issue.latitude)]
            },
            'properties': {
                'id': issue.id,
                'title': issue.title,
                'category': issue.category.name,
                'authority': issue.category.authority.name,
                'severity': issue.severity,
                'status': issue.status,
                'days_ignored': issue.days_ignored,
                'urgency_level': issue.urgency_level,
                'urgency_color': issue.urgency_color,
                'confirmation_count': issue.confirmation_count,
            }
        })
    
    return JsonResponse({
        'type': 'FeatureCollection',
        'features': features,
        'count': len(features)
    })


def api_issue_detail(request, issue_id):
    """Return detailed information about a specific issue"""
    issue = get_object_or_404(
        Issue.objects.select_related('category', 'category__authority', 'reported_by')
        .annotate(confirmation_count=Count('confirmations')),
        id=issue_id
    )
    
    # Check if current user has confirmed this issue
    user_confirmed = False
    if request.user.is_authenticated:
        user_confirmed = IssueConfirmation.objects.filter(
            issue=issue, user=request.user
        ).exists()
    
    data = {
        'id': issue.id,
        'title': issue.title,
        'description': issue.description,
        'category': issue.category.name,
        'authority': issue.category.authority.name,
        'authority_color': issue.category.authority.color,
        'severity': issue.severity,
        'status': issue.status,
        'status_display': issue.get_status_display(),
        'address': issue.address,
        'latitude': float(issue.latitude),
        'longitude': float(issue.longitude),
        'reported_at': issue.reported_at.isoformat(),
        'days_since_report': issue.days_since_report,
        'days_ignored': issue.days_ignored,
        'urgency_level': issue.urgency_level,
        'urgency_color': issue.urgency_color,
        'confirmation_count': issue.confirmation_count,
        'reported_by': issue.reported_by.username if issue.reported_by else 'Anonymous',
        'user_confirmed': user_confirmed,
        'image_url': issue.image.url if issue.image else None,
    }
    
    return JsonResponse(data)


def api_statistics(request):
    """Return aggregate statistics for the dashboard"""
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    
    total = Issue.objects.count()
    by_status = {
        'ignored': Issue.objects.filter(status='ignored').count(),
        'acknowledged': Issue.objects.filter(status='acknowledged').count(),
        'in_progress': Issue.objects.filter(status='in_progress').count(),
        'resolved': Issue.objects.filter(status='resolved').count(),
    }
    
    by_authority = list(
        Issue.objects.values('category__authority__name', 'category__authority__color')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    # Average days ignored for unresolved issues
    ignored_issues = Issue.objects.filter(status='ignored')
    avg_days_ignored = 0
    if ignored_issues.exists():
        total_days = sum(i.days_ignored for i in ignored_issues)
        avg_days_ignored = total_days // ignored_issues.count()
    
    # Recent activity
    new_this_week = Issue.objects.filter(reported_at__gte=week_ago).count()
    resolved_this_week = Issue.objects.filter(resolved_at__gte=week_ago).count()
    
    # Top ignored areas (by address keyword)
    critical_count = Issue.objects.filter(severity__gte=4, status='ignored').count()
    
    return JsonResponse({
        'total': total,
        'by_status': by_status,
        'by_authority': by_authority,
        'avg_days_ignored': avg_days_ignored,
        'new_this_week': new_this_week,
        'resolved_this_week': resolved_this_week,
        'critical_count': critical_count,
    })


# Authentication Views
def register_view(request):
    """User registration"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Welcome to The Blindspot Initiative!')
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'core/register.html', {'form': form})


def login_view(request):
    """User login"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    """User logout"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('index')


@login_required
@require_POST
def confirm_issue(request, issue_id):
    """Confirm an issue exists (community validation)"""
    issue = get_object_or_404(Issue, id=issue_id)
    
    confirmation, created = IssueConfirmation.objects.get_or_create(
        issue=issue,
        user=request.user,
        defaults={'comment': request.POST.get('comment', '')}
    )
    
    if created:
        # Update user profile stats
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.confirmations_count += 1
        profile.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Issue confirmed',
            'confirmation_count': issue.confirmations.count()
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'You have already confirmed this issue'
        })


@login_required
def report_issue(request):
    """Report a new issue"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            category = get_object_or_404(Category, id=data.get('category_id'))
            
            issue = Issue.objects.create(
                title=data.get('title'),
                description=data.get('description', ''),
                category=category,
                latitude=data.get('latitude'),
                longitude=data.get('longitude'),
                address=data.get('address', ''),
                severity=int(data.get('severity', category.default_severity)),
                reported_by=request.user,
            )
            
            # Update user profile stats
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            profile.reports_count += 1
            profile.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Issue reported successfully',
                'issue_id': issue.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    # GET request - show report form
    categories = Category.objects.select_related('authority').all()
    return render(request, 'core/report.html', {'categories': categories})
