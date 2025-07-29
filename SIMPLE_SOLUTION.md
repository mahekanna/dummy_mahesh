# Simple React + API Solution

## The Problem
You have:
1. A working Flask web portal (`web_portal/app.py`)
2. A React frontend that expects REST APIs
3. Existing Python scripts and CSV data

## The Simple Solution
I created a minimal API (`simple_api.py`) that:
- Uses your existing authentication system
- Reads from your existing CSV files
- Provides simple JSON endpoints for React
- No complex dependencies or frameworks

## How to Use

### 1. Start the API
```bash
./start_simple.sh
```

This will:
- Install only Flask, Flask-CORS, and PyJWT
- Start the API on port 8001
- No virtual environments or complex setup

### 2. Available Endpoints

#### Login
```bash
POST /api/login
Body: {"username": "admin@company.com", "password": "admin123"}
Returns: {"success": true, "token": "...", "user": {...}}
```

#### Get Servers
```bash
GET /api/servers
Returns: List of all servers from your CSV
```

#### Update Server
```bash
PUT /api/servers/servername
Body: {"patcherEmail": "new@email.com", "incidentTicket": "INC123"}
```

#### Get Patching Status
```bash
GET /api/patching/status
Returns: Current quarter statistics
```

#### Approve Servers
```bash
POST /api/approvals/approve
Body: {"servers": ["server1", "server2"]}
```

### 3. Update React Frontend

In your React `api.ts`, change the base URL:
```javascript
this.baseURL = 'http://localhost:8001/api';
```

Then update the endpoints:
- `/auth/login` → `/api/login`
- `/servers` → `/api/servers`
- etc.

## What This Does

1. **Reads your existing CSV files** - No database changes
2. **Uses your existing authentication** - UserManager from config/users.py
3. **Provides simple JSON APIs** - What React expects
4. **Minimal dependencies** - Just Flask, CORS, and JWT

## Next Steps

If you need more endpoints, just add them to `simple_api.py`:

```python
@app.route('/api/your-endpoint', methods=['GET'])
def your_endpoint():
    # Your logic here
    return jsonify({'success': True, 'data': result})
```

## Why This Works

- **No complexity** - Just a simple Flask API
- **Uses existing code** - Your CSV handlers and authentication
- **React-compatible** - Returns JSON in the format React expects
- **Easy to extend** - Add endpoints as needed

This is a straightforward solution that bridges your existing Flask/Python system with the React frontend without overengineering.