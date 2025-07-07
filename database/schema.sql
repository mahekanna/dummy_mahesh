-- Database schema for Linux patching automation system
-- PostgreSQL version

-- Servers table with custom quarter fields
CREATE TABLE servers (
    id SERIAL PRIMARY KEY,
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Patch history table
CREATE TABLE patch_history (
    id SERIAL PRIMARY KEY,
    server_name VARCHAR(255),
    patch_date DATE,
    patch_time TIME,
    quarter INTEGER,
    year INTEGER,
    status VARCHAR(50),
    patch_details TEXT,
    start_time TIMESTAMP,
    completion_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_name) REFERENCES servers(server_name) ON DELETE CASCADE
);

-- Notifications table
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    server_name VARCHAR(255),
    notification_type VARCHAR(50),
    recipient_email VARCHAR(255),
    subject VARCHAR(500),
    body_content TEXT,
    sent_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'Pending',
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_name) REFERENCES servers(server_name) ON DELETE CASCADE
);

-- Pre-check results table
CREATE TABLE precheck_results (
    id SERIAL PRIMARY KEY,
    server_name VARCHAR(255),
    check_date DATE,
    check_time TIME,
    quarter INTEGER,
    year INTEGER,
    connectivity_check BOOLEAN DEFAULT FALSE,
    disk_space_check BOOLEAN DEFAULT FALSE,
    dell_hardware_check BOOLEAN DEFAULT FALSE,
    overall_status VARCHAR(20),
    check_details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_name) REFERENCES servers(server_name) ON DELETE CASCADE
);

-- Users table (for web portal authentication)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Patch schedules table (for tracking scheduled jobs)
CREATE TABLE patch_schedules (
    id SERIAL PRIMARY KEY,
    server_name VARCHAR(255),
    scheduled_date DATE,
    scheduled_time TIME,
    quarter INTEGER,
    year INTEGER,
    job_id VARCHAR(100),
    job_type VARCHAR(20), -- 'at' or 'cron'
    status VARCHAR(20) DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_name) REFERENCES servers(server_name) ON DELETE CASCADE
);

-- Configuration table
CREATE TABLE configuration (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default configuration
INSERT INTO configuration (config_key, config_value, description) VALUES
('current_quarter', '3', 'Current quarter (1=Nov-Jan, 2=Feb-Apr, 3=May-Jul, 4=Aug-Oct)'),
('current_year', '2025', 'Current year for patching'),
('default_patch_day', 'Thursday', 'Default day of week for patching'),
('freeze_period_start', 'Thursday', 'Start of schedule freeze period'),
('freeze_period_end', 'Tuesday', 'End of schedule freeze period');

-- Comments
COMMENT ON TABLE servers IS 'Stores server information for patching management';
COMMENT ON COLUMN servers.q1_patch_date IS 'Q1 (Nov-Jan) patch date';
COMMENT ON COLUMN servers.q2_patch_date IS 'Q2 (Feb-Apr) patch date';
COMMENT ON COLUMN servers.q3_patch_date IS 'Q3 (May-Jul) patch date';
COMMENT ON COLUMN servers.q4_patch_date IS 'Q4 (Aug-Oct) patch date';
