from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Count, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta
from functools import wraps
import json
import math

<<<<<<< HEAD
from .models import Authority, Category, Issue, IssueConfirmation, UserProfile, NotificationLog, AuthorityUser, IssueStatusLog
from .notifications import send_authority_notification


def landing_page(request):
    """Landing page - The opening experience"""
    # Get some stats for impact
    stats = {
        'total_issues': Issue.objects.count(),
        'unresolved': Issue.objects.exclude(status='resolved').count(),
        'days_ignored': Issue.objects.filter(status='ignored').count(),
    }
    return render(request, 'core/landing.html', {'stats': stats})
=======
from .models import Authority, Category, Issue, IssueConfirmation, IssueComment, UserProfile
>>>>>>> 2df7404 (11th commit)


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
    
    # Get notification status
    notification = issue.notifications.first()
    notification_status = None
    if notification:
        notification_status = {
            'sent_at': notification.sent_at.isoformat(),
            'status': notification.status,
            'authority_notified': notification.authority.name,
        }
    
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
        'escalation_label': issue.escalation_label,
        'escalation_display': issue.escalation_display,
        'notification': notification_status,
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
        Issue.objects.values('category__authority__id', 'category__authority__name', 'category__authority__color')
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
            
            # Send notification to authority (non-blocking)
            send_authority_notification(issue)
            
            # Update user profile stats
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            profile.reports_count += 1
            profile.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Issue reported successfully. Authority has been notified.',
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


