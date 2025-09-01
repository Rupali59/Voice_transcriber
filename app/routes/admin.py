"""
Admin routes for request tracking and monitoring
"""

from flask import Blueprint, render_template, request, jsonify, current_app

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
def dashboard():
    """Admin dashboard for request tracking"""
    return render_template('admin/dashboard.html')

@admin_bp.route('/requests')
def requests_view():
    """View all requests"""
    return render_template('admin/requests.html')

@admin_bp.route('/statistics')
def statistics_view():
    """View request statistics"""
    return render_template('admin/statistics.html')
