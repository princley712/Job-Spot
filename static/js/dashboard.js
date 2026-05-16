/**
 * Job Aggregator — Dashboard Controller
 *
 * Handles:
 *  1. Fetching & rendering job applications from the API
 *  2. Opening external apply links via the redirect endpoint
 *  3. Detecting tab-return (visibilitychange + focus) → showing the
 *     "Did you apply?" modal
 *  4. Modal actions → PATCH/DELETE API calls → UI updates
 */

// ── Configuration ────────────────────────────────────────────────────────────

const API_BASE = "/api/v1";

// Temporary: In production this comes from the auth flow.
// For demo purposes, set your JWT token here or use the /docs endpoint.
const AUTH_TOKEN = localStorage.getItem("jwt_token") || "";

const HEADERS = {
    "Content-Type": "application/json",
    ...(AUTH_TOKEN && { Authorization: `Bearer ${AUTH_TOKEN}` }),
};


// ── State ────────────────────────────────────────────────────────────────────

let applications = [];          // full list from API
let currentFilter = "pending";  // active filter tab
let pendingRedirect = null;     // { applicationId, jobTitle } — set before opening external tab


// ── DOM References ───────────────────────────────────────────────────────────

const grid          = document.getElementById("jobs-grid");
const filterBar     = document.getElementById("filter-bar");
const modalOverlay  = document.getElementById("modal-overlay");
const modalJobName  = document.getElementById("modal-job-name");
const btnApplied    = document.getElementById("modal-btn-applied");
const btnLater      = document.getElementById("modal-btn-later");
const btnSkip       = document.getElementById("modal-btn-skip");
const toastContainer = document.getElementById("toast-container");


// ── API Helpers ──────────────────────────────────────────────────────────────

async function apiFetch(path, options = {}) {
    const res = await fetch(`${API_BASE}${path}`, {
        headers: HEADERS,
        ...options,
    });
    if (!res.ok) {
        const err = await res.text();
        throw new Error(`API ${res.status}: ${err}`);
    }
    if (res.status === 204) return null;
    return res.json();
}


// ── Data Loading ─────────────────────────────────────────────────────────────

async function loadApplications() {
    try {
        applications = await apiFetch("/applications/");
        updateStats();
        renderGrid();
    } catch (err) {
        console.error("Failed to load applications:", err);
        renderDemoData();  // Fall back to demo data for preview
    }
}

function updateStats() {
    const counts = { pending: 0, applied: 0, interviewing: 0 };
    applications.forEach((app) => {
        if (counts[app.status] !== undefined) counts[app.status]++;
    });
    document.getElementById("stat-pending").textContent = counts.pending;
    document.getElementById("stat-applied").textContent = counts.applied;
    document.getElementById("stat-interviewing").textContent = counts.interviewing;
}


// ── Rendering ────────────────────────────────────────────────────────────────

