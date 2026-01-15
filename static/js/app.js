/**
 * The Blindspot Initiative
 * Interactive Map Application
 */

// Global state
let map;
let tileLayer;
let markersLayer;
let heatmapLayer;
let userLocationMarker;
let customLocationMarker;
let issuesData = [];
let nearbyMarkerIds = []; // Track IDs of nearby issues for glow effect
let isCustomLocation = false; // Track if viewing a custom searched location
let searchDebounceTimer;
let currentFilters = {
    authority: 'all',
    status: 'all'
};
let heatmapVisible = false;

// Initialize the application
document.addEventListener('DOMContentLoaded', function () {
    initMap();
    loadIssues();
<<<<<<< HEAD
    loadSilenceScores(); // Load authority silence scores
=======
    loadUnaddressedIssues();
>>>>>>> 2df7404 (11th commit)
    setupEventListeners();
    setupLocationSearch(); // Initialize location search
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

    // Initialize map tiles based on current theme
    updateMapTheme();

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
 * Update map tiles based on current theme
 */
function updateMapTheme() {
    if (!map) return;

    // Remove existing layer if any
    if (tileLayer) {
        map.removeLayer(tileLayer);
    }

    const isLightMode = document.body.classList.contains('light-mode');
    const tileUrl = isLightMode
        ? 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
        : 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';

    tileLayer = L.tileLayer(tileUrl, {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(map);
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
 * Adds glow effect if marker is within proximity radius
 */
function createIssueIcon(props) {
    const urgency = props.urgency_level;
    const icon = props.icon || 'fa-exclamation';

    // Add nearby-glow class if this issue is within 3km radius
    const isNearby = nearbyMarkerIds.includes(props.id);
    const nearbyClass = isNearby ? ' marker-nearby-glow' : '';

    return L.divIcon({
        className: `issue-marker urgency-${urgency}${nearbyClass}`,
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
 * Show user's location and nearby issues ("You Walked Past This" mode)
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

                // Zoom to city-neighborhood level (14 instead of 15 for wider view)
                map.setView([lat, lng], 14);

                // Load nearby unresolved issues within 3km radius
                await loadNearbyUnresolvedIssues(lat, lng);

                btn.classList.remove('active');
                btn.innerHTML = '<i class="fa-solid fa-location-crosshairs"></i><span>My Location</span>';
            },
            function (error) {
                console.error('Geolocation error:', error);
                showProximityOverlay('Unable to get your location. Please enable location services.');
                setTimeout(hideProximityOverlay, 4000);
                btn.classList.remove('active');
                btn.innerHTML = '<i class="fa-solid fa-location-crosshairs"></i><span>My Location</span>';
            },
            {
                enableHighAccuracy: true,
                timeout: 10000
            }
        );
    } else {
        showProximityOverlay('Geolocation is not supported by your browser.');
        setTimeout(hideProximityOverlay, 4000);
        btn.classList.remove('active');
        btn.innerHTML = '<i class="fa-solid fa-location-crosshairs"></i><span>My Location</span>';
    }
}

/**
 * Load unresolved issues within 3km radius using Haversine distance
 */
async function loadNearbyUnresolvedIssues(lat, lng) {
    try {
        const response = await fetch(`${MAP_CONFIG.apiIssuesRadius}?lat=${lat}&lng=${lng}&radius=3`);
        const data = await response.json();

        const unresolvedCount = data.unresolved_count;
        nearbyMarkerIds = data.nearby_issue_ids;

        // Show subtle, non-intrusive proximity overlay
        if (unresolvedCount > 0) {
            showProximityOverlay(`Within 3 km of you, ${unresolvedCount} unresolved civic issues remain.`);
        } else {
            showProximityOverlay('No unresolved civic issues within 3 km of you.');
        }

        // Auto-hide after 5 seconds
        setTimeout(hideProximityOverlay, 5000);

        // Refresh markers to apply glow effect to nearby ones
        renderMarkers(issuesData);

    } catch (error) {
        console.error('Error loading nearby unresolved issues:', error);
    }
}

/**
 * Show the proximity overlay with a message
 */
function showProximityOverlay(message) {
    const overlay = document.getElementById('proximity-overlay');
    const messageEl = document.getElementById('proximity-message');

    messageEl.textContent = message;
    overlay.classList.add('visible');
}

/**
 * Hide the proximity overlay
 */
function hideProximityOverlay() {
    const overlay = document.getElementById('proximity-overlay');
    overlay.classList.remove('visible');
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

/**
<<<<<<< HEAD
 * Load and display silence scores for all authorities
 */
async function loadSilenceScores() {
    try {
        const response = await fetch(MAP_CONFIG.apiSilenceScores);
        const data = await response.json();

        // Update each authority filter button with silence score
        data.authorities.forEach(auth => {
            const btn = document.querySelector(`.filter-btn[data-authority="${auth.id}"]`);
            if (btn) {
                // Check if silence score element already exists
                let scoreEl = btn.querySelector('.silence-score');
                if (!scoreEl) {
                    scoreEl = document.createElement('span');
                    scoreEl.className = 'silence-score';
                    btn.appendChild(scoreEl);
                }

                // Only show if score > 0
                if (auth.silence_score > 0) {
                    scoreEl.textContent = `Silence: ${auth.silence_score}`;
                    scoreEl.title = `Average ${auth.silence_score} days of inaction per issue`;
                } else {
                    scoreEl.textContent = '';
                }
            }
        });

    } catch (error) {
        console.error('Error loading silence scores:', error);
    }
}

/**
 * Setup location search functionality
 */
function setupLocationSearch() {
    const searchInput = document.getElementById('location-search');
    const clearBtn = document.getElementById('search-clear');
    const suggestionsContainer = document.getElementById('search-suggestions');

    if (!searchInput) return;

    // Input event with debounce for autocomplete
    searchInput.addEventListener('input', function (e) {
        const query = e.target.value.trim();

        // Show/hide clear button
        clearBtn.style.display = query ? 'block' : 'none';

        // Clear previous timer
        clearTimeout(searchDebounceTimer);

        if (query.length < 3) {
            hideSuggestions();
            return;
        }

        // Debounce API calls (300ms)
        searchDebounceTimer = setTimeout(() => {
            geocodeLocation(query);
        }, 300);
    });

    // Enter key to select first suggestion
    searchInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            const firstSuggestion = suggestionsContainer.querySelector('.suggestion-item');
            if (firstSuggestion) {
                firstSuggestion.click();
            }
        }
    });

    // Clear button
    clearBtn.addEventListener('click', clearLocationSearch);

    // Hide suggestions when clicking outside
    document.addEventListener('click', function (e) {
        if (!e.target.closest('.search-panel')) {
            hideSuggestions();
        }
    });
}

/**
 * Geocode location using OpenStreetMap Nominatim API
 */
async function geocodeLocation(query) {
    try {
        const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5&countrycodes=in`;

        const response = await fetch(url, {
            headers: {
                'Accept': 'application/json',
                'User-Agent': 'BlindspotInitiative/1.0'
            }
        });

        const results = await response.json();
        showSearchSuggestions(results);

    } catch (error) {
        console.error('Geocoding error:', error);
=======
 * Load unaddressed issues for the sidebar list
 */
async function loadUnaddressedIssues() {
    const listEl = document.getElementById('unaddressed-list');
    if (!listEl) return;

    try {
        const response = await fetch(MAP_CONFIG.apiUnaddressed);
        const data = await response.json();

        if (data.issues.length === 0) {
            listEl.innerHTML = `
                <div class="unaddressed-empty">
                    <i class="fa-solid fa-check-circle"></i>
                    <p>All issues are being addressed!</p>
                </div>
            `;
            return;
        }

        listEl.innerHTML = data.issues.map(issue => `
            <div class="unaddressed-item" data-issue-id="${issue.id}">
                <div class="unaddressed-rank urgency-${issue.urgency_level}">${issue.rank}</div>
                <div class="unaddressed-info">
                    <div class="unaddressed-title" onclick="showIssueDetails(${issue.id})">
                        ${escapeHtml(issue.title)}
                    </div>
                    <div class="unaddressed-meta">
                        <span class="unaddressed-days">
                            <i class="fa-solid fa-clock"></i> ${issue.days_ignored} days
                        </span>
                        <span class="unaddressed-category">${escapeHtml(issue.category)}</span>
                    </div>
                    <div class="unaddressed-actions">
                        <button class="unaddressed-comment-btn" onclick="toggleComments(${issue.id})">
                            <i class="fa-solid fa-comment"></i> ${issue.comment_count}
                        </button>
                        <span class="unaddressed-confirms">
                            <i class="fa-solid fa-users"></i> ${issue.confirmation_count}
                        </span>
                    </div>
                </div>
            </div>
            <div class="comment-section" id="comments-${issue.id}" style="display: none;">
                <div class="comment-list" id="comment-list-${issue.id}"></div>
                ${MAP_CONFIG.isAuthenticated ? `
                    <div class="comment-form">
                        <input type="text" class="comment-input" id="comment-input-${issue.id}" 
                               placeholder="Add your comment..." maxlength="500">
                        <button class="comment-submit" onclick="submitComment(${issue.id})">
                            <i class="fa-solid fa-paper-plane"></i>
                        </button>
                    </div>
                ` : `
                    <div class="comment-login-prompt">
                        <a href="/login/">Login</a> to comment
                    </div>
                `}
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading unaddressed issues:', error);
        listEl.innerHTML = '<div class="unaddressed-error">Failed to load</div>';
>>>>>>> 2df7404 (11th commit)
    }
}

/**
<<<<<<< HEAD
 * Display autocomplete suggestions
 */
function showSearchSuggestions(results) {
    const container = document.getElementById('search-suggestions');

    if (results.length === 0) {
        container.innerHTML = '<div class="no-results">No locations found</div>';
        container.classList.add('visible');
        return;
    }

    container.innerHTML = results.map(result => `
        <div class="suggestion-item" 
             data-lat="${result.lat}" 
             data-lng="${result.lon}"
             data-name="${escapeHtml(result.display_name)}">
            <i class="fa-solid fa-location-dot"></i>
            <span>${escapeHtml(result.display_name)}</span>
        </div>
    `).join('');

    // Add click handlers
    container.querySelectorAll('.suggestion-item').forEach(item => {
        item.addEventListener('click', function () {
            const lat = parseFloat(this.dataset.lat);
            const lng = parseFloat(this.dataset.lng);
            const name = this.dataset.name;
            selectLocation(lat, lng, name);
        });
    });

    container.classList.add('visible');
}

/**
 * Hide search suggestions
 */
function hideSuggestions() {
    const container = document.getElementById('search-suggestions');
    if (container) {
        container.classList.remove('visible');
=======
 * Toggle comments section for an issue
 */
async function toggleComments(issueId) {
    const section = document.getElementById(`comments-${issueId}`);
    const commentList = document.getElementById(`comment-list-${issueId}`);

    if (section.style.display === 'none') {
        section.style.display = 'block';

        // Load comments
        try {
            const response = await fetch(`/api/issues/${issueId}/comments/`);
            const data = await response.json();

            if (data.comments.length === 0) {
                commentList.innerHTML = '<div class="no-comments">No comments yet. Be the first!</div>';
            } else {
                commentList.innerHTML = data.comments.map(c => `
                    <div class="comment-item">
                        <div class="comment-header">
                            <span class="comment-user">${escapeHtml(c.user)}</span>
                            <span class="comment-date">${formatDate(c.created_at)}</span>
                        </div>
                        <div class="comment-content">${escapeHtml(c.content)}</div>
                    </div>
                `).join('');
            }
        } catch (error) {
            commentList.innerHTML = '<div class="comment-error">Failed to load comments</div>';
        }
    } else {
        section.style.display = 'none';
    }
}

/**
 * Submit a comment for an issue
 */
async function submitComment(issueId) {
    const input = document.getElementById(`comment-input-${issueId}`);
    const content = input.value.trim();

    if (!content) {
        alert('Please enter a comment');
        return;
    }

    try {
        const response = await fetch(`/api/issues/${issueId}/comment/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': MAP_CONFIG.csrfToken
            },
            body: JSON.stringify({ content })
        });

        const data = await response.json();

        if (data.success) {
            input.value = '';
            // Reload comments
            const commentList = document.getElementById(`comment-list-${issueId}`);
            const c = data.comment;
            const newComment = `
                <div class="comment-item">
                    <div class="comment-header">
                        <span class="comment-user">${escapeHtml(c.user)}</span>
                        <span class="comment-date">Just now</span>
                    </div>
                    <div class="comment-content">${escapeHtml(c.content)}</div>
                </div>
            `;

            // Check if "no comments" message exists and replace it
            if (commentList.querySelector('.no-comments')) {
                commentList.innerHTML = newComment;
            } else {
                commentList.insertAdjacentHTML('afterbegin', newComment);
            }

            // Update comment count
            loadUnaddressedIssues();
        } else {
            alert(data.message);
        }
    } catch (error) {
        console.error('Error submitting comment:', error);
        alert('Failed to submit comment. Please try again.');
>>>>>>> 2df7404 (11th commit)
    }
}

/**
<<<<<<< HEAD
 * Select a location and pan map to it
 */
async function selectLocation(lat, lng, name) {
    const searchInput = document.getElementById('location-search');

    // Update input with selected location name (shortened)
    const shortName = name.split(',').slice(0, 2).join(', ');
    searchInput.value = shortName;

    // Hide suggestions
    hideSuggestions();

    // Mark as custom location mode
    isCustomLocation = true;
    updateLocationButtonState();

    // Remove previous custom location marker
    if (customLocationMarker) {
        map.removeLayer(customLocationMarker);
    }

    // Add marker for selected location
    customLocationMarker = L.marker([lat, lng], {
        icon: L.divIcon({
            className: 'custom-location-wrapper',
            html: '<div class="custom-location-marker"><i class="fa-solid fa-map-pin"></i></div>',
            iconSize: [24, 24],
            iconAnchor: [12, 24]
        })
    }).addTo(map);

    // Zoom to city-neighborhood level
    map.setView([lat, lng], 14);

    // Load nearby unresolved issues (reuse existing function)
    await loadNearbyUnresolvedIssues(lat, lng);
}

/**
 * Clear location search and reset to default
 */
function clearLocationSearch() {
    const searchInput = document.getElementById('location-search');
    const clearBtn = document.getElementById('search-clear');

    searchInput.value = '';
    clearBtn.style.display = 'none';
    hideSuggestions();

    // Reset custom location mode
    isCustomLocation = false;
    updateLocationButtonState();

    // Remove custom location marker
    if (customLocationMarker) {
        map.removeLayer(customLocationMarker);
        customLocationMarker = null;
    }

    // Clear nearby markers glow
    nearbyMarkerIds = [];
    renderMarkers(issuesData);
    hideProximityOverlay();

    // Reset map to default center
    map.setView(MAP_CONFIG.center, MAP_CONFIG.zoom);
}

/**
 * Update My Location button state based on custom location mode
 */
function updateLocationButtonState() {
    const btn = document.getElementById('btn-my-location');
    if (isCustomLocation) {
        btn.classList.add('dimmed');
    } else {
        btn.classList.remove('dimmed');
    }
=======
 * Format ISO date to relative time
 */
function formatDate(isoDate) {
    const date = new Date(isoDate);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
>>>>>>> 2df7404 (11th commit)
}
