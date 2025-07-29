"""
Email Templates for Linux Patching Automation
"""

from datetime import datetime
from typing import Dict, List, Any

class EmailTemplates:
    """Email template generator for various patching notifications"""
    
    @staticmethod
    def get_base_style():
        """Get base CSS style for all emails"""
        return """
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 800px; margin: 0 auto; padding: 20px; }
            .header { background-color: #2c3e50; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }
            .content { background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }
            .status-success { color: #27ae60; font-weight: bold; }
            .status-failed { color: #e74c3c; font-weight: bold; }
            .status-pending { color: #f39c12; font-weight: bold; }
            .status-scheduled { color: #3498db; font-weight: bold; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #34495e; color: white; }
            tr:hover { background-color: #f5f5f5; }
            .footer { margin-top: 20px; padding: 10px; text-align: center; color: #7f8c8d; font-size: 12px; }
            .button { display: inline-block; padding: 10px 20px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px; margin: 10px 5px; }
            .button:hover { background-color: #2980b9; }
            .alert { padding: 15px; margin: 10px 0; border-radius: 5px; }
            .alert-info { background-color: #d1ecf1; border: 1px solid #bee5eb; color: #0c5460; }
            .alert-warning { background-color: #fff3cd; border: 1px solid #ffeeba; color: #856404; }
            .alert-danger { background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
            .summary-box { background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 15px 0; }
            .metric { display: inline-block; margin: 10px 20px; }
            .metric-value { font-size: 24px; font-weight: bold; color: #2c3e50; }
            .metric-label { font-size: 14px; color: #7f8c8d; }
        </style>
        """
    
    @staticmethod
    def precheck_notification(servers: List[Dict], quarter: str) -> Dict[str, str]:
        """Pre-check notification email template"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        passed_count = sum(1 for s in servers if s.get('precheck_status') == 'passed')
        failed_count = len(servers) - passed_count
        
        subject = f"[Patching Pre-Check] {quarter} - {passed_count} Passed, {failed_count} Failed"
        
        body = f"""
        <html>
        <head>{EmailTemplates.get_base_style()}</head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Linux Patching Pre-Check Report</h2>
                    <p>{quarter} Patching Cycle</p>
                </div>
                
                <div class="content">
                    <div class="summary-box">
                        <h3>Pre-Check Summary</h3>
                        <div class="metric">
                            <div class="metric-value">{len(servers)}</div>
                            <div class="metric-label">Total Servers</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value" style="color: #27ae60;">{passed_count}</div>
                            <div class="metric-label">Passed</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value" style="color: #e74c3c;">{failed_count}</div>
                            <div class="metric-label">Failed</div>
                        </div>
                    </div>
                    
                    <p><strong>Pre-check completed at:</strong> {current_time}</p>
                    
                    {EmailTemplates._generate_precheck_details(servers)}
                    
                    <div class="alert alert-info">
                        <strong>Next Steps:</strong>
                        <ul>
                            <li>Review failed pre-checks and resolve issues</li>
                            <li>Approve servers for patching using the CLI tool</li>
                            <li>Patching will commence as per schedule</li>
                        </ul>
                    </div>
                </div>
                
                <div class="footer">
                    <p>This is an automated message from Linux Patching Automation System</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return {"subject": subject, "body": body, "type": "html"}
    
    @staticmethod
    def _generate_precheck_details(servers: List[Dict]) -> str:
        """Generate detailed pre-check results table"""
        if not servers:
            return "<p>No servers to display.</p>"
        
        failed_servers = [s for s in servers if s.get('precheck_status') != 'passed']
        
        if not failed_servers:
            return "<div class='alert alert-success'>All servers passed pre-checks!</div>"
        
        html = "<h4>Failed Pre-Checks</h4><table>"
        html += "<tr><th>Server</th><th>Check Type</th><th>Issue</th><th>Details</th></tr>"
        
        for server in failed_servers:
            issues = server.get('precheck_issues', [])
            for issue in issues:
                html += f"""
                <tr>
                    <td>{server.get('name', 'Unknown')}</td>
                    <td>{issue.get('check', 'Unknown')}</td>
                    <td>{issue.get('issue', 'Unknown')}</td>
                    <td>{issue.get('details', 'N/A')}</td>
                </tr>
                """
        
        html += "</table>"
        return html
    
    @staticmethod
    def patching_started(server: str, quarter: str, scheduled_time: str) -> Dict[str, str]:
        """Patching started notification"""
        subject = f"[Patching Started] {server} - {quarter}"
        
        body = f"""
        <html>
        <head>{EmailTemplates.get_base_style()}</head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Patching Started</h2>
                </div>
                
                <div class="content">
                    <div class="alert alert-info">
                        <strong>Patching has started for:</strong> {server}
                    </div>
                    
                    <table>
                        <tr><td><strong>Server:</strong></td><td>{server}</td></tr>
                        <tr><td><strong>Quarter:</strong></td><td>{quarter}</td></tr>
                        <tr><td><strong>Scheduled Time:</strong></td><td>{scheduled_time}</td></tr>
                        <tr><td><strong>Started At:</strong></td><td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
                    </table>
                    
                    <p>You will receive another notification when patching is complete.</p>
                </div>
                
                <div class="footer">
                    <p>Linux Patching Automation System</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return {"subject": subject, "body": body, "type": "html"}
    
    @staticmethod
    def patching_completed(result: Dict) -> Dict[str, str]:
        """Patching completed notification"""
        server = result.get('server', 'Unknown')
        status = "Success" if result.get('success') else "Failed"
        status_class = "status-success" if result.get('success') else "status-failed"
        
        subject = f"[Patching {status}] {server}"
        
        body = f"""
        <html>
        <head>{EmailTemplates.get_base_style()}</head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Patching Completed</h2>
                </div>
                
                <div class="content">
                    <h3>Server: {server}</h3>
                    <p>Status: <span class="{status_class}">{status}</span></p>
                    
                    <table>
                        <tr><td><strong>Start Time:</strong></td><td>{result.get('start_time', 'N/A')}</td></tr>
                        <tr><td><strong>End Time:</strong></td><td>{result.get('end_time', 'N/A')}</td></tr>
                        <tr><td><strong>Duration:</strong></td><td>{result.get('duration', 'N/A')}</td></tr>
                        <tr><td><strong>Patches Applied:</strong></td><td>{result.get('patches_applied', 0)}</td></tr>
                        <tr><td><strong>Reboot Required:</strong></td><td>{result.get('reboot_required', 'No')}</td></tr>
                    </table>
                    
                    {EmailTemplates._generate_patch_details(result)}
                    
                    {EmailTemplates._generate_postcheck_results(result)}
                </div>
                
                <div class="footer">
                    <p>Linux Patching Automation System</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return {"subject": subject, "body": body, "type": "html"}
    
    @staticmethod
    def _generate_patch_details(result: Dict) -> str:
        """Generate patch details section"""
        if not result.get('success'):
            error = result.get('error', 'Unknown error')
            return f"""
            <div class="alert alert-danger">
                <strong>Error Details:</strong><br/>
                {error}
            </div>
            """
        
        patches = result.get('patches', [])
        if not patches:
            return "<p>No patch details available.</p>"
        
        html = "<h4>Patches Applied</h4><table>"
        html += "<tr><th>Package</th><th>Old Version</th><th>New Version</th></tr>"
        
        for patch in patches[:10]:  # Show first 10 patches
            html += f"""
            <tr>
                <td>{patch.get('package', 'Unknown')}</td>
                <td>{patch.get('old_version', 'N/A')}</td>
                <td>{patch.get('new_version', 'N/A')}</td>
            </tr>
            """
        
        if len(patches) > 10:
            html += f"<tr><td colspan='3'>... and {len(patches) - 10} more packages</td></tr>"
        
        html += "</table>"
        return html
    
    @staticmethod
    def _generate_postcheck_results(result: Dict) -> str:
        """Generate post-check results section"""
        postchecks = result.get('postchecks', {})
        if not postchecks:
            return ""
        
        all_passed = all(postchecks.values())
        alert_class = "alert-success" if all_passed else "alert-warning"
        
        html = f"""
        <h4>Post-Patching Checks</h4>
        <div class="alert {alert_class}">
            <strong>Post-check Status:</strong> {'All Passed' if all_passed else 'Some Checks Failed'}
        </div>
        <table>
        <tr><th>Check</th><th>Status</th></tr>
        """
        
        for check, passed in postchecks.items():
            status = "Passed" if passed else "Failed"
            status_class = "status-success" if passed else "status-failed"
            html += f"<tr><td>{check}</td><td class='{status_class}'>{status}</td></tr>"
        
        html += "</table>"
        return html
    
    @staticmethod
    def approval_request(servers: List[Dict], quarter: str, requester: str) -> Dict[str, str]:
        """Approval request email template"""
        subject = f"[Approval Required] {quarter} Patching - {len(servers)} Servers"
        
        server_list = ""
        for server in servers[:20]:  # Show first 20 servers
            server_list += f"""
            <tr>
                <td>{server.get('name', 'Unknown')}</td>
                <td>{server.get('group', 'N/A')}</td>
                <td>{server.get('os', 'N/A')}</td>
                <td>{server.get('patch_date', 'N/A')}</td>
                <td>{server.get('patch_time', 'N/A')}</td>
            </tr>
            """
        
        if len(servers) > 20:
            server_list += f"<tr><td colspan='5'>... and {len(servers) - 20} more servers</td></tr>"
        
        body = f"""
        <html>
        <head>{EmailTemplates.get_base_style()}</head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Patching Approval Request</h2>
                    <p>{quarter} Patching Cycle</p>
                </div>
                
                <div class="content">
                    <div class="alert alert-warning">
                        <strong>Action Required:</strong> Please review and approve the following servers for patching.
                    </div>
                    
                    <table>
                        <tr><td><strong>Requested By:</strong></td><td>{requester}</td></tr>
                        <tr><td><strong>Request Date:</strong></td><td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
                        <tr><td><strong>Total Servers:</strong></td><td>{len(servers)}</td></tr>
                        <tr><td><strong>Quarter:</strong></td><td>{quarter}</td></tr>
                    </table>
                    
                    <h4>Servers Pending Approval</h4>
                    <table>
                        <tr>
                            <th>Server Name</th>
                            <th>Host Group</th>
                            <th>OS</th>
                            <th>Patch Date</th>
                            <th>Patch Time</th>
                        </tr>
                        {server_list}
                    </table>
                    
                    <div style="text-align: center; margin: 20px 0;">
                        <p><strong>To approve these servers, use the CLI command:</strong></p>
                        <code style="background-color: #f5f5f5; padding: 10px; display: inline-block;">
                            patch-manager approval approve --quarter {quarter} --all
                        </code>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Linux Patching Automation System</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return {"subject": subject, "body": body, "type": "html"}
    
    @staticmethod
    def daily_summary(stats: Dict) -> Dict[str, str]:
        """Daily summary report email"""
        subject = f"[Daily Summary] Linux Patching - {datetime.now().strftime('%Y-%m-%d')}"
        
        body = f"""
        <html>
        <head>{EmailTemplates.get_base_style()}</head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Daily Patching Summary</h2>
                    <p>{datetime.now().strftime('%A, %B %d, %Y')}</p>
                </div>
                
                <div class="content">
                    <div class="summary-box">
                        <h3>Today's Statistics</h3>
                        <div class="metric">
                            <div class="metric-value">{stats.get('total_servers', 0)}</div>
                            <div class="metric-label">Total Servers</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value" style="color: #3498db;">{stats.get('scheduled_today', 0)}</div>
                            <div class="metric-label">Scheduled Today</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value" style="color: #27ae60;">{stats.get('completed_today', 0)}</div>
                            <div class="metric-label">Completed</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value" style="color: #e74c3c;">{stats.get('failed_today', 0)}</div>
                            <div class="metric-label">Failed</div>
                        </div>
                    </div>
                    
                    {EmailTemplates._generate_daily_details(stats)}
                    
                    <h4>Upcoming Patches (Next 7 Days)</h4>
                    {EmailTemplates._generate_upcoming_patches(stats.get('upcoming', []))}
                    
                    <h4>Recent Failures</h4>
                    {EmailTemplates._generate_recent_failures(stats.get('recent_failures', []))}
                </div>
                
                <div class="footer">
                    <p>Linux Patching Automation System - Daily Report</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return {"subject": subject, "body": body, "type": "html"}
    
    @staticmethod
    def _generate_daily_details(stats: Dict) -> str:
        """Generate daily activity details"""
        completed = stats.get('completed_servers', [])
        failed = stats.get('failed_servers', [])
        
        html = ""
        
        if completed:
            html += "<h4>Successfully Patched Today</h4><ul>"
            for server in completed[:10]:
                html += f"<li>{server.get('name')} - Completed at {server.get('time')}</li>"
            if len(completed) > 10:
                html += f"<li>... and {len(completed) - 10} more</li>"
            html += "</ul>"
        
        if failed:
            html += "<h4>Failed Patches Today</h4><ul>"
            for server in failed:
                html += f"<li>{server.get('name')} - {server.get('error')}</li>"
            html += "</ul>"
        
        return html
    
    @staticmethod
    def _generate_upcoming_patches(upcoming: List[Dict]) -> str:
        """Generate upcoming patches table"""
        if not upcoming:
            return "<p>No patches scheduled for the next 7 days.</p>"
        
        html = "<table><tr><th>Date</th><th>Server</th><th>Group</th><th>Time</th></tr>"
        
        for patch in upcoming[:20]:
            html += f"""
            <tr>
                <td>{patch.get('date')}</td>
                <td>{patch.get('server')}</td>
                <td>{patch.get('group')}</td>
                <td>{patch.get('time')}</td>
            </tr>
            """
        
        if len(upcoming) > 20:
            html += f"<tr><td colspan='4'>... and {len(upcoming) - 20} more</td></tr>"
        
        html += "</table>"
        return html
    
    @staticmethod
    def _generate_recent_failures(failures: List[Dict]) -> str:
        """Generate recent failures table"""
        if not failures:
            return "<p>No recent failures.</p>"
        
        html = "<table><tr><th>Date</th><th>Server</th><th>Error</th><th>Action Required</th></tr>"
        
        for failure in failures[:10]:
            html += f"""
            <tr>
                <td>{failure.get('date')}</td>
                <td>{failure.get('server')}</td>
                <td>{failure.get('error')}</td>
                <td>{failure.get('action', 'Review logs')}</td>
            </tr>
            """
        
        html += "</table>"
        return html
    
    @staticmethod
    def quarterly_report(quarter: str, stats: Dict) -> Dict[str, str]:
        """Quarterly patching report"""
        subject = f"[Quarterly Report] {quarter} Patching Summary"
        
        success_rate = (stats.get('completed', 0) / stats.get('total', 1)) * 100 if stats.get('total', 0) > 0 else 0
        
        body = f"""
        <html>
        <head>{EmailTemplates.get_base_style()}</head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Quarterly Patching Report</h2>
                    <p>{quarter} - {datetime.now().year}</p>
                </div>
                
                <div class="content">
                    <div class="summary-box">
                        <h3>Quarter Summary</h3>
                        <div class="metric">
                            <div class="metric-value">{stats.get('total', 0)}</div>
                            <div class="metric-label">Total Servers</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value" style="color: #27ae60;">{stats.get('completed', 0)}</div>
                            <div class="metric-label">Completed</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value" style="color: #e74c3c;">{stats.get('failed', 0)}</div>
                            <div class="metric-label">Failed</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">{success_rate:.1f}%</div>
                            <div class="metric-label">Success Rate</div>
                        </div>
                    </div>
                    
                    <h4>Patching Timeline</h4>
                    <table>
                        <tr><td><strong>Quarter Start:</strong></td><td>{stats.get('start_date')}</td></tr>
                        <tr><td><strong>Quarter End:</strong></td><td>{stats.get('end_date')}</td></tr>
                        <tr><td><strong>Total Patching Windows:</strong></td><td>{stats.get('patching_windows', 0)}</td></tr>
                        <tr><td><strong>Average Patch Duration:</strong></td><td>{stats.get('avg_duration', 'N/A')}</td></tr>
                    </table>
                    
                    <h4>Group Performance</h4>
                    {EmailTemplates._generate_group_performance(stats.get('group_stats', {}))}
                    
                    <h4>Common Issues</h4>
                    {EmailTemplates._generate_common_issues(stats.get('common_issues', []))}
                    
                    <h4>Recommendations</h4>
                    {EmailTemplates._generate_recommendations(stats)}
                </div>
                
                <div class="footer">
                    <p>Linux Patching Automation System - Quarterly Report</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return {"subject": subject, "body": body, "type": "html"}
    
    @staticmethod
    def _generate_group_performance(group_stats: Dict) -> str:
        """Generate group performance table"""
        if not group_stats:
            return "<p>No group statistics available.</p>"
        
        html = "<table><tr><th>Host Group</th><th>Total</th><th>Completed</th><th>Failed</th><th>Success Rate</th></tr>"
        
        for group, stats in group_stats.items():
            total = stats.get('total', 0)
            completed = stats.get('completed', 0)
            failed = stats.get('failed', 0)
            rate = (completed / total * 100) if total > 0 else 0
            
            html += f"""
            <tr>
                <td>{group}</td>
                <td>{total}</td>
                <td>{completed}</td>
                <td>{failed}</td>
                <td>{rate:.1f}%</td>
            </tr>
            """
        
        html += "</table>"
        return html
    
    @staticmethod
    def _generate_common_issues(issues: List[Dict]) -> str:
        """Generate common issues table"""
        if not issues:
            return "<p>No common issues identified.</p>"
        
        html = "<table><tr><th>Issue</th><th>Occurrences</th><th>Affected Servers</th></tr>"
        
        for issue in issues[:10]:
            html += f"""
            <tr>
                <td>{issue.get('description')}</td>
                <td>{issue.get('count', 0)}</td>
                <td>{', '.join(issue.get('servers', [])[:3])}...</td>
            </tr>
            """
        
        html += "</table>"
        return html
    
    @staticmethod
    def _generate_recommendations(stats: Dict) -> str:
        """Generate recommendations based on statistics"""
        recommendations = []
        
        success_rate = (stats.get('completed', 0) / stats.get('total', 1)) * 100 if stats.get('total', 0) > 0 else 0
        
        if success_rate < 90:
            recommendations.append("Success rate is below 90%. Review failed patches and common issues.")
        
        if stats.get('avg_duration_minutes', 0) > 120:
            recommendations.append("Average patch duration exceeds 2 hours. Consider optimizing patch windows.")
        
        if stats.get('failed', 0) > 10:
            recommendations.append("High number of failures detected. Schedule remediation sessions.")
        
        if not recommendations:
            recommendations.append("Patching performance is within acceptable parameters.")
        
        html = "<ul>"
        for rec in recommendations:
            html += f"<li>{rec}</li>"
        html += "</ul>"
        
        return html
    
    @staticmethod
    def critical_alert(server: str, issue: str, details: str) -> Dict[str, str]:
        """Critical alert email for immediate attention"""
        subject = f"[CRITICAL] Patching Issue - {server}"
        
        body = f"""
        <html>
        <head>{EmailTemplates.get_base_style()}</head>
        <body>
            <div class="container">
                <div class="header" style="background-color: #e74c3c;">
                    <h2>CRITICAL PATCHING ALERT</h2>
                    <p>Immediate Attention Required</p>
                </div>
                
                <div class="content">
                    <div class="alert alert-danger">
                        <strong>Server:</strong> {server}<br/>
                        <strong>Issue:</strong> {issue}<br/>
                        <strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </div>
                    
                    <h4>Details</h4>
                    <div style="background-color: #f8f8f8; padding: 15px; border-left: 4px solid #e74c3c;">
                        <pre>{details}</pre>
                    </div>
                    
                    <h4>Recommended Actions</h4>
                    <ol>
                        <li>Check server connectivity and status</li>
                        <li>Review patching logs for detailed error information</li>
                        <li>Execute rollback if necessary</li>
                        <li>Contact system owner if issue persists</li>
                    </ol>
                    
                    <div style="text-align: center; margin: 20px 0;">
                        <a href="#" class="button" style="background-color: #e74c3c;">View Server Status</a>
                        <a href="#" class="button">View Logs</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>This is a critical alert from Linux Patching Automation System</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return {"subject": subject, "body": body, "type": "html"}
    
    @staticmethod
    def rollback_notification(server: str, reason: str, status: str) -> Dict[str, str]:
        """Rollback notification email"""
        subject = f"[Rollback] {server} - {status}"
        
        status_class = "status-success" if status == "Success" else "status-failed"
        
        body = f"""
        <html>
        <head>{EmailTemplates.get_base_style()}</head>
        <body>
            <div class="container">
                <div class="header" style="background-color: #f39c12;">
                    <h2>Patching Rollback Notification</h2>
                </div>
                
                <div class="content">
                    <h3>Rollback Details</h3>
                    <table>
                        <tr><td><strong>Server:</strong></td><td>{server}</td></tr>
                        <tr><td><strong>Reason:</strong></td><td>{reason}</td></tr>
                        <tr><td><strong>Status:</strong></td><td class="{status_class}">{status}</td></tr>
                        <tr><td><strong>Time:</strong></td><td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
                    </table>
                    
                    <div class="alert alert-warning">
                        <strong>Important:</strong> This server has been rolled back to its previous state. 
                        Please investigate the issue before attempting to patch again.
                    </div>
                </div>
                
                <div class="footer">
                    <p>Linux Patching Automation System</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return {"subject": subject, "body": body, "type": "html"}