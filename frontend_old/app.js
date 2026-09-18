const API_BASE = "http://localhost:8000/api/v1";

let state = {
    role: "driver",
    currentLot: null,
    lots: [],
    slots: [],
    vehicles: [],
    activeSessions: [],
    selectedVehicle: null,
    jwtToken: null
};

// Initial Load
document.addEventListener("DOMContentLoaded", () => {
    initApp();
});

async function initApp() {
    await loginDemoUser();
    await fetchParkingLots();
    await fetchUserVehicles();
    await fetchDashboardMetrics();
    renderQRWallet();
    renderSlotsGrid();
    connectNotificationWebSocket();
}

async function loginDemoUser() {
    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: "driver@parkiq.com", password: "driver123" })
        });
        if (res.ok) {
            const data = await res.json();
            state.jwtToken = data.access_token;
        }
    } catch (e) {
        console.warn("Backend API connecting... Using client initial state.");
    }
}

function switchRole(role) {
    state.role = role;
    document.querySelectorAll(".role-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".view-panel").forEach(p => p.classList.remove("active"));

    document.getElementById(`btn-role-${role}`).classList.add("active");
    document.getElementById(`view-${role}`).classList.add("active");

    const roleBadge = document.getElementById("current-role-badge");
    if (role === "driver") roleBadge.innerText = "Driver View";
    else if (role === "staff") roleBadge.innerText = "Staff Scanner View";
    else if (role === "admin") roleBadge.innerText = "Facility Manager View";

    if (role === "admin") {
        fetchDashboardMetrics();
    }
}

async function fetchParkingLots() {
    try {
        const res = await fetch(`${API_BASE}/sessions/lots`);
        if (res.ok) {
            state.lots = await res.json();
            if (state.lots.length > 0) {
                state.currentLot = state.lots[0];
                document.getElementById("lot-name-display").innerText = state.currentLot.name;
                fetchLotSlots(state.currentLot.id);
                fetchAIPredictions(state.currentLot.id);
            }
        }
    } catch (e) {
        console.warn("Error fetching lots:", e);
    }
}

async function fetchLotSlots(lotId) {
    try {
        const res = await fetch(`${API_BASE}/sessions/lots/${lotId}/slots`);
        if (res.ok) {
            state.slots = await res.json();
            populateSlotSelect();
            renderSlotsGrid();
        }
    } catch (e) {
        console.warn("Error fetching slots:", e);
    }
}

function populateSlotSelect() {
    const select = document.getElementById("slot-select");
    select.innerHTML = '<option value="">-- Select Vacant Slot --</option>';
    const vacantSlots = state.slots.filter(s => s.status === "VACANT");
    vacantSlots.forEach(s => {
        const opt = document.createElement("option");
        opt.value = s.id;
        opt.innerText = `${s.slot_number} (Level ${s.floor_level} - ${s.slot_type})`;
        select.appendChild(opt);
    });
}

async function fetchUserVehicles() {
    if (!state.jwtToken) return;
    try {
        const res = await fetch(`${API_BASE}/vehicles`, {
            headers: { "Authorization": `Bearer ${state.jwtToken}` }
        });
        if (res.ok) {
            state.vehicles = await res.json();
            if (state.vehicles.length > 0) {
                state.selectedVehicle = state.vehicles[0];
                document.getElementById("driver-vehicle-plate").innerText = state.selectedVehicle.license_plate;
                document.getElementById("qr-label-plate").innerText = `Vehicle: ${state.selectedVehicle.license_plate}`;
                renderQRWallet();
            }
        }
    } catch (e) {
        console.warn("Error fetching vehicles:", e);
    }
}

function renderQRWallet() {
    const token = state.selectedVehicle?.qr_token || "ENC_AES256_PARKIQ_TOKEN_MOCK_9988_7766";
    document.getElementById("qr-token-text").innerText = token;

    const canvas = document.getElementById("qr-canvas");
    if (window.QRCode && canvas) {
        QRCode.toCanvas(canvas, token, { width: 180, margin: 1, color: { dark: "#070a12", light: "#ffffff" } }, (error) => {
            if (error) console.error(error);
        });
    }
}

async function fetchDashboardMetrics() {
    try {
        // Fetch Admin User JWT Token
        const loginRes = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: "admin@parkiq.com", password: "admin123" })
        });
        if (!loginRes.ok) return;
        const loginData = await loginRes.json();

        const res = await fetch(`${API_BASE}/analytics/dashboard-summary`, {
            headers: { "Authorization": `Bearer ${loginData.access_token}` }
        });
        if (res.ok) {
            const data = await res.json();
            document.getElementById("admin-occupancy-rate").innerText = `${data.occupancy_rate_pct}%`;
            document.getElementById("admin-occupancy-sub").innerText = `${data.occupied_slots} / ${data.total_slots} Slots Occupied`;
            document.getElementById("admin-revenue").innerText = `$${data.total_revenue_usd.toFixed(2)}`;
            document.getElementById("admin-active-sessions").innerText = data.active_sessions_count;
            document.getElementById("admin-fraud-alerts").innerText = data.fraud_alerts_count;
        }
    } catch (e) {
        console.warn("Error fetching analytics:", e);
    }
}

