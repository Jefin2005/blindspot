/**
 * The Blindspot Initiative
 * Interactive Map Application
 */

// Global state
let map;
let markersLayer;
let heatmapLayer;
let userLocationMarker;
let issuesData = [];
let currentFilters = {
    authority: 'all',
    status: 'all'
};
let heatmapVisible = false;

// Initialize the application
document.addEventListener('DOMContentLoaded', function () {
    initMap();
    loadIssues();
    setupEventListeners();
});

/**
 * Initialize Leaflet Map
 */
function initMap() {
    // Create map centered on Cochin
    map = L.map('map', {
        center: MAP_CONFIG.center,
        zoom: MAP_CONFIG.zoom,
        zoomControl: true,
        attributionControl: true
    });

    // Add dark-themed map tiles (CartoDB Dark Matter)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(map);

    // Create marker cluster group
    markersLayer = L.markerClusterGroup({
        chunkedLoading: true,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        maxClusterRadius: 60,
        iconCreateFunction: function (cluster) {
            const count = cluster.getChildCount();
            let size = 'small';
            if (count > 10) size = 'medium';
            if (count > 30) size = 'large';

            return L.divIcon({
                html: `<div><span>${count}</span></div>`,
                className: `marker-cluster marker-cluster-${size}`,
                iconSize: L.point(40, 40)
            });
        }
    });

    map.addLayer(markersLayer);
}

/**
 * Load issues from API
 */
async function loadIssues() {
    try {
        let url = MAP_CONFIG.apiIssues;
        const params = new URLSearchParams();

        if (currentFilters.authority !== 'all') {
            params.append('authority', currentFilters.authority);
        }
        if (currentFilters.status !== 'all') {
            params.append('status', currentFilters.status);
        }

        if (params.toString()) {
            url += '?' + params.toString();
        }

        const response = await fetch(url);
        const geojson = await response.json();

        issuesData = geojson.features;
        renderMarkers(issuesData);

        if (heatmapVisible) {
            renderHeatmap(issuesData);
        }

        // Update statistics and filter counts
        await loadStatistics();

    } catch (error) {
        console.error('Error loading issues:', error);
    }
}

/**
 * Load and update statistics including authority counts
 */
