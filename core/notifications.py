"""
Notification service for The Blindspot Initiative.
Handles sending email notifications to authorities when issues are reported.
"""
import threading
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone


def send_authority_notification(issue):
    """
    Send notification email to the responsible authority.
    Uses threading to avoid blocking the request.
    """
    authority = issue.category.authority
    
    # Skip if no email configured for this authority
    if not authority.email:
        return None
    
    # Run email sending in a separate thread to avoid blocking
    thread = threading.Thread(
        target=_send_notification_email,
        args=(issue, authority)
    )
    thread.daemon = True
    thread.start()
    
    return True


def _send_notification_email(issue, authority):
    """
    Internal function to send the email and log the result.
    Runs in a separate thread.
    """
    from .models import NotificationLog
    
    # Create log entry first (pending)
    notification_log = NotificationLog.objects.create(
        issue=issue,
        authority=authority,
        email_address=authority.email,
        status='pending'
    )
    
    try:
        # Build the email content
        subject = f"[Blindspot Initiative] New Issue Report #{issue.id}: {issue.title}"
        
        # Create map link
        map_link = f"https://www.google.com/maps?q={issue.latitude},{issue.longitude}"
        
        # Severity display
        severity_labels = {
            1: 'Minor',
            2: 'Low',
            3: 'Moderate',
            4: 'High',
            5: 'Critical'
        }
        
        message = f"""
THE BLINDSPOT INITIATIVE - CIVIC ISSUE NOTIFICATION
====================================================

A new civic issue has been reported and requires your attention.

ISSUE DETAILS
-------------
Issue ID: #{issue.id}
Title: {issue.title}
Category: {issue.category.name}
Authority: {authority.name}
Severity: {severity_labels.get(issue.severity, 'Unknown')} (Level {issue.severity}/5)

LOCATION
--------
Address: {issue.address or 'Not specified'}
Coordinates: {issue.latitude}, {issue.longitude}
View on Map: {map_link}

DESCRIPTION
-----------
{issue.description}

REPORT DETAILS
--------------
Reported On: {issue.reported_at.strftime('%B %d, %Y at %I:%M %p')}
Current Status: {issue.get_status_display()}

TRANSPARENCY NOTICE
-------------------
This issue has been publicly logged on The Blindspot Initiative platform 
(https://blindspot.org). The community is actively monitoring the status 
of this report.

This is an automated notification from The Blindspot Initiative - 
a civic accountability platform documenting government neglect in public spaces.

---
The Blindspot Initiative
"These problems were never invisible — we just stopped seeing them."
"""
        
        # Send the email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[authority.email],
            fail_silently=False
        )
        
        # Update log to sent
        notification_log.status = 'sent'
        notification_log.save()
        
    except Exception as e:
        # Log the failure
        notification_log.status = 'failed'
        notification_log.error_message = str(e)
        notification_log.save()
