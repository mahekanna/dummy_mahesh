#!/usr/bin/env python3
"""
Simple REST API for Linux Patching Automation
Direct conversion of Flask web portal to API endpoints
"""

import os
import sys
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your existing modules
from utils.csv_handler import CSVHandler
from config.settings import Config
from config.users import UserManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
CORS(app)

# Initialize handlers
csv_handler = CSVHandler()
user_manager = UserManager()

# Simple JWT implementation
def create_token(email):
    return jwt.encode({'email': email}, app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return data['email']
    except:
        return None

# Authentication endpoint
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Use your existing authentication
    user_data = user_manager.authenticate_user(username, password)
    if user_data:
        token = create_token(user_data['email'])
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'email': user_data['email'],
                'name': user_data['name'],
                'role': user_data['role']
            }
        })
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

# Get servers endpoint
@app.route('/api/servers', methods=['GET'])
def get_servers():
    # Read servers from your CSV
    servers = csv_handler.read_servers(normalize_fields=True)
    
    # Convert to React-friendly format
    formatted_servers = []
    for server in servers:
        formatted_servers.append({
            'id': server.get('server_name', ''),
            'serverName': server.get('server_name', ''),
            'hostGroup': server.get('host_group', ''),
            'environment': server.get('environment', ''),
            'primaryOwner': server.get('primary_owner', ''),
            'patcherEmail': server.get('patcher_email', ''),
            'q1PatchDate': server.get('q1_patch_date', ''),
            'q1PatchTime': server.get('q1_patch_time', ''),
            'q2PatchDate': server.get('q2_patch_date', ''),
            'q2PatchTime': server.get('q2_patch_time', ''),
            'q3PatchDate': server.get('q3_patch_date', ''),
            'q3PatchTime': server.get('q3_patch_time', ''),
            'q4PatchDate': server.get('q4_patch_date', ''),
            'q4PatchTime': server.get('q4_patch_time', ''),
            'currentStatus': server.get('current_quarter_status', 'pending')
        })
    
    return jsonify({
        'success': True,
        'data': formatted_servers,
        'total': len(formatted_servers)
    })

# Update server endpoint
@app.route('/api/servers/<server_name>', methods=['PUT'])
def update_server(server_name):
    data = request.get_json()
    servers = csv_handler.read_servers(normalize_fields=True)
    
    # Find and update server
    for i, server in enumerate(servers):
        if server.get('server_name') == server_name:
            # Update fields
            if 'patcherEmail' in data:
                servers[i]['patcher_email'] = data['patcherEmail']
            if 'incidentTicket' in data:
                servers[i]['incident_ticket'] = data['incidentTicket']
            if 'q1PatchDate' in data:
                servers[i]['q1_patch_date'] = data['q1PatchDate']
            if 'q1PatchTime' in data:
                servers[i]['q1_patch_time'] = data['q1PatchTime']
            # Add more fields as needed
            
            # Save back to CSV
            csv_handler.write_servers(servers)
            return jsonify({'success': True, 'message': 'Server updated'})
    
    return jsonify({'success': False, 'message': 'Server not found'}), 404

# Get patching status
@app.route('/api/patching/status', methods=['GET'])
def get_patching_status():
    servers = csv_handler.read_servers(normalize_fields=True)
    quarter = Config.get_current_quarter()
    
    stats = {
        'currentQuarter': quarter,
        'totalServers': len(servers),
        'pending': 0,
        'approved': 0,
        'completed': 0,
        'failed': 0
    }
    
    for server in servers:
        status = server.get('current_quarter_status', 'pending')
        if status == 'pending':
            stats['pending'] += 1
        elif status in ['approved', 'scheduled']:
            stats['approved'] += 1
        elif status == 'completed':
            stats['completed'] += 1
        elif status == 'failed':
            stats['failed'] += 1
    
    return jsonify({
        'success': True,
        'data': stats
    })

# Approve servers
@app.route('/api/approvals/approve', methods=['POST'])
def approve_servers():
    data = request.get_json()
    server_names = data.get('servers', [])
    quarter = Config.get_current_quarter()
    
    servers = csv_handler.read_servers(normalize_fields=True)
    approved_count = 0
    
    for server in servers:
        if server.get('server_name') in server_names:
            server[f'q{quarter}_approval_status'] = 'approved'
            server['current_quarter_status'] = 'approved'
            approved_count += 1
    
    csv_handler.write_servers(servers)
    
    return jsonify({
        'success': True,
        'message': f'Approved {approved_count} servers'
    })

# Health check
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    print("Starting Simple API on port 8001...")
    app.run(host='0.0.0.0', port=8001, debug=False)