async function loadStatistics() {
    try {
        const response = await fetch(MAP_CONFIG.apiStatistics);
        const stats = await response.json();

        // Update dashboard stats
        const statTotal = document.getElementById('stat-total');
        const statIgnored = document.getElementById('stat-ignored');
        const statCritical = document.getElementById('stat-critical');
        const statResolved = document.getElementById('stat-resolved');

        if (statTotal) statTotal.textContent = stats.total;
        if (statIgnored) statIgnored.textContent = stats.by_status.ignored;
        if (statCritical) statCritical.textContent = stats.critical_count;
        if (statResolved) statResolved.textContent = stats.by_status.resolved;

        // Update authority filter counts
        // First reset all to 0
        document.querySelectorAll('[id^="authority-count-"]').forEach(el => {
            el.textContent = '0';
        });

        // Then update with actual counts
        stats.by_authority.forEach(auth => {
            const countEl = document.getElementById(`authority-count-${auth.category__authority__id}`);
            if (countEl) {
                countEl.textContent = auth.count;
            }
        });

    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

/**
 * Render markers on the map
 */
function renderMarkers(features) {
    markersLayer.clearLayers();

    features.forEach(feature => {
        const props = feature.properties;
        const coords = feature.geometry.coordinates;

        // Create custom icon
        const icon = createIssueIcon(props);

        // Create marker
        const marker = L.marker([coords[1], coords[0]], { icon: icon });

        // Bind popup
        marker.bindPopup(createPopupContent(props), {
            maxWidth: 350,
            className: 'issue-popup'
        });

        // Add to cluster group
        markersLayer.addLayer(marker);
    });
}

/**
 * Create custom marker icon based on urgency
 */
function createIssueIcon(props) {
    const urgency = props.urgency_level;
    const icon = props.icon || 'fa-exclamation';

    return L.divIcon({
        className: `issue-marker urgency-${urgency}`,
        html: `<i class="fa-solid ${icon}"></i>`,
        iconSize: [32, 32],
        iconAnchor: [16, 16]
    });
}

/**
 * Create popup content HTML
 */
function createPopupContent(props) {
    const statusClass = props.status.replace('_', '-');

    return `
        <div class="popup-content">
            <div class="popup-header">
                <div class="popup-icon" style="background: ${props.authority_color}">
                    <i class="fa-solid ${props.icon || 'fa-exclamation'}"></i>
                </div>
                <div>
                    <div class="popup-title">${escapeHtml(props.title)}</div>
                    <div class="popup-category">${escapeHtml(props.category)} • ${escapeHtml(props.authority)}</div>
                </div>
            </div>
            
            <div class="popup-stats">
                <div class="popup-stat">
                    <div class="popup-stat-value" style="color: ${props.urgency_color}">${props.days_since_report}</div>
                    <div class="popup-stat-label">Days Since Report</div>
                </div>
                <div class="popup-stat">
                    <div class="popup-stat-value">${props.confirmation_count}</div>
                    <div class="popup-stat-label">Confirmations</div>
                </div>
                <div class="popup-stat">
                    <div class="popup-stat-value">${props.severity}/5</div>
                    <div class="popup-stat-label">Severity</div>
                </div>
                <div class="popup-stat">
                    <div class="popup-stat-value">${props.days_ignored}</div>
                    <div class="popup-stat-label">Days Ignored</div>
                </div>
            </div>
            
            ${props.address ? `
                <div class="popup-address">
                    <i class="fa-solid fa-location-dot"></i>
                    <span>${escapeHtml(props.address)}</span>
                </div>
            ` : ''}
            
            <span class="popup-status ${statusClass}">
                <i class="fa-solid fa-${getStatusIcon(props.status)}"></i>
                ${props.status_display}
            </span>
            
            <div class="popup-actions">
                ${MAP_CONFIG.isAuthenticated ? `
                    <button class="popup-btn popup-btn-confirm" onclick="confirmIssue(${props.id})">
                        <i class="fa-solid fa-check"></i> Confirm
                    </button>
                ` : ''}
                <button class="popup-btn popup-btn-details" onclick="showIssueDetails(${props.id})">
                    <i class="fa-solid fa-arrow-right"></i> Details
                </button>
            </div>
        </div>
    `;
}

/**
 * Get icon for status
 */
function getStatusIcon(status) {
    const icons = {
        'ignored': 'eye-slash',
        'acknowledged': 'eye',
        'in_progress': 'clock',
        'resolved': 'check-circle'
    };
    return icons[status] || 'circle';
}

/**
 * Render heatmap layer
 */
function renderHeatmap(features) {
    if (heatmapLayer) {
        map.removeLayer(heatmapLayer);
    }

    const heatData = features.map(f => {
        const coords = f.geometry.coordinates;
        const intensity = getHeatIntensity(f.properties);
        return [coords[1], coords[0], intensity];
    });

    heatmapLayer = L.heatLayer(heatData, {
        radius: 35,
        blur: 20,
        maxZoom: 15,
        gradient: {
            0.2: '#22c55e',
            0.4: '#eab308',
            0.6: '#f97316',
            0.8: '#ef4444',
            1.0: '#dc2626'
        }
    }).addTo(map);
}

/**
 * Calculate heat intensity based on issue properties
 */
function getHeatIntensity(props) {
    // Combine severity and days ignored for intensity
    const severityWeight = props.severity / 5;
    const daysWeight = Math.min(props.days_ignored / 60, 1);
    return (severityWeight + daysWeight) / 2;
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Authority filter buttons
    document.querySelectorAll('.filter-btn[data-authority]').forEach(btn => {
        btn.addEventListener('click', function () {
            document.querySelectorAll('.filter-btn[data-authority]').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentFilters.authority = this.dataset.authority;
            loadIssues();
        });
    });

    // Status filter buttons
    document.querySelectorAll('.status-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            document.querySelectorAll('.status-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentFilters.status = this.dataset.status;
            loadIssues();
        });
    });

    // My Location button
    document.getElementById('btn-my-location').addEventListener('click', showMyLocation);

    // Toggle Heatmap button
    document.getElementById('btn-toggle-heatmap').addEventListener('click', toggleHeatmap);

    // Refresh button
    document.getElementById('btn-refresh').addEventListener('click', loadIssues);

    // Nearby panel close
    document.getElementById('nearby-close').addEventListener('click', function () {
        document.getElementById('nearby-panel').style.display = 'none';
    });

    // Modal close
    document.getElementById('modal-close').addEventListener('click', closeModal);
    document.querySelector('.modal-backdrop').addEventListener('click', closeModal);
}

