from flask import current_app, url_for, render_template
from flask_mail import Message
from app import mail
from threading import Thread
from datetime import datetime

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    send_email(
        '[Nutrisist] Reset Your Password',
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[user.email],
        text_body=render_template('auth/email/reset_password.txt',
                                user=user,
                                reset_url=reset_url),
        html_body=render_template('auth/email/reset_password.html',
                                user=user,
                                reset_url=reset_url,
                                year=datetime.utcnow().year)
    ) 