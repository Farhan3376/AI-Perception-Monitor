// CV Monitor Pro - Frontend JS

document.addEventListener("DOMContentLoaded", () => {
    initApp();
});

let chartInstance = null;

async function initApp() {
    // Determine base URLs relative to where the dashboard was loaded
    const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
    const host = window.location.host; // e.g., localhost:8000
    const WSS_BASE = `${protocol}${host}`;
    const API_BASE = `${window.location.protocol}//${host}/api`;

    // 1. Fetch Cameras and setup websockets
    try {
        const res = await fetch(`${API_BASE}/cameras`);
        const cameras = await res.json();
        setupCameras(cameras, WSS_BASE);
        setConnectionState(true);
    } catch (e) {
        setConnectionState(false);
        console.error("Failed to load cameras", e);
    }

    // 2. Load Alerts
    loadAlerts(API_BASE);
    setInterval(() => loadAlerts(API_BASE), 5000); // Poll every 5s

    // 3. Setup Chart
    setupChart();
}

function setConnectionState(isConnected) {
    const dot = document.getElementById("connection-dot");
    const txt = document.getElementById("connection-text");
    if (isConnected) {
        dot.className = "dot green";
        txt.textContent = "API Connected";
    } else {
        dot.className = "dot red";
        txt.textContent = "API Disconnected";
    }
}

// ── Cameras ─────────────────────────────────────────────────────────────
function setupCameras(cameras, wssBase) {
    const grid = document.getElementById("camera-grid");
    grid.innerHTML = "";

    cameras.forEach(cam => {
        // Create UI Card
        const tile = document.createElement("div");
        tile.className = "camera-tile";

        const img = document.createElement("img");
        img.id = `img-${cam.id}`;
        img.alt = `Live Feed: ${cam.name}`;

        const overlay = document.createElement("div");
        overlay.className = "tile-overlay";
        overlay.innerHTML = `
            <span>${cam.name}</span>
            <span id="fps-${cam.id}">0.0 FPS</span>
        `;

        tile.appendChild(img);
        tile.appendChild(overlay);
        grid.appendChild(tile);

        // Connect WebSocket
        const wsUrl = `${wssBase}/ws/stream/${cam.id}`;
        const ws = new WebSocket(wsUrl);
        // Ensure binary data is read as Blob
        ws.binaryType = "blob";

        ws.onopen = () => console.log(`[WS] Connected to ${cam.id}`);
        
        ws.onmessage = async (event) => {
            // event.data is a Blob containing the JPEG bytes
            if (event.data instanceof Blob) {
                // Read the blob into an object URL and assign it directly to the img src
                const url = URL.createObjectURL(event.data);
                
                // Keep a reference to the old URL so we can revoke it and prevent memory leaks
                const oldUrl = img.src;
                img.src = url;
                
                // Give browser a frame to paint before destroying the old blob
                if (oldUrl && oldUrl.startsWith("blob:")) {
                    setTimeout(() => URL.revokeObjectURL(oldUrl), 10);
                }

                document.getElementById(`fps-${cam.id}`).textContent = "LIVE";
            }
        };

        ws.onerror = (e) => console.error(`[WS Error] ${cam.id}`, e);
        ws.onclose = () => {
            document.getElementById(`fps-${cam.id}`).textContent = "OFFLINE";
            document.getElementById(`fps-${cam.id}`).style.color = "var(--danger)";
        };
    });
}

// ── Alerts Table ────────────────────────────────────────────────────────
async function loadAlerts(apiBase) {
    try {
        const res = await fetch(`${apiBase}/alerts?limit=10`);
        const alerts = await res.json();
        
        const tbody = document.getElementById("alerts-table-body");
        tbody.innerHTML = "";

        alerts.forEach(a => {
            const tr = document.createElement("tr");
            
            // Format time
            const d = new Date(a.timestamp);
            const timeStr = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            
            // Badge color
            let badgeClass = "bg-info";
            if (a.severity === "warning") badgeClass = "bg-warning";
            if (a.severity === "critical" || a.severity === "danger") badgeClass = "bg-danger";

            tr.innerHTML = `
                <td>${timeStr}</td>
                <td>${a.camera_id}</td>
                <td><span class="badge ${badgeClass}">${a.alert_type}</span></td>
                <td>${a.severity}</td>
                <td style="color: var(--text-main);">${a.message}</td>
            `;
            tbody.appendChild(tr);
        });
        
        // Update Chart data roughly based on alerts for simplicity in this demo
        updateChartDemo(alerts);
        
    } catch (e) {
        console.error("Alerts fetch error", e);
    }
}

// ── Chart.js ────────────────────────────────────────────────────────────
function setupChart() {
    const ctx = document.getElementById('detChart').getContext('2d');
    
    // Chart defaults
    Chart.defaults.color = "#a1a1aa";
    Chart.defaults.font.family = "inherit";

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['10m ago', '8m ago', '6m ago', '4m ago', '2m ago', 'Now'],
            datasets: [{
                label: 'Events / Min',
                data: [0, 0, 0, 0, 0, 0],
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: '#27272a' },
                    ticks: { precision: 0 }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

function updateChartDemo(alerts) {
    // Mocking chart data based on loaded alerts just for visual feedback.
    // In a real app, you'd fetch /api/events and bucket them by timestamp.
    if (!chartInstance) return;
    
    // Shift data left
    const d = chartInstance.data.datasets[0].data;
    d.shift();
    // Add random jitter to simulate live traffic, boosted if there are recent alerts
    const base = alerts.length > 0 ? 5 : 1;
    d.push(Math.floor(Math.random() * 4) + base);
    
    chartInstance.update();
}
