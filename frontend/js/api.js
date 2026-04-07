// ── EventHub API Utility ──
const API_BASE = 'http://127.0.0.1:5000';

const api = {
    getToken() {
        return localStorage.getItem('eventhub_token');
    },

    getUser() {
        const raw = localStorage.getItem('eventhub_user');
        return raw ? JSON.parse(raw) : null;
    },

    setAuth(token, user) {
        localStorage.setItem('eventhub_token', token);
        localStorage.setItem('eventhub_user', JSON.stringify(user));
    },

    clearAuth() {
        localStorage.removeItem('eventhub_token');
        localStorage.removeItem('eventhub_user');
    },

    isLoggedIn() {
        return !!this.getToken();
    },

    headers(json = true) {
        const h = {};
        if (json) h['Content-Type'] = 'application/json';
        const token = this.getToken();
        if (token) h['Authorization'] = `Bearer ${token}`;
        return h;
    },

    async request(method, path, body = null) {
        const opts = {
            method,
            headers: this.headers(),
        };
        if (body) opts.body = JSON.stringify(body);
        const res = await fetch(`${API_BASE}${path}`, opts);
        const data = await res.json();
        if (!res.ok) {
            throw { status: res.status, ...data };
        }
        return data;
    },

    get(path) { return this.request('GET', path); },
    post(path, body) { return this.request('POST', path, body); },
    put(path, body) { return this.request('PUT', path, body); },
    patch(path, body) { return this.request('PATCH', path, body); },
    delete(path) { return this.request('DELETE', path); },

    // Notifications
    async getNotifications() { return this.get('/notifications'); },
    async markRead(id) { return this.patch(`/notifications/${id}/read`); },
<<<<<<< HEAD
=======
    async markAllRead() { return this.patch('/notifications/read-all'); },
>>>>>>> temp-fix

    // Event Updates
    async getEventUpdates(eventId) { return this.get(`/events/${eventId}/updates`); },
    async postEventUpdate(eventId, message) { return this.post(`/institutes/events/${eventId}/updates`, { message }); },

    // Event Results & Hall of Fame
    async getEventResults(eventId) { return this.get(`/results/event/${eventId}`); },
    async setEventResults(eventId, winners) { return this.post(`/results/event/${eventId}`, { winners }); },
    async qualifyParticipants(eventId, userIds, targetRound) { return this.post(`/institutes/events/${eventId}/qualify`, { user_ids: userIds, target_round: targetRound }); },

    // Rewards & Legacy
    async getRewardHistory() { return this.get('/participants/rewards/history'); },
    async syncRewards() { return this.post('/participants/rewards/sync'); },

    // Social & Identity
    async searchUsers(query) { return this.get(`/social/search?q=${encodeURIComponent(query)}`); },
    async followUser(userId) { return this.post(`/social/follow/${userId}`); },
    async unfollowUser(userId) { return this.post(`/social/unfollow/${userId}`); },
    async getUserProfile(userId) { return this.get(`/social/profile/${userId}`); },

    // Legacy
    async getFullLegacy() { return this.get('/participants/legacy'); },
};

// ── Toast Notifications ──
function showToast(message, type = 'info') {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `toast alert-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
}

// ── Navigation Builder ──
function buildNav() {
    const user = api.getUser();
    const role = user?.role;
    const nav = document.getElementById('main-nav');
    if (!nav) return;

    let links = `<a href="index.html">🏠 Home</a>`;
    links += `<a href="leaderboard.html">🏆 Leaderboard</a>`;

    if (!user) {
        links += `<a href="login.html" class="btn btn-secondary btn-sm">Login</a>`;
        links += `<a href="register.html" class="btn btn-primary btn-sm">Register</a>`;
    } else {
        // Profile link between Leaderboard and Dashboard
        links += `<a href="profile.html">👤 Profile</a>`;

        if (role === 'ADMIN') {
            links += `<a href="admin-dashboard.html">⚙️ Admin</a>`;
        } else if (role === 'INSTITUTE' || role === 'VOLUNTEER') {
            links += `<a href="institute-dashboard.html">🏛️ Dashboard</a>`;
        } else {
            links += `<a href="dashboard.html">📋 Dashboard</a>`;
        }
        links += `<button onclick="logout()" class="btn btn-secondary btn-sm" style="margin-left: 10px;">Logout</button>`;
    }

    nav.innerHTML = links;
}

function logout() {
    api.clearAuth();
    window.location.href = 'index.html';
}

// ── Auth Guard ──
function requireAuth(allowedRoles = null) {
    if (!api.isLoggedIn()) {
        window.location.href = 'login.html';
        return false;
    }
    if (allowedRoles) {
        const user = api.getUser();
        if (!allowedRoles.includes(user?.role)) {
            window.location.href = 'index.html';
            return false;
        }
    }
    return true;
}

// ── Helpers ──
function formatDate(iso) {
    if (!iso) return 'TBD';
    const d = new Date(iso);
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

function formatDateTime(iso) {
    if (!iso) return 'TBD';
    const d = new Date(iso);
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function statusBadge(status) {
    const s = (status || '').toUpperCase();
    const cls = s === 'APPROVED' || s === 'PAID' ? 'badge-approved'
        : s === 'REJECTED' ? 'badge-rejected'
        : s === 'PENDING' ? 'badge-pending'
        : 'badge-unpaid';
    return `<span class="badge ${cls}">${s}</span>`;
}

function badgeBadge(badge) {
    const b = (badge || 'Wood').toLowerCase();
    return `<span class="badge badge-${b}">${badge}</span>`;
}

// Init nav on load
document.addEventListener('DOMContentLoaded', buildNav);
