// frontend/js/app.js
// Client-side controller for Zenith '26 Student Event Portal

document.addEventListener("DOMContentLoaded", () => {
  // State variables
  let currentCategory = "All";
  let currentSearch = "";
  let searchDebounceTimer = null;
  let activeEventData = null;

  // DOM Elements
  const eventsGrid = document.getElementById("events-grid");
  const loadingState = document.getElementById("loading-state");
  const errorState = document.getElementById("error-state");
  const errorMessageText = document.getElementById("error-message-text");
  const emptyState = document.getElementById("empty-state");
  const eventCountDisplay = document.getElementById("event-count-display");
  const searchInput = document.getElementById("search-input");
  const clearSearchBtn = document.getElementById("clear-search-btn");
  const retryBtn = document.getElementById("retry-btn");
  const resetFiltersBtn = document.getElementById("reset-filters-btn");
  const categoryButtons = document.querySelectorAll(".category-btn");

  // Modal DOM Elements
  const detailModal = document.getElementById("detail-modal");
  const closeModalBtn = document.getElementById("close-modal-btn");
  const cancelModalBtn = document.getElementById("cancel-modal-btn");
  const modalEventIcon = document.getElementById("modal-event-icon");
  const modalEventTitle = document.getElementById("modal-event-title");
  const modalEventCategory = document.getElementById("modal-event-category");
  const modalEventFee = document.getElementById("modal-event-fee");
  const modalEventDateTime = document.getElementById("modal-event-datetime");
  const modalEventVenue = document.getElementById("modal-event-venue");
  const modalEventSeats = document.getElementById("modal-event-seats");
  const modalEventDescription = document.getElementById("modal-event-description");

  // Form DOM Elements
  const registrationForm = document.getElementById("registration-form");
  const regEventId = document.getElementById("reg-event-id");
  const regName = document.getElementById("reg-name");
  const regRoll = document.getElementById("reg-roll");
  const regEmail = document.getElementById("reg-email");
  const regPhone = document.getElementById("reg-phone");
  const errorName = document.getElementById("error-name");
  const errorRoll = document.getElementById("error-roll");
  const errorEmail = document.getElementById("error-email");
  const formErrorAlert = document.getElementById("form-error-alert");
  const formErrorText = document.getElementById("form-error-text");
  const formSuccessAlert = document.getElementById("form-success-alert");
  const formSuccessText = document.getElementById("form-success-text");
  const submitRegBtn = document.getElementById("submit-reg-btn");
  const submitBtnSpinner = document.getElementById("submit-btn-spinner");
  const submitBtnText = document.getElementById("submit-btn-text");

  // Category Color Helper
  const categoryStyles = {
    Technical: { badge: "bg-blue-50 text-blue-700 border-blue-200" },
    Cultural: { badge: "bg-purple-50 text-purple-700 border-purple-200" },
    Sports: { badge: "bg-emerald-50 text-emerald-700 border-emerald-200" },
    Gaming: { badge: "bg-rose-50 text-rose-700 border-rose-200" },
    Workshop: { badge: "bg-amber-50 text-amber-700 border-amber-200" }
  };

  /**
   * Fetch events from GET /api/events with category and search query parameters.
   */
  async function fetchEvents() {
    // Show loading state
    eventsGrid.innerHTML = "";
    loadingState.classList.remove("hidden");
    errorState.classList.add("hidden");
    emptyState.classList.add("hidden");

    try {
      const params = new URLSearchParams();
      if (currentCategory && currentCategory !== "All") {
        params.append("category", currentCategory);
      }
      if (currentSearch && currentSearch.trim() !== "") {
        params.append("search", currentSearch.trim());
      }

      const url = `/api/events${params.toString() ? "?" + params.toString() : ""}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Server returned status ${response.status}: ${response.statusText}`);
      }

      const events = await response.json();
      loadingState.classList.add("hidden");
      renderEvents(events);
    } catch (err) {
      console.error("Error fetching events:", err);
      loadingState.classList.add("hidden");
      errorState.classList.remove("hidden");
      errorMessageText.textContent = `Unable to connect to /api/events: ${err.message}. Please verify the backend server is running.`;
    }
  }

  /**
   * Render list of events inside #events-grid
   */
  function renderEvents(events) {
    eventCountDisplay.textContent = events.length;

    if (!events || events.length === 0) {
      emptyState.classList.remove("hidden");
      return;
    }

    eventsGrid.innerHTML = "";

    events.forEach(event => {
      const card = document.createElement("div");
      card.className = "bg-white rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-xl hover:-translate-y-1 transition duration-200 flex flex-col overflow-hidden animate-fade-in group";

      const catStyle = categoryStyles[event.category] || { badge: "bg-slate-100 text-slate-700 border-slate-200" };
      const isFull = event.available_seats <= 0;
      const feeLabel = event.fee > 0 ? `₹${event.fee}` : "Free";

      card.innerHTML = `
        <div class="p-6 flex-grow flex flex-col justify-between space-y-4">
          <!-- Card Header: Icon, Category & Seats Badge -->
          <div class="flex items-start justify-between gap-3">
            <div class="w-12 h-12 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-center text-2xl shadow-inner group-hover:scale-105 transition">
              ${event.icon || "⚡"}
            </div>
            <div class="flex flex-col items-end gap-1">
              <span class="text-xs font-semibold px-2.5 py-0.5 rounded-full border ${catStyle.badge}">
                ${event.category}
              </span>
              ${isFull 
                ? `<span class="text-xs font-bold px-2.5 py-0.5 rounded-full bg-red-100 text-red-700 border border-red-200 uppercase tracking-wider">FULL</span>`
                : `<span class="text-xs font-medium text-slate-500 bg-slate-50 px-2 py-0.5 rounded-md border border-slate-100">${event.available_seats} / ${event.capacity} left</span>`
              }
            </div>
          </div>

          <!-- Title & Brief Description -->
          <div class="space-y-1">
            <h3 class="text-lg font-bold text-slate-900 group-hover:text-indigo-600 transition leading-snug">
              ${escapeHtml(event.title)}
            </h3>
            <p class="text-xs text-slate-500 line-clamp-2 leading-relaxed">
              ${escapeHtml(event.description || "Join this exciting fest event at Zenith '26.")}
            </p>
          </div>

          <!-- Logistics: Date, Time, Venue -->
          <div class="space-y-1.5 pt-2 border-t border-slate-100 text-xs text-slate-600">
            <div class="flex items-center gap-2">
              <span class="text-slate-400">📅</span>
              <span>${event.event_date} · ${event.event_time}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-slate-400">📍</span>
              <span class="truncate">${escapeHtml(event.venue)}</span>
            </div>
          </div>
        </div>

        <!-- Card Footer: Fee and Action Button -->
        <div class="px-6 py-3.5 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
          <div class="text-xs font-bold ${event.fee > 0 ? 'text-indigo-600' : 'text-emerald-600'}">
            ${feeLabel}
          </div>
          <button 
            data-event-id="${event.id}" 
            class="view-details-btn px-4 py-2 rounded-xl text-xs font-semibold text-white ${isFull ? 'bg-slate-700 hover:bg-slate-800' : 'bg-indigo-600 hover:bg-indigo-700 shadow-sm shadow-indigo-200'} transition active:scale-95 flex items-center gap-1"
          >
            <span>${isFull ? 'View Event' : 'View & Register'}</span>
            <span>→</span>
          </button>
        </div>
      `;

      eventsGrid.appendChild(card);
    });

    // Attach click listeners to "View Details" buttons
    document.querySelectorAll(".view-details-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-event-id");
        openEventDetail(id);
      });
    });
  }

  /**
   * Fetch specific event details and open the modal
   */
  async function openEventDetail(eventId) {
    try {
      const res = await fetch(`/api/events/${eventId}`);
      if (!res.ok) {
        alert("Failed to load event details.");
        return;
      }
      activeEventData = await res.json();

      // Reset form states
      registrationForm.reset();
      clearFormAlerts();
      regEventId.value = activeEventData.id;

      // Populate Modal Info
      modalEventIcon.textContent = activeEventData.icon || "⚡";
      modalEventTitle.textContent = activeEventData.title;
      modalEventCategory.textContent = activeEventData.category;
      modalEventFee.textContent = activeEventData.fee > 0 ? `Fee: ₹${activeEventData.fee}` : "Free Entry";
      modalEventDateTime.textContent = `${activeEventData.event_date} · ${activeEventData.event_time}`;
      modalEventVenue.textContent = activeEventData.venue;

      if (activeEventData.available_seats <= 0) {
        modalEventSeats.innerHTML = `<span class="text-red-600 font-bold">FULL (0 / ${activeEventData.capacity} available)</span>`;
        submitRegBtn.disabled = true;
        submitRegBtn.classList.add("opacity-50", "cursor-not-allowed");
        submitBtnText.textContent = "Event Full";
      } else {
        modalEventSeats.innerHTML = `<span class="text-emerald-600 font-bold">${activeEventData.available_seats}</span> / ${activeEventData.capacity} seats remaining`;
        submitRegBtn.disabled = false;
        submitRegBtn.classList.remove("opacity-50", "cursor-not-allowed");
        submitBtnText.textContent = "Confirm Registration";
      }

      modalEventDescription.textContent = activeEventData.description || "No specific description provided.";

      // Display Modal
      detailModal.classList.remove("hidden");
      document.body.classList.add("overflow-hidden");
    } catch (err) {
      console.error("Error opening event detail:", err);
      alert("Error loading event information.");
    }
  }

  /**
   * Close the modal
   */
  function closeModal() {
    detailModal.classList.add("hidden");
    document.body.classList.remove("overflow-hidden");
    clearFormAlerts();
  }

  function clearFormAlerts() {
    formErrorAlert.classList.add("hidden");
    formSuccessAlert.classList.add("hidden");
    errorName.classList.add("hidden");
    errorRoll.classList.add("hidden");
    errorEmail.classList.add("hidden");
  }

  /**
   * Handle Registration Form Submission
   */
  registrationForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearFormAlerts();

    const eventId = regEventId.value;
    const studentName = regName.value.trim();
    const rollNumber = regRoll.value.trim();
    const email = regEmail.value.trim();
    const phone = regPhone.value.trim();

    // Client-side validation checks
    let isValid = true;
    if (!studentName) {
      errorName.classList.remove("hidden");
      isValid = false;
    }
    if (!rollNumber) {
      errorRoll.classList.remove("hidden");
      isValid = false;
    }
    if (!email || !email.includes("@")) {
      errorEmail.classList.remove("hidden");
      isValid = false;
    }

    if (!isValid) {
      return;
    }

    // Set loading state on submit button
    submitRegBtn.disabled = true;
    submitBtnSpinner.classList.remove("hidden");
    submitBtnText.textContent = "Registering...";

    try {
      const response = await fetch(`/api/events/${eventId}/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          student_name: studentName,
          roll_number: rollNumber,
          email: email,
          phone: phone || null
        })
      });

      const data = await response.json();

      if (response.status === 201) {
        // Step 7: On success (201), show clear confirmation message with event name
        formSuccessAlert.classList.remove("hidden");
        formSuccessText.textContent = `Congratulations, ${studentName}! You are officially registered for "${activeEventData.title}". A confirmation has been recorded.`;
        registrationForm.reset();

        // Refresh events list to reflect updated seat count
        await fetchEvents();

        // Also update seats in current open modal
        if (activeEventData) {
          activeEventData.available_seats = Math.max(0, activeEventData.available_seats - 1);
          modalEventSeats.innerHTML = `<span class="text-emerald-600 font-bold">${activeEventData.available_seats}</span> / ${activeEventData.capacity} seats remaining`;
        }

        // Auto close modal after 2.5 seconds
        setTimeout(() => {
          closeModal();
        }, 2200);

      } else {
        // Step 7: On failure (400/409), show exact error message the server sent back
        formErrorAlert.classList.remove("hidden");
        formErrorText.textContent = data.detail || "Registration failed. Please try again.";
      }
    } catch (err) {
      console.error("Registration request failed:", err);
      formErrorAlert.classList.remove("hidden");
      formErrorText.textContent = "Network error: unable to reach the registration server.";
    } finally {
      submitRegBtn.disabled = false;
      submitBtnSpinner.classList.add("hidden");
      submitBtnText.textContent = "Confirm Registration";
    }
  });

  // Modal close triggers
  closeModalBtn.addEventListener("click", closeModal);
  cancelModalBtn.addEventListener("click", closeModal);
  detailModal.addEventListener("click", (e) => {
    if (e.target === detailModal) closeModal();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !detailModal.classList.contains("hidden")) {
      closeModal();
    }
  });

  // Category filter buttons click handler
  categoryButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      categoryButtons.forEach(b => {
        b.classList.remove("bg-indigo-600", "text-white", "shadow-indigo-200");
        b.classList.add("bg-white", "text-slate-700", "border-slate-200");
      });

      btn.classList.remove("bg-white", "text-slate-700", "border-slate-200");
      btn.classList.add("bg-indigo-600", "text-white", "shadow-indigo-200");

      currentCategory = btn.getAttribute("data-category");
      fetchEvents();
    });
  });

  // Search input change with debounce
  searchInput.addEventListener("input", (e) => {
    const val = e.target.value;
    currentSearch = val;
    if (val.length > 0) {
      clearSearchBtn.classList.remove("hidden");
    } else {
      clearSearchBtn.classList.add("hidden");
    }

    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
      fetchEvents();
    }, 250);
  });

  clearSearchBtn.addEventListener("click", () => {
    searchInput.value = "";
    currentSearch = "";
    clearSearchBtn.classList.add("hidden");
    fetchEvents();
  });

  retryBtn.addEventListener("click", fetchEvents);

  resetFiltersBtn.addEventListener("click", () => {
    currentSearch = "";
    searchInput.value = "";
    clearSearchBtn.classList.add("hidden");
    currentCategory = "All";
    categoryButtons.forEach(b => {
      if (b.getAttribute("data-category") === "All") {
        b.classList.remove("bg-white", "text-slate-700", "border-slate-200");
        b.classList.add("bg-indigo-600", "text-white", "shadow-indigo-200");
      } else {
        b.classList.remove("bg-indigo-600", "text-white", "shadow-indigo-200");
        b.classList.add("bg-white", "text-slate-700", "border-slate-200");
      }
    });
    fetchEvents();
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
  fetchEvents();
});
