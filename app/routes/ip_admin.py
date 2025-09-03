"""
IP-based file management admin routes
"""

from flask import Blueprint, render_template, jsonify, request, current_app

ip_admin_bp = Blueprint('ip_admin', __name__, url_prefix='/admin/ip')

@ip_admin_bp.route('/')
def ip_dashboard():
    """IP management dashboard"""
    return render_template('admin/ip_dashboard.html')

@ip_admin_bp.route('/stats')
def get_ip_stats():
    """Get overall IP statistics"""
    try:
        from app import get_ip_file_service
        from app import get_ip_file_service
        ip_file_service = get_ip_file_service()
        
        # Get all IPs and their stats
        all_ips = list(ip_file_service.ip_quotas.keys())
        total_files = sum(len(files) for files in ip_file_service.ip_files.values())
        total_size_mb = sum(
            sum(f.size_mb for f in files) 
            for files in ip_file_service.ip_files.values()
        )
        
        # Get top IPs by file count
        top_ips_by_files = sorted(
            [(ip, len(files)) for ip, files in ip_file_service.ip_files.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Get top IPs by size
        top_ips_by_size = sorted(
            [(ip, sum(f.size_mb for f in files)) for ip, files in ip_file_service.ip_files.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Get blocked IPs
        blocked_ips = [
            ip for ip, quota in ip_file_service.ip_quotas.items()
            if quota.is_blocked
        ]
        
        return jsonify({
            'success': True,
            'stats': {
                'total_ips': len(all_ips),
                'total_files': total_files,
                'total_size_mb': round(total_size_mb, 2),
                'blocked_ips': len(blocked_ips),
                'top_ips_by_files': top_ips_by_files,
                'top_ips_by_size': top_ips_by_size,
                'blocked_ips_list': blocked_ips
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Get IP stats error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get stats'}), 500

@ip_admin_bp.route('/ip/<ip_address>')
def get_ip_details(ip_address):
    """Get detailed information about a specific IP"""
    try:
        from app import get_ip_file_service
        from app import get_ip_file_service
        ip_file_service = get_ip_file_service()
        stats = ip_file_service.get_ip_stats(ip_address)
        
        return jsonify({
            'success': True,
            'ip_details': stats
        })
        
    except Exception as e:
        current_app.logger.error(f"Get IP details error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get IP details'}), 500

@ip_admin_bp.route('/ip/<ip_address>/block', methods=['POST'])
def block_ip(ip_address):
    """Block an IP address"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'Manual block')
        hours = data.get('hours', 24)
        
        from app import get_ip_file_service
        ip_file_service = get_ip_file_service()
        ip_file_service._block_ip(ip_address, reason, hours)
        
        return jsonify({
            'success': True,
            'message': f'IP {ip_address} blocked for {hours} hours'
        })
        
    except Exception as e:
        current_app.logger.error(f"Block IP error: {e}")
        return jsonify({'success': False, 'error': 'Failed to block IP'}), 500

@ip_admin_bp.route('/ip/<ip_address>/unblock', methods=['POST'])
def unblock_ip(ip_address):
    """Unblock an IP address"""
    try:
        from app import get_ip_file_service
        ip_file_service = get_ip_file_service()
        quota = ip_file_service.ip_quotas.get(ip_address)
        
        if quota:
            quota.is_blocked = False
            quota.block_reason = None
            quota.block_until = None
            ip_file_service._save_data()
        
        return jsonify({
            'success': True,
            'message': f'IP {ip_address} unblocked'
        })
        
    except Exception as e:
        current_app.logger.error(f"Unblock IP error: {e}")
        return jsonify({'success': False, 'error': 'Failed to unblock IP'}), 500

@ip_admin_bp.route('/ip/<ip_address>/cleanup', methods=['POST'])
def cleanup_ip_files(ip_address):
    """Clean up all files for an IP address"""
    try:
        from app import get_ip_file_service
        ip_file_service = get_ip_file_service()
        deleted_count = ip_file_service.cleanup_ip_files(ip_address)
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up {deleted_count} files for IP {ip_address}',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        current_app.logger.error(f"Cleanup IP files error: {e}")
        return jsonify({'success': False, 'error': 'Failed to cleanup IP files'}), 500

@ip_admin_bp.route('/cleanup-all', methods=['POST'])
def cleanup_all_old_files():
    """Manually trigger cleanup of all old files"""
    try:
        from app import get_ip_file_service
        ip_file_service = get_ip_file_service()
        ip_file_service._cleanup_old_files()
        
        return jsonify({
            'success': True,
            'message': 'Cleanup completed successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Cleanup all files error: {e}")
        return jsonify({'success': False, 'error': 'Failed to cleanup files'}), 500

# Storage Management Endpoints

@ip_admin_bp.route('/storage/stats')
def get_storage_stats():
    """Get comprehensive storage statistics"""
    try:
        from app import get_storage_manager
        storage_manager = get_storage_manager()
        stats = storage_manager.get_storage_stats()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_size_mb': round(stats.total_size_mb, 2),
                'total_files': stats.total_files,
                'disk_usage_percent': round(stats.disk_usage_percent, 2),
                'available_space_mb': round(stats.available_space_mb, 2),
                'oldest_file_age_hours': round(stats.oldest_file_age_hours, 2),
                'newest_file_age_hours': round(stats.newest_file_age_hours, 2),
                'average_file_size_mb': round(stats.average_file_size_mb, 2)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Get storage stats error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get storage stats'}), 500

@ip_admin_bp.route('/storage/health')
def get_storage_health():
    """Get storage health information"""
    try:
        from app import get_storage_manager
        storage_manager = get_storage_manager()
        health = storage_manager.get_storage_health()
        
        return jsonify({
            'success': True,
            'health': health
        })
        
    except Exception as e:
        current_app.logger.error(f"Get storage health error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get storage health'}), 500

@ip_admin_bp.route('/storage/cleanup', methods=['POST'])
def trigger_storage_cleanup():
    """Manually trigger storage cleanup"""
    try:
        from app import get_storage_manager
        storage_manager = get_storage_manager()
        
        cleanup_results = storage_manager.smart_cleanup()
        
        total_deleted = sum(result['deleted_files'] for result in cleanup_results.values())
        total_freed = sum(result['freed_space_mb'] for result in cleanup_results.values())
        
        return jsonify({
            'success': True,
            'message': f'Storage cleanup completed. Deleted {total_deleted} files, freed {total_freed:.2f} MB',
            'results': cleanup_results,
            'summary': {
                'total_deleted_files': total_deleted,
                'total_freed_mb': round(total_freed, 2)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Storage cleanup error: {e}")
        return jsonify({'success': False, 'error': 'Failed to cleanup storage'}), 500

@ip_admin_bp.route('/storage/cleanup/age', methods=['POST'])
def cleanup_by_age():
    """Clean up files by age"""
    try:
        from app import get_storage_manager
        storage_manager = get_storage_manager()
        
        data = request.get_json() or {}
        max_age_hours = data.get('max_age_hours')
        
        deleted_files, freed_space = storage_manager.cleanup_by_age(max_age_hours)
        
        return jsonify({
            'success': True,
            'message': f'Age cleanup completed. Deleted {deleted_files} files, freed {freed_space:.2f} MB',
            'deleted_files': deleted_files,
            'freed_space_mb': round(freed_space, 2)
        })
        
    except Exception as e:
        current_app.logger.error(f"Age cleanup error: {e}")
        return jsonify({'success': False, 'error': 'Failed to cleanup by age'}), 500

@ip_admin_bp.route('/storage/cleanup/size', methods=['POST'])
def cleanup_by_size():
    """Clean up files by size"""
    try:
        from app import get_storage_manager
        storage_manager = get_storage_manager()
        
        data = request.get_json() or {}
        target_size_mb = data.get('target_size_mb')
        
        if not target_size_mb:
            return jsonify({'error': 'target_size_mb is required'}), 400
        
        deleted_files, freed_space = storage_manager.cleanup_by_size(target_size_mb)
        
        return jsonify({
            'success': True,
            'message': f'Size cleanup completed. Deleted {deleted_files} files, freed {freed_space:.2f} MB',
            'deleted_files': deleted_files,
            'freed_space_mb': round(freed_space, 2)
        })
        
    except Exception as e:
        current_app.logger.error(f"Size cleanup error: {e}")
        return jsonify({'success': False, 'error': 'Failed to cleanup by size'}), 500

@ip_admin_bp.route('/storage/cleanup/emergency', methods=['POST'])
def emergency_cleanup():
    """Trigger emergency cleanup"""
    try:
        from app import get_storage_manager
        storage_manager = get_storage_manager()
        
        deleted_files, freed_space = storage_manager.emergency_cleanup()
        
        return jsonify({
            'success': True,
            'message': f'Emergency cleanup completed. Deleted {deleted_files} files, freed {freed_space:.2f} MB',
            'deleted_files': deleted_files,
            'freed_space_mb': round(freed_space, 2)
        })
        
    except Exception as e:
        current_app.logger.error(f"Emergency cleanup error: {e}")
        return jsonify({'success': False, 'error': 'Failed to perform emergency cleanup'}), 500

@ip_admin_bp.route('/storage/logs')
def get_cleanup_logs():
    """Get recent cleanup logs"""
    try:
        from app import get_storage_manager
        storage_manager = get_storage_manager()
        
        limit = request.args.get('limit', 50, type=int)
        logs = storage_manager.get_cleanup_log(limit)
        
        return jsonify({
            'success': True,
            'logs': logs,
            'count': len(logs)
        })
        
    except Exception as e:
        current_app.logger.error(f"Get cleanup logs error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get cleanup logs'}), 500
