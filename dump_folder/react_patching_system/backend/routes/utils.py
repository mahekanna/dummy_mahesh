"""
Utility API routes - AI recommendations, timezone info, system health
"""

from flask import Blueprint, request, jsonify
import sys
import os
import calendar
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from utils.csv_handler import CSVHandler
from utils.timezone_handler import TimezoneHandler
from config.settings import Config

utils_bp = Blueprint('utils', __name__)

# Initialize handlers
csv_handler = CSVHandler()
timezone_handler = TimezoneHandler()

@utils_bp.route('/api/utils/available-dates/<quarter>')
def api_available_dates(current_user, quarter):
    """API endpoint to get available patching dates"""
    try:
        # Generate available patching dates (Thursdays) for the quarter
        current_year = datetime.now().year
        quarter_months = Config.QUARTERS.get(quarter, {}).get('months', [])
        
        available_dates = []
        
        for month in quarter_months:
            # Adjust year for Q1 which spans two years
            year = current_year
            if quarter == '1' and month in [11, 12]:
                if datetime.now().month < 11:
                    year = current_year
                else:
                    year = current_year
            elif quarter == '1' and month == 1:
                if datetime.now().month < 11:
                    year = current_year + 1
                else:
                    year = current_year + 1
            
            # Find all Thursdays in the month
            cal = calendar.monthcalendar(year, month)
            thursdays = [
                datetime(year, month, week[calendar.THURSDAY]).strftime('%Y-%m-%d')
                for week in cal
                if week[calendar.THURSDAY] != 0
            ]
            
            available_dates.extend(thursdays)
        
        return jsonify({
            'success': True,
            'dates': available_dates
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@utils_bp.route('/api/utils/server-timezone/<server_name>')
def api_server_timezone(current_user, server_name):
    """API endpoint to get server timezone information"""
    try:
        servers = csv_handler.read_servers(normalize_fields=True)
        server = None
        
        for s in servers:
            if s.get('server_name') == server_name:
                server = s
                break
        
        if not server:
            return jsonify({'success': False, 'message': 'Server not found'}), 404
        
        # Get timezone information
        server_timezone = server.get('server_timezone', 'UTC')
        now = datetime.now()
        timezone_abbr = timezone_handler.get_timezone_abbreviation(server_timezone, now)
        
        # Get current time in server timezone
        server_time = timezone_handler.get_current_time_in_timezone(server_timezone)
        
        return jsonify({
            'success': True,
            'timezone': server_timezone,
            'abbreviation': timezone_abbr,
            'current_time': server_time.strftime('%Y-%m-%d %H:%M:%S'),
            'offset': server_time.strftime('%z')
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@utils_bp.route('/api/utils/ai-recommendation/<server_name>/<quarter>')
def api_ai_recommendation(current_user, server_name, quarter):
    """API endpoint to get AI-powered scheduling recommendations"""
    try:
        from scripts.load_predictor import SmartLoadPredictor
        from scripts.intelligent_scheduler import SmartScheduler
        
        # Initialize predictors
        load_predictor = SmartLoadPredictor()
        intelligent_scheduler = SmartScheduler()
        
        # Get load-based recommendation
        load_recommendation = load_predictor.analyze_server_load_patterns(server_name)
        
        # Get intelligent scheduling recommendation
        available_thursdays = intelligent_scheduler.get_quarter_thursdays(quarter)
        
        if not available_thursdays:
            return jsonify({
                'success': False,
                'message': 'No available Thursday dates found for this quarter'
            })
        
        # Parse the recommended time from load predictor
        recommended_time = load_recommendation.get('recommended_time', '20:00')
        
        # Find the best Thursday based on load analysis
        best_thursday = None
        if load_recommendation.get('confidence_level') == 'High':
            # Use first available Thursday for high confidence
            best_thursday = available_thursdays[0]
        elif load_recommendation.get('confidence_level') == 'Medium':
            # Use second Thursday if available for medium confidence
            best_thursday = available_thursdays[1] if len(available_thursdays) > 1 else available_thursdays[0]
        else:
            # Use later Thursday for low confidence
            best_thursday = available_thursdays[-1] if available_thursdays else available_thursdays[0]
        
        # Format the response
        response = {
            'success': True,
            'recommended_date': best_thursday.strftime('%Y-%m-%d'),
            'recommended_time': recommended_time,
            'confidence_level': load_recommendation.get('confidence_level', 'Medium'),
            'reasoning': load_recommendation.get('reasoning', ['AI-based scheduling recommendation']),
            'risk_factors': load_recommendation.get('risk_factors', []),
            'alternative_times': load_recommendation.get('alternative_times', [])
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error generating recommendation: {str(e)}'
        }), 500

@utils_bp.route('/api/utils/system/health')
def api_system_health(current_user):
    """Get system health information"""
    try:
        import shutil
        
        # Check disk space
        free_space = shutil.disk_usage('/').free / (1024**3)  # GB
        
        health_status = 'healthy'
        health_message = 'All systems operational'
        
        if free_space < 1:
            health_status = 'critical'
            health_message = 'Low disk space - critical'
        elif free_space < 5:
            health_status = 'warning'
            health_message = 'Low disk space - warning'
        
        # Check CSV file accessibility
        csv_accessible = True
        try:
            csv_handler.read_servers()
        except Exception:
            csv_accessible = False
            health_status = 'error'
            health_message = 'CSV file access error'
        
        # Check LDAP status if enabled
        ldap_status = 'disabled'
        if Config.LDAP_ENABLED:
            try:
                from utils.nslcd_ldap_auth import NSLCDLDAPAuthenticator
                auth = NSLCDLDAPAuthenticator()
                if auth.test_ldap_connection():
                    ldap_status = 'connected'
                else:
                    ldap_status = 'error'
            except Exception:
                ldap_status = 'error'
        
        return jsonify({
            'success': True,
            'health': {
                'status': health_status,
                'message': health_message,
                'details': {
                    'disk_space_gb': round(free_space, 2),
                    'csv_accessible': csv_accessible,
                    'ldap_status': ldap_status,
                    'timestamp': datetime.now().isoformat()
                }
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@utils_bp.route('/api/utils/system/stats')
def api_system_stats(current_user):
    """Get system statistics"""
    try:
        servers = csv_handler.read_servers(normalize_fields=True)
        current_quarter = Config.get_current_quarter()
        
        # Calculate statistics
        stats = {
            'total_servers': len(servers),
            'pending': 0,
            'approved': 0,
            'scheduled': 0,
            'completed': 0,
            'failed': 0
        }
        
        host_groups = {}
        environments = {}
        
        for server in servers:
            approval_status = server.get(f'q{current_quarter}_approval_status', 'Pending')
            patch_status = server.get('current_quarter_status', 'Pending')
            
            # Count by approval status
            if approval_status in ['Approved', 'Auto-Approved']:
                stats['approved'] += 1
            else:
                stats['pending'] += 1
            
            # Count by patch status
            if patch_status == 'Scheduled':
                stats['scheduled'] += 1
            elif patch_status == 'Completed':
                stats['completed'] += 1
            elif patch_status == 'Failed':
                stats['failed'] += 1
            
            # Count host groups
            hg = server.get('host_group', 'unknown')
            host_groups[hg] = host_groups.get(hg, 0) + 1
            
            # Count environments
            env = server.get('environment', 'unknown')
            environments[env] = environments.get(env, 0) + 1
        
        return jsonify({
            'success': True,
            'stats': {
                'overview': stats,
                'host_groups': host_groups,
                'environments': environments,
                'current_quarter': current_quarter,
                'quarter_info': Config.QUARTERS.get(current_quarter, {}),
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@utils_bp.route('/api/utils/quarters')
def api_quarters_info(current_user):
    """Get quarters information"""
    try:
        current_quarter = Config.get_current_quarter()
        
        quarters_info = {}
        for quarter_id, quarter_data in Config.QUARTERS.items():
            quarters_info[quarter_id] = {
                'id': quarter_id,
                'name': quarter_data['name'],
                'months': quarter_data['months'],
                'is_current': quarter_id == current_quarter,
                'description': get_quarter_description(quarter_id)
            }
        
        return jsonify({
            'success': True,
            'current_quarter': current_quarter,
            'quarters': quarters_info
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@utils_bp.route('/api/utils/test-email', methods=['POST'])
def api_test_email(current_user):
    """Test email configuration (admin only)"""
    if current_user['role'] != 'admin':
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        from utils.email_sender import EmailSender
        
        data = request.get_json()
        recipient = data.get('recipient')
        
        if not recipient:
            return jsonify({'success': False, 'message': 'Recipient email required'}), 400
        
        email_sender = EmailSender()
        
        # Send test email
        subject = "Linux Patching System - Test Email"
        body = f"""
        This is a test email from the Linux Patching Automation System.
        
        Test performed by: {current_user['name']} ({current_user['email']})
        Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        If you received this email, the email configuration is working correctly.
        """
        
        success = email_sender.send_email(recipient, subject, body)
        
        return jsonify({
            'success': success,
            'message': 'Test email sent successfully' if success else 'Failed to send test email'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

def get_quarter_description(quarter_id):
    """Get quarter description"""
    descriptions = {
        '1': 'November to January',
        '2': 'February to April',
        '3': 'May to July',
        '4': 'August to October'
    }
    return descriptions.get(quarter_id, 'Unknown')