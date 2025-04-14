from flask import current_app, render_template
from flask_mail import Mail, Message
from threading import Thread

mail = Mail()

def send_async_email(app, msg):
    """Send email asynchronously."""
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, text_body, html_body, sender=None):
    """Send email with both text and HTML versions."""
    msg = Message(
        subject=subject,
        recipients=recipients,
        sender=sender or current_app.config['MAIL_DEFAULT_SENDER']
    )
    msg.body = text_body
    msg.html = html_body
    
    # Send email asynchronously
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()

def send_verification_email(user, token):
    """Send email verification link."""
    verification_url = url_for('auth.verify_email', token=token, _external=True)
    
    send_email(
        'Verify Your Email Address',
        [user.email],
        render_template(
            'auth/email/verify_email.txt',
            user=user,
            verification_url=verification_url
        ),
        render_template(
            'auth/email/verify_email.html',
            user=user,
            verification_url=verification_url
        )
    )

def send_password_reset_email(user, token):
    """Send password reset link."""
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    send_email(
        'Reset Your Password',
        [user.email],
        render_template(
            'auth/email/reset_password.txt',
            user=user,
            reset_url=reset_url
        ),
        render_template(
            'auth/email/reset_password.html',
            user=user,
            reset_url=reset_url
        )
    ) 