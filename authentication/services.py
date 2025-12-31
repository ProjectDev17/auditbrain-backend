from django.contrib.auth import get_user_model
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.core.mail import send_mail
from django.conf import settings
from core.services import audit_logger
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class PasswordResetService:
    """
    Servicio para gestionar recuperación de contraseñas.
    Usa tokens firmados con expiración de 1 hora.
    """
    
    SALT = 'password-reset'
    MAX_AGE = 3600  # 1 hora
    
    @classmethod
    def generate_token(cls, email):
        """Genera un token firmado para el email."""
        signer = TimestampSigner(salt=cls.SALT)
        return signer.sign(email)
    
    @classmethod
    def verify_token(cls, token):
        """Verifica y decodifica un token. Retorna email o None."""
        signer = TimestampSigner(salt=cls.SALT)
        try:
            email = signer.unsign(token, max_age=cls.MAX_AGE)
            return email
        except (SignatureExpired, BadSignature):
            return None
    
    @classmethod
    def send_reset_email(cls, email):
        """Envía email de recuperación (o lo muestra en consola en dev)."""
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # No revelar si el email existe por seguridad
            logger.warning(f"Password reset requested for non-existent email: {email}")
            audit_logger.log_security_event(
                action='PASSWORD_RESET_REQUEST',
                user_email=email,
                success=False,
                details={'reason': 'user_not_found'}
            )
            return
        
        token = cls.generate_token(email)
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        
        # Logging
        audit_logger.log_security_event(
            action='PASSWORD_RESET_REQUEST',
            user_email=email,
            success=True
        )
        
        # En desarrollo, mostrar en consola
        if settings.DEBUG:
            logger.info(f"Password reset link: {reset_link}")
            print(f"\n{'='*50}")
            print(f"PASSWORD RESET REQUEST")
            print(f"{'='*50}")
            print(f"Email: {email}")
            print(f"Link: {reset_link}")
            print(f"{'='*50}\n")
        else:
            # En producción, enviar email real
            send_mail(
                'Recuperación de contraseña - AuditBrain',
                f'Usa este enlace para recuperar tu contraseña: {reset_link}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
    
    @classmethod
    def reset_password(cls, token, new_password):
        """Resetea la contraseña usando un token válido."""
        email = cls.verify_token(token)
        if not email:
            audit_logger.log_security_event(
                action='PASSWORD_RESET_CONFIRM',
                success=False,
                details={'reason': 'invalid_token'}
            )
            return False
        
        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            
            audit_logger.log_security_event(
                action='PASSWORD_RESET_CONFIRM',
                user_email=email,
                success=True
            )
            
            logger.info(f"Password reset successful for: {email}")
            return True
        except User.DoesNotExist:
            audit_logger.log_security_event(
                action='PASSWORD_RESET_CONFIRM',
                user_email=email,
                success=False,
                details={'reason': 'user_not_found'}
            )
            return False
