// frontend/js/app.js

// Global variables
let reportModal;
let analyticsModal;
let updateInterval;
let charts = {};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize modals
    reportModal = new bootstrap.Modal(document.getElementById('reportModal'));
    analyticsModal = new bootstrap.Modal(document.getElementById('analyticsModal'));
    
    // Set up event listeners
    document.getElementById('severity').addEventListener('input', (e) => {
        document.getElementById('severity-display').textContent = e.target.value + '/10';
    });
    
    document.getElementById('severity-filter').addEventListener('input', (e) => {
        document.getElementById('severity-value').textContent = e.target.value;
    });
    
    // Start auto-refresh
    startAutoRefresh();
});

// Show report modal
function showReportModal() {
    // Reset form
    document.getElementById('report-form').reset();
    document.getElementById('selected-lat').textContent = '28.6139';
    document.getElementById('selected-lng').textContent = '77.2090';
    document.getElementById('location-input').value = '';
    
    if (emergencyMap.tempMarker) {
        emergencyMap.map.removeLayer(emergencyMap.tempMarker);
    }
    
    reportModal.show();
}

// Submit report
async function submitReport() {
    const form = document.getElementById('report-form');
    
    // Validate form
    if (!document.getElementById('emergency-type').value) {
        showToast('Please select emergency type', 'error');
        return;
    }
    
    const data = {
        type: document.getElementById('emergency-type').value,
        location: [
            parseFloat(document.getElementById('selected-lng').textContent),
            parseFloat(document.getElementById('selected-lat').textContent)
        ],
        location_type: document.getElementById('location-type').value,
        description: document.getElementById('description').value,
        severity: parseInt(document.getElementById('severity').value),
        caller_type: document.getElementById('caller-type').value,
        address: document.getElementById('location-input').value || 'Unknown location'
    };
    
    try {
        showLoading('Submitting report...');
        
        const response = await fetch('http://localhost:5000/api/incidents/report', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        hideLoading();
        
        showToast('Emergency reported successfully!', 'success');
        reportModal.hide();
        
        // Refresh data
        emergencyMap.loadData();
        
    } catch (error) {
        console.error('Error submitting report:', error);
        showToast('Failed to submit report. Using mock response.', 'warning');
        hideLoading();
        
        // Mock success
        showToast('Mock: Emergency reported (ID: ' + Math.floor(Math.random() * 1000) + ')', 'success');
        reportModal.hide();
    }
}

// Get current location
function getCurrentLocation() {
    if (navigator.geolocation) {
        showLoading('Getting your location...');
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const { latitude, longitude } = position.coords;
                
                document.getElementById('selected-lat').textContent = latitude.toFixed(6);
                document.getElementById('selected-lng').textContent = longitude.toFixed(6);
                document.getElementById('location-input').value = `Current Location`;
                
                emergencyMap.addTempMarker(latitude, longitude);
                emergencyMap.map.setView([latitude, longitude], 15);
                
                hideLoading();
                showToast('Location detected', 'success');
            },
            (error) => {
                hideLoading();
                showToast('Failed to get location: ' + error.message, 'error');
            }
        );
    } else {
        showToast('Geolocation not supported', 'error');
    }
}

// Update dashboard with data
function updateDashboard(incidents, resources, crowds) {
    // Update counts
    const incidentCount = incidents.features ? incidents.features.length : 0;
    const resourceCount = resources.features ? resources.features.length : 0;
    
    document.getElementById('active-incidents').textContent = incidentCount;
    document.getElementById('available-resources').textContent = resourceCount;
    
    // Update incident list
    updateIncidentList(incidents);
    
    // Update resource table
    updateResourceTable(resources);

    // 👥 Update crowd detections panel if present
    if (crowds) updateCrowdPanel(crowds);
}