<<<<<<< HEAD
def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on Earth
    using the Haversine formula.
    
    Returns distance in kilometers.
    """
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def api_issues_radius(request):
    """
    Return unresolved issues within a specified radius (default 3km).
    Uses Haversine formula for accurate distance calculation.
    
    Query params:
        lat: latitude of center point
        lng: longitude of center point  
        radius: radius in km (default 3)
    """
    try:
        lat = float(request.GET.get('lat', 0))
        lng = float(request.GET.get('lng', 0))
        radius_km = float(request.GET.get('radius', 3))  # Default 3km
    except ValueError:
        return JsonResponse({'error': 'Invalid coordinates'}, status=400)
    
    # Get all unresolved issues (not resolved)
    unresolved_statuses = ['ignored', 'acknowledged', 'in_progress']
    issues = Issue.objects.filter(
        status__in=unresolved_statuses
    ).select_related('category', 'category__authority')
    
    # Filter by distance using Haversine formula
    nearby_issues = []
    for issue in issues:
        distance = haversine_distance(
            lat, lng,
            float(issue.latitude), float(issue.longitude)
        )
        if distance <= radius_km:
            nearby_issues.append({
                'id': issue.id,
                'title': issue.title,
                'latitude': float(issue.latitude),
                'longitude': float(issue.longitude),
                'distance_km': round(distance, 2),
                'days_since_report': issue.days_since_report,
                'urgency_level': issue.urgency_level,
                'urgency_color': issue.urgency_color,
                'status': issue.status,
                'category': issue.category.name,
                'authority': issue.category.authority.name,
            })
    
    # Sort by distance
    nearby_issues.sort(key=lambda x: x['distance_km'])
    
    return JsonResponse({
        'center': {'lat': lat, 'lng': lng},
        'radius_km': radius_km,
        'unresolved_count': len(nearby_issues),
        'nearby_issue_ids': [i['id'] for i in nearby_issues],
        'issues': nearby_issues
    })


def api_authority_silence_scores(request):
    """
    Return silence scores for all authorities.
    
    Silence Score = total_unresolved_days / total_issues
    Computed dynamically to reflect live conditions.
    """
    authorities = Authority.objects.all()
    
    scores = []
    for authority in authorities:
        score = authority.get_silence_score()
        scores.append({
            'id': authority.id,
            'name': authority.name,
            'silence_score': score,
            'color': authority.color,
        })
    
    # Sort by silence score descending (worst performers first)
    scores.sort(key=lambda x: x['silence_score'], reverse=True)
    
    return JsonResponse({
        'authorities': scores
    })


# ========================================
# AUTHORITY AUTHENTICATION & DASHBOARD
# ========================================

def authority_required(view_func):
    """
    Decorator that checks if the user is an authenticated authority user.
    Redirects to authority login if not authenticated or not an authority.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please login to access the authority dashboard.')
            return redirect('authority_login')
        
        try:
            authority_user = request.user.authority_profile
            if not authority_user.is_active:
                messages.error(request, 'Your authority account has been deactivated.')
                return redirect('authority_login')
        except AuthorityUser.DoesNotExist:
            messages.error(request, 'You do not have authority access.')
            return redirect('index')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def authority_login(request):
    """Separate login page for authority users"""
    if request.user.is_authenticated:
        # Check if user is an authority
        if hasattr(request.user, 'authority_profile'):
            return redirect('authority_dashboard')
        else:
            messages.info(request, 'You are logged in as a citizen, not an authority.')
            return redirect('index')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # Check if this user is linked to an authority
            try:
                authority_user = user.authority_profile
                if not authority_user.is_active:
                    messages.error(request, 'Your authority account has been deactivated.')
                    return redirect('authority_login')
                
                login(request, user)
                messages.success(request, f'Welcome, {authority_user.authority.name}!')
                return redirect('authority_dashboard')
            except AuthorityUser.DoesNotExist:
                messages.error(request, 'This account is not registered as an authority user.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'core/authority_login.html', {'form': form})


def authority_logout(request):
    """Logout authority user"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('authority_login')


@authority_required
def authority_dashboard(request):
    """Dashboard showing issues assigned to the logged-in authority"""
    authority_user = request.user.authority_profile
    authority = authority_user.authority
    
    # Get issues for this authority only
    issues = Issue.objects.filter(
        category__authority=authority
    ).select_related('category').order_by('-reported_at')
    
    # Filter by status if requested
    status_filter = request.GET.get('status', '')
    if status_filter:
        issues = issues.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(issues, 20)  # 20 issues per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Statistics for this authority
    stats = {
        'total': Issue.objects.filter(category__authority=authority).count(),
        'ignored': Issue.objects.filter(category__authority=authority, status='ignored').count(),
        'acknowledged': Issue.objects.filter(category__authority=authority, status='acknowledged').count(),
        'in_progress': Issue.objects.filter(category__authority=authority, status='in_progress').count(),
        'resolved': Issue.objects.filter(category__authority=authority, status='resolved').count(),
    }
    
    context = {
        'authority': authority,
        'authority_user': authority_user,
        'page_obj': page_obj,
        'stats': stats,
        'status_filter': status_filter,
    }
    return render(request, 'core/authority_dashboard.html', context)


@authority_required
@require_POST
def authority_accept_issue(request, issue_id):
    """Accept an issue: Ignored → Acknowledged"""
    authority_user = request.user.authority_profile
    issue = get_object_or_404(Issue, id=issue_id, category__authority=authority_user.authority)
    
    # Validate status transition
    if issue.status != 'ignored':
        messages.error(request, f'Cannot accept issue. Current status is "{issue.get_status_display()}".')
        return redirect('authority_dashboard')
    
    # Update status
    previous_status = issue.status
    issue.status = 'acknowledged'
    issue.acknowledged_at = timezone.now()
    issue.status_updated_at = timezone.now()
    issue.save()
    
    # Log the change
    IssueStatusLog.objects.create(
        issue=issue,
        authority_user=authority_user,
        previous_status=previous_status,
        new_status='acknowledged',
        notes=request.POST.get('notes', '')
    )
    
    messages.success(request, f'Issue #{issue.id} has been accepted.')
    return redirect('authority_dashboard')


@authority_required
@require_POST
def authority_start_progress(request, issue_id):
    """Start progress on an issue: Acknowledged → In Progress"""
    authority_user = request.user.authority_profile
    issue = get_object_or_404(Issue, id=issue_id, category__authority=authority_user.authority)
    
    # Validate status transition
    if issue.status != 'acknowledged':
        messages.error(request, f'Cannot start progress. Issue must be "Acknowledged" first.')
        return redirect('authority_dashboard')
    
    # Update status
    previous_status = issue.status
    issue.status = 'in_progress'
    issue.in_progress_at = timezone.now()
    issue.status_updated_at = timezone.now()
    issue.save()
    
    # Log the change
    IssueStatusLog.objects.create(
        issue=issue,
        authority_user=authority_user,
        previous_status=previous_status,
        new_status='in_progress',
        notes=request.POST.get('notes', '')
    )
    
    messages.success(request, f'Issue #{issue.id} is now in progress.')
    return redirect('authority_dashboard')


@authority_required
@require_POST
def authority_complete_issue(request, issue_id):
    """Complete an issue: In Progress → Resolved"""
    authority_user = request.user.authority_profile
    issue = get_object_or_404(Issue, id=issue_id, category__authority=authority_user.authority)
    
    # Validate status transition
    if issue.status != 'in_progress':
        messages.error(request, f'Cannot complete. Issue must be "In Progress" first.')
        return redirect('authority_dashboard')
    
    # Update status
    previous_status = issue.status
    issue.status = 'resolved'
    issue.resolved_at = timezone.now()
    issue.status_updated_at = timezone.now()
    issue.save()
    
    # Log the change
    IssueStatusLog.objects.create(
        issue=issue,
        authority_user=authority_user,
        previous_status=previous_status,
        new_status='resolved',
        notes=request.POST.get('notes', '')
    )
    
    messages.success(request, f'Issue #{issue.id} has been marked as resolved.')
    return redirect('authority_dashboard')
=======
def api_unaddressed_issues(request):
    """Return unaddressed (ignored) issues sorted by days ignored (descending)"""
    issues = Issue.objects.filter(status='ignored').select_related(
        'category', 'category__authority'
    ).annotate(
        confirmation_count=Count('confirmations'),
        comment_count=Count('comments')
    )
    
    # Sort by days ignored (calculated in Python since it's a property)
    issues_list = list(issues)
    issues_list.sort(key=lambda x: x.days_ignored, reverse=True)
    
    # Limit to top 20 for sidebar display
    issues_list = issues_list[:20]
    
    result = []
    for rank, issue in enumerate(issues_list, 1):
        result.append({
            'id': issue.id,
            'rank': rank,
            'title': issue.title,
            'category': issue.category.name,
            'authority': issue.category.authority.name,
            'days_ignored': issue.days_ignored,
            'urgency_level': issue.urgency_level,
            'urgency_color': issue.urgency_color,
            'confirmation_count': issue.confirmation_count,
            'comment_count': issue.comment_count,
            'address': issue.address,
        })
    
    return JsonResponse({'issues': result})


def api_issue_comments(request, issue_id):
    """Get comments for an issue"""
    issue = get_object_or_404(Issue, id=issue_id)
    comments = issue.comments.select_related('user').all()[:10]
    
    result = [{
        'id': c.id,
        'user': c.user.username,
        'content': c.content,
        'created_at': c.created_at.isoformat(),
    } for c in comments]
    
    return JsonResponse({'comments': result})


@login_required
@require_POST
def api_add_comment(request, issue_id):
    """Add a comment to an unaddressed issue"""
    issue = get_object_or_404(Issue, id=issue_id)
    
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        
        if not content:
            return JsonResponse({
                'success': False,
                'message': 'Comment content is required'
            }, status=400)
        
        if len(content) > 500:
            return JsonResponse({
                'success': False,
                'message': 'Comment must be 500 characters or less'
            }, status=400)
        
        comment = IssueComment.objects.create(
            issue=issue,
            user=request.user,
            content=content
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Comment added successfully',
            'comment': {
                'id': comment.id,
                'user': comment.user.username,
                'content': comment.content,
                'created_at': comment.created_at.isoformat(),
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

>>>>>>> 2df7404 (11th commit)
