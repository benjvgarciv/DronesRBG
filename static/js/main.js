/**
 * Drones RBG - Global Aerospace HUD Logic & Utilities
 */

document.addEventListener('DOMContentLoaded', () => {
    initClock();
    initMongoHeartbeat();
});

// Digital Aerospace Mission Control Clock
function initClock() {
    const clockEl = document.getElementById('hudClockText');
    if (!clockEl) return;

    function update() {
        const now = new Date();
        const utcHours = String(now.getUTCHours()).padStart(2, '0');
        const utcMinutes = String(now.getUTCMinutes()).padStart(2, '0');
        const utcSeconds = String(now.getUTCSeconds()).padStart(2, '0');
        const localTime = now.toLocaleTimeString('es-CL', { hour12: false });
        clockEl.textContent = `${utcHours}:${utcMinutes}:${utcSeconds} UTC • ${localTime} LOC`;
    }
    update();
    setInterval(update, 1000);
}

// Periodic Ping to MongoDB Status
function initMongoHeartbeat() {
    const statusPill = document.getElementById('mongoStatusPill');
    if (!statusPill) return;

    async function checkStatus() {
        try {
            const res = await fetch('/api/status/');
            if (!res.ok) return;
            const data = await res.json();
            
            const dot = statusPill.querySelector('.pulse-dot');
            const text = statusPill.querySelector('.status-text');

            if (data.is_mock) {
                if (dot) { dot.className = 'pulse-dot warning'; }
                if (text) { text.textContent = 'Modo Simulado (In-Memory)'; }
            } else {
                if (dot) { dot.className = 'pulse-dot success'; }
                if (text) { text.textContent = 'Servidor Conectado'; }
            }
        } catch (e) {
            console.warn('[Heartbeat] Connection check failed:', e);
        }
    }
    // Check every 25 seconds
    setInterval(checkStatus, 25000);
}

// Global Copy Helper
function copyTextToClipboard(text, feedbackBtn) {
    navigator.clipboard.writeText(text).then(() => {
        if (feedbackBtn) {
            const original = feedbackBtn.innerHTML;
            feedbackBtn.innerHTML = '✓ ¡Copiado!';
            feedbackBtn.style.color = '#10b981';
            setTimeout(() => {
                feedbackBtn.innerHTML = original;
                feedbackBtn.style.color = '';
            }, 2000);
        }
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
}
