// ========================================
// State Management
// ========================================
let sessionId = generateSessionId();
let conversationHistory = [];
let intelligence = {
  bank_accounts: [],
  upi_ids: [],
  phone_numbers: [],
  phishing_links: [],
  suspicious_keywords: [],
};
let scamInfo = null;
let isUserScrolledUp = false;
const MAX_CHAR_COUNT = 500;

// ========================================
// Initialization
// ========================================
document.addEventListener("DOMContentLoaded", () => {
  loadConfig();
  updateSessionDisplay();
  checkHealth();
  setInterval(refreshMetrics, 30000);
  setupScrollObserver();
  updateCharCounter();
});

// ========================================
// API Functions
// ========================================
function getApiUrl() {
  const url = document.getElementById("apiUrl").value.trim().replace(/\/$/, "");
  // If empty, use the current origin (works for both local and deployed)
  return url || window.location.origin;
}

function getApiKey() {
  return document.getElementById("apiKey").value.trim();
}

async function checkHealth() {
  const healthEl = document.getElementById("healthStatus");
  const statusCard = document.getElementById("statusHealth");

  try {
    const response = await fetch(`${getApiUrl()}/health`, {
      headers: getApiKey() ? { "x-api-key": getApiKey() } : {},
    });

    if (response.ok) {
      const data = await response.json();
      healthEl.textContent = "Healthy";
      healthEl.className = "status-value healthy";
      statusCard.classList.remove("warning");
      document.getElementById("activeSessions").textContent =
        data.active_sessions || 0;
      showToast("Connected to API successfully!", "success");
      refreshMetrics();
    } else {
      const errorData = await parseErrorResponse(response);
      throw new Error(errorData.message);
    }
  } catch (error) {
    healthEl.textContent = "Offline";
    healthEl.className = "status-value error";
    statusCard.classList.add("warning");
    showToast(`Connection failed: ${error.message}`, "error");
  }
}

async function parseErrorResponse(response) {
  try {
    const data = await response.json();
    return {
      message:
        data.detail ||
        data.message ||
        `HTTP ${response.status}: ${response.statusText}`,
      status: response.status,
    };
  } catch (e) {
    return {
      message: `HTTP ${response.status}: ${response.statusText}`,
      status: response.status,
    };
  }
}

async function refreshMetrics() {
  try {
    // Fetch info endpoint for rate limits
    const rootRes = await fetch(`${getApiUrl()}/info`, {
      headers: getApiKey() ? { "x-api-key": getApiKey() } : {},
    });

    if (rootRes.ok) {
      const rootData = await rootRes.json();
      if (rootData.rate_limits) {
        document.getElementById("rpmStatus").textContent =
          rootData.rate_limits.rpm || "-/30";
      }
    }

    // Fetch metrics
    const metricsRes = await fetch(`${getApiUrl()}/metrics`, {
      headers: getApiKey() ? { "x-api-key": getApiKey() } : {},
    });

    if (metricsRes.ok) {
      const metricsData = await metricsRes.json();
      document.getElementById("scamsDetected").textContent =
        metricsData.scams_detected || 0;
      document.getElementById("activeSessions").textContent =
        metricsData.total_sessions || 0;
    }
  } catch (error) {
    console.log("Metrics refresh failed:", error);
  }
}

