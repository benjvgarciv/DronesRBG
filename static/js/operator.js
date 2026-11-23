/**
 * Drones RBG - Flight Operator Hub Logic (Monochrome Edition - Light Map & Black Accents)
 * Handles interactive route planning, heterogeneous waypoint definition,
 * and live mission simulation with real-time HUD telemetry instruments.
 */

let operatorMap = null;
let routePolyline = null;
let droneMarker = null;
let waypointMarkers = [];
let plannedWaypoints = [];

// Simulation State
let activeMissionId = null;
let simulationInterval = null;
let currentTick = 0;
let isSimulationRunning = false;

// Default Santiago base coordinates
const DEFAULT_LAT = -33.4372;
const DEFAULT_LNG = -70.6506;

document.addEventListener('DOMContentLoaded', () => {
    initOperatorMap();
    initWaypointTaskSelector();
    initFormHandlers();
    loadActiveMissionSelector();
});

// Initialize Leaflet Map with CartoDB Positron (Light Monochrome)
function initOperatorMap() {
    const mapElement = document.getElementById('operatorMap');
    if (!mapElement) return;

    operatorMap = L.map('operatorMap', {
        center: [DEFAULT_LAT, DEFAULT_LNG],
        zoom: 14,
        zoomControl: true
    });

    // Esri World Topo / Street Map (High reliability, fast CDN, no 403 blocks, industrial look)
    const streetLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles &copy; Esri &mdash; Drones RBG Flight Telemetry',
        maxZoom: 19
    }).addTo(operatorMap);

    // High-resolution satellite imagery layer for drone tactical planning
    const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles &copy; Esri &mdash; World Imagery | Drones RBG',
        maxZoom: 19
    });

    // Topographic Terrain layer
    const topoLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles &copy; Esri &mdash; Topo Map',
        maxZoom: 19
    });

    // Add layer switch control between Street, Satellite and Topo
    L.control.layers({
        "Mapa Táctico (Esri Calles)": streetLayer,
        "Vista Satelital (Esri Satélite)": satelliteLayer,
        "Mapa Topográfico (Relieve)": topoLayer
    }, null, { position: 'topright' }).addTo(operatorMap);

    // Initial base marker (Clean Black & White)
    const homeIcon = L.divIcon({
        className: 'custom-home-icon',
        html: `<div style="background:#000000;width:14px;height:14px;border-radius:50%;border:2px solid #ffffff;box-shadow:0 0 0 2px #000000;"></div>`,
        iconSize: [14, 14],
        iconAnchor: [7, 7]
    });
    L.marker([DEFAULT_LAT, DEFAULT_LNG], { icon: homeIcon })
        .addTo(operatorMap)
        .bindPopup("<b>Base Central RBG Santiago</b><br>Hangar & Centro de Operaciones");

    // Click on map to add waypoints
    operatorMap.on('click', (e) => {
        addWaypointFromMap(e.latlng.lat, e.latlng.lng);
    });

    // Load initial sample waypoints
    resetToSampleRoute();
}

// Add a waypoint from map click
function addWaypointFromMap(lat, lng) {
    const wpNum = plannedWaypoints.length + 1;
    const taskTypeSelect = document.getElementById('taskTypeSelect');
    const taskType = taskTypeSelect ? taskTypeSelect.value : 'PHOTO_CAPTURE';
    const taskConfig = generateTaskConfig(taskType, wpNum);

    const wp = {
        wp_num: wpNum,
        lat: parseFloat(lat.toFixed(6)),
        lng: parseFloat(lng.toFixed(6)),
        alt: 50.0,
        speed_ms: 8.0,
        action: taskType,
        task_config: taskConfig
    };

    plannedWaypoints.push(wp);
    renderRoute();
    renderWaypointsList();
}

