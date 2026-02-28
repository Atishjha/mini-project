// frontend/js/map.js - Enhanced version with better emergency visualization
// and integrated location selection for reporting

class EmergencyMap {
    constructor() {
        this.map = null;
        this.incidentsLayer = null;
        this.resourcesLayer = null;
        this.routesLayer = null;
        this.heatmapLayer = null;
        this.crowdLayer = null;          // 👥 Crowd detection layer
        this.selectedLocation = null;
        this.tempMarker = null;
        this.activeIncidents = [];
        this.activeCrowds = [];          // 👥 Crowd detection data cache
        this.baseUrl = 'http://localhost:5000';
        this.isReportModalOpen = false;
        
        this.initialize();
        this.startLiveUpdates();
    }
    
    initialize() {
        // Initialize map centered on Delhi
        this.map = L.map('map').setView([28.6139, 77.2090], 12);
        
        // Add multiple base layers for better context
        const baseLayers = {
            "Street Map": L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors',
                maxZoom: 19
            }),
            "Satellite": L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                attribution: 'Tiles © Esri',
                maxZoom: 19
            }),
            "Dark Mode": L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                attribution: '© CartoDB',
                maxZoom: 19
            })
        };
        
        // Add default base layer
        baseLayers["Street Map"].addTo(this.map);
        
        // Create layer groups
        this.incidentsLayer = L.layerGroup().addTo(this.map);
        this.resourcesLayer = L.layerGroup().addTo(this.map);
        this.routesLayer = L.layerGroup().addTo(this.map);
        this.crowdLayer = L.layerGroup().addTo(this.map);  // 👥 Crowd layer
        
        // Add layer control
        L.control.layers(baseLayers, {
            'Active Incidents': this.incidentsLayer,
            'Emergency Resources': this.resourcesLayer,
            'Dispatch Routes': this.routesLayer,
            '👥 Crowd Detections': this.crowdLayer      // 👥 Toggle crowd layer
        }).addTo(this.map);
        
        // Add controls
        this.addControls();
        this.addLegend();
        this.addEmergencyInfo();
        
        // Add click handler for location selection
        this.map.on('click', (e) => {
            this.handleMapClick(e);
        });
        
        // Load initial data
        this.loadData();
        
        // Set up modal state tracking
        this.setupModalTracking();
    }
    
    setupModalTracking() {
        // Track when report modal is open/closed
        const modalEl = document.getElementById('reportModal');
        if (modalEl) {
            modalEl.addEventListener('show.bs.modal', () => {
                this.isReportModalOpen = true;
                console.log('Report modal opened');
            });
            
            modalEl.addEventListener('hide.bs.modal', () => {
                this.isReportModalOpen = false;
                console.log('Report modal closed');
            });
        }
    }
    
    addEmergencyInfo() {
        // Add emergency info panel
        const infoControl = L.control({ position: 'topright' });
        infoControl.onAdd = () => {
            const div = L.DomUtil.create('div', 'emergency-info-panel');
            div.innerHTML = `
                <div class="card bg-dark text-white">
                    <div class="card-header bg-danger">
                        <h6 class="mb-0"><i class="fas fa-exclamation-triangle"></i> LIVE EMERGENCIES</h6>
                    </div>
                    <div class="card-body p-2" id="live-emergency-list">
                        <p class="text-muted small mb-0">Loading emergencies...</p>
                    </div>
                </div>
            `;
            return div;
        };
        infoControl.addTo(this.map);
    }
    
    addControls() {
        // Add zoom control
        L.control.zoom({
            position: 'topright'
        }).addTo(this.map);
        
        // Add scale control
        L.control.scale({
            imperial: false,
            position: 'bottomleft'
        }).addTo(this.map);
        
        // Add locate control
        L.control.locate({
            position: 'topright',
            strings: {
                title: "Show my location"
            }
        }).addTo(this.map);
        
        // Add fullscreen control
        L.control.fullscreen({
            position: 'topright'
        }).addTo(this.map);
        
        // Add custom emergency button
        const emergencyBtn = L.control({ position: 'topleft' });
        emergencyBtn.onAdd = () => {
            const div = L.DomUtil.create('div', 'emergency-btn');
            div.innerHTML = `
                <button class="btn btn-danger btn-lg" onclick="window.openReportModal ? window.openReportModal() : showReportModal()">
                    <i class="fas fa-exclamation-triangle"></i> REPORT EMERGENCY
                </button>
            `;
            return div;
        };
        emergencyBtn.addTo(this.map);
    }
    
    addLegend() {
        const legend = L.control({ position: 'bottomright' });
        
        legend.onAdd = () => {
            const div = L.DomUtil.create('div', 'legend');
            div.innerHTML = `
                <h6><i class="fas fa-info-circle"></i> Emergency Legend</h6>
                <div class="legend-item">
                    <div class="legend-marker critical"></div>
                    <span><strong>CRITICAL</strong> (Severity 5)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-marker high"></div>
                    <span><strong>HIGH</strong> (Severity 4)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-marker medium"></div>
                    <span><strong>MEDIUM</strong> (Severity 3)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-marker low"></div>
                    <span><strong>LOW</strong> (Severity 1-2)</span>
                </div>
                <hr>
                <div class="legend-item">
                    <i class="fas fa-ambulance" style="color: #dc3545; font-size: 20px;"></i>
                    <span style="margin-left: 10px;">Ambulance</span>
                </div>
                <div class="legend-item">
                    <i class="fas fa-fire-extinguisher" style="color: #ffc107; font-size: 20px;"></i>
                    <span style="margin-left: 10px;">Fire Truck</span>
                </div>
                <div class="legend-item">
                    <i class="fas fa-car" style="color: #28a745; font-size: 20px;"></i>
                    <span style="margin-left: 10px;">Police</span>
                </div>
                <hr>
                <div class="legend-item">
                    <div class="pulsating-marker"></div>
                    <span style="margin-left: 10px;">Active Emergency</span>
                </div>
                <hr>
                <strong style="font-size:12px;">👥 CROWD DENSITY</strong>
                <div class="legend-item" style="margin-top:4px;">
                    <div style="width:18px;height:18px;border-radius:50%;background:#8B0000;opacity:0.85;margin-right:10px;border:2px solid white;"></div>
                    <span>Critical (&gt;3/m²)</span>
                </div>
                <div class="legend-item">
                    <div style="width:16px;height:16px;border-radius:50%;background:#FF4500;opacity:0.8;margin-right:10px;border:2px solid white;"></div>
                    <span>High (1.5–3/m²)</span>
                </div>
                <div class="legend-item">
                    <div style="width:14px;height:14px;border-radius:50%;background:#FFA500;opacity:0.75;margin-right:10px;border:2px solid white;"></div>
                    <span>Moderate (0.5–1.5/m²)</span>
                </div>
                <div class="legend-item">
                    <div style="width:12px;height:12px;border-radius:50%;background:#32CD32;opacity:0.7;margin-right:10px;border:2px solid white;"></div>
                    <span>Low (&lt;0.5/m²)</span>
                </div>
                <div class="legend-item" style="margin-top:4px;">
                    <span style="font-size:14px;margin-right:8px;">⚠️</span>
                    <span style="font-size:11px;">Anomalous crowd</span>
                </div>
            `;
            return div;
        };
        
        legend.addTo(this.map);
    }
    
    async loadData() {
        try {
            if (typeof showLoading === 'function') showLoading('Loading emergency data...');
            
            // Fetch incidents, resources, and crowd detections in parallel
            const [incidents, resources, crowds] = await Promise.all([
                this.fetchIncidents(),
                this.fetchResources(),
                this.fetchCrowds()
            ]);
            
            // Store active incidents
            this.activeIncidents = incidents.features || [];
            this.activeCrowds = crowds.features || [];
            
            // Update layers
            this.renderIncidents(incidents);
            this.renderResources(resources);
            this.renderCrowds(crowds);
            
            // Update dashboard and emergency info
            if (typeof updateDashboard === 'function') updateDashboard(incidents, resources, crowds);
            this.updateEmergencyList(incidents);
            
            if (typeof hideLoading === 'function') hideLoading();
            if (typeof updateLastUpdated === 'function') updateLastUpdated();
            
            // Show summary toast
            if (this.activeIncidents.length > 0 && typeof showToast === 'function') {
                showToast(`${this.activeIncidents.length} active emergency/emergencies`, 'warning');
            }
            
        } catch (error) {
            console.error('Error loading data:', error);
            if (typeof showToast === 'function') showToast('Failed to load data. Using cached data.', 'warning');
            if (typeof hideLoading === 'function') hideLoading();
        }
    }
    
    async fetchIncidents() {
        try {
            const response = await fetch(`${this.baseUrl}/api/incidents/active`);
            if (!response.ok) throw new Error('Failed to fetch incidents');
            return await response.json();
        } catch (error) {
            console.error('Fetch incidents error:', error);
            return this.getMockIncidents();
        }
    }
    
    async fetchResources() {
        try {
            const response = await fetch(`${this.baseUrl}/api/resources/available`);
            if (!response.ok) throw new Error('Failed to fetch resources');
            return await response.json();
        } catch (error) {
            console.error('Fetch resources error:', error);
            return this.getMockResources();
        }
    }

    // ─────────────────────────────────────────────
    // 👥 CROWD DETECTION METHODS
    // ─────────────────────────────────────────────

    async fetchCrowds() {
        try {
            const response = await fetch(`${this.baseUrl}/api/crowd/geojson`);
            if (!response.ok) throw new Error('Failed to fetch crowd data');
            return await response.json();
        } catch (error) {
            console.error('Fetch crowds error:', error);
            return this.getMockCrowds();
        }
    }

    renderCrowds(data) {
        this.crowdLayer.clearLayers();

        if (!data.features || data.features.length === 0) return;

        data.features.forEach(feature => {
            const coords = feature.geometry.coordinates;  // [lng, lat]
            const props  = feature.properties;
            const lat = coords[1], lng = coords[0];

            const { color, radius } = this.getCrowdStyle(props.crowd_density, props.estimated_crowd_size);

            // Outer semi-transparent circle shows crowd spread
            const circle = L.circleMarker([lat, lng], {
                radius:      radius,
                color:       color,
                fillColor:   color,
                fillOpacity: 0.35,
                weight:      props.is_anomalous ? 3 : 1.5,
                dashArray:   props.is_anomalous ? '6,4' : null
            });

            // Inner icon marker
            const iconHtml = `
                <div style="
                    background:${color};
                    border:2px solid white;
                    border-radius:50%;
                    width:28px;height:28px;
                    display:flex;align-items:center;justify-content:center;
                    color:white;font-size:13px;
                    box-shadow:0 2px 6px rgba(0,0,0,0.4);
                    ${props.is_anomalous ? 'animation:pulse 1.5s infinite;' : ''}
                ">
                    👥
                    ${props.is_anomalous ? '<span style="position:absolute;top:-6px;right:-6px;font-size:10px;">⚠️</span>' : ''}
                </div>
            `;
            const marker = L.marker([lat, lng], {
                icon: L.divIcon({
                    html:      iconHtml,
                    className: 'emergency-marker-container',
                    iconSize:  [28, 28]
                })
            });

            const popup = this.createCrowdPopup(props, lat, lng);
            circle.bindPopup(popup);
            marker.bindPopup(popup);

            circle.addTo(this.crowdLayer);
            marker.addTo(this.crowdLayer);
        });
    }

    getCrowdStyle(density, crowdSize) {
        const styles = {
            critical: { color: '#8B0000', baseRadius: 24 },
            high:     { color: '#FF4500', baseRadius: 20 },
            moderate: { color: '#FFA500', baseRadius: 16 },
            low:      { color: '#32CD32', baseRadius: 12 }
        };
        const s = styles[density] || styles.moderate;
        // Scale radius slightly with crowd size (capped so it doesn't get huge)
        const bonus = Math.min(Math.floor(crowdSize / 1000), 8);
        return { color: s.color, radius: s.baseRadius + bonus };
    }

    createCrowdPopup(props, lat, lng) {
        const densityColors = {
            critical: '#8B0000', high: '#FF4500',
            moderate: '#FFA500', low:  '#32CD32'
        };
        const color = densityColors[props.crowd_density] || '#FFA500';
        const anomalyBadge = props.is_anomalous
            ? `<span class="badge" style="background:#FF4500;">⚠️ ANOMALOUS</span>` : '';

        return `
            <div style="min-width:240px;font-family:Segoe UI,sans-serif;">
                <div style="background:${color};color:white;padding:8px 10px;border-radius:5px 5px 0 0;margin:-12px -12px 10px -12px;">
                    <strong>👥 CROWD DETECTION</strong>
                    <span style="float:right;background:rgba(255,255,255,0.25);padding:1px 7px;border-radius:10px;font-size:12px;">
                        ${props.crowd_density.toUpperCase()}
                    </span>
                </div>
                <div style="padding:0 4px;">
                    <p style="margin:4px 0;"><i class="fas fa-map-marker-alt" style="color:#666;width:18px;"></i>
                        <strong>${props.address}</strong></p>
                    <p style="margin:4px 0;"><i class="fas fa-building" style="color:#666;width:18px;"></i>
                        ${props.place_type.replace(/_/g,' ')}</p>
                    <p style="margin:4px 0;"><i class="fas fa-users" style="color:#666;width:18px;"></i>
                        ~<strong>${props.estimated_crowd_size.toLocaleString()}</strong> people</p>
                    <p style="margin:4px 0;"><i class="fas fa-satellite" style="color:#666;width:18px;"></i>
                        Source: ${props.detection_source}
                        <span style="float:right;font-size:11px;color:#666;">
                            ${Math.round(props.detection_confidence * 100)}% confidence
                        </span>
                    </p>
                    <p style="margin:4px 0;"><i class="fas fa-shield-alt" style="color:#666;width:18px;"></i>
                        Risk: <strong style="color:${color};">${props.risk_level.toUpperCase()}</strong>
                        ${anomalyBadge}
                    </p>
                    ${props.event ? `<p style="margin:4px 0;"><i class="fas fa-calendar" style="color:#666;width:18px;"></i> Event: ${props.event}</p>` : ''}
                    <p style="margin:4px 0;font-size:11px;color:#888;">
                        <i class="fas fa-clock" style="width:18px;"></i>
                        ${new Date(props.detected_at).toLocaleString()}
                    </p>
                    <div style="display:flex;gap:5px;margin-top:8px;">
                        <button class="btn btn-sm btn-primary" onclick="zoomToLocation(${lat},${lng})" style="flex:1;padding:4px;">
                            <i class="fas fa-search"></i> Zoom
                        </button>
                        <button class="btn btn-sm btn-info" onclick="getDirections(${lat},${lng})" style="flex:1;padding:4px;">
                            <i class="fas fa-directions"></i> Directions
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    getMockCrowds() {
        return {
            type: 'FeatureCollection',
            features: [
                {
                    type: 'Feature',
                    geometry: { type: 'Point', coordinates: [77.2090, 28.6139] },
                    properties: {
                        id: 1, address: 'Connaught Place, Delhi',
                        place_type: 'commercial', estimated_crowd_size: 1200,
                        crowd_density: 'high', density_score: 0.78,
                        detection_source: 'camera', detection_confidence: 0.91,
                        is_anomalous: false, risk_level: 'high',
                        detected_at: new Date().toISOString(), event: null
                    }
                },
                {
                    type: 'Feature',
                    geometry: { type: 'Point', coordinates: [77.2167, 28.6448] },
                    properties: {
                        id: 2, address: 'Chandni Chowk, Delhi',
                        place_type: 'market', estimated_crowd_size: 3400,
                        crowd_density: 'critical', density_score: 0.95,
                        detection_source: 'satellite', detection_confidence: 0.87,
                        is_anomalous: true, risk_level: 'critical',
                        detected_at: new Date().toISOString(), event: 'festival'
                    }
                },
                {
                    type: 'Feature',
                    geometry: { type: 'Point', coordinates: [77.2295, 28.6129] },
                    properties: {
                        id: 3, address: 'India Gate Lawns, Delhi',
                        place_type: 'open_field', estimated_crowd_size: 450,
                        crowd_density: 'moderate', density_score: 0.42,
                        detection_source: 'drone', detection_confidence: 0.95,
                        is_anomalous: false, risk_level: 'moderate',
                        detected_at: new Date().toISOString(), event: null
                    }
                },
                {
                    type: 'Feature',
                    geometry: { type: 'Point', coordinates: [77.2588, 28.5535] },
                    properties: {
                        id: 4, address: 'Nehru Stadium, Delhi',
                        place_type: 'stadium', estimated_crowd_size: 28000,
                        crowd_density: 'critical', density_score: 0.98,
                        detection_source: 'sensor', detection_confidence: 0.99,
                        is_anomalous: false, risk_level: 'critical',
                        detected_at: new Date().toISOString(), event: 'sports_event'
                    }
                },
                {
                    type: 'Feature',
                    geometry: { type: 'Point', coordinates: [77.0514, 28.5921] },
                    properties: {
                        id: 5, address: 'Dwarka Sector 10 Ground',
                        place_type: 'open_field', estimated_crowd_size: 80,
                        crowd_density: 'low', density_score: 0.12,
                        detection_source: 'drone', detection_confidence: 0.82,
                        is_anomalous: false, risk_level: 'safe',
                        detected_at: new Date().toISOString(), event: null
                    }
                }
            ]
        };
    }
    
    renderIncidents(data) {
        this.incidentsLayer.clearLayers();
        
        if (!data.features || data.features.length === 0) {
            return;
        }
        
        data.features.forEach(feature => {
            const coords = feature.geometry.coordinates;
            const props = feature.properties;
            
            // Get severity-based styling
            const severity = props.severity || 3;
            const { color, size, pulse } = this.getSeverityStyle(severity);
            
            // Create custom marker with pulsing effect for active emergencies
            const markerHtml = `
                <div class="emergency-marker ${pulse ? 'pulse' : ''}" 
                     style="background-color: ${color}; width: ${size}px; height: ${size}px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; border: 2px solid white;">
                    ${severity}
                </div>
            `;
            
            const marker = L.marker([coords[1], coords[0]], {
                icon: L.divIcon({
                    html: markerHtml,
                    className: 'emergency-marker-container',
                    iconSize: [size, size]
                })
            });
            
            // Enhanced popup with more details
            const popupContent = this.createEnhancedIncidentPopup(props, coords);
            marker.bindPopup(popupContent);
            
            // Add hover effect
            marker.on('mouseover', () => {
                this.showIncidentPreview(props, coords);
            });
            
            marker.on('mouseout', () => {
                this.hideIncidentPreview();
            });
            
            marker.addTo(this.incidentsLayer);
        });
        
        // Fit bounds to show all incidents
        if (data.features.length > 0) {
            const bounds = L.latLngBounds(data.features.map(f => 
                [f.geometry.coordinates[1], f.geometry.coordinates[0]]
            ));
            this.map.fitBounds(bounds, { padding: [50, 50] });
        }
    }
    
    getSeverityStyle(severity) {
        const styles = {
            5: { color: '#ff0000', size: 40, pulse: true },  // Critical - Red, pulsing
            4: { color: '#ff6600', size: 35, pulse: true },  // High - Orange, pulsing
            3: { color: '#ffcc00', size: 30, pulse: false }, // Medium - Yellow
            2: { color: '#00cc00', size: 25, pulse: false }, // Low - Green
            1: { color: '#009900', size: 20, pulse: false }  // Very Low - Dark Green
        };
        return styles[severity] || styles[3];
    }
    
    createEnhancedIncidentPopup(props, coords) {
        const severity = props.severity || 3;
        const severityClass = this.getSeverityClass(severity);
        const timeAgo = this.getTimeAgo(props.reported_at);
        
        return `
            <div class="incident-popup" style="min-width: 250px;">
                <div class="popup-header ${severityClass}" style="padding: 10px; background-color: ${this.getSeverityColor(severity)}; color: white; border-radius: 5px 5px 0 0;">
                    <h5 style="margin: 0;"><i class="fas fa-exclamation-triangle"></i> ${props.type.toUpperCase()}</h5>
                    <span class="severity-badge" style="background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: 12px; font-size: 12px;">Severity: ${severity}/5</span>
                </div>
                
                <div class="popup-body" style="padding: 10px;">
                    <div class="info-row" style="display: flex; margin-bottom: 8px;">
                        <i class="fas fa-map-marker-alt" style="width: 20px; color: #666;"></i>
                        <span><strong>Location:</strong> ${props.address || 'Unknown'}</span>
                    </div>
                    
                    <div class="info-row" style="display: flex; margin-bottom: 8px;">
                        <i class="fas fa-clock" style="width: 20px; color: #666;"></i>
                        <span><strong>Reported:</strong> ${new Date(props.reported_at).toLocaleString()} (${timeAgo})</span>
                    </div>
                    
                    <div class="info-row" style="display: flex; margin-bottom: 8px;">
                        <i class="fas fa-info-circle" style="width: 20px; color: #666;"></i>
                        <span><strong>Status:</strong> <span class="badge bg-danger">${props.status}</span></span>
                    </div>
                    
                    ${props.description ? `
                        <div class="info-row" style="display: flex; margin-bottom: 8px;">
                            <i class="fas fa-align-left" style="width: 20px; color: #666;"></i>
                            <span><strong>Description:</strong> ${props.description}</span>
                        </div>
                    ` : ''}
                    
                    <div class="action-buttons" style="display: flex; gap: 5px; margin-top: 10px;">
                        <button class="btn btn-primary btn-sm" onclick="zoomToLocation(${coords[1]}, ${coords[0]})" style="flex: 1; padding: 5px;">
                            <i class="fas fa-search"></i> Zoom
                        </button>
                        
                        ${window.hasPermission && hasPermission('dispatch_resources') ? `
                            <button class="btn btn-danger btn-sm" onclick="dispatchToIncident(${props.id})" style="flex: 1; padding: 5px;">
                                <i class="fas fa-truck"></i> Dispatch
                            </button>
                        ` : ''}
                        
                        <button class="btn btn-info btn-sm" onclick="getDirections(${coords[1]}, ${coords[0]})" style="flex: 1; padding: 5px;">
                            <i class="fas fa-directions"></i> Directions
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    updateEmergencyList(incidents) {
        const listContainer = document.getElementById('live-emergency-list');
        if (!listContainer) return;
        
        if (!incidents.features || incidents.features.length === 0) {
            listContainer.innerHTML = '<p class="text-muted small mb-0">No active emergencies</p>';
            return;
        }
        
        // Sort by severity (highest first)
        const sorted = [...incidents.features].sort((a, b) => 
            (b.properties.severity || 0) - (a.properties.severity || 0)
        );
        
        let html = '';
        sorted.forEach(feature => {
            const props = feature.properties;
            const coords = feature.geometry.coordinates;
            const severity = props.severity || 3;
            const severityColor = this.getSeverityColor(severity);
            const timeAgo = this.getTimeAgo(props.reported_at);
            
            html += `
                <div class="emergency-list-item" onclick="zoomToLocation(${coords[1]}, ${coords[0]})" style="cursor: pointer; padding: 8px; border-bottom: 1px solid #444;">
                    <div class="d-flex align-items-center">
                        <div class="emergency-indicator" style="width: 12px; height: 12px; border-radius: 50%; background-color: ${severityColor};"></div>
                        <div class="flex-grow-1 ms-2">
                            <strong>${props.type.toUpperCase()}</strong>
                            <small class="text-muted d-block">${props.address || 'Unknown'}</small>
                        </div>
                        <div class="text-end">
                            <span class="badge bg-danger">${severity}</span>
                            <small class="text-muted d-block">${timeAgo}</small>
                        </div>
                    </div>
                </div>
            `;
        });
        
        listContainer.innerHTML = html;
    }
    
    showIncidentPreview(props, coords) {
        // Show a small preview tooltip on hover
        const preview = L.popup({ className: 'preview-popup', offset: [0, -30] })
            .setLatLng([coords[1], coords[0]])
            .setContent(`
                <strong>${props.type}</strong><br>
                Severity: ${props.severity}/5<br>
                ${props.address || ''}
            `)
            .openOn(this.map);
    }
    
    hideIncidentPreview() {
        this.map.closePopup();
    }
    
    getSeverityColor(severity) {
        const colors = {
            5: '#ff0000',
            4: '#ff6600',
            3: '#ffcc00',
            2: '#00cc00',
            1: '#009900'
        };
        return colors[severity] || '#ffcc00';
    }
    
    getSeverityClass(severity) {
        const classes = {
            5: 'critical',
            4: 'high',
            3: 'medium',
            2: 'low',
            1: 'low'
        };
        return classes[severity] || 'medium';
    }
    
    getTimeAgo(timestamp) {
        const now = new Date();
        const past = new Date(timestamp);
        const diffMs = now - past;
        const diffMins = Math.floor(diffMs / 60000);
        
        if (diffMins < 1) return 'just now';
        if (diffMins < 60) return `${diffMins} min ago`;
        
        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        
        const diffDays = Math.floor(diffHours / 24);
        return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    }
    
    renderResources(data) {
        this.resourcesLayer.clearLayers();
        
        if (!data.features || data.features.length === 0) {
            return;
        }
        
        data.features.forEach(feature => {
            const coords = feature.geometry.coordinates;
            const props = feature.properties;
            
            // Create custom icon based on resource type
            const icon = this.getResourceIcon(props.type);
            
            const marker = L.marker([coords[1], coords[0]], { icon: icon });
            
            const popupContent = this.createResourcePopup(props, coords);
            marker.bindPopup(popupContent);
            
            marker.addTo(this.resourcesLayer);
        });
    }
    
    getResourceIcon(type) {
        const icons = {
            'ambulance': L.divIcon({
                html: '<i class="fas fa-ambulance" style="color: #dc3545; font-size: 24px;"></i>',
                className: 'resource-icon',
                iconSize: [30, 30]
            }),
            'fire_truck': L.divIcon({
                html: '<i class="fas fa-fire-extinguisher" style="color: #ffc107; font-size: 24px;"></i>',
                className: 'resource-icon',
                iconSize: [30, 30]
            }),
            'police': L.divIcon({
                html: '<i class="fas fa-car" style="color: #28a745; font-size: 24px;"></i>',
                className: 'resource-icon',
                iconSize: [30, 30]
            })
        };
        return icons[type] || icons.ambulance;
    }
    
    createResourcePopup(props, coords) {
        return `
            <div class="resource-popup" style="min-width: 200px;">
                <h5><i class="fas fa-truck"></i> ${props.type.replace('_', ' ').toUpperCase()}</h5>
                <p><strong>ID:</strong> ${props.id}</p>
                <p><strong>Status:</strong> <span class="badge bg-success">${props.status}</span></p>
                <p><strong>Capacity:</strong> ${props.capacity || 'N/A'}</p>
                <p><strong>Location:</strong> ${coords[1].toFixed(4)}, ${coords[0].toFixed(4)}</p>
                ${window.hasPermission && hasPermission('dispatch_resources') ? `
                    <button class="btn btn-sm btn-success w-100 mt-2" onclick="dispatchResource(${props.id})">
                        <i class="fas fa-play"></i> Dispatch
                    </button>
                ` : ''}
            </div>
        `;
    }
    
    handleMapClick(e) {
        const { lat, lng } = e.latlng;
        console.log('Map clicked at:', lat, lng);
        console.log('Report modal open?', this.isReportModalOpen);
        
        // Store selected location
        this.selectedLocation = { lat, lng };
        
        // If report modal is open, update the form
        if (this.isReportModalOpen) {
            this.selectLocationForReport(lat, lng);
        } else {
            // Just add temporary marker for normal clicks
            this.addTempMarker(lat, lng);
        }
    }
    
    selectLocationForReport(lat, lng) {
        console.log('Selecting location for report:', lat, lng);
        
        // Update form inputs
        const latElement = document.getElementById('selected-lat');
        const lngElement = document.getElementById('selected-lng');
        const locationInput = document.getElementById('location-input');
        const submitBtn = document.getElementById('submit-btn');
        
        if (latElement) latElement.textContent = lat.toFixed(6);
        if (lngElement) lngElement.textContent = lng.toFixed(6);
        if (locationInput) locationInput.value = `Lat: ${lat.toFixed(6)}, Lng: ${lng.toFixed(6)}`;
        
        // Add temporary marker
        this.addTempMarker(lat, lng);
        
        // Enable submit button
        if (submitBtn) submitBtn.disabled = false;
        
        // Show toast notification
        if (typeof showToast === 'function') {
            showToast('Location selected! Click Submit to continue', 'success');
        }
        
        // Switch to map tab if it exists
        const mapTab = document.getElementById('map-tab');
        if (mapTab && typeof bootstrap !== 'undefined') {
            const tab = new bootstrap.Tab(mapTab);
            tab.show();
        }
    }
    
    addTempMarker(lat, lng) {
        // Remove existing temp marker
        if (this.tempMarker) {
            this.map.removeLayer(this.tempMarker);
        }
        
        // Add new temp marker with animation
        this.tempMarker = L.circleMarker([lat, lng], {
            radius: 12,
            color: '#007bff',
            fillColor: '#007bff',
            fillOpacity: 0.8,
            weight: 3,
            className: 'location-marker'
        }).addTo(this.map);
    }
    
    clearTempMarker() {
        if (this.tempMarker) {
            this.map.removeLayer(this.tempMarker);
            this.tempMarker = null;
        }
    }
    
    toggleHeatmap() {
        if (this.heatmapLayer) {
            this.map.removeLayer(this.heatmapLayer);
            this.heatmapLayer = null;
            if (typeof showToast === 'function') showToast('Heatmap disabled', 'info');
        } else {
            this.createHeatmap();
        }
    }
    
    createHeatmap() {
        // Collect incident locations for heatmap
        const heatData = [];
        this.incidentsLayer.eachLayer(layer => {
            const latlng = layer.getLatLng();
            heatData.push([latlng.lat, latlng.lng, 1]);
        });
        
        if (heatData.length > 0) {
            this.heatmapLayer = L.heatLayer(heatData, {
                radius: 25,
                blur: 15,
                maxZoom: 10,
                gradient: {
                    0.2: '#00ff00',
                    0.4: '#ffff00',
                    0.6: '#ff9900',
                    0.8: '#ff0000'
                }
            }).addTo(this.map);
            
            if (typeof showToast === 'function') showToast('Heatmap enabled', 'success');
        } else {
            if (typeof showToast === 'function') showToast('No data for heatmap', 'warning');
        }
    }
    
    centerMap() {
        if (this.activeIncidents.length > 0) {
            // Center on first incident
            const incident = this.activeIncidents[0];
            const coords = incident.geometry.coordinates;
            this.map.setView([coords[1], coords[0]], 14);
        } else {
            this.map.setView([28.6139, 77.2090], 12);
        }
    }
    
    startLiveUpdates() {
        // Update every 30 seconds
        setInterval(() => this.loadData(), 30000);
    }
    
    getMockIncidents() {
        return {
            type: 'FeatureCollection',
            features: [
                {
                    type: 'Feature',
                    geometry: { type: 'Point', coordinates: [77.2090, 28.6139] },
                    properties: {
                        id: 1,
                        type: 'fire',
                        severity: 5,
                        address: 'Connaught Place, Central Delhi',
                        reported_at: new Date(Date.now() - 5 * 60000).toISOString(),
                        status: 'active',
                        description: 'Building fire, 3rd floor, people trapped'
                    }
                },
                {
                    type: 'Feature',
                    geometry: { type: 'Point', coordinates: [77.2190, 28.6239] },
                    properties: {
                        id: 2,
                        type: 'medical',
                        severity: 4,
                        address: 'Preet Vihar, East Delhi',
                        reported_at: new Date(Date.now() - 15 * 60000).toISOString(),
                        status: 'active',
                        description: 'Heart attack patient needs immediate attention'
                    }
                },
                {
                    type: 'Feature',
                    geometry: { type: 'Point', coordinates: [77.2290, 28.6099] },
                    properties: {
                        id: 3,
                        type: 'accident',
                        severity: 4,
                        address: 'Saket, South Delhi',
                        reported_at: new Date(Date.now() - 25 * 60000).toISOString(),
                        status: 'active',
                        description: 'Multiple vehicle collision, injuries reported'
                    }
                }
            ]
        };
    }
    
    getMockResources() {
        return {
            type: 'FeatureCollection',
            features: [
                {
                    type: 'Feature',
                    geometry: { type: 'Point', coordinates: [77.1990, 28.6039] },
                    properties: {
                        id: 1,
                        type: 'ambulance',
                        status: 'available',
                        capacity: 4
                    }
                },
                {
                    type: 'Feature',
                    geometry: { type: 'Point', coordinates: [77.2290, 28.6339] },
                    properties: {
                        id: 2,
                        type: 'fire_truck',
                        status: 'available',
                        capacity: 6
                    }
                }
            ]
        };
    }
}