function renderGrid() {
    const filtered =
        currentFilter === "all"
            ? applications
            : applications.filter((a) => a.status === currentFilter);

    if (filtered.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                          d="M21 21l-5.2-5.2m0 0A7.5 7.5 0 105.3 5.3a7.5 7.5 0 0010.5 10.5z"/>
                </svg>
                <h3>No jobs in this view</h3>
                <p>Try a different filter or wait for the next scrape cycle</p>
            </div>`;
        return;
    }

    grid.innerHTML = filtered
        .map((app, i) => renderCard(app, i))
        .join("");

    // Attach click handlers
    grid.querySelectorAll("[data-action='apply-redirect']").forEach((btn) => {
        btn.addEventListener("click", (e) => {
            e.preventDefault();
            handleApplyClick(btn.dataset.appId, btn.dataset.jobTitle);
        });
    });

    grid.querySelectorAll("[data-action='dismiss']").forEach((btn) => {
        btn.addEventListener("click", () => handleDismiss(btn.dataset.appId));
    });
}

function renderCard(app, index) {
    const job = app.job;
    const score = app.match_score;
    const scoreClass =
        score >= 0.7 ? "match-high" : score >= 0.4 ? "match-medium" : "match-low";
    const scoreLabel = score != null ? `${Math.round(score * 100)}% match` : "";

    const locationStr = job.location || "—";
    const remoteTag = job.is_remote
        ? `<span class="remote-tag">Remote</span>`
        : "";

    const statusBadge =
        app.status !== "pending"
            ? `<span class="status-badge status-${app.status}">${app.status}</span>`
            : "";

    const applyBtn =
        app.status === "pending"
            ? `<button class="btn btn-primary" data-action="apply-redirect"
                        data-app-id="${app.id}" data-job-title="${escapeHtml(job.title)}">
                    Apply →
               </button>
               <button class="btn btn-danger" data-action="dismiss" data-app-id="${app.id}"
                        title="Not interested">✕</button>`
            : statusBadge;

    return `
        <div class="job-card" style="animation-delay: ${index * 0.05}s">
            <div class="job-info">
                <div class="job-title-row">
                    <span class="job-title">${escapeHtml(job.title)}</span>
                    ${scoreLabel ? `<span class="match-badge ${scoreClass}">${scoreLabel}</span>` : ""}
                </div>
                <div class="job-meta">
                    <span>${escapeHtml(job.company)}</span>
                    <span>📍 ${escapeHtml(locationStr)}</span>
                    <span class="source-tag">${job.source}</span>
                    ${remoteTag}
                </div>
            </div>
            <div class="job-actions">
                ${applyBtn}
            </div>
        </div>`;
}


// ── Redirect Flow ────────────────────────────────────────────────────────────

function handleApplyClick(applicationId, jobTitle) {
    // 1. Store redirect context
    pendingRedirect = { applicationId, jobTitle };

    // 2. Open the redirect endpoint in a new tab
    //    The backend logs the click and 302s to the external apply URL
    window.open(`${API_BASE}/apply/${applicationId}`, "_blank");
}


// ── Tab-Return Detection (visibilitychange + focus) ──────────────────────────
//
// When the user clicks "Apply →", we open the external job page in a new tab.
// When they switch back to our tab, we detect it and show the modal.

document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible" && pendingRedirect) {
        // Small delay to let the browser settle after tab switch
        setTimeout(() => showModal(), 300);
    }
});

// Fallback for browsers/OS where visibilitychange is unreliable
window.addEventListener("focus", () => {
    if (pendingRedirect) {
        setTimeout(() => showModal(), 300);
    }
});


// ── Modal Logic ──────────────────────────────────────────────────────────────

function showModal() {
    if (!pendingRedirect) return;
    modalJobName.textContent = pendingRedirect.jobTitle;
    modalOverlay.classList.add("visible");
}

function hideModal() {
    modalOverlay.classList.remove("visible");
}

// ── "Yes, I Applied" ──
btnApplied.addEventListener("click", async () => {
    const { applicationId } = pendingRedirect;
    hideModal();
    try {
        await apiFetch(`/applications/${applicationId}/status`, {
            method: "PATCH",
            body: JSON.stringify({ status: "applied", note: "Marked via dashboard" }),
        });
        showToast("Application marked as Applied ✅", "success");
    } catch (err) {
        console.error(err);
        showToast("Failed to update — try again", "error");
    }
    pendingRedirect = null;
    loadApplications();
});

// ── "Not Yet" ──
btnLater.addEventListener("click", () => {
    hideModal();
    showToast("Kept in your pending list — expires in 7 days", "info");
    pendingRedirect = null;
});

// ── "Not Interested" ──
btnSkip.addEventListener("click", async () => {
    const { applicationId } = pendingRedirect;
    hideModal();
    try {
        await apiFetch(`/applications/${applicationId}`, {
            method: "DELETE",
        });
        showToast("Job removed from your list", "info");
    } catch (err) {
        console.error(err);
        showToast("Failed to remove — try again", "error");
    }
    pendingRedirect = null;
    loadApplications();
});

// Close modal on overlay click (outside the modal box)
modalOverlay.addEventListener("click", (e) => {
    if (e.target === modalOverlay) {
        hideModal();
        pendingRedirect = null;
    }
});

// Close modal on Escape key
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && pendingRedirect) {
        hideModal();
        pendingRedirect = null;
    }
});


// ── Filter Bar ───────────────────────────────────────────────────────────────

filterBar.addEventListener("click", (e) => {
    const btn = e.target.closest(".filter-btn");
    if (!btn) return;

    filterBar.querySelectorAll(".filter-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");

    currentFilter = btn.dataset.filter;
    renderGrid();
});


// ── Toast Notifications ──────────────────────────────────────────────────────

function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);

    // Auto-remove after animation completes
    setTimeout(() => toast.remove(), 3500);
}


// ── Utilities ────────────────────────────────────────────────────────────────

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}


// ── Demo Data (used when API is unavailable) ─────────────────────────────────

function renderDemoData() {
    applications = [
        {
            id: "demo-1",
            status: "pending",
            match_score: 0.87,
            expires_at: new Date(Date.now() + 7 * 86400000).toISOString(),
            created_at: new Date().toISOString(),
            job: {
                id: "j1", title: "Senior Python Developer", company: "Stripe",
                location: "San Francisco, CA", is_remote: true, source: "linkedin",
                apply_url: "#",
            },
        },
        {
            id: "demo-2",
            status: "pending",
            match_score: 0.72,
            expires_at: new Date(Date.now() + 5 * 86400000).toISOString(),
            created_at: new Date().toISOString(),
            job: {
                id: "j2", title: "Backend Engineer", company: "Figma",
                location: "Remote", is_remote: true, source: "greenhouse",
                apply_url: "#",
            },
        },
        {
            id: "demo-3",
            status: "pending",
            match_score: 0.58,
            expires_at: new Date(Date.now() + 6 * 86400000).toISOString(),
            created_at: new Date().toISOString(),
            job: {
                id: "j3", title: "Full Stack Developer", company: "Vercel",
                location: "Remote", is_remote: true, source: "lever",
                apply_url: "#",
            },
        },
        {
            id: "demo-4",
            status: "pending",
            match_score: 0.41,
            expires_at: new Date(Date.now() + 3 * 86400000).toISOString(),
            created_at: new Date().toISOString(),
            job: {
                id: "j4", title: "Software Engineer II", company: "Netflix",
                location: "Los Gatos, CA", is_remote: false, source: "indeed",
                apply_url: "#",
            },
        },
        {
            id: "demo-5",
            status: "applied",
            match_score: 0.91,
            applied_at: new Date(Date.now() - 2 * 86400000).toISOString(),
            created_at: new Date().toISOString(),
            job: {
                id: "j5", title: "Staff Engineer — Platform", company: "Datadog",
                location: "New York, NY", is_remote: true, source: "linkedin",
                apply_url: "#",
            },
        },
        {
            id: "demo-6",
            status: "interviewing",
            match_score: 0.83,
            created_at: new Date().toISOString(),
            job: {
                id: "j6", title: "Principal Engineer", company: "Shopify",
                location: "Remote", is_remote: true, source: "greenhouse",
                apply_url: "#",
            },
        },
    ];

    updateStats();
    renderGrid();
    showToast("Running in demo mode — connect API for live data", "info");
}


// ── Boot ─────────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    loadApplications();
});