// Generate heterogeneous task configuration based on action type
function generateTaskConfig(taskType, wpNum) {
    switch (taskType) {
        case 'PHOTO_CAPTURE':
            return {
                type: 'Captura Fotográfica Alta Resolución',
                camera: 'RGB 48MP Wide Gimbal',
                iso: 100,
                shutter_speed: '1/1000s',
                aperture: 'f/2.8',
                gimbal_pitch_deg: -45,
                target_component: `Punto de Interés Estructural #${wpNum}`
            };
        case 'THERMAL_SCAN':
            return {
                type: 'Escaneo Térmico Radiométrico',
                sensor: 'FLIR Vue Pro R 640',
                palette: 'IronBow',
                emissivity: 0.95,
                temp_alarm_celsius: 75.0,
                target: `Inspección de Puntos Calientes #${wpNum}`
            };
        case 'HOVER_PANORAMA_360':
            return {
                type: 'Giro Panorámico Estabilizado 360°',
                duration_sec: 15,
                rotation_deg_per_sec: 24,
                overlap_percent: 75
            };
        case 'MULTISPECTRAL_SCAN':
            return {
                type: 'Adquisición Multiespectral NDVI',
                bands: ['Green 560nm', 'Red 668nm', 'RedEdge 717nm', 'Near-IR 842nm'],
                ground_sampling_distance_cm: 5.0
            };
        case 'PERIMETER_SURVEILLANCE':
            return {
                type: 'Ronda Táctica de Vigilancia IA',
                ai_model: 'YOLO-V8 Aero Surveillance',
                target_classes: ['Person', 'Vehicle'],
                auto_spotlight: true
            };
        case 'RETURN_TO_HOME_LAND':
            return {
                type: 'Aterrizaje Autónomo Precisión RTK',
                precision_pad_detection: true,
                descent_speed_ms: 1.2
            };
        default:
            return { type: 'Navegación Estándar' };
    }
}

// Render polyline and waypoint markers on Leaflet (Clean Black & White)
function renderRoute() {
    waypointMarkers.forEach(m => operatorMap.removeLayer(m));
    waypointMarkers = [];

    if (routePolyline) {
        operatorMap.removeLayer(routePolyline);
        routePolyline = null;
    }

    if (plannedWaypoints.length === 0) return;

    const latlngs = plannedWaypoints.map(w => [w.lat, w.lng]);

    // Draw clean high-contrast black route line
    routePolyline = L.polyline(latlngs, {
        color: '#111827',
        weight: 2.5,
        opacity: 0.9,
        dashArray: '5, 8',
        lineCap: 'round'
    }).addTo(operatorMap);

    // Place numbered marker for each waypoint
    plannedWaypoints.forEach((w) => {
        const markerHtml = `
            <div style="background:#111827;color:#ffffff;border:2px solid #ffffff;border-radius:50%;width:22px;height:22px;display:flex;align-items:center;justify-content:center;font-weight:600;font-size:10px;font-family:monospace;box-shadow:0 1px 4px rgba(0,0,0,0.3);">
                ${w.wp_num}
            </div>
        `;
        const icon = L.divIcon({
            className: 'wp-map-marker',
            html: markerHtml,
            iconSize: [22, 22],
            iconAnchor: [11, 11]
        });

        const marker = L.marker([w.lat, w.lng], { icon: icon }).addTo(operatorMap);
        marker.bindPopup(`
            <div style="font-family:sans-serif;font-size:12px;color:#111827;">
                <b>Waypoint #${w.wp_num}</b><br>
                <b>Tarea:</b> ${getActionLabel(w.action)}<br>
                <b>Altitud:</b> ${w.alt} m | <b>Vel:</b> ${w.speed_ms} m/s<br>
                <div style="margin-top:4px;font-size:11px;color:#4b5563;line-height:1.5;">
                    ${formatTaskConfig(w.task_config)}
                </div>
            </div>
        `);
        waypointMarkers.push(marker);
    });

    calculateRouteMetrics();
}

// Calculate total route distance, flight duration and battery consumption
function calculateRouteMetrics() {
    if (plannedWaypoints.length < 2) {
        document.getElementById('metricWpCount').textContent = plannedWaypoints.length;
        document.getElementById('metricDistance').textContent = '0 m';
        document.getElementById('metricEstTime').textContent = '0 min';
        document.getElementById('metricEstBattery').textContent = '0 %';
        return;
    }

    let totalDist = 0;
    for (let i = 0; i < plannedWaypoints.length - 1; i++) {
        const p1 = L.latLng(plannedWaypoints[i].lat, plannedWaypoints[i].lng);
        const p2 = L.latLng(plannedWaypoints[i+1].lat, plannedWaypoints[i+1].lng);
        totalDist += p1.distanceTo(p2);
    }

    const distMeters = Math.round(totalDist);
    const avgSpeed = 8.5; // m/s
    const flightSec = distMeters / avgSpeed + (plannedWaypoints.length * 15);
    const flightMin = Math.round(flightSec / 60);
    const estBattery = Math.min(100, Math.round(flightMin * 1.8));

    document.getElementById('metricWpCount').textContent = plannedWaypoints.length;
    document.getElementById('metricDistance').textContent = `${distMeters} m`;
    document.getElementById('metricEstTime').textContent = `${flightMin} min`;
    document.getElementById('metricEstBattery').textContent = `~${estBattery}%`;
}

