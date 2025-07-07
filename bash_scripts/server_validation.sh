#!/bin/bash

SERVER_NAME="$1"

# Function to check disk space
check_disk_space() {
    local threshold=85
    
    ssh "$SERVER_NAME" "df -h | awk 'NR>1 {print \$5 \" \" \$6}'" | while read usage mount; do
        usage_num=$(echo "$usage" | sed 's/%//')
        if [ "$usage_num" -gt "$threshold" ]; then
            echo "WARNING: $mount usage is $usage"
            return 1
        fi
    done
    
    return 0
}

# Function to check system load
check_system_load() {
    local load=$(ssh "$SERVER_NAME" "cat /proc/loadavg | awk '{print \$1}'")
    local cpu_count=$(ssh "$SERVER_NAME" "nproc")
    
    # Convert to integer comparison
    load_int=$(echo "$load * 100" | bc | cut -d'.' -f1)
    threshold_int=$(echo "$cpu_count * 200" | bc)  # 2x CPU count
    
    if [ "$load_int" -gt "$threshold_int" ]; then
        echo "WARNING: High load average: $load (CPUs: $cpu_count)"
        return 1
    fi
    
    return 0
}

# Function to check memory usage
check_memory() {
    local mem_usage=$(ssh "$SERVER_NAME" "free | awk 'NR==2{printf \"%.0f\", \$3*100/\$2}'")
    
    if [ "$mem_usage" -gt 90 ]; then
        echo "WARNING: High memory usage: ${mem_usage}%"
        return 1
    fi
    
    return 0
}

# Function to check for active users
check_active_users() {
    local active_users=$(ssh "$SERVER_NAME" "who | wc -l")
    
    if [ "$active_users" -gt 0 ]; then
        echo "WARNING: $active_users active user(s) on the system"
        ssh "$SERVER_NAME" "who"
        # Don't fail the check, just warn
    fi
    
    return 0
}

# Function to check critical services
check_critical_services() {
    local services=("sshd" "network" "NetworkManager")
    local failed=0
    
    for service in "${services[@]}"; do
        status=$(ssh "$SERVER_NAME" "systemctl is-active $service 2>/dev/null || echo 'unknown'")
        
        if [ "$status" != "active" ]; then
            echo "WARNING: Service $service is not active (status: $status)"
            failed=1
        fi
    done
    
    return $failed
}

# Main validation
echo "Running post-patch validation for $SERVER_NAME"

# Check if server is reachable
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "$SERVER_NAME" "echo 'connectivity_test'" >/dev/null 2>&1; then
    echo "ERROR: Cannot connect to $SERVER_NAME"
    exit 1
fi

OVERALL_STATUS=0

# Check disk space
echo "Checking disk space..."
if ! check_disk_space; then
    OVERALL_STATUS=1
fi

# Check system load
echo "Checking system load..."
if ! check_system_load; then
    OVERALL_STATUS=1
fi

# Check memory
echo "Checking memory usage..."
if ! check_memory; then
    OVERALL_STATUS=1
fi

# Check active users
echo "Checking for active users..."
check_active_users

# Check critical services
echo "Checking critical services..."
if ! check_critical_services; then
    OVERALL_STATUS=1
fi

# Check kernel version
echo "Checking kernel version..."
KERNEL_VERSION=$(ssh "$SERVER_NAME" "uname -r")
echo "Current kernel version: $KERNEL_VERSION"

# Check for package manager locks
echo "Checking for package manager locks..."
if ssh "$SERVER_NAME" "test -f /var/lib/dpkg/lock || test -f /var/lib/apt/lists/lock || test -f /var/cache/apt/archives/lock" 2>/dev/null; then
    echo "WARNING: Package manager locks detected"
elif ssh "$SERVER_NAME" "test -f /var/run/yum.pid || test -f /var/lib/rpm/.rpm.lock" 2>/dev/null; then
    echo "WARNING: Package manager locks detected"
else
    echo "No package manager locks detected"
fi

if [ $OVERALL_STATUS -eq 0 ]; then
    echo "All validation checks passed"
else
    echo "Some validation checks failed"
fi

exit $OVERALL_STATUS
