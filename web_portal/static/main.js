// main.js - JavaScript for Linux Patching Portal

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Server timezone information
    const serverDetailPage = document.getElementById('server-detail-page');
    if (serverDetailPage) {
        const serverName = serverDetailPage.dataset.serverName;
        fetch(`/api/server_timezone/${serverName}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('timezone-abbr').textContent = data.abbreviation;
                document.getElementById('timezone-info').innerHTML = 
                    `<strong>Current time in ${data.abbreviation}:</strong> ${data.current_time} (UTC${data.offset})`;
            })
            .catch(error => console.error('Error fetching timezone info:', error));
    }
    
    // Quarter selector logic
    const quarterSelector = document.getElementById('quarter');
    if (quarterSelector) {
        quarterSelector.addEventListener('change', function() {
            const quarter = this.value;
            fetch(`/api/available_dates/${quarter}`)
                .then(response => response.json())
                .then(dates => {
                    const dateInput = document.getElementById('patch_date');
                    dateInput.setAttribute('list', 'available-dates');
                    
                    // Create datalist for available dates
                    let datalist = document.getElementById('available-dates');
                    if (!datalist) {
                        datalist = document.createElement('datalist');
                        datalist.id = 'available-dates';
                        dateInput.parentNode.appendChild(datalist);
                    }
                    
                    datalist.innerHTML = '';
                    dates.forEach(date => {
                        const option = document.createElement('option');
                        option.value = date;
                        datalist.appendChild(option);
                    });
                    
                    // Update quarter-specific fields
                    updateQuarterFields(quarter);
                });
        });
    }
    
    // Update fields based on selected quarter
    function updateQuarterFields(quarter) {
        const serverDetailPage = document.getElementById('server-detail-page');
        if (!serverDetailPage) return;
        
        const serverName = serverDetailPage.dataset.serverName;
        fetch(`/api/server_quarter_data/${serverName}/${quarter}`)
            .then(response => response.json())
            .then(data => {
                if (data.patch_date) {
                    document.getElementById('patch_date').value = data.patch_date;
                }
                if (data.patch_time) {
                    document.getElementById('patch_time').value = data.patch_time;
                }
            })
            .catch(error => console.error('Error fetching quarter data:', error));
    }
    
    // Form validation
    const scheduleForm = document.getElementById('schedule-form');
    if (scheduleForm) {
        scheduleForm.addEventListener('submit', function(event) {
            const dateInput = document.getElementById('patch_date');
            const timeInput = document.getElementById('patch_time');
            
            if (!dateInput.value || !timeInput.value) {
                event.preventDefault();
                alert('Please select both date and time for patching');
                return false;
            }
            
            // Validate date format (YYYY-MM-DD)
            const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
            if (!dateRegex.test(dateInput.value)) {
                event.preventDefault();
                alert('Please enter a valid date in YYYY-MM-DD format');
                return false;
            }
            
            // Validate time format (HH:MM)
            const timeRegex = /^\d{2}:\d{2}$/;
            if (!timeRegex.test(timeInput.value)) {
                event.preventDefault();
                alert('Please enter a valid time in HH:MM format');
                return false;
            }
            
            return true;
        });
    }
});

// Helper function to format dates
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    
    return date.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Helper function to format times
function formatTime(timeString) {
    if (!timeString) return '';
    
    // Parse HH:MM format
    const [hours, minutes] = timeString.split(':');
    
    // Create a date object with the time
    const date = new Date();
    date.setHours(parseInt(hours, 10));
    date.setMinutes(parseInt(minutes, 10));
    
    return date.toLocaleTimeString(undefined, {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    });
}
