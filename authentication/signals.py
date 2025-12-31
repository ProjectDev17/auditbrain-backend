from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver
from core.services import audit_logger
import logging

logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Registrar login exitoso en MongoDB."""
    audit_logger.log_security_event(
        action='LOGIN_SUCCESS',
        user_email=user.email,
        ip_address=request.META.get('REMOTE_ADDR') if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT') if request else None,
        success=True
    )
    logger.info(f"User logged in: {user.email}")


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """Registrar intento de login fallido en MongoDB."""
    email = credentials.get('username') or credentials.get('email', 'unknown')
    audit_logger.log_security_event(
        action='LOGIN_FAILED',
        user_email=email,
        ip_address=request.META.get('REMOTE_ADDR') if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT') if request else None,
        success=False
    )
    logger.warning(f"Failed login attempt for: {email}")