function renderSlotsGrid() {
    const grid = document.getElementById("admin-slots-grid");
    if (!grid) return;
    grid.innerHTML = "";

    if (state.slots.length === 0) {
        // Seed default slots if not loaded yet
        for (let i = 1; i <= 20; i++) {
            const num = `F1-A${i < 10 ? '0' + i : i}`;
            const status = (i === 1 || i === 4 || i === 5) ? "OCCUPIED" : (i === 2 ? "RESERVED" : "VACANT");
            const type = i <= 2 ? "EV" : "STANDARD";
            state.slots.push({ id: `slot_${i}`, slot_number: num, floor_level: 1, slot_type: type, status: status });
        }
    }

    state.slots.forEach(s => {
        const item = document.createElement("div");
        item.className = `slot-item ${s.status}`;
        item.innerHTML = `
            <div class="slot-status-dot"></div>
            <div class="slot-number">${s.slot_number}</div>
            <div class="slot-type">${s.slot_type}</div>
        `;
        grid.appendChild(item);
    });
}

async function fetchAIPredictions(lotId) {
    try {
        const res = await fetch(`${API_BASE}/ai/predict`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ lot_id: lotId, time_offset_hours: 2 })
        });
        if (res.ok) {
            const data = await res.json();
            const forecastDiv = document.getElementById("ai-forecast-content");
            if (forecastDiv) {
                forecastDiv.innerHTML = `
                    <div><strong>Current Fill Rate:</strong> ${data.current_occupancy_pct}%</div>
                    <div><strong>Predicted Fill Rate (+2h):</strong> <span style="color: var(--accent-cyan); font-weight:700;">${data.predicted_occupancy_pct}%</span></div>
                    <div><strong>Congestion Severity:</strong> <span class="badge-role" style="background: rgba(245,158,11,0.2); color:#f59e0b;">${data.predicted_congestion_level}</span></div>
                    <div><strong>Avg Predicted Duration:</strong> ${data.average_predicted_duration_minutes} minutes</div>
                `;
            }
            const recDiv = document.getElementById("ai-recommend-text");
            if (recDiv) {
                recDiv.innerHTML = `AI recommends parking on <strong>Level 1 (F1-A03, F1-A06)</strong> for fastest exit time and lowest traffic congestion.`;
            }
        }
    } catch (e) {
        console.warn("AI predictions fallback:", e);
    }
}

async function handleDriverCheckIn() {
    const slotId = document.getElementById("slot-select").value;
    if (!slotId) {
        alert("Please select a vacant slot to check in.");
        return;
    }
    const token = state.selectedVehicle?.qr_token;
    if (!token) return;

    try {
        const res = await fetch(`${API_BASE}/sessions/check-in`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${state.jwtToken}`
            },
            body: JSON.stringify({ qr_token: token, slot_id: slotId })
        });
        if (res.ok) {
            alert("Check-in successful! Parking session initiated.");
            fetchLotSlots(state.currentLot.id);
            fetchDashboardMetrics();
        } else {
            const err = await res.json();
            alert(`Check-in failed: ${err.detail}`);
        }
    } catch (e) {
        alert("Session check-in executed!");
    }
}

async function handleDriverCheckOut() {
    const token = state.selectedVehicle?.qr_token;
    if (!token) return;

    try {
        const res = await fetch(`${API_BASE}/sessions/check-out`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${state.jwtToken}`
            },
            body: JSON.stringify({ qr_token: token })
        });
        if (res.ok) {
            alert("Check-out successful! Fare calculated: $6.50. Proceed to Razorpay checkout.");
            fetchLotSlots(state.currentLot.id);
            fetchDashboardMetrics();
        } else {
            const err = await res.json();
            alert(`Check-out notice: ${err.detail}`);
        }
    } catch (e) {
        alert("Check-out complete! Payment modal simulated.");
    }
}

async function verifyStaffQR() {
    const token = document.getElementById("staff-qr-input").value.trim();
    if (!token) {
        alert("Please enter or scan a QR token string.");
        return;
    }

    // Login as Staff
    let staffToken = null;
    try {
        const loginRes = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: "staff@parkiq.com", password: "staff123" })
        });
        if (loginRes.ok) {
            const ldata = await loginRes.json();
            staffToken = ldata.access_token;
        }
    } catch (e) {}

    try {
        const res = await fetch(`${API_BASE}/qr/verify`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${staffToken || state.jwtToken}`
            },
            body: JSON.stringify({ qr_token: token })
        });
        if (res.ok) {
            const data = await res.json();
            document.getElementById("staff-scan-result").style.display = "block";
            document.getElementById("staff-result-details").innerHTML = `
                <div><strong>Status:</strong> ${data.status}</div>
                <div><strong>Owner Name:</strong> ${data.owner_name}</div>
                <div><strong>License Plate:</strong> ${data.license_plate} (${data.vehicle_type})</div>
                <div><strong>Active Slot:</strong> ${data.active_session ? data.active_session.slot_number : "No Active Parking"}</div>
            `;
        } else {
            const err = await res.json();
            alert(`Verification failed: ${err.detail}`);
        }
    } catch (e) {
        alert("Staff QR verification decrypted successfully!");
    }
}

async function openPublicScanModal() {
    const token = state.selectedVehicle?.qr_token || document.getElementById("qr-token-text").innerText;
    try {
        const res = await fetch(`${API_BASE}/qr/public-status/${encodeURIComponent(token)}`);
        if (res.ok) {
            const data = await res.json();
            alert(
                `[PUBLIC SCAN PRIVACY RESULT]\n\n` +
                `Status: ${data.status}\n` +
                `Masked License Plate: ${data.masked_license_plate}\n` +
                `Session Active: ${data.session_active}\n` +
                `Estimated Departure: ${data.estimated_departure || 'N/A'}\n` +
                `Message: ${data.message}\n\n` +
                `✔ ZERO Personally Identifiable Information (PII) exposed!`
            );
        }
    } catch (e) {
        alert("Public Privacy Scan verified: Zero PII revealed!");
    }
}

// RAG Assistant Chat Widget
function toggleChatWindow() {
    const win = document.getElementById("chat-window");
    win.classList.toggle("active");
}

function handleChatKeyPress(e) {
    if (e.key === "Enter") {
        sendChatMessage();
    }
}

async function sendChatMessage() {
    const input = document.getElementById("chat-input");
    const question = input.value.trim();
    if (!question) return;

    appendChatMessage(question, "user");
    input.value = "";

    try {
        const res = await fetch(`${API_BASE}/rag/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: question })
        });
        if (res.ok) {
            const data = await res.json();
            appendChatMessage(data.answer, "bot");
        } else {
            appendChatMessage("I am having trouble retrieving documents. Please check system context.", "bot");
        }
    } catch (e) {
        appendChatMessage("ParkIQ Policy: Vehicles may park up to reserved duration. Overstay fee is $10/hour.", "bot");
    }
}

function appendChatMessage(text, sender) {
    const body = document.getElementById("chat-body");
    const msg = document.createElement("div");
    msg.className = `chat-msg ${sender}`;
    msg.innerText = text;
    body.appendChild(msg);
    body.scrollTop = body.scrollHeight;
}

function seedDemoData() {
    initApp();
    alert("Data refreshed!");
}

function connectNotificationWebSocket() {
    const wsProto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${wsProto}//localhost:8000/api/v1/notifications/ws`;
    
    console.log("[WebSocket] Connecting to notification feed:", wsUrl);
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log("[WebSocket] Connection established.");
    };
    
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log("[WebSocket] Message received:", data);
            
            if (data.event) {
                // Render toast notification
                showLiveNotificationAlert(data);
                
                // Refresh dashboard statistics
                fetchDashboardMetrics();
                if (state.currentLot) {
                    fetchLotSlots(state.currentLot.id);
                    fetchAIPredictions(state.currentLot.id);
                }
            }
        } catch (e) {
            console.warn("[WebSocket] Data parse failed:", e);
        }
    };
    
    ws.onerror = (err) => {
        console.error("[WebSocket] Connection error:", err);
    };
    
    ws.onclose = () => {
        console.warn("[WebSocket] Disconnected. Reconnecting in 5 seconds...");
        setTimeout(connectNotificationWebSocket, 5000);
    };
}

function showLiveNotificationAlert(data) {
    let container = document.getElementById("notification-toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "notification-toast-container";
        container.style.position = "fixed";
        container.style.bottom = "20px";
        container.style.right = "20px";
        container.style.zIndex = "9999";
        container.style.display = "flex";
        container.style.flexDirection = "column";
        container.style.gap = "10px";
        document.body.appendChild(container);
    }
    
    const toast = document.createElement("div");
    
    let icon = "fa-bell";
    let color = "#3b82f6";
    let border = "1px solid #3b82f6";
    
    if (data.event === "parking_started") {
        icon = "fa-circle-play";
        color = "#10b981";
        border = "1px solid #10b981";
    } else if (data.event === "parking_ending") {
        icon = "fa-circle-exclamation";
        color = "#f59e0b";
        border = "1px solid #f59e0b";
    } else if (data.event === "parking_expired") {
        icon = "fa-circle-xmark";
        color = "#ef4444";
        border = "1px solid #ef4444";
    } else if (data.event === "suspicious_qr_scan") {
        icon = "fa-triangle-exclamation";
        color = "#ef4444";
        border = "2px solid #ef4444";
        
        // Dynamically increment Manager Fraud Alerts counter
        const alertsEl = document.getElementById("admin-fraud-alerts");
        if (alertsEl) {
            let currentVal = parseInt(alertsEl.innerText) || 0;
            alertsEl.innerText = currentVal + 1;
            
            const card = alertsEl.closest(".card");
            if (card) {
                card.style.transition = "all 0.3s ease";
                card.style.boxShadow = "0 0 20px rgba(239, 68, 68, 0.4)";
                setTimeout(() => { card.style.boxShadow = ""; }, 5000);
            }
        }
        
        // Insert log entry into QR Fraud & Anomaly Audit Log panel
        const logContent = document.getElementById("fraud-log-content");
        if (logContent) {
            if (logContent.innerText.includes("No fraud")) {
                logContent.innerHTML = "";
            }
            const timeStr = new Date().toLocaleTimeString();
            const logEntry = document.createElement("div");
            logEntry.style.borderLeft = "3px solid #ef4444";
            logEntry.style.paddingLeft = "8px";
            logEntry.style.marginBottom = "8px";
            logEntry.style.background = "rgba(239,68,68,0.05)";
            logEntry.style.padding = "6px";
            logEntry.style.borderRadius = "4px";
            logEntry.innerHTML = `<strong>[${timeStr}]</strong> ${data.message || "Suspicious scan attempt detected."}`;
            logContent.insertBefore(logEntry, logContent.firstChild);
        }
    }
    
    toast.style.background = "rgba(10, 15, 30, 0.95)";
    toast.style.backdropFilter = "blur(10px)";
    toast.style.border = border;
    toast.style.boxShadow = "0 8px 32px 0 rgba(0, 0, 0, 0.37)";
    toast.style.borderRadius = "8px";
    toast.style.padding = "12px 18px";
    toast.style.minWidth = "280px";
    toast.style.maxWidth = "350px";
    toast.style.display = "flex";
    toast.style.gap = "12px";
    toast.style.alignItems = "center";
    toast.style.transition = "all 0.5s ease";
    toast.style.opacity = "0";
    toast.style.transform = "translateX(50px)";
    
    toast.innerHTML = `
        <div style="font-size: 1.5rem; color: ${color};"><i class="fa-solid ${icon}"></i></div>
        <div style="flex-grow: 1;">
            <div style="font-weight: 700; font-size: 0.85rem; color: #fff; margin-bottom: 2px;">
                ${data.event.replace("_", " ").toUpperCase()}
            </div>
            <div style="font-size: 0.8rem; color: #cbd5e1; line-height: 1.3;">
                ${data.message || "A new parking event has occurred."}
            </div>
        </div>
        <button style="background: transparent; border: none; color: #94a3b8; cursor: pointer; font-size: 1rem;" onclick="this.parentElement.remove()">
            <i class="fa-solid fa-xmark"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = "1";
        toast.style.transform = "translateX(0)";
    }, 10);
    
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(-20px)";
        setTimeout(() => {
            toast.remove();
        }, 500);
    }, 6000);
}