/**
 * Show user's location and nearby issues
 */
function showMyLocation() {
    const btn = document.getElementById('btn-my-location');
    btn.classList.add('active');
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i><span>Locating...</span>';

    if ('geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition(
            async function (position) {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;

                // Add user location marker
                if (userLocationMarker) {
                    map.removeLayer(userLocationMarker);
                }

                userLocationMarker = L.marker([lat, lng], {
                    icon: L.divIcon({
                        className: 'user-location-wrapper',
                        html: '<div class="user-location-pulse"></div><div class="user-location-marker"></div>',
                        iconSize: [20, 20],
                        iconAnchor: [10, 10]
                    })
                }).addTo(map);

                // Pan to location
                map.setView([lat, lng], 15);

                // Load nearby issues
                await loadNearbyIssues(lat, lng);

                btn.classList.remove('active');
                btn.innerHTML = '<i class="fa-solid fa-location-crosshairs"></i><span>My Location</span>';
            },
            function (error) {
                console.error('Geolocation error:', error);
                alert('Unable to get your location. Please enable location services.');
                btn.classList.remove('active');
                btn.innerHTML = '<i class="fa-solid fa-location-crosshairs"></i><span>My Location</span>';
            },
            {
                enableHighAccuracy: true,
                timeout: 10000
            }
        );
    } else {
        alert('Geolocation is not supported by your browser.');
        btn.classList.remove('active');
        btn.innerHTML = '<i class="fa-solid fa-location-crosshairs"></i><span>My Location</span>';
    }
}

/**
 * Load issues near a location
 */
