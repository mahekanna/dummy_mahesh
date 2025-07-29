"""
Admin API routes - converted from Flask admin functionality
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from config.settings import Config
from scripts.admin_manager import AdminManager
from scripts.ldap_manager import LDAPManager
from scripts.intelligent_scheduler import SmartScheduler
from scripts.load_predictor import SmartLoadPredictor

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user['role'] != 'admin':
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

@admin_bp.route('/api/admin/reports/generate/<report_type>', methods=['POST'])
def api_generate_report(current_user, report_type):
    """Generate and send admin reports"""
    try:
        admin_manager = AdminManager()
        
        if report_type == 'daily':
            success = admin_manager.send_daily_report()
        elif report_type == 'weekly':
            success = admin_manager.send_weekly_report()
        elif report_type == 'monthly':
            success = admin_manager.send_monthly_report()
        else:
            return jsonify({'success': False, 'message': 'Invalid report type'})
        
        return jsonify({
            'success': success,
            'message': f'{report_type.title()} report generated and sent' if success else 'Failed to generate report'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/admin/database/sync', methods=['POST'])
def api_sync_database(current_user):
    """Sync CSV to database"""
    try:
        admin_manager = AdminManager()
        success = admin_manager.sync_csv_to_database()
        
        return jsonify({
            'success': success,
            'message': 'Database sync completed' if success else 'Database sync failed'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/admin/data/cleanup', methods=['POST'])
def api_cleanup_data(current_user):
    """Clean up old data"""
    try:
        admin_manager = AdminManager()
        success = admin_manager.cleanup_old_data()
        
        return jsonify({
            'success': success,
            'message': 'Data cleanup completed' if success else 'Data cleanup failed'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/admin/scheduling/intelligent', methods=['POST'])
def api_intelligent_scheduling(current_user):
    """Run intelligent scheduling"""
    try:
        scheduler = SmartScheduler()
        current_quarter = Config.get_current_quarter()
        scheduler.assign_smart_schedules(current_quarter)
        
        return jsonify({
            'success': True,
            'message': 'Intelligent scheduling completed successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/admin/ldap/sync', methods=['POST'])
def api_sync_ldap_users(current_user):
    """Sync users from LDAP"""
    try:
        ldap_manager = LDAPManager()
        success, message = ldap_manager.sync_users_from_ldap()
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/admin/ldap/test', methods=['POST'])
def api_test_ldap_connection(current_user):
    """Test LDAP connection"""
    try:
        ldap_manager = LDAPManager()
        success, message = ldap_manager.test_ldap_connection()
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/admin/load-patterns/analyze', methods=['POST'])
def api_analyze_load_patterns(current_user):
    """Analyze load patterns for all servers"""
    try:
        predictor = SmartLoadPredictor()
        current_quarter = Config.get_current_quarter()
        recommendations = predictor.analyze_all_servers(current_quarter)
        
        return jsonify({
            'success': True,
            'message': f'Analyzed load patterns for {len(recommendations)} servers'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/admin/predictions/generate', methods=['POST'])
def api_generate_predictions(current_user):
    """Generate AI predictions for unscheduled servers"""
    try:
        from utils.csv_handler import CSVHandler
        
        predictor = SmartLoadPredictor()
        csv_handler = CSVHandler()
        servers = csv_handler.read_servers()
        
        # Generate predictions for servers without schedules
        prediction_count = 0
        for server in servers:
            # Simulate historical data if needed
            predictor.simulate_historical_data(server['Server Name'], days=7)
            prediction_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Generated predictions for {prediction_count} servers'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/admin/data/backup', methods=['POST'])
def api_backup_data(current_user):
    """Create backup of all data"""
    try:
        admin_manager = AdminManager()
        
        # Create backup
        backup_path = admin_manager._backup_csv_file()
        
        if backup_path:
            return jsonify({
                'success': True,
                'message': f'Data backup created successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to create backup'
            })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/admin/server-groups/sync', methods=['POST'])
def api_sync_host_groups(current_user):
    """Sync host groups from CSV to configuration"""
    try:
        from scripts.sync_host_groups import HostGroupSyncer
        syncer = HostGroupSyncer()
        result = syncer.run_full_sync()
        
        return jsonify({
            'success': result['success'],
            'message': f"Found {result.get('host_groups_found', 0)} host groups: {', '.join(result.get('host_groups', []))}" if result['success'] else result.get('error', 'Unknown error'),
            'details': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/admin/config/admin', methods=['GET', 'PUT'])
def admin_config(current_user):
    """Get/Update admin configuration"""
    try:
        admin_manager = AdminManager()
        
        if request.method == 'GET':
            config = admin_manager.load_admin_config()
            return jsonify({
                'success': True,
                'config': config
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            # Load current config
            config = admin_manager.load_admin_config()
            
            # Update config
            if 'admin_email' in data:
                config['admin_settings']['admin_email'] = data['admin_email']
            if 'backup_admin_email' in data:
                config['admin_settings']['backup_admin_email'] = data['backup_admin_email']
            if 'send_daily_reports' in data:
                config['admin_settings']['notification_settings']['send_daily_reports'] = data['send_daily_reports']
            if 'send_weekly_reports' in data:
                config['admin_settings']['notification_settings']['send_weekly_reports'] = data['send_weekly_reports']
            if 'send_error_alerts' in data:
                config['admin_settings']['notification_settings']['send_error_alerts'] = data['send_error_alerts']
            
            if admin_manager.save_admin_config(config):
                return jsonify({'success': True, 'message': 'Admin configuration updated successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to update admin configuration'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/admin/config/ldap', methods=['GET', 'PUT'])
def ldap_config(current_user):
    """Get/Update LDAP configuration"""
    try:
        ldap_manager = LDAPManager()
        
        if request.method == 'GET':
            # Get LDAP config from admin config
            admin_manager = AdminManager()
            admin_config = admin_manager.load_admin_config()
            ldap_config = admin_config.get('ldap_configuration', {})
            
            return jsonify({
                'success': True,
                'config': ldap_config
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            # Update LDAP config
            new_config = {
                'enabled': data.get('enabled', False),
                'server': data.get('server', ''),
                'base_dn': data.get('base_dn', ''),
                'bind_dn': data.get('bind_dn', '')
            }
            
            if data.get('bind_password'):
                new_config['bind_password'] = data['bind_password']
            
            if ldap_manager.update_ldap_config(new_config):
                return jsonify({'success': True, 'message': 'LDAP configuration updated successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to update LDAP configuration'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500