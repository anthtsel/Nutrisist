from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from . import main

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('health_insights.dashboard'))
    return redirect(url_for('auth.login'))

@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/support')
def support():
    return render_template('support.html') 