async function sendMessage() {
  const input = document.getElementById("messageInput");
  const sendBtn = document.getElementById("sendBtn");
  const sendIcon = document.getElementById("sendIcon");
  const sendLoading = document.getElementById("sendLoading");

  const text = input.value.trim();
  if (!text) return;

  // Disable button and show loading
  sendBtn.disabled = true;
  sendIcon.style.display = "none";
  sendLoading.style.display = "block";

  // Add user message to UI
  const sender = "scammer";
  addMessage(text, sender);
  input.value = "";
  autoResizeTextarea(input);
  updateCharCounter();

  // Show typing indicator
  showTypingIndicator();

  // Build request
  const timestamp = Date.now();
  const message = { sender, text, timestamp };

  conversationHistory.push(message);

  const requestBody = {
    sessionId: sessionId,
    message: message,
    conversationHistory: conversationHistory.slice(0, -1),
    metadata: {
      channel: "web",
      language: "English",
      locale: "IN",
    },
  };

  try {
    const response = await fetch(`${getApiUrl()}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": getApiKey(),
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorData = await parseErrorResponse(response);
      throw new Error(errorData.message);
    }

    const data = await response.json();

    // Hide typing indicator
    hideTypingIndicator();

    let replyText = data.reply || data.response || "No response received";

    // Robustness check: if reply is a JSON string, parse it
    if (
      typeof replyText === "string" &&
      (replyText.trim().startsWith("{") || replyText.trim().startsWith("["))
    ) {
      try {
        const parsed = JSON.parse(replyText);
        replyText =
          parsed.reply ||
          parsed.response ||
          (parsed.text ? parsed.text : replyText);
      } catch (e) {
        console.warn("Reply looked like JSON but failed to parse", e);
      }
    }

    if (replyText) {
      addMessage(replyText, "user");
      conversationHistory.push({
        sender: "user",
        text: replyText,
        timestamp: Date.now(),
      });
    }

    // Update intelligence panel with extracted data
    // Fetch intelligence from separate endpoint (chat response is status+reply only per requirements)
    try {
      const intelRes = await fetch(
        `${getApiUrl()}/api/intelligence?sessionId=${encodeURIComponent(sessionId)}`,
        { headers: getApiKey() ? { "x-api-key": getApiKey() } : {} },
      );
      if (intelRes.ok) {
        const intelData = await intelRes.json();
        if (intelData.intelligence) updateIntelligence(intelData.intelligence);
      }
    } catch (e) {
      console.log("Intelligence fetch failed:", e);
    }

    // Refresh metrics after each message
    refreshMetrics();
  } catch (error) {
    hideTypingIndicator();
    addMessage(`Error: ${error.message}`, "system");
    showToast(`Failed to send message: ${error.message}`, "error");
  } finally {
    sendBtn.disabled = false;
    sendIcon.style.display = "block";
    sendLoading.style.display = "none";
  }
}

// ========================================
// UI Functions
// ========================================
function addMessage(text, sender) {
  const container = document.getElementById("chatMessages");
  const wrapper = document.createElement("div");
  wrapper.className = `message-wrapper ${sender}`;

  const avatarEmoji =
    sender === "scammer"
      ? '<i class="fa-solid fa-triangle-exclamation" style="color: #fcd115;"></i>'
      : sender === "user"
        ? '<i class="fa-solid fa-robot" style="color: #ffffff;"></i>'
        : '<i class="fa-solid fa-bullhorn" style="color: #8b5cf6;"></i>';

  const senderLabel =
    sender === "scammer"
      ? "Scammer"
      : sender === "user"
        ? "Honeypot AI"
        : "System";

  const timestamp = formatTimestamp(new Date());
  const readStatus =
    sender === "scammer" ? "delivered" : sender === "user" ? "read" : "";

  wrapper.innerHTML = `
    <div class="message-avatar ${sender}">${avatarEmoji}</div>
    <div class="message ${sender}">
      ${
        sender !== "system"
          ? `
        <div class="message-header">
          <div class="message-sender">${senderLabel}</div>
          <div class="message-timestamp">${timestamp}</div>
        </div>
      `
          : ""
      }
      <div class="message-text">${escapeHtml(text)}</div>
      ${
        readStatus
          ? `
        <div class="message-footer">
          <span class="read-indicator ${readStatus}">${readStatus === "read" ? '<i class="fa-solid fa-check-double" style="color: #3b82f6;"></i>' : '<i class="fa-solid fa-check" style="color: #6b7280;"></i>'}</span>
        </div>
      `
          : ""
      }
    </div>
  `;

  container.appendChild(wrapper);
  smartScroll();
}

function updateIntelligence(intel) {
  if (!intel) return;

  // Merge new intelligence
  for (const key in intel) {
    if (intelligence[key] && intel[key]) {
      const existing = new Set(intelligence[key]);
      intel[key].forEach((item) => existing.add(item));
      intelligence[key] = Array.from(existing);
    }
  }

  // Update UI
  updateIntelSection("bankAccounts", "bankCount", intelligence.bank_accounts);
  updateIntelSection("upiIds", "upiCount", intelligence.upi_ids);
  updateIntelSection("phoneNumbers", "phoneCount", intelligence.phone_numbers);
  updateIntelSection("phishingLinks", "linkCount", intelligence.phishing_links);
}

function updateIntelSection(containerId, countId, items) {
  const container = document.getElementById(containerId);
  const countBadge = document.getElementById(countId);

  countBadge.textContent = items.length;

  if (items.length === 0) {
    container.innerHTML =
      '<span class="intel-empty">No data extracted yet</span>';
  } else {
    container.innerHTML = items
      .map((item) => `<span class="intel-item">${escapeHtml(item)}</span>`)
      .join("");
  }
}

function showScamAlert(scamType, confidence, persona) {
  const panel = document.getElementById("scamAlertPanel");
  document.getElementById("scamType").textContent = scamType || "Unknown";
  document.getElementById("scamConfidence").textContent = Math.round(
    confidence * 100,
  );
  document.getElementById("scamPersona").textContent = persona || "Unknown";
  document.getElementById("confidenceBar").style.width = `${confidence * 100}%`;
  panel.style.display = "block";
  scamInfo = { scamType, confidence, persona };
}

function resetSession() {
  sessionId = generateSessionId();
  conversationHistory = [];
  intelligence = {
    bank_accounts: [],
    upi_ids: [],
    phone_numbers: [],
    phishing_links: [],
    suspicious_keywords: [],
  };
  scamInfo = null;
  isUserScrolledUp = false;

  // Reset UI
  document.getElementById("chatMessages").innerHTML = `
    <div class="message-wrapper system">
      <div class="message-avatar system"><i class="fa-solid fa-bullhorn" style="color: #8b5cf6;"></i></div>
      <div class="message system">
        <div class="message-text">New session started. Enter a scam message to test the honeypot.</div>
      </div>
    </div>
  `;
  document.getElementById("scamAlertPanel").style.display = "none";
  document.getElementById("newMessageIndicator").classList.remove("visible");

  updateIntelSection("bankAccounts", "bankCount", []);
  updateIntelSection("upiIds", "upiCount", []);
  updateIntelSection("phoneNumbers", "phoneCount", []);
  updateIntelSection("phishingLinks", "linkCount", []);

  updateSessionDisplay();
  showToast("New session started", "success");
}

function updateSessionDisplay() {
  document.getElementById("sessionIdDisplay").textContent = sessionId.slice(
    0,
    30,
  );
}

function insertQuickMessage(type) {
  const messages = {
    lottery:
      "Congratulations! You've won ₹50,00,000 in our Lucky Draw! Send ₹2,500 processing fee to claim. Contact: 9876543210 or pay at lottery.claim-now.tk",
    bank: "Dear customer, your SBI account is blocked due to KYC expiry. Update immediately at sbi-kyc-update.com or call 8203549852. Ignore to lose access.",
    job: "Hi! Work from home opportunity! Earn ₹15,000/day. No experience needed. Pay ₹500 registration fee to join. UPI: job.recruiter@ybl",
    kyc: "Your Paytm KYC is incomplete. Complete verification within 24 hours to avoid account suspension. Visit paytm-kyc-verify.in or transfer ₹1 to verify@paytm",
    delivery:
      "Your Amazon package #AWB7829341 is held at warehouse. Pay ₹49 delivery charge to release. Click: amazon-delivery-fee.in/pay or UPI: delivery.amt@ybl",
    investment:
      "URGENT: Bitcoin investment opportunity! Invest ₹10,000 today and get ₹1,50,000 in 7 days. Guaranteed returns! Join now: crypto-profit-india.com. WhatsApp: 7890123456",
    otp: "Dear user, your OTP for ₹24,999 transaction is 847291. If not initiated by you, call 9012345678 immediately to block your card. Do NOT share this OTP.",
    customs:
      "Indian Customs Notice: Your international parcel is held. Pay ₹3,200 customs duty within 24 hours or it will be returned. Pay at: customs-india-clearance.com. Ref: ICP/2026/89341",
    insurance:
      "ALERT: Your LIC policy #48291037 lapses TODAY. Renew immediately to avoid losing ₹12,00,000 coverage. Pay ₹1,999 renewal at lic-renew-online.in or call 8765432109",
    techsupport:
      "Microsoft Security Alert! Your Windows license has expired and your PC is infected with 3 viruses. Call our toll-free helpline 1800-585-8484 immediately. Visit: microsoft-support-india.tk",
  };

  const input = document.getElementById("messageInput");
  input.value = messages[type] || "";
  input.focus();
  autoResizeTextarea(input);
  updateCharCounter();
}

// ========================================
// Storage Functions
// ========================================
function saveConfig() {
  localStorage.setItem(
    "honeypot_api_url",
    document.getElementById("apiUrl").value,
  );
  localStorage.setItem(
    "honeypot_api_key",
    document.getElementById("apiKey").value,
  );
}

function loadConfig() {
  const savedUrl = localStorage.getItem("honeypot_api_url");
  const savedKey = localStorage.getItem("honeypot_api_key");

  // Only load saved URL if it's not a localhost URL on a deployed site
  // This prevents issues when the app is deployed but has cached localhost values
  if (savedUrl) {
    const isLocalhost =
      savedUrl.includes("localhost") || savedUrl.includes("127.0.0.1");
    const isDeployed =
      !window.location.hostname.includes("localhost") &&
      !window.location.hostname.includes("127.0.0.1");

    if (!(isLocalhost && isDeployed)) {
      document.getElementById("apiUrl").value = savedUrl;
    }
  }
  if (savedKey) document.getElementById("apiKey").value = savedKey;
}

// ========================================
// Utility Functions
// ========================================
function generateSessionId() {
  return (
    "sess_" +
    Date.now().toString(36) +
    "_" +
    Math.random().toString(36).substring(2, 9)
  );
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function showToast(message, type = "success") {
  const container = document.getElementById("toastContainer");
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;

  const icon =
    type === "success"
      ? '<i class="fa-solid fa-check" style="color: #10b981;"></i>'
      : type === "error"
        ? '<i class="fa-solid fa-xmark" style="color: #ef4444;"></i>'
        : '<i class="fa-solid fa-exclamation" style="color: #f59e0b;"></i>';
  toast.innerHTML = `<span style="font-size: 1.2rem;">${icon}</span><span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = "toast-in 0.3s ease reverse";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ========================================
// Enhanced Chat UX Functions
// ========================================

// Typing indicator
function showTypingIndicator() {
  const indicator = document.getElementById("typingIndicator");
  indicator.classList.add("visible");
  smartScroll();
}

function hideTypingIndicator() {
  const indicator = document.getElementById("typingIndicator");
  indicator.classList.remove("visible");
}

// Auto-resize textarea
function autoResizeTextarea(textarea) {
  textarea.style.height = "auto";
  const newHeight = Math.min(textarea.scrollHeight, 150);
  textarea.style.height = newHeight + "px";
}

// Handle textarea keydown (Enter to send, Shift+Enter for new line)
function handleInputKeydown(event) {
  if (event.key === "Enter") {
    if (event.shiftKey) {
      // Shift+Enter: allow default behavior (new line)
      return;
    } else {
      // Enter only: send message
      event.preventDefault();
      sendMessage();
    }
  }
}

// Character counter
function updateCharCounter() {
  const input = document.getElementById("messageInput");
  const counter = document.getElementById("charCounter");
  const count = input.value.length;

  counter.textContent = `${count}/${MAX_CHAR_COUNT}`;

  counter.classList.remove("warning", "error");
  if (count > MAX_CHAR_COUNT * 0.9) {
    counter.classList.add("error");
  } else if (count > MAX_CHAR_COUNT * 0.7) {
    counter.classList.add("warning");
  }
}

// Scroll observer for new message indicator
function setupScrollObserver() {
  const container = document.getElementById("chatMessages");

  container.addEventListener("scroll", () => {
    const isAtBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight <
      50;
    isUserScrolledUp = !isAtBottom;

    if (isAtBottom) {
      document
        .getElementById("newMessageIndicator")
        .classList.remove("visible");
    }
  });
}

// Smart scroll - auto scroll if at bottom, show indicator if scrolled up
function smartScroll() {
  const container = document.getElementById("chatMessages");

  if (!isUserScrolledUp) {
    container.scrollTo({
      top: container.scrollHeight,
      behavior: "smooth",
    });
  } else {
    document.getElementById("newMessageIndicator").classList.add("visible");
  }
}

// Scroll to bottom when clicking indicator
function scrollToBottom() {
  const container = document.getElementById("chatMessages");
  isUserScrolledUp = false;
  document.getElementById("newMessageIndicator").classList.remove("visible");
  container.scrollTo({
    top: container.scrollHeight,
    behavior: "smooth",
  });
}

// Format timestamp for messages
function formatTimestamp(date) {
  const now = new Date();
  const diff = now - date;

  // If less than a minute ago
  if (diff < 60000) {
    return "Just now";
  }

  // If today, show time
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  // Otherwise show date and time
  return date.toLocaleDateString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
