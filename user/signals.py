# C:\Users\user\Desktop\config\user\signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.conf import settings

@receiver(post_save, sender=get_user_model())
def send_verification_email(sender, instance, created, **kwargs):
    if created:
        # Generate email verification token
        token = default_token_generator.make_token(instance)
        uid = urlsafe_base64_encode(instance.pk.encode())
        
        # Create verification link
        verification_link = f'http://example.com/verify-email/?uid={uid}&token={token}'
        
        # Send email with verification link
        subject = 'Verify your email address'
        message = render_to_string('user/email_verification_email.html', {
            'user': instance,
            'verification_link': verification_link,
        })
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.email]) # Ощибка

