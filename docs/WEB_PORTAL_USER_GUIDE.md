# 🌐 Web Portal User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Server Management](#server-management)
4. [Approval Workflow](#approval-workflow)
5. [Scheduling](#scheduling)
6. [Reports](#reports)
7. [Admin Panel](#admin-panel)
8. [User Account Management](#user-account-management)
9. [Keyboard Shortcuts](#keyboard-shortcuts)
10. [Tips and Best Practices](#tips-and-best-practices)

---

## Getting Started

### First Login

1. **Access the Portal**
   ```
   URL: http://your-server:5001
   Default Credentials:
   - Username: admin
   - Password: admin
   ```

2. **Change Default Password**
   - Click on your username (top right)
   - Select "Change Password"
   - Enter current and new password
   - Click "Update Password"

3. **Set Your Preferences**
   - Navigate to Settings → Preferences
   - Set timezone
   - Configure email notifications
   - Choose default view options

### User Interface Overview

```
┌─────────────────────────────────────────────────────────────┐
│  🏠 Dashboard  📊 Reports  📅 Schedule  👥 Servers  ⚙️ Admin │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   Stats     │  │   Charts    │  │   Alerts    │       │
│  │  Widget     │  │   Widget    │  │   Widget    │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                             │
│  ┌─────────────────────────────────────────────────┐       │
│  │          Main Content Area                       │       │
│  └─────────────────────────────────────────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Dashboard Overview

### Key Metrics Section

The dashboard displays real-time statistics:

- **Total Servers**: Total number of managed servers
- **Pending Approvals**: Servers awaiting approval (click to view)
- **Scheduled Patches**: Upcoming patches this quarter
- **Completed**: Successfully patched servers
- **Failed**: Servers with failed patches (requires attention)

### Interactive Charts

#### 1. Status Distribution (Donut Chart)
- **Click segments** to filter servers by status
- Hover for detailed counts
- Legend shows all status types

#### 2. Host Group Distribution (Bar Chart)
- **Click bars** to filter by host group
- Shows server count per group
- Useful for identifying large groups

#### 3. Patching Timeline (Line Chart)
- Shows trends over time
- Completed vs Scheduled patches
- Helps identify peak periods

### Quick Actions Panel

Located on the right side:
- 📥 **Import CSV**: Upload new server data
- 📊 **Generate Report**: Quick report generation
- 📅 **View Schedule**: Current quarter schedule
- ✉️ **Send Notifications**: Bulk email operations

### Alerts and Notifications

Top of dashboard shows:
- 🔴 **Critical**: Failed patches, system errors
- 🟡 **Warning**: Pending approvals, upcoming deadlines
- 🟢 **Info**: Completed patches, system updates

---

## Server Management

### Server List View

#### Navigation
1. Click **"Servers"** in main menu
2. Default view shows all servers

#### Table Features

**Column Headers (Sortable):**
- Server Name
- Host Group
- Status
- Primary Owner
- Patch Date/Time
- Actions

**Filtering Options:**
- **Status Filter**: All, Pending, Approved, Scheduled, Completed, Failed
- **Host Group**: Filter by specific groups
- **Search Box**: Real-time search by server name
- **Date Range**: Filter by patch dates

#### Bulk Operations

1. **Select Servers**:
   - Click checkbox next to server names
   - Use "Select All" checkbox in header
   - Shift+Click for range selection

2. **Available Actions**:
   - ✅ **Approve Selected**: Approve multiple servers
   - 📅 **Schedule Selected**: Bulk scheduling
   - 📧 **Email Owners**: Send notifications
   - 📥 **Export Selected**: Download as CSV

### Server Details Page

Click any server name to view details:

#### Information Sections

1. **Basic Information**
   - Server Name
   - Host Group
   - Operating System
   - Environment (Prod/Dev/Test)
   - Location

2. **Ownership**
   - Primary Owner (with email link)
   - Secondary Owner
   - Last Modified By
   - Modification Date

3. **Patching Schedule**
   - Quarterly tabs (Q1-Q4)
   - Approval Status per quarter
   - Scheduled Date/Time
   - Historical data

4. **Patch History**
   - Table showing past patches
   - Status, Date, Duration
   - View logs link

#### Actions Available

- **Edit Details**: Modify server information
- **Change Schedule**: Update patch date/time
- **Approve Patch**: Approve for current quarter
- **View History**: Detailed patch history
- **Download Logs**: Get patch execution logs

---

## Approval Workflow

### Viewing Pending Approvals

1. **From Dashboard**: Click "Pending Approvals" widget
2. **From Menu**: Servers → Filter → Status: Pending
3. **Quick Filter**: Use status badges at top

### Approval Methods

#### Individual Approval
1. Navigate to server details
2. Click "Approve" button
3. Select quarter (if not current)
4. Add optional comments
5. Confirm approval

#### Bulk Approval
1. From server list, select multiple servers
2. Click "Actions" → "Approve Selected"
3. Choose quarter
4. Review server list
5. Confirm bulk approval

#### Approval by Owner
1. Go to Admin → Bulk Operations
2. Select "Approve by Owner"
3. Enter owner email
4. Select quarter
5. Preview affected servers
6. Execute approval

### Approval Status Indicators

- 🔴 **Pending**: Awaiting approval
- 🟡 **Approved**: Approved but not scheduled
- 🟢 **Scheduled**: Approved and scheduled
- ✅ **Completed**: Successfully patched
- ❌ **Failed**: Patch failed

---

## Scheduling

### Manual Scheduling

#### Single Server Scheduling
1. Navigate to server details
2. Click "Schedule Patch"
3. Select date from calendar
4. Choose time slot (30-min intervals)
5. View conflicts/warnings
6. Confirm schedule

#### Bulk Scheduling
1. Select multiple servers
2. Click "Schedule Selected"
3. Choose scheduling method:
   - Same date/time for all
   - Distribute across dates
   - Intelligent scheduling

### Intelligent Scheduling

#### Access
- Dashboard → "Run Intelligent Scheduling"
- Admin → "Intelligent Scheduler"

#### Configuration
1. **Select Servers**: Choose servers to schedule
2. **Set Constraints**:
   - Max servers per hour: 5 (default)
   - Patching window: 8 PM - 12 AM
   - Blackout dates
3. **Priority Groups**:
   - Critical servers first/last
   - Group dependencies
4. **Review & Apply**: Preview schedule before applying

### Schedule Calendar View

#### Features
- **Month View**: Overview of all scheduled patches
- **Week View**: Detailed weekly schedule
- **Day View**: Hour-by-hour schedule
- **List View**: Tabular format

#### Color Coding
- 🟦 **Scheduled**: Normal scheduled patches
- 🟩 **Completed**: Successfully completed
- 🟥 **Failed**: Failed patches
- 🟨 **In Progress**: Currently patching

#### Drag and Drop
- Drag server blocks to reschedule
- Drop on different date/time
- Conflicts highlighted in red
- Confirm changes

---

## Reports

### Accessing Reports

1. Click **"Reports"** in main menu
2. Select report type from dropdown
3. Configure filters
4. Generate report

### Available Report Types

#### 1. Executive Summary
- High-level overview
- Success/failure rates
- Compliance metrics
- Graphical representations

#### 2. Detailed Server Report
- Complete server inventory
- All patching details
- Approval status
- Schedule information

#### 3. Compliance Report
- Servers meeting SLA
- Overdue patches
- Approval compliance
- Policy violations

#### 4. Patch History Report
- Historical patching data
- Success rates over time
- Average patch duration
- Failure analysis

#### 5. Custom Reports
- Build your own reports
- Select fields to include
- Apply custom filters
- Save report templates

### Report Features

#### Filters
- **Date Range**: Start and end dates
- **Quarter**: Q1-Q4
- **Host Group**: Specific groups
- **Status**: Filter by status
- **Owner**: By primary owner

#### Export Options
- 📄 **PDF**: Formatted report with charts
- 📊 **Excel**: Data with multiple sheets
- 📑 **CSV**: Raw data export
- 📧 **Email**: Send to recipients

#### Scheduling Reports
1. Generate desired report
2. Click "Schedule This Report"
3. Set frequency (Daily/Weekly/Monthly)
4. Choose recipients
5. Set delivery time

### Interactive Charts

Reports include interactive elements:
- Click charts to drill down
- Hover for detailed tooltips
- Export individual charts
- Fullscreen view option

---

## Admin Panel

### Accessing Admin Features

**Requirements**: Admin role required

1. Click ⚙️ **Admin** in main menu
2. Or navigate to `/admin`

### Admin Sections

#### 1. User Management

**View Users**
- List all users
- See roles and last login
- Active/inactive status

**Create User**
1. Click "Add User"
2. Fill in:
   - Username (unique)
   - Email address
   - Initial password
   - Role selection
3. Set permissions
4. Save user

**Edit User**
- Change role
- Reset password
- Update email
- Disable/enable account

**Roles & Permissions**
| Role | View | Approve | Schedule | Admin |
|------|------|---------|----------|--------|
| admin | ✓ | ✓ | ✓ | ✓ |
| user | ✓ | ✓ | ✓ | ✗ |
| approver | ✓ | ✓ | ✗ | ✗ |
| readonly | ✓ | ✗ | ✗ | ✗ |

#### 2. System Configuration

**Email Settings**
- SMTP server configuration
- Test email functionality
- Email templates
- Notification rules

**Patching Windows**
- Define allowed hours
- Set max servers/hour
- Configure blackout dates
- Quarter definitions

**LDAP Integration**
- Enable/disable LDAP
- Server configuration
- Group mappings
- Test connection

#### 3. Data Management

**Import/Export**
- Upload CSV files
- Download templates
- Export full database
- Backup operations

**Host Groups**
- View all groups
- Edit group settings
- Set group priorities
- Define dependencies

#### 4. System Monitoring

**Service Status**
- Web portal health
- Monitor service status
- Database connectivity
- Email system status

**System Logs**
- View recent logs
- Filter by severity
- Download log files
- Clear old logs

**Performance Metrics**
- Response times
- Database queries
- Memory usage
- Active sessions

### Advanced Admin Features

#### Bulk Operations
- Mass approve servers
- Bulk schedule updates
- Group email notifications
- Batch status updates

#### Automation Rules
- Create approval rules
- Auto-scheduling policies
- Notification triggers
- Custom workflows

#### Audit Trail
- User activities
- Configuration changes
- Approval history
- Access logs

---

## User Account Management

### Your Profile

Access via username dropdown (top right):

#### Update Profile
- Change display name
- Update email address
- Set timezone preference
- Configure notifications

#### Security Settings
- Change password
- View login history
- Active sessions
- Two-factor authentication (if enabled)

### Notification Preferences

Configure what emails you receive:
- ✉️ Approval requests
- ✉️ Schedule changes
- ✉️ Patch completions
- ✉️ Failure alerts
- ✉️ System announcements

### Personal Dashboard

Customize your dashboard:
1. Click "Customize Dashboard"
2. Drag widgets to rearrange
3. Add/remove widgets
4. Save layout

Available widgets:
- My Servers
- Pending Approvals
- Recent Activity
- Quick Links
- Calendar View

---

## Keyboard Shortcuts

### Global Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+K` | Quick search |
| `Ctrl+/` | Show shortcuts |
| `Esc` | Close dialog/modal |
| `F5` | Refresh data |

### Navigation

| Shortcut | Action |
|----------|--------|
| `Alt+D` | Go to Dashboard |
| `Alt+S` | Go to Servers |
| `Alt+R` | Go to Reports |
| `Alt+C` | Go to Calendar |
| `Alt+A` | Go to Admin |

### Server List

| Shortcut | Action |
|----------|--------|
| `Ctrl+A` | Select all |
| `Ctrl+Click` | Multi-select |
| `Shift+Click` | Range select |
| `Space` | Toggle selection |
| `Enter` | Open details |

### Actions

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` | Save changes |
| `Ctrl+E` | Export data |
| `Ctrl+P` | Print view |
| `Ctrl+Z` | Undo last action |

---

## Tips and Best Practices

### Efficient Workflow

1. **Use Filters Effectively**
   - Save common filters
   - Combine multiple criteria
   - Use search for quick finds

2. **Bulk Operations**
   - Group similar servers
   - Use shift+click for ranges
   - Preview before executing

3. **Keyboard Navigation**
   - Learn shortcuts
   - Tab through forms
   - Use arrow keys in lists

### Data Management

1. **Regular Exports**
   - Weekly backup exports
   - Document changes
   - Keep audit trail

2. **Naming Conventions**
   - Consistent server names
   - Clear group names
   - Descriptive schedules

### Communication

1. **Use Comments**
   - Add notes to approvals
   - Document special cases
   - Leave context for others

2. **Email Notifications**
   - Keep owners informed
   - Send reminders early
   - Include relevant details

### Security

1. **Access Control**
   - Regular password changes
   - Appropriate role assignment
   - Remove inactive users

2. **Audit Compliance**
   - Review audit logs
   - Track all changes
   - Document decisions

### Performance

1. **Optimize Views**
   - Use pagination
   - Limit date ranges
   - Filter unnecessary data

2. **Browser Tips**
   - Use modern browsers
   - Clear cache regularly
   - Enable JavaScript

---

## Troubleshooting Common Issues

### Can't Login
- Verify username/password
- Check CAPS LOCK
- Clear browser cookies
- Contact admin for reset

### Page Not Loading
- Check internet connection
- Verify portal URL
- Try different browser
- Check with IT for firewall

### Missing Data
- Refresh the page (F5)
- Check filters
- Verify permissions
- Log out and back in

### Export Not Working
- Check popup blocker
- Try different format
- Reduce data size
- Use Chrome/Firefox

### Schedule Conflicts
- Review existing schedules
- Check maintenance windows
- Verify dependencies
- Use intelligent scheduler

---

## Support Resources

### Getting Help
1. **Built-in Help**: Click ? icon
2. **User Guide**: This document
3. **Admin Contact**: admin@company.com
4. **IT Support**: ext. 1234

### Training Resources
- Video tutorials: `/help/videos`
- Practice environment: `test.server:5001`
- FAQ section: `/help/faq`

### Feature Requests
Submit via:
- Admin panel → Feedback
- Email: patching-team@company.com
- IT ticket system

---

**Remember**: The web portal is designed to make patching operations efficient and transparent. Take time to explore features and customize your workflow!