// Get human-readable Spanish action label
function getActionLabel(action) {
    if (!action) return 'Punto de Ruta';
    const actionLabels = {
        'TAKEOFF_ASCEND': 'Despegue y Ascenso',
        'TAKEOFF': 'Despegue Inicial',
        'ASCEND': 'Ascenso Táctico',
        'PHOTO_CAPTURE': 'Captura Fotográfica',
        'THERMAL_SCAN': 'Escaneo Térmico',
        'THERMAL_IRRIGATION_CHECK': 'Monitoreo Térmico de Riego',
        'HOVER_PANORAMA_360': 'Panorámica 360°',
        'HOVER': 'Vuelo Estacionario',
        'PANORAMA': 'Giro Panorámico',
        'MULTISPECTRAL_SCAN': 'Escaneo Multiespectral',
        'PERIMETER_SURVEILLANCE': 'Vigilancia Perimetral',
        'AI_INTRUSION_DETECTION': 'Detección IA de Intrusión',
        'RETURN_TO_HOME_LAND': 'Regreso y Aterrizaje',
        'RETURN_TO_HOME': 'Regreso a Base',
        'LANDING': 'Aterrizaje',
        'LAND': 'Aterrizaje',
        'WAYPOINT_NAV': 'Navegación de Ruta',
        'WAYPOINT': 'Punto de Ruta'
    };
    if (actionLabels[action]) return actionLabels[action];
    return action
        .toLowerCase()
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
}

// Format heterogeneous task_config into clean, human-readable labels
function formatTaskConfig(taskConfig) {
    if (!taskConfig || typeof taskConfig !== 'object') {
        return '<span style="color:#64748b;">Navegación Estándar</span>';
    }

    const keyLabels = {
        'camera': 'Cámara',
        'sensor': 'Sensor',
        'iso': 'ISO',
        'shutter_speed': 'Obturador',
        'aperture': 'Apertura',
        'gimbal_pitch_deg': 'Gimbal',
        'palette': 'Paleta',
        'emissivity': 'Emisividad',
        'temp_alarm_celsius': 'Alarma Temp',
        'duration_sec': 'Duración',
        'rotation_deg_per_sec': 'Rotación',
        'overlap_percent': 'Solape',
        'bands': 'Bandas',
        'ground_sampling_distance_cm': 'GSD',
        'ai_model': 'Modelo IA',
        'target_classes': 'Objetivos',
        'auto_spotlight': 'Foco Auto',
        'precision_pad_detection': 'Detección RTK',
        'descent_speed_ms': 'Vel. Descenso',
        'target_component': 'Objetivo',
        'target': 'Objetivo'
    };

    const parts = [];
    for (const [key, val] of Object.entries(taskConfig)) {
        if (key === 'type') continue; // Omitir tipo interno repetido
        const label = keyLabels[key] || key;
        let formattedVal = val;
        if (Array.isArray(val)) {
            formattedVal = val.join(', ');
        } else if (typeof val === 'boolean') {
            formattedVal = val ? 'Activado' : 'Desactivado';
        } else if (key === 'gimbal_pitch_deg') {
            formattedVal = `${val}°`;
        } else if (key === 'duration_sec') {
            formattedVal = `${val}s`;
        } else if (key === 'rotation_deg_per_sec') {
            formattedVal = `${val}°/s`;
        } else if (key === 'overlap_percent') {
            formattedVal = `${val}%`;
        } else if (key === 'temp_alarm_celsius') {
            formattedVal = `${val}°C`;
        } else if (key === 'descent_speed_ms') {
            formattedVal = `${val} m/s`;
        } else if (key === 'ground_sampling_distance_cm') {
            formattedVal = `${val} cm`;
        }
        parts.push(`<strong>${label}:</strong> ${formattedVal}`);
    }

    if (parts.length === 0) {
        return '<span style="color:#64748b;">Navegación Estándar</span>';
    }

    return parts.join(' <span style="color:#94a3b8;margin:0 4px;">·</span> ');
}

// Render the list of waypoints with their heterogeneous settings in the sidebar
function renderWaypointsList() {
    const container = document.getElementById('waypointsTimeline');
    if (!container) return;

    if (plannedWaypoints.length === 0) {
        container.innerHTML = `
            <div style="text-align:center;padding:2rem;color:#6b7280;font-size:0.82rem;">
                Haz clic en el mapa para añadir waypoints a la ruta
            </div>
        `;
        return;
    }

    container.innerHTML = plannedWaypoints.map((w, idx) => {
        return `
            <div class="wp-item-card">
                <div class="wp-header">
                    <span class="wp-badge">WP #${w.wp_num}</span>
                    <span class="wp-action-tag">${getActionLabel(w.action)}</span>
                    <button class="btn btn-sm btn-outline" style="padding:0.15rem 0.4rem;font-size:0.68rem;" onclick="deleteWaypoint(${idx})">Eliminar</button>
                </div>
                <div class="wp-details">
                    <span>Lat: ${w.lat}</span>
                    <span>Lng: ${w.lng}</span>
                    <span>Alt: ${w.alt}m</span>
                </div>
                <div class="wp-task-clean" style="margin-top:0.45rem;padding:0.5rem 0.75rem;background:#f8fafc;border-radius:var(--radius-xs);font-size:0.73rem;color:#334155;border-left:3px solid #0284c7;border-top:1px solid var(--border-subtle);border-right:1px solid var(--border-subtle);border-bottom:1px solid var(--border-subtle);line-height:1.6;">
                    ${formatTaskConfig(w.task_config)}
                </div>
            </div>
        `;
    }).join('');
}

// Delete a waypoint
function deleteWaypoint(index) {
    plannedWaypoints.splice(index, 1);
    plannedWaypoints.forEach((w, i) => { w.wp_num = i + 1; });
    renderRoute();
    renderWaypointsList();
}

// Reset to sample multi-task route
function resetToSampleRoute() {
    plannedWaypoints = [
        {
            wp_num: 1,
            lat: -33.4372,
            lng: -70.6506,
            alt: 35.0,
            speed_ms: 5.0,
            action: "TAKEOFF_ASCEND",
            task_config: { type: "Despegue Vertical Seguro", climb_rate_ms: 2.5, hover_sec: 5 }
        },
        {
            wp_num: 2,
            lat: -33.4348,
            lng: -70.6482,
            alt: 55.0,
            speed_ms: 10.0,
            action: "PHOTO_CAPTURE",
            task_config: { type: "Captura Fotográfica Alta Resolución", camera: "RGB 48MP", iso: 100, shutter_speed: "1/1200s", aperture: "f/2.8", target: "Aislador Transformador TR-01" }
        },
        {
            wp_num: 3,
            lat: -33.4325,
            lng: -70.6455,
            alt: 50.0,
            speed_ms: 6.0,
            action: "THERMAL_SCAN",
            task_config: { type: "Escaneo Térmico Radiométrico", sensor: "FLIR Vue Pro R", palette: "IronBow", emissivity: 0.95, temp_alarm_celsius: 75.0 }
        },
        {
            wp_num: 4,
            lat: -33.4310,
            lng: -70.6490,
            alt: 60.0,
            speed_ms: 4.0,
            action: "HOVER_PANORAMA_360",
            task_config: { type: "Giro Panorámico Estabilizado 360°", duration_sec: 20, rotation_deg_per_sec: 18 }
        },
        {
            wp_num: 5,
            lat: -33.4372,
            lng: -70.6506,
            alt: 0.0,
            speed_ms: 3.0,
            action: "RETURN_TO_HOME_LAND",
            task_config: { type: "Aterrizaje Autónomo Precisión RTK", precision_pad_detection: true }
        }
    ];

    renderRoute();
    renderWaypointsList();
}

function initWaypointTaskSelector() {
    const selector = document.getElementById('taskTypeSelect');
    if (!selector) return;
}

// Form Handlers (Save Mission to MongoDB)
function initFormHandlers() {
    const saveBtn = document.getElementById('btnSaveMission');
    if (!saveBtn) return;

    saveBtn.addEventListener('click', async () => {
        if (plannedWaypoints.length < 2) {
            alert('Por favor añade al menos 2 waypoints para formar una ruta de misión.');
            return;
        }

        const missionName = document.getElementById('inputMissionName').value || 'Misión Industrial RBG';
        const sector = document.getElementById('selectSector').value;
        const droneId = document.getElementById('selectDrone').value;
        const totalDist = parseInt(document.getElementById('metricDistance').textContent) || 2000;
        const estTime = parseInt(document.getElementById('metricEstTime').textContent) || 20;

        const payload = {
            name: missionName,
            sector: sector,
            assigned_drone_id: droneId,
            estimated_duration_min: estTime,
            total_distance_m: totalDist,
            safety_altitude_m: 45.0,
            created_by: 'Operador de Vuelo',
            waypoints: plannedWaypoints
        };

        saveBtn.disabled = true;
        saveBtn.textContent = 'Programando misión...';

        try {
            const res = await fetch('/api/missions/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const result = await res.json();
            if (res.ok) {
                alert(`Misión ${result.mission.mission_id} programada y guardada exitosamente.`);
                activeMissionId = result.mission.mission_id;
                location.reload();
            } else {
                alert('Error al guardar: ' + (result.error || 'Desconocido'));
            }
        } catch (e) {
            alert('Error en conexión: ' + e);
        } finally {
            saveBtn.disabled = false;
            saveBtn.textContent = 'Guardar y Programar Misión';
        }
    });

    const resetBtn = document.getElementById('btnResetRoute');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            plannedWaypoints = [];
            renderRoute();
            renderWaypointsList();
        });
    }

    const defaultRouteBtn = document.getElementById('btnSampleRoute');
    if (defaultRouteBtn) {
        defaultRouteBtn.addEventListener('click', () => {
            resetToSampleRoute();
        });
    }

    const startSimBtn = document.getElementById('btnStartSimulation');
    const pauseSimBtn = document.getElementById('btnPauseSimulation');
    const stepSimBtn = document.getElementById('btnStepSimulation');

    if (startSimBtn) {
        startSimBtn.addEventListener('click', startSimulation);
    }
    if (pauseSimBtn) {
        pauseSimBtn.addEventListener('click', pauseSimulation);
    }
    if (stepSimBtn) {
        stepSimBtn.addEventListener('click', () => stepSimulation(true));
    }
}

function loadActiveMissionSelector() {
    const sel = document.getElementById('activeMissionSelect');
    if (!sel) return;

    activeMissionId = sel.value;
    sel.addEventListener('change', () => {
        activeMissionId = sel.value;
        loadMissionToMap(activeMissionId);
    });

    if (activeMissionId) {
        loadMissionToMap(activeMissionId);
    }
}

async function loadMissionToMap(missionId) {
    if (!missionId) return;
    try {
        const res = await fetch(`/api/missions/${missionId}/`);
        if (!res.ok) return;
        const data = await res.json();
        const m = data.mission;
        if (m && m.waypoints && m.waypoints.length > 0) {
            plannedWaypoints = m.waypoints;
            renderRoute();
            renderWaypointsList();
            if (plannedWaypoints[0]) {
                operatorMap.setView([plannedWaypoints[0].lat, plannedWaypoints[0].lng], 14);
            }
        }
    } catch (e) {
        console.error('Error loading mission: ', e);
    }
}

function startSimulation() {
    if (!activeMissionId) {
        alert('Por favor selecciona una misión para ejecutar.');
        return;
    }

    if (isSimulationRunning) return;
    isSimulationRunning = true;

    const startBtn = document.getElementById('btnStartSimulation');
    if (startBtn) {
        startBtn.textContent = 'Transmitiendo...';
    }

    stepSimulation(false);
    simulationInterval = setInterval(() => {
        stepSimulation(false);
    }, 2500);
}

function pauseSimulation() {
    isSimulationRunning = false;
    if (simulationInterval) {
        clearInterval(simulationInterval);
        simulationInterval = null;
    }
    const startBtn = document.getElementById('btnStartSimulation');
    if (startBtn) {
        startBtn.textContent = 'Iniciar Vuelo';
    }
}

async function stepSimulation(isManualStep = false) {
    if (!activeMissionId) return;

    currentTick++;

    try {
        const res = await fetch(`/api/missions/${activeMissionId}/simulate-step/?step=${currentTick}`, {
            method: 'POST'
        });

        if (!res.ok) {
            pauseSimulation();
            return;
        }

        const packet = await res.json();
        updateHUDCockpit(packet);
        updateDroneMarker(packet);
        appendTelemetryLog(packet);

        if (packet.fraction_complete >= 100) {
            pauseSimulation();
            if (typeof showMissionSummaryModal === 'function') {
                showMissionSummaryModal(packet);
            }
        }
    } catch (e) {
        console.error('Simulation step error:', e);
        if (!isManualStep) pauseSimulation();
    }
}

function updateHUDCockpit(p) {
    if (!p) return;

    const speedKm = p.flight_dynamics ? p.flight_dynamics.speed_kmh : 0;
    const speedValEl = document.getElementById('hudSpeedVal');
    if (speedValEl) speedValEl.textContent = speedKm;

    const altM = p.gps ? p.gps.altitude_m : 0;
    const altValEl = document.getElementById('hudAltVal');
    if (altValEl) altValEl.textContent = altM;

    const batt = p.power ? p.power.battery_pct : 100;
    const battValEl = document.getElementById('hudBatteryVal');
    const battBar = document.getElementById('hudBatteryBar');
    if (battValEl) battValEl.textContent = batt;
    if (battBar) {
        battBar.style.width = `${batt}%`;
    }

    const tempC = p.diagnostics ? p.diagnostics.motor_temp_c : 30;
    const tempValEl = document.getElementById('hudTempVal');
    if (tempValEl) tempValEl.textContent = tempC;

    const pitch = p.flight_dynamics ? p.flight_dynamics.pitch_deg : 0;
    const roll = p.flight_dynamics ? p.flight_dynamics.roll_deg : 0;
    const horizonBox = document.getElementById('attitudeGyro');
    if (horizonBox) {
        horizonBox.style.transform = `rotate(${roll}deg) translateY(${pitch * 1.5}px)`;
    }

    const actionEl = document.getElementById('hudCurrentAction');
    if (actionEl && p.current_action) {
        actionEl.textContent = p.current_action;
    }
}

// Clean Monochrome Aircraft Marker on Leaflet
function updateDroneMarker(p) {
    if (!operatorMap || !p.gps) return;
    const lat = p.gps.lat;
    const lng = p.gps.lng;

    const droneIcon = L.divIcon({
        className: 'live-drone-icon',
        html: `
            <div style="width:26px;height:26px;background:#111827;border:2px solid #ffffff;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#ffffff;box-shadow:0 2px 6px rgba(0,0,0,0.35);">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/></svg>
            </div>
        `,
        iconSize: [26, 26],
        iconAnchor: [13, 13]
    });

    if (!droneMarker) {
        droneMarker = L.marker([lat, lng], { icon: droneIcon }).addTo(operatorMap);
    } else {
        droneMarker.setLatLng([lat, lng]);
    }

    droneMarker.bindPopup(`
        <div style="color:#111827;font-family:sans-serif;font-size:12px;">
            <b>Drone en Vuelo</b><br>
            <b>Tarea:</b> ${p.current_action || 'Navegación'}<br>
            <b>Altitud:</b> ${p.gps.altitude_m} m | <b>Batería:</b> ${p.power.battery_pct}%<br>
            <b>Timestamp:</b> ${p.timestamp}
        </div>
    `);

    if (!operatorMap.getBounds().contains([lat, lng])) {
        operatorMap.panTo([lat, lng]);
    }
}

// Append Telemetry Burst to Table
function appendTelemetryLog(p) {
    const tableBody = document.getElementById('liveTelemetryTableBody');
    if (!tableBody) return;

    const timeStr = new Date(p.timestamp).toLocaleTimeString('es-CL');
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td style="font-family:monospace;color:#111827;">${timeStr}</td>
        <td><span class="panel-badge" style="font-size:0.68rem;">${p.current_action || 'WAYPOINT'}</span></td>
        <td style="font-family:monospace;">${p.gps.lat.toFixed(5)}, ${p.gps.lng.toFixed(5)}</td>
        <td style="font-family:monospace;">${p.gps.altitude_m} m</td>
        <td style="font-family:monospace;">${p.flight_dynamics.speed_kmh} km/h</td>
        <td style="font-family:monospace;font-weight:600;">${p.power.battery_pct}%</td>
        <td style="font-family:monospace;">${p.diagnostics.motor_temp_c}°C</td>
    `;

    tableBody.insertBefore(tr, tableBody.firstChild);

    while (tableBody.children.length > 15) {
        tableBody.removeChild(tableBody.lastChild);
    }
}
