"""
API Routes Module
"""

from .auth import auth_bp
from .servers import servers_bp
from .patching import patching_bp
from .approvals import approvals_bp
from .reports import reports_bp
from .system import system_bp
from .audit import audit_bp
from .health import health_bp

__all__ = [
    'auth_bp',
    'servers_bp', 
    'patching_bp',
    'approvals_bp',
    'reports_bp',
    'system_bp',
    'audit_bp',
    'health_bp'
]