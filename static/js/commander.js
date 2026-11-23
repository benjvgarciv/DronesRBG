/**
 * Drones RBG - Fleet Commander & Auditor Hub Logic (High-Contrast White & Black Edition)
 * Chart.js telemetry visualization optimized for crisp white panels.
 */

let batteryChartInstance = null;
let diagnosticChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    initMissionSelector();
    initChartRenderer();
});

function initMissionSelector() {
    const selector = document.getElementById('auditorMissionSelector');
    if (!selector) return;

    selector.addEventListener('change', () => {
        const missionId = selector.value;
        if (missionId) {
            window.location.href = `/commander/?mission_id=${missionId}`;
        }
    });
}

function initChartRenderer() {
    const chartDataElement = document.getElementById('auditChartDataJson');
    if (!chartDataElement) return;

    let auditData;
    try {
        auditData = JSON.parse(chartDataElement.textContent);
    } catch (e) {
        console.error('Failed to parse audit data JSON:', e);
        return;
    }

    if (!auditData || !auditData.chart_data || auditData.chart_data.timestamps.length === 0) {
        console.warn('No time-series telemetry data available for charts.');
        return;
    }

    renderBatteryVsConditionsChart(auditData.chart_data);
    renderDiagnosticPowerChart(auditData.chart_data);
}

// Chart 1: Battery Consumption (%) vs Speed (km/h) & Altitude (m)
function renderBatteryVsConditionsChart(data) {
    const ctx = document.getElementById('batteryVsConditionsChart');
    if (!ctx) return;

    if (batteryChartInstance) {
        batteryChartInstance.destroy();
    }

    batteryChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.timestamps,
            datasets: [
                {
                    label: 'Nivel de Batería (%)',
                    data: data.battery,
                    borderColor: '#111827',
                    backgroundColor: 'rgba(17, 24, 39, 0.04)',
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.2,
                    yAxisID: 'yBattery',
                    pointRadius: 1,
                    pointHoverRadius: 4
                },
                {
                    label: 'Velocidad (km/h)',
                    data: data.speed,
                    borderColor: '#4b5563',
                    borderWidth: 1.8,
                    borderDash: [4, 4],
                    fill: false,
                    tension: 0.2,
                    yAxisID: 'ySpeedAlt',
                    pointRadius: 1,
                    pointHoverRadius: 4
                },
                {
                    label: 'Altitud (m)',
                    data: data.altitude,
                    borderColor: '#9ca3af',
                    borderWidth: 1.8,
                    borderDash: [2, 2],
                    fill: false,
                    tension: 0.2,
                    yAxisID: 'ySpeedAlt',
                    pointRadius: 1,
                    pointHoverRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#111827',
                        font: { family: 'Inter', size: 11, weight: '600' },
                        boxWidth: 14
                    }
                },
                tooltip: {
                    backgroundColor: '#000000',
                    titleColor: '#ffffff',
                    bodyColor: '#e5e7eb',
                    borderColor: '#374151',
                    borderWidth: 1,
                    padding: 8,
                    titleFont: { family: 'JetBrains Mono', size: 11 },
                    bodyFont: { family: 'JetBrains Mono', size: 11 }
                }
            },
            scales: {
                x: {
                    grid: { color: '#f3f4f6' },
                    ticks: { color: '#6b7280', font: { family: 'JetBrains Mono', size: 10 }, maxTicksLimit: 12 }
                },
                yBattery: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    min: 0,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Batería (%)',
                        color: '#111827',
                        font: { family: 'Inter', size: 10, weight: 'bold' }
                    },
                    grid: { color: '#f3f4f6' },
                    ticks: { color: '#111827', font: { family: 'JetBrains Mono', size: 10 } }
                },
                ySpeedAlt: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Velocidad (km/h) / Altitud (m)',
                        color: '#4b5563',
                        font: { family: 'Inter', size: 10, weight: 'bold' }
                    },
                    grid: { drawOnChartArea: false },
                    ticks: { color: '#4b5563', font: { family: 'JetBrains Mono', size: 10 } }
                }
            }
        }
    });
}

// Chart 2: Instantaneous Power (Watts) vs Motor Temperature (°C)
function renderDiagnosticPowerChart(data) {
    const ctx = document.getElementById('diagnosticPowerChart');
    if (!ctx) return;

    if (diagnosticChartInstance) {
        diagnosticChartInstance.destroy();
    }

    diagnosticChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.timestamps,
            datasets: [
                {
                    label: 'Potencia Consumida (Watts)',
                    data: data.power_w,
                    borderColor: '#111827',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.2,
                    yAxisID: 'yPower',
                    pointRadius: 1
                },
                {
                    label: 'Temperatura Motor (°C)',
                    data: data.motor_temp,
                    borderColor: '#6b7280',
                    borderWidth: 1.8,
                    borderDash: [3, 3],
                    fill: false,
                    tension: 0.2,
                    yAxisID: 'yTemp',
                    pointRadius: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: { color: '#111827', font: { family: 'Inter', size: 11, weight: '600' }, boxWidth: 14 }
                },
                tooltip: {
                    backgroundColor: '#000000',
                    titleColor: '#ffffff',
                    bodyColor: '#e5e7eb',
                    borderColor: '#374151',
                    borderWidth: 1,
                    titleFont: { family: 'JetBrains Mono', size: 11 },
                    bodyFont: { family: 'JetBrains Mono', size: 11 }
                }
            },
            scales: {
                x: {
                    grid: { color: '#f3f4f6' },
                    ticks: { color: '#6b7280', font: { family: 'JetBrains Mono', size: 10 }, maxTicksLimit: 12 }
                },
                yPower: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Potencia (Watts)',
                        color: '#111827',
                        font: { family: 'Inter', size: 10, weight: 'bold' }
                    },
                    grid: { color: '#f3f4f6' },
                    ticks: { color: '#111827', font: { family: 'JetBrains Mono', size: 10 } }
                },
                yTemp: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Temperatura (°C)',
                        color: '#4b5563',
                        font: { family: 'Inter', size: 10, weight: 'bold' }
                    },
                    grid: { drawOnChartArea: false },
                    ticks: { color: '#4b5563', font: { family: 'JetBrains Mono', size: 10 } }
                }
            }
        }
    });
}