// Initialize map when DOM is loaded
let emergencyMap;
document.addEventListener('DOMContentLoaded', () => {
    emergencyMap = new EmergencyMap();
    
    // Expose map instance globally
    window.emergencyMap = emergencyMap;
});

// Global helper functions
function zoomToLocation(lat, lng) {
    if (emergencyMap) {
        emergencyMap.map.setView([lat, lng], 16);
        emergencyMap.addTempMarker(lat, lng);
    }
}

function getDirections(lat, lng) {
    window.open(`https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`, '_blank');
}

function dispatchResource(resourceId) {
    if (typeof showToast === 'function') {
        showToast(`Dispatching resource ${resourceId}...`, 'info');
    }
}

// Function to manually set location from address search
function setLocationFromAddress(lat, lng, address) {
    if (emergencyMap) {
        emergencyMap.selectLocationForReport(lat, lng);
        
        // Update address info if elements exist
        const addressInfo = document.getElementById('selected-address-info');
        const selectedAddress = document.getElementById('selected-address');
        const addressLat = document.getElementById('address-lat');
        const addressLng = document.getElementById('address-lng');
        
        if (addressInfo && selectedAddress && addressLat && addressLng) {
            selectedAddress.textContent = address;
            addressLat.textContent = lat.toFixed(6);
            addressLng.textContent = lng.toFixed(6);
            addressInfo.style.display = 'block';
        }
    }
}

// Make functions globally available
window.setLocationFromAddress = setLocationFromAddress;