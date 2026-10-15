// frontend/js/admin.js
// Admin Dashboard Controller for Zenith '26 Fest Operations

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements - Stats
  const statTotalEvents = document.getElementById("stat-total-events");
  const statTotalRegistrations = document.getElementById("stat-total-registrations");
  const statUtilizationPct = document.getElementById("stat-utilization-pct");
  const statCapacityFraction = document.getElementById("stat-capacity-fraction");
  const statUtilizationBar = document.getElementById("stat-utilization-bar");
  const statUpcomingEvents = document.getElementById("stat-upcoming-events");
  const categoriesContainer = document.getElementById("categories-container");
  const lastUpdatedText = document.getElementById("last-updated-text");

  // DOM Elements - Error & Refresh
  const adminErrorBanner = document.getElementById("admin-error-banner");
  const adminErrorText = document.getElementById("admin-error-text");
  const adminRetryBtn = document.getElementById("admin-retry-btn");
  const refreshDashboardBtn = document.getElementById("refresh-dashboard-btn");

  // DOM Elements - Tabs & Views
  const tabEventsBtn = document.getElementById("tab-events-btn");
  const tabRegistrationsBtn = document.getElementById("tab-registrations-btn");
  const viewEventsSection = document.getElementById("view-events-section");
  const viewRegistrationsSection = document.getElementById("view-registrations-section");

  // DOM Elements - Events Table
  const eventsTableBody = document.getElementById("events-table-body");
  const tableEventsCount = document.getElementById("table-events-count");

  // DOM Elements - Registrations Table
  const filterRegistrationEvent = document.getElementById("filter-registration-event");
  const registrationsTableBody = document.getElementById("registrations-table-body");
  const registrationsCountDisplay = document.getElementById("registrations-count-display");

  // DOM Elements - Add Event Modal (Stretch Goal)
  const addEventBtn = document.getElementById("add-event-btn");
  const addEventModal = document.getElementById("add-event-modal");
  const closeAddEventModal = document.getElementById("close-add-event-modal");
  const cancelAddEventBtn = document.getElementById("cancel-add-event-btn");
  const addEventForm = document.getElementById("add-event-form");
  const addEventErrorAlert = document.getElementById("add-event-error-alert");

  // Cached state
  let allEvents = [];
  let allRegistrations = [];

  const categoryEmoji = {
    Technical: "💻",
    Cultural: "🎭",
    Sports: "⚽",
    Gaming: "🎮",
    Workshop: "⚡"
  };

  /**
   * Load all data for Admin Dashboard
   */
  async function loadDashboard() {
    adminErrorBanner.classList.add("hidden");
    try {
      await Promise.all([
        fetchStats(),
        fetchEventsTable(),
        fetchRegistrations()
      ]);
      const now = new Date();
      lastUpdatedText.textContent = `Synced ${now.toLocaleTimeString()}`;
    } catch (err) {
      console.error("Dashboard error:", err);
      adminErrorBanner.classList.remove("hidden");
      adminErrorText.textContent = err.message || "Failed to load dashboard data.";
    }
  }

  /**
   * Fetch GET /api/stats and populate top stat cards & category breakdown
   */
  async function fetchStats() {
    const res = await fetch("/api/stats");
    if (!res.ok) throw new Error(`Stats endpoint returned status ${res.status}`);
    const stats = await res.json();

    statTotalEvents.textContent = stats.total_events;
    statTotalRegistrations.textContent = stats.total_registrations;
    statUtilizationPct.textContent = `${stats.overall_utilization_pct}%`;
    statCapacityFraction.textContent = `of ${stats.total_capacity} seats`;
    
    // Utilization progress bar
    const barWidth = Math.min(100, Math.max(0, stats.overall_utilization_pct));
    statUtilizationBar.style.width = `${barWidth}%`;
    if (barWidth >= 90) {
      statUtilizationBar.className = "bg-red-600 h-1.5 rounded-full transition-all duration-500";
    } else if (barWidth >= 70) {
      statUtilizationBar.className = "bg-amber-500 h-1.5 rounded-full transition-all duration-500";
    } else {
      statUtilizationBar.className = "bg-indigo-600 h-1.5 rounded-full transition-all duration-500";
    }

    statUpcomingEvents.textContent = stats.upcoming_events_count;

    // Render category counts
    renderCategoryBreakdown(stats.events_by_category);
  }

  /**
   * Render category badges / counts
   */
  function renderCategoryBreakdown(categories) {
    categoriesContainer.innerHTML = "";
    const entries = Object.entries(categories || {});

    if (entries.length === 0) {
      categoriesContainer.innerHTML = `<div class="text-xs text-slate-400 col-span-full">No category data recorded.</div>`;
      return;
    }

    entries.forEach(([cat, count]) => {
      const emoji = categoryEmoji[cat] || "📌";
      const card = document.createElement("div");
      card.className = "p-3 rounded-xl bg-slate-50 border border-slate-200/70 text-center hover:bg-slate-100 transition";
      card.innerHTML = `
        <div class="text-base mb-0.5">${emoji}</div>
        <div class="text-xs font-semibold text-slate-600 truncate">${escapeHtml(cat)}</div>
        <div class="text-lg font-black text-slate-900">${count} <span class="text-xs font-normal text-slate-400">events</span></div>
      `;
      categoriesContainer.appendChild(card);
    });
  }

  /**
   * Fetch GET /api/events and populate utilization table
   */
  async function fetchEventsTable() {
    const res = await fetch("/api/events");
    if (!res.ok) throw new Error(`Events endpoint returned status ${res.status}`);
    allEvents = await res.json();

    // Populate dropdown in registration filter
    populateEventFilterDropdown(allEvents);

    tableEventsCount.textContent = allEvents.length;

    // Compute booked registrations and utilization percentage per event
    const eventsWithStats = allEvents.map(event => {
      const booked = event.capacity - event.available_seats;
      const utilization = event.capacity > 0 ? (booked / event.capacity) * 100 : 0;
      return {
        ...event,
        booked,
        utilizationPct: Math.round(utilization * 10) / 10
      };
    });

    // Step 8: Sort by utilization percentage descending by default
    eventsWithStats.sort((a, b) => b.utilizationPct - a.utilizationPct);

    eventsTableBody.innerHTML = "";

    eventsWithStats.forEach(event => {
      const isHighDemand = event.utilizationPct >= 90;
      const tr = document.createElement("tr");

      // Highlight in warning color if over 90%
      if (isHighDemand) {
        tr.className = "bg-amber-50/70 hover:bg-amber-100/70 border-l-4 border-amber-500 transition";
      } else {
        tr.className = "hover:bg-slate-50/80 transition";
      }

      tr.innerHTML = `
        <td class="py-3.5 px-4 font-semibold text-slate-900">
          <div class="flex items-center gap-2">
            <span class="text-lg">${event.icon || "⚡"}</span>
            <div>
              <span class="block">${escapeHtml(event.title)}</span>
              ${isHighDemand ? '<span class="text-[10px] font-bold uppercase tracking-wider text-amber-700 bg-amber-100 px-1.5 py-0.2 rounded">🔥 High Demand (&gt;90%)</span>' : ''}
            </div>
          </div>
        </td>
        <td class="py-3.5 px-3">
          <span class="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-medium border border-slate-200">
            ${escapeHtml(event.category)}
          </span>
        </td>
        <td class="py-3.5 px-3 text-slate-600 text-xs">
          ${event.event_date}<br><span class="text-slate-400">${event.event_time}</span>
        </td>
        <td class="py-3.5 px-3 text-slate-600 truncate max-w-[140px]">
          ${escapeHtml(event.venue)}
        </td>
        <td class="py-3.5 px-3 font-semibold text-slate-800">
          ${event.booked} <span class="text-slate-400 font-normal">/ ${event.capacity}</span>
        </td>
        <td class="py-3.5 px-4 text-right">
          <div class="inline-flex items-center gap-2">
            <div class="w-16 bg-slate-100 rounded-full h-1.5 overflow-hidden">
              <div class="${isHighDemand ? 'bg-amber-600' : 'bg-indigo-600'} h-1.5 rounded-full" style="width: ${Math.min(100, event.utilizationPct)}%"></div>
            </div>
            <span class="font-bold ${isHighDemand ? 'text-amber-800' : 'text-slate-800'} text-xs">
              ${event.utilizationPct}%
            </span>
          </div>
        </td>
      `;

      eventsTableBody.appendChild(tr);
    });
  }

  /**
   * Populate event filter dropdown
   */
  function populateEventFilterDropdown(events) {
    const currentVal = filterRegistrationEvent.value;
    filterRegistrationEvent.innerHTML = `<option value="">All Events</option>`;
    events.forEach(ev => {
      const opt = document.createElement("option");
      opt.value = ev.id;
      opt.textContent = `${ev.title} (${ev.category})`;
      if (String(ev.id) === currentVal) opt.selected = true;
      filterRegistrationEvent.appendChild(opt);
    });
  }

  /**
   * Fetch GET /api/registrations (raw registrations list)
   */
  async function fetchRegistrations() {
    const selectedEventId = filterRegistrationEvent.value;
    let url = "/api/registrations";
    if (selectedEventId) {
      url += `?event_id=${selectedEventId}`;
    }

    const res = await fetch(url);
    if (!res.ok) throw new Error(`Registrations endpoint returned status ${res.status}`);
    allRegistrations = await res.json();

    renderRegistrations(allRegistrations);
  }

  /**
   * Render registration roster table
   */
  function renderRegistrations(registrations) {
    registrationsCountDisplay.textContent = registrations.length;
    registrationsTableBody.innerHTML = "";

    if (!registrations || registrations.length === 0) {
      registrationsTableBody.innerHTML = `
        <tr>
          <td colspan="8" class="text-center py-10 text-xs text-slate-400">
            No registrations found for the selected filter.
          </td>
        </tr>
      `;
      return;
    }

    registrations.forEach(reg => {
      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-50 transition";

      // Format date
      let formattedDate = reg.registered_at;
      try {
        formattedDate = new Date(reg.registered_at).toLocaleString();
      } catch (e) {}

      tr.innerHTML = `
        <td class="py-3 px-4 font-mono text-xs text-slate-400">#${reg.id}</td>
        <td class="py-3 px-3 font-semibold text-slate-900">${escapeHtml(reg.student_name)}</td>
        <td class="py-3 px-3 font-mono text-xs text-slate-600">${escapeHtml(reg.roll_number)}</td>
        <td class="py-3 px-3 text-slate-600">${escapeHtml(reg.email)}</td>
        <td class="py-3 px-3 text-slate-500">${escapeHtml(reg.phone || "-")}</td>
        <td class="py-3 px-3">
          <span class="text-xs font-medium px-2 py-0.5 rounded bg-indigo-50 text-indigo-700">
            ${escapeHtml(reg.event_title)}
          </span>
        </td>
        <td class="py-3 px-3 text-slate-500 text-xs">${formattedDate}</td>
        <td class="py-3 px-4 text-right">
          <!-- Stretch Goal 2: Cancel registration -->
          <button 
            data-reg-id="${reg.id}" 
            data-student="${escapeHtml(reg.student_name)}" 
            data-event="${escapeHtml(reg.event_title)}"
            class="cancel-reg-btn text-xs font-semibold text-red-600 hover:text-red-800 hover:bg-red-50 px-2.5 py-1 rounded-lg border border-red-200 transition"
          >
            Cancel
          </button>
        </td>
      `;

      registrationsTableBody.appendChild(tr);
    });

    // Attach cancellation handlers
    document.querySelectorAll(".cancel-reg-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const regId = btn.getAttribute("data-reg-id");
        const student = btn.getAttribute("data-student");
        const eventTitle = btn.getAttribute("data-event");
        handleCancelRegistration(regId, student, eventTitle);
      });
    });
  }

  /**
   * Stretch Goal 2: Cancel registration with confirmation
   */
  async function handleCancelRegistration(regId, student, eventTitle) {
    const confirmed = confirm(`Are you sure you want to cancel the registration #${regId} for "${student}" in "${eventTitle}"?\nThis will immediately free up one seat.`);
    if (!confirmed) return;

    try {
      const res = await fetch(`/api/registrations/${regId}`, {
        method: "DELETE"
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to cancel registration.");
      }

      // Success: reload tables & stats
      await loadDashboard();
    } catch (err) {
      alert(`Error cancelling registration: ${err.message}`);
    }
  }

  /**
   * Filter dropdown change
   */
  filterRegistrationEvent.addEventListener("change", fetchRegistrations);

  /**
   * Tab Navigation Switcher
   */
  tabEventsBtn.addEventListener("click", () => {
    tabEventsBtn.classList.add("border-indigo-600", "text-indigo-600", "font-bold");
    tabEventsBtn.classList.remove("border-transparent", "text-slate-500");
    tabRegistrationsBtn.classList.remove("border-indigo-600", "text-indigo-600", "font-bold");
    tabRegistrationsBtn.classList.add("border-transparent", "text-slate-500");

    viewEventsSection.classList.remove("hidden");
    viewRegistrationsSection.classList.add("hidden");
  });

  tabRegistrationsBtn.addEventListener("click", () => {
    tabRegistrationsBtn.classList.add("border-indigo-600", "text-indigo-600", "font-bold");
    tabRegistrationsBtn.classList.remove("border-transparent", "text-slate-500");
    tabEventsBtn.classList.remove("border-indigo-600", "text-indigo-600", "font-bold");
    tabEventsBtn.classList.add("border-transparent", "text-slate-500");

    viewRegistrationsSection.classList.remove("hidden");
    viewEventsSection.classList.add("hidden");
  });

  refreshDashboardBtn.addEventListener("click", loadDashboard);
  adminRetryBtn.addEventListener("click", loadDashboard);

  /**
   * Stretch Goal 1: Add Event Modal Actions
   */
  addEventBtn.addEventListener("click", () => {
    addEventForm.reset();
    addEventErrorAlert.classList.add("hidden");
    addEventModal.classList.remove("hidden");
  });

  closeAddEventModal.addEventListener("click", () => addEventModal.classList.add("hidden"));
  cancelAddEventBtn.addEventListener("click", () => addEventModal.classList.add("hidden"));

  addEventForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    addEventErrorAlert.classList.add("hidden");

    const payload = {
      title: document.getElementById("new-event-title").value.trim(),
      category: document.getElementById("new-event-category").value,
      icon: document.getElementById("new-event-icon").value.trim() || "⚡",
      venue: document.getElementById("new-event-venue").value.trim(),
      event_date: document.getElementById("new-event-date").value,
      event_time: document.getElementById("new-event-time").value.trim(),
      capacity: parseInt(document.getElementById("new-event-capacity").value, 10),
      fee: parseInt(document.getElementById("new-event-fee").value, 10) || 0,
      description: document.getElementById("new-event-desc").value.trim() || null
    };

    try {
      const res = await fetch("/api/events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to create event");
      }

      addEventModal.classList.add("hidden");
      await loadDashboard();
    } catch (err) {
      addEventErrorAlert.classList.remove("hidden");
      addEventErrorAlert.textContent = err.message;
    }
  });

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Initial load
  loadDashboard();
});