async function loadNearbyIssues(lat, lng) {
    try {
        const response = await fetch(`${MAP_CONFIG.apiIssuesNearby}?lat=${lat}&lng=${lng}&radius=0.02`);
        const data = await response.json();

        const panel = document.getElementById('nearby-panel');
        const content = document.getElementById('nearby-content');

        if (data.features.length === 0) {
            content.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-check-circle"></i>
                    <h3>No issues nearby</h3>
                    <p>Your area seems clear. Stay vigilant!</p>
                </div>
            `;
        } else {
            content.innerHTML = data.features.map(f => {
                const p = f.properties;
                return `
                    <div class="nearby-item" onclick="focusIssue(${p.id}, ${f.geometry.coordinates[1]}, ${f.geometry.coordinates[0]})">
                        <div class="nearby-urgency" style="background: ${p.urgency_color}; box-shadow: 0 0 6px ${p.urgency_color};"></div>
                        <div class="nearby-info">
                            <div class="nearby-title">${escapeHtml(p.title)}</div>
                            <div class="nearby-meta">${p.category} • ${p.days_ignored} days ignored</div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        panel.style.display = 'block';

    } catch (error) {
        console.error('Error loading nearby issues:', error);
    }
}

/**
 * Focus on a specific issue
 */
function focusIssue(id, lat, lng) {
    map.setView([lat, lng], 17);
    document.getElementById('nearby-panel').style.display = 'none';
}

/**
 * Toggle heatmap visibility
 */
function toggleHeatmap() {
    const btn = document.getElementById('btn-toggle-heatmap');
    heatmapVisible = !heatmapVisible;

    if (heatmapVisible) {
        btn.classList.add('active');
        renderHeatmap(issuesData);
    } else {
        btn.classList.remove('active');
        if (heatmapLayer) {
            map.removeLayer(heatmapLayer);
        }
    }
}

/**
 * Show issue details in modal
 */
async function showIssueDetails(issueId) {
    const modal = document.getElementById('issue-modal');
    const modalBody = document.getElementById('modal-body');

    modalBody.innerHTML = '<div class="loading"><i class="fa-solid fa-spinner fa-spin"></i> Loading...</div>';
    modal.classList.add('active');

    try {
        const response = await fetch(`/api/issues/${issueId}/`);
        const issue = await response.json();

        modalBody.innerHTML = `
            <div class="issue-detail">
                <div class="issue-detail-header" style="border-left: 4px solid ${issue.authority_color}; padding-left: 1rem; margin-bottom: 1.5rem;">
                    <h2 style="font-size: 1.25rem; margin-bottom: 0.25rem;">${escapeHtml(issue.title)}</h2>
                    <p style="color: var(--text-muted); font-size: 0.9rem;">${escapeHtml(issue.category)} • ${escapeHtml(issue.authority)}</p>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem;">
                    <div class="stat-card">
                        <div class="stat-value" style="color: ${issue.urgency_color}">${issue.days_since_report}</div>
                        <div class="stat-label">Days Reported</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" style="color: var(--color-critical)">${issue.days_ignored}</div>
                        <div class="stat-label">Days Ignored</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${issue.severity}/5</div>
                        <div class="stat-label">Severity</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${issue.confirmation_count}</div>
                        <div class="stat-label">Confirmed</div>
                    </div>
                </div>
                
                <div style="margin-bottom: 1.5rem;">
                    <h4 style="font-size: 0.85rem; text-transform: uppercase; color: var(--text-muted); margin-bottom: 0.5rem;">Description</h4>
                    <p style="color: var(--text-secondary); line-height: 1.7;">${escapeHtml(issue.description)}</p>
                </div>
                
                <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.5rem; padding: 1rem; background: var(--bg-elevated); border-radius: var(--radius-md);">
                    <i class="fa-solid fa-location-dot" style="color: var(--color-critical);"></i>
                    <span style="color: var(--text-secondary);">${escapeHtml(issue.address) || 'Location not specified'}</span>
                </div>
                
                <div style="display: flex; align-items: center; justify-content: space-between; padding-top: 1rem; border-top: 1px solid var(--border-subtle);">
                    <span class="popup-status ${issue.status}">
                        <i class="fa-solid fa-${getStatusIcon(issue.status)}"></i>
                        ${issue.status_display}
                    </span>
                    <span style="font-size: 0.8rem; color: var(--text-muted);">
                        Reported by ${escapeHtml(issue.reported_by)}
                    </span>
                </div>
                
                ${MAP_CONFIG.isAuthenticated && !issue.user_confirmed ? `
                    <button class="btn btn-primary" style="width: 100%; margin-top: 1rem;" onclick="confirmIssue(${issue.id})">
                        <i class="fa-solid fa-check"></i> Confirm This Issue
                    </button>
                ` : ''}
            </div>
        `;

    } catch (error) {
        console.error('Error loading issue details:', error);
        modalBody.innerHTML = '<div class="error">Failed to load issue details.</div>';
    }
}

/**
 * Confirm an issue
 */
async function confirmIssue(issueId) {
    if (!MAP_CONFIG.isAuthenticated) {
        window.location.href = '/login/';
        return;
    }

    try {
        const response = await fetch(`/api/issues/${issueId}/confirm/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': MAP_CONFIG.csrfToken
            }
        });

        const data = await response.json();

        if (data.success) {
            alert('Issue confirmed! Thank you for validating this report.');
            loadIssues();
        } else {
            alert(data.message);
        }

    } catch (error) {
        console.error('Error confirming issue:', error);
        alert('Failed to confirm issue. Please try again.');
    }
}

/**
 * Close modal
 */
function closeModal() {
    document.getElementById('issue-modal').classList.remove('active');
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
