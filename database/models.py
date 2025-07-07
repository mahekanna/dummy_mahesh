# database/models.py
import sqlite3
from datetime import datetime
from config.settings import Config

try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

class DatabaseManager:
    def __init__(self, use_sqlite=None):
        # Auto-detect database type from config if not specified
        if use_sqlite is None:
            self.use_sqlite = getattr(Config, 'USE_SQLITE', True)
        else:
            self.use_sqlite = use_sqlite
        self.connection = None
        
    def connect(self):
        if self.use_sqlite:
            # Use absolute path for SQLite database
            import os
            db_path = os.path.join(Config.PROJECT_ROOT, 'patching.db')
            self.connection = sqlite3.connect(db_path)
        else:
            if not PSYCOPG2_AVAILABLE:
                raise ImportError("psycopg2 is not installed. Install it with: pip install psycopg2-binary")
            self.connection = psycopg2.connect(
                host=Config.DB_HOST,
                port=int(Config.DB_PORT) if hasattr(Config, 'DB_PORT') else 5432,
                database=Config.DB_NAME,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD
            )
        return self.connection
    
    def create_tables(self):
        cursor = self.connection.cursor()
        
        # Define SQL syntax based on database type
        if self.use_sqlite:
            primary_key_sql = "INTEGER PRIMARY KEY AUTOINCREMENT"
            timestamp_default = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        else:
            primary_key_sql = "SERIAL PRIMARY KEY"
            timestamp_default = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        
        # Servers table with modified quarter fields
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS servers (
                id {primary_key_sql},
                server_name VARCHAR(255) UNIQUE NOT NULL,
                server_timezone VARCHAR(50) NOT NULL,
                q1_patch_date DATE,
                q1_patch_time TIME,
                q2_patch_date DATE,
                q2_patch_time TIME,
                q3_patch_date DATE,
                q3_patch_time TIME,
                q4_patch_date DATE,
                q4_patch_time TIME,
                current_quarter_status VARCHAR(50) DEFAULT 'Pending',
                primary_owner VARCHAR(255),
                secondary_owner VARCHAR(255),
                host_group VARCHAR(100),
                engr_domain VARCHAR(100),
                location VARCHAR(100),
                created_at {timestamp_default},
                updated_at {timestamp_default}
            )
        ''')
        
        # Patch History table
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS patch_history (
                id {primary_key_sql},
                server_name VARCHAR(255),
                patch_date DATE,
                patch_time TIME,
                quarter INTEGER,
                year INTEGER,
                status VARCHAR(50),
                patch_details TEXT,
                start_time TIMESTAMP,
                completion_time TIMESTAMP,
                created_at {timestamp_default},
                FOREIGN KEY (server_name) REFERENCES servers(server_name)
            )
        ''')
        
        # Notifications table
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS notifications (
                id {primary_key_sql},
                server_name VARCHAR(255),
                notification_type VARCHAR(50),
                recipient_email VARCHAR(255),
                sent_at TIMESTAMP,
                status VARCHAR(20) DEFAULT 'Pending',
                FOREIGN KEY (server_name) REFERENCES servers(server_name)
            )
        ''')
        
        # Pre-check results table
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS precheck_results (
                id {primary_key_sql},
                server_name VARCHAR(255),
                check_date DATE,
                check_time TIME,
                quarter INTEGER,
                year INTEGER,
                connectivity_check BOOLEAN DEFAULT FALSE,
                disk_space_check BOOLEAN DEFAULT FALSE,
                dell_hardware_check BOOLEAN DEFAULT FALSE,
                overall_status VARCHAR(20),
                check_details TEXT,
                created_at {timestamp_default},
                FOREIGN KEY (server_name) REFERENCES servers(server_name)
            )
        ''')
        
        # Configuration table
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS configuration (
                id {primary_key_sql},
                config_key VARCHAR(100) UNIQUE NOT NULL,
                config_value TEXT,
                description TEXT,
                updated_at {timestamp_default}
            )
        ''')
        
        # Insert default configuration with database-specific syntax
        if self.use_sqlite:
            # SQLite syntax
            cursor.execute('''
                INSERT OR IGNORE INTO configuration (config_key, config_value, description)
                VALUES 
                    ('current_quarter', '3', 'Current quarter (1=Nov-Jan, 2=Feb-Apr, 3=May-Jul, 4=Aug-Oct)'),
                    ('current_year', '2025', 'Current year for patching'),
                    ('default_patch_day', 'Thursday', 'Default day of week for patching'),
                    ('freeze_period_start', 'Thursday', 'Start day of schedule freeze period'),
                    ('freeze_period_end', 'Tuesday', 'End day of schedule freeze period')
            ''')
        else:
            # PostgreSQL syntax
            cursor.execute('''
                INSERT INTO configuration (config_key, config_value, description)
                VALUES 
                    ('current_quarter', '3', 'Current quarter (1=Nov-Jan, 2=Feb-Apr, 3=May-Jul, 4=Aug-Oct)'),
                    ('current_year', '2025', 'Current year for patching'),
                    ('default_patch_day', 'Thursday', 'Default day of week for patching'),
                    ('freeze_period_start', 'Thursday', 'Start day of schedule freeze period'),
                    ('freeze_period_end', 'Tuesday', 'End day of schedule freeze period')
                ON CONFLICT (config_key) DO NOTHING
            ''')
        
        self.connection.commit()
    
    def get_servers_for_quarter(self, quarter, year=None):
        """Get all servers scheduled for a specific quarter"""
        if not year:
            year = datetime.now().year
            
        cursor = self.connection.cursor()
        
        if self.use_sqlite:
            cursor.execute(f'''
                SELECT * FROM servers
                WHERE q{quarter}_patch_date IS NOT NULL
                ORDER BY q{quarter}_patch_date, q{quarter}_patch_time
            ''')
        else:
            cursor.execute(f'''
                SELECT * FROM servers
                WHERE q{quarter}_patch_date IS NOT NULL
                ORDER BY q{quarter}_patch_date, q{quarter}_patch_time
            ''')
        
        columns = [desc[0] for desc in cursor.description]
        servers = []
        
        for row in cursor.fetchall():
            servers.append(dict(zip(columns, row)))
        
        return servers
    
    def update_server_schedule(self, server_name, quarter, patch_date, patch_time):
        """Update server patching schedule for a specific quarter"""
        cursor = self.connection.cursor()
        
        cursor.execute(f'''
            UPDATE servers
            SET q{quarter}_patch_date = ?, q{quarter}_patch_time = ?, current_quarter_status = 'Scheduled'
            WHERE server_name = ?
        ''', (patch_date, patch_time, server_name))
        
        self.connection.commit()
        return cursor.rowcount > 0
    
    def record_patch_history(self, server_name, patch_date, patch_time, quarter, year, status, details=None):
        """Record patch history for a server"""
        cursor = self.connection.cursor()
        
        cursor.execute('''
            INSERT INTO patch_history (
                server_name, patch_date, patch_time, quarter, year, 
                status, patch_details, start_time
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (server_name, patch_date, patch_time, quarter, year, status, details))
        
        self.connection.commit()
        return cursor.lastrowid
    
    def update_patch_completion(self, history_id, status, details=None):
        """Update patch completion status"""
        cursor = self.connection.cursor()
        
        cursor.execute('''
            UPDATE patch_history
            SET status = ?, patch_details = ?, completion_time = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, details, history_id))
        
        self.connection.commit()
        return cursor.rowcount > 0
    
    def upsert_server(self, server_data):
        """Insert or update server data"""
        try:
            cursor = self.connection.cursor()
            
            # Extract server info
            server_name = server_data.get('Server Name')
            if not server_name:
                return False
            
            # For SQLite, use INSERT OR REPLACE
            if self.use_sqlite:
                cursor.execute('''
                    INSERT OR REPLACE INTO servers (
                        server_name, server_timezone, primary_owner, secondary_owner,
                        host_group, engr_domain, location, incident_ticket, patcher_email,
                        q1_patch_date, q1_patch_time, q1_approval_status,
                        q2_patch_date, q2_patch_time, q2_approval_status,
                        q3_patch_date, q3_patch_time, q3_approval_status,
                        q4_patch_date, q4_patch_time, q4_approval_status,
                        current_quarter_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    server_name,
                    server_data.get('Server Timezone', ''),
                    server_data.get('primary_owner', ''),
                    server_data.get('secondary_owner', ''),
                    server_data.get('host_group', ''),
                    server_data.get('engr_domain', ''),
                    server_data.get('location', ''),
                    server_data.get('incident_ticket', ''),
                    server_data.get('patcher_email', ''),
                    server_data.get('Q1 Patch Date', ''),
                    server_data.get('Q1 Patch Time', ''),
                    server_data.get('Q1 Approval Status', 'Pending'),
                    server_data.get('Q2 Patch Date', ''),
                    server_data.get('Q2 Patch Time', ''),
                    server_data.get('Q2 Approval Status', 'Pending'),
                    server_data.get('Q3 Patch Date', ''),
                    server_data.get('Q3 Patch Time', ''),
                    server_data.get('Q3 Approval Status', 'Pending'),
                    server_data.get('Q4 Patch Date', ''),
                    server_data.get('Q4 Patch Time', ''),
                    server_data.get('Q4 Approval Status', 'Pending'),
                    server_data.get('Current Quarter Patching Status', 'Pending')
                ))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            print(f"Error upserting server {server_name}: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