// 👥 Update crowd detection sidebar panel
function updateCrowdPanel(crowds) {
    const container = document.getElementById('crowd-list-container');
    if (!container) return;

    const features = crowds.features || [];
    if (features.length === 0) {
        container.innerHTML = '<p class="text-muted text-center small">No crowd detections</p>';
        return;
    }

    // Sort: critical first, then anomalous, then by crowd size
    const sorted = [...features].sort((a, b) => {
        const order = { critical: 0, high: 1, moderate: 2, low: 3, safe: 4 };
        const ao = order[a.properties.risk_level] ?? 5;
        const bo = order[b.properties.risk_level] ?? 5;
        if (ao !== bo) return ao - bo;
        if (b.properties.is_anomalous !== a.properties.is_anomalous)
            return b.properties.is_anomalous ? 1 : -1;
        return b.properties.estimated_crowd_size - a.properties.estimated_crowd_size;
    });

    const riskColors = {
        critical: '#8B0000', high: '#FF4500',
        moderate: '#FFA500', safe: '#32CD32', low: '#32CD32'
    };

    let html = '';
    sorted.forEach(f => {
        const p = f.properties;
        const coords = f.geometry.coordinates;  // [lng, lat]
        const color = riskColors[p.risk_level] || '#FFA500';

        html += `
            <div class="incident-item" style="border-left-color:${color};cursor:pointer;"
                 onclick="zoomToLocation(${coords[1]}, ${coords[0]})">
                <div class="d-flex justify-content-between align-items-center">
                    <strong style="font-size:13px;">
                        👥 ${p.place_type.replace(/_/g,' ').toUpperCase()}
                        ${p.is_anomalous ? '<span title="Anomalous crowd">⚠️</span>' : ''}
                    </strong>
                    <span class="badge" style="background:${color};color:white;">
                        ${p.risk_level.toUpperCase()}
                    </span>
                </div>
                <small class="d-block">${p.address}</small>
                <small class="d-block text-muted">
                    ~${p.estimated_crowd_size.toLocaleString()} people &bull;
                    ${p.crowd_density} &bull; via ${p.detection_source}
                </small>
            </div>
        `;
    });

    container.innerHTML = html;

    // Update crowd count badge if element exists
    const badge = document.getElementById('crowd-count');
    if (badge) {
        const critical = features.filter(f => f.properties.risk_level === 'critical').length;
        badge.textContent = features.length;
        badge.className = `badge ${critical > 0 ? 'bg-danger' : 'bg-warning'}`;
    }
}

// Update incident list
function updateIncidentList(incidents) {
    const container = document.getElementById('incident-list-container');
    
    if (!incidents.features || incidents.features.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">No active incidents</p>';
        return;
    }
    
    let html = '';
    incidents.features.forEach(feature => {
        const props = feature.properties;
        const coords = feature.geometry.coordinates;
        
        html += `
            <div class="incident-item ${props.type}" onclick="zoomToIncident(${coords[1]}, ${coords[0]})">
                <div class="d-flex justify-content-between">
                    <strong><i class="fas fa-exclamation-circle"></i> ${props.type.toUpperCase()}</strong>
                    <span class="badge bg-${props.severity > 3 ? 'danger' : 'warning'}">${props.severity}/5</span>
                </div>
                <small>${props.address || 'Unknown location'}</small>
                <small class="d-block text-muted">${new Date(props.reported_at).toLocaleTimeString()}</small>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Update resource table
function updateResourceTable(resources) {
    const tbody = document.getElementById('resource-table-body');
    
    if (!resources.features || resources.features.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No resources available</td></tr>';
        return;
    }
    
    let html = '';
    resources.features.forEach(feature => {
        const props = feature.properties;
        const coords = feature.geometry.coordinates;
        
        html += `
            <tr>
                <td>${props.id}</td>
                <td>
                    <i class="fas ${getResourceIcon(props.type)}"></i>
                    ${props.type.replace('_', ' ').toUpperCase()}
                </td>
                <td><span class="badge bg-success">${props.status}</span></td>
                <td>${coords[1].toFixed(4)}, ${coords[0].toFixed(4)}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="selectResource(${props.id})">
                        <i class="fas fa-location-dot"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// Get resource icon
function getResourceIcon(type) {
    const icons = {
        'ambulance': 'fa-ambulance',
        'fire_truck': 'fa-truck',
        'police': 'fa-car',
        'default': 'fa-truck'
    };
    return icons[type] || icons.default;
}

// Zoom to incident
function zoomToIncident(lat, lng) {
    emergencyMap.map.setView([lat, lng], 15);
}

// Select resource
function selectResource(id) {
    showToast(`Resource ${id} selected`, 'info');
}

// Dispatch to incident
function dispatchToIncident(incidentId) {
    showToast(`Dispatching resources to incident ${incidentId}`, 'info');
}

// Apply filters
function applyFilters() {
    const type = document.getElementById('incident-type-filter').value;
    const severity = document.getElementById('severity-filter').value;
    
    showToast(`Filters applied: Type=${type}, Severity>=${severity}`, 'success');
    // In real app, would filter incidents on map
}

// Toggle heatmap
function toggleHeatmap() {
    emergencyMap.toggleHeatmap();
}

// Show analytics
async function showAnalytics() {
    analyticsModal.show();
    
    // Create charts
    setTimeout(() => {
        createCharts();
    }, 500);
}

// Create analytics charts
function createCharts() {
    // Incident type chart
    const incidentCtx = document.getElementById('incident-chart').getContext('2d');
    new Chart(incidentCtx, {
        type: 'doughnut',
        data: {
            labels: ['Fire', 'Medical', 'Accident', 'Flood', 'Other'],
            datasets: [{
                data: [30, 25, 20, 15, 10],
                backgroundColor: ['#ff4444', '#ffbb33', '#ff8800', '#33b5e5', '#aa66cc']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Incidents by Type'
                }
            }
        }
    });
    
    // Severity distribution chart
    const severityCtx = document.getElementById('severity-chart').getContext('2d');
    new Chart(severityCtx, {
        type: 'bar',
        data: {
            labels: ['1', '2', '3', '4', '5'],
            datasets: [{
                label: 'Number of Incidents',
                data: [5, 10, 25, 30, 20],
                backgroundColor: '#ff4444'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Severity Distribution'
                }
            }
        }
    });
    
    // Timeline chart
    const timelineCtx = document.getElementById('timeline-chart').getContext('2d');
    new Chart(timelineCtx, {
        type: 'line',
        data: {
            labels: ['6am', '9am', '12pm', '3pm', '6pm', '9pm'],
            datasets: [{
                label: 'Incident Count',
                data: [12, 19, 25, 22, 30, 15],
                borderColor: '#ff4444',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Incident Timeline'
                }
            }
        }
    });
}

// Refresh data
function refreshData() {
    emergencyMap.loadData();
}

// Center map
function centerMap() {
    emergencyMap.centerMap();
}

// Update last updated time
function updateLastUpdated() {
    document.getElementById('last-updated').textContent = 
        'Updated: ' + new Date().toLocaleTimeString();
}

// Start auto-refresh
function startAutoRefresh() {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
    updateInterval = setInterval(() => {
        emergencyMap.loadData();
    }, 30000);
}

// Show loading overlay
function showLoading(message = 'Loading...') {
    let overlay = document.getElementById('loadingOverlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-spinner"></div>
            <div class="loading-message">${message}</div>
        `;
        document.body.appendChild(overlay);
    } else {
        overlay.querySelector('.loading-message').textContent = message;
        overlay.style.display = 'flex';
    }
}

// Hide loading overlay
function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast, { delay: 5000 });
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// Create toast container
function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

// Add these functions to app.js

// Zoom to specific location
window.zoomToLocation = function(lat, lng) {
    if (emergencyMap) {
        emergencyMap.map.setView([lat, lng], 16);
        emergencyMap.addTempMarker(lat, lng);
    }
};

// Get directions to location
window.getDirections = function(lat, lng) {
    window.open(`https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`, '_blank');
};

// Dispatch specific resource
window.dispatchResource = function(resourceId) {
    if (!hasPermission('dispatch_resources')) {
        showToast('You do not have permission to dispatch resources', 'error');
        return;
    }
    
    // Find the resource
    const resource = emergencyMap.resourcesLayer.eachLayer(layer => {
        // Implementation depends on how you store resource data
    });
    
    showToast(`Dispatching resource ${resourceId}...`, 'info');
};

// Filter incidents by severity
function filterBySeverity(minSeverity) {
    emergencyMap.incidentsLayer.eachLayer(layer => {
        // You'll need to store severity in layer options
        // This is a placeholder implementation
    });
}

// Show only critical incidents
function showCriticalOnly() {
    filterBySeverity(4);
}

// Make functions globally available
window.filterBySeverity = filterBySeverity;
window.showCriticalOnly = showCriticalOnly;
// Make functions globally available
window.showReportModal = showReportModal;
window.submitReport = submitReport;
window.getCurrentLocation = getCurrentLocation;
window.applyFilters = applyFilters;
window.toggleHeatmap = toggleHeatmap;
window.showAnalytics = showAnalytics;
window.refreshData = refreshData;
window.centerMap = centerMap;
window.zoomToIncident = zoomToIncident;
window.selectResource = selectResource;
window.dispatchToIncident = dispatchToIncident;