from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from . import admin
from ..models import User, UserRole
from .. import db
from ..auth.decorators import admin_required
from datetime import datetime

@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard showing system statistics."""
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    verified_users = User.query.filter_by(email_verified=True).count()
    locked_users = User.query.filter(User.locked_until > datetime.utcnow()).count()
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         verified_users=verified_users,
                         locked_users=locked_users,
                         recent_users=recent_users)

@admin.route('/users')
@login_required
@admin_required
def users():
    """List all users with management options."""
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=20)
    return render_template('admin/users.html', users=users)

@admin.route('/user/<int:id>')
@login_required
@admin_required
def user_detail(id):
    """Show detailed user information."""
    user = User.query.get_or_404(id)
    return render_template('admin/user_detail.html', user=user)

@admin.route('/user/<int:id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_user_active(id):
    """Toggle user active status."""
    user = User.query.get_or_404(id)
    if user == current_user:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('admin.users'))
        
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} has been {status}.', 'success')
    return redirect(url_for('admin.users'))

@admin.route('/user/<int:id>/reset-login-attempts', methods=['POST'])
@login_required
@admin_required
def reset_login_attempts(id):
    """Reset user's failed login attempts."""
    user = User.query.get_or_404(id)
    user.failed_login_attempts = 0
    user.locked_until = None
    db.session.commit()
    
    flash(f'Login attempts reset for user {user.username}.', 'success')
    return redirect(url_for('admin.user_detail', id=user.id))

@admin.route('/user/<int:id>/change-role', methods=['POST'])
@login_required
@admin_required
def change_user_role(id):
    """Change user's role."""
    user = User.query.get_or_404(id)
    if user == current_user:
        flash('You cannot change your own role.', 'danger')
        return redirect(url_for('admin.users'))
        
    new_role = request.form.get('role')
    if new_role not in [role.value for role in UserRole]:
        flash('Invalid role specified.', 'danger')
        return redirect(url_for('admin.users'))
        
    user.role = new_role
    db.session.commit()
    
    flash(f'Role updated for user {user.username}.', 'success')
    return redirect(url_for('admin.user_detail', id=user.id)) 