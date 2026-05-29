const apiBaseInput = document.createElement("input");
apiBaseInput.type = "hidden";

const state = {
  apiBase: localStorage.getItem("apiBaseUrl") || "http://127.0.0.1:8000",
  lastResponse: null,
};

const apiBaseUrl = () => {
  const saved = document.querySelector("#apiBaseUrl");
  return (saved?.value || state.apiBase || "http://127.0.0.1:8000").replace(/\/+$/, "");
};

function setStatus(text, variant = "warning") {
  const status = document.querySelector("#apiStatus");
  status.className = `badge badge-${variant}`;
  status.textContent = text;
}

function setResult(title, data, { markdown = "", warnings = [], errors = [], badge = "success" } = {}) {
  document.querySelector("#resultTitle").textContent = title;
  const resultBadge = document.querySelector("#resultBadge");
  resultBadge.className = `badge badge-${badge}`;
  resultBadge.textContent = badge;

  document.querySelector("#jsonPreview").textContent = JSON.stringify(data, null, 2);
  document.querySelector("#markdownPreview").textContent = markdown || "# No markdown available\n\nThe selected action did not return markdown.";

  const metrics = document.querySelector("#metrics");
  metrics.innerHTML = "";
  const metricItems = [
    ["Status", data?.status || data?.summary?.status || (data?.success ? "success" : "unknown")],
    ["Provider", data?.provider || data?.token_usage?.provider || data?.cost_usage?.provider || "—"],
    ["Model", data?.model || data?.token_usage?.model || data?.cost_usage?.model || "—"],
    ["Tokens", data?.total_tokens ?? data?.token_summary?.total_tokens ?? data?.token_usage?.total_tokens ?? "—"],
    ["Cost", data?.total_cost ?? data?.cost_summary?.total_cost ?? data?.cost_usage?.total_cost ?? "—"],
    ["Workflow", data?.workflow_type || data?.workflow_id || "—"],
  ];
  for (const [label, value] of metricItems) {
    const card = document.createElement("div");
    card.className = "metric-card";
    card.innerHTML = `<div class="label">${label}</div><div class="value">${escapeHtml(String(value ?? "—"))}</div>`;
    metrics.appendChild(card);
  }

  const messages = document.querySelector("#messages");
  messages.innerHTML = "";
  const sections = [
    ["Warnings", warnings, "warning"],
    ["Errors", errors, "error"],
  ];
  for (const [title, items, cls] of sections) {
    if (!items || !items.length) continue;
    const wrap = document.createElement("div");
    wrap.className = `message ${cls}`;
    wrap.innerHTML = `<strong>${title}</strong><ul>${items.map((item) => `<li>${escapeHtml(String(item))}</li>`).join("")}</ul>`;
    messages.appendChild(wrap);
  }
}

function escapeHtml(text) {
  return text.replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#39;",
  })[char]);
}

function formToObject(form) {
  const data = new FormData(form);
  const payload = {};
  for (const [key, value] of data.entries()) {
    const checkbox = form.querySelector(`[name="${key}"]`);
    if (checkbox && checkbox.type === "checkbox") {
      payload[key] = checkbox.checked;
    } else if (["platforms", "assets"].includes(key)) {
      payload[key] = String(value).split(",").map((item) => item.trim()).filter(Boolean);
    } else {
      payload[key] = String(value).trim();
    }
  }
  return payload;
}

async function callApi(path, payload = null, method = "GET") {
  const url = `${apiBaseUrl()}${path}`;
  const options = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (payload) options.body = JSON.stringify(payload);
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data?.errors?.[0] || data?.detail || `Request failed: ${response.status}`);
  }
  return data;
}

async function runRequest(title, path, payload, method = "POST") {
  setStatus("loading", "warning");
  document.querySelector("#resultTitle").textContent = title;
  document.querySelector("#jsonPreview").textContent = "Loading...";
  try {
    const result = await callApi(path, payload, method);
    state.lastResponse = result;
    const data = result.data || result;
    setResult(title, data, {
      markdown: data?.markdown || data?.markdown_report?.markdown || data?.reporting?.markdown_report?.markdown || "",
      warnings: result.warnings || data?.warnings || [],
      errors: result.errors || data?.errors || [],
      badge: result.success ? "success" : "warning",
    });
    setStatus("online", "success");
  } catch (error) {
    setStatus("error", "error");
    setResult(title, {}, { warnings: [], errors: [error.message], badge: "error" });
  }
}

function wireTabs() {
  document.querySelectorAll(".tab").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((tab) => tab.classList.remove("active"));
      document.querySelectorAll(".panel").forEach((panel) => panel.classList.remove("active"));
      button.classList.add("active");
      document.getElementById(button.dataset.panel).classList.add("active");
    });
  });
}

function wireForms() {
  document.getElementById("generateForm").addEventListener("submit", (event) => {
    event.preventDefault();
    runRequest("Generate Content", "/generate", formToObject(event.currentTarget));
  });
  document.getElementById("workflowForm").addEventListener("submit", (event) => {
    event.preventDefault();
    runRequest("Workflow Execution", "/workflow", formToObject(event.currentTarget));
  });
  document.getElementById("campaignForm").addEventListener("submit", (event) => {
    event.preventDefault();
    runRequest("Campaign Builder", "/campaign", formToObject(event.currentTarget));
  });
  document.getElementById("assetsForm").addEventListener("submit", (event) => {
    event.preventDefault();
    runRequest("Asset Planner", "/assets", formToObject(event.currentTarget));
  });
  document.getElementById("reportDemoBtn").addEventListener("click", async () => {
    const payload = {
      report_type: document.getElementById("markdownReportType").value || "workflow_report",
      title: "Markdown Report",
      brand: "wenzel_partner",
      workflow_result: state.lastResponse?.data?.workflow_result || state.lastResponse?.data?.workflow || {},
      pipeline_result: state.lastResponse?.data || {},
      campaign_result: state.lastResponse?.data?.campaign_result || {},
      asset_result: state.lastResponse?.data?.asset_result || state.lastResponse?.data?.asset_coordination_result || {},
      token_summary: state.lastResponse?.data?.token_summary || {},
      cost_summary: state.lastResponse?.data?.cost_summary || {},
      storage_summary: state.lastResponse?.data?.storage_summary || {},
      metadata: { source: "frontend" },
    };
    runRequest("Markdown Report", "/reports/markdown", payload);
  });
}

function wireTools() {
  document.getElementById("healthBtn").addEventListener("click", () => runRequest("Health Check", "/health", null, "GET"));
  document.getElementById("configBtn").addEventListener("click", () => runRequest("Config Summary", "/config", null, "GET"));
  document.getElementById("configBtnInline").addEventListener("click", () => runRequest("Config Summary", "/config", null, "GET"));
  document.getElementById("latestReportBtn").addEventListener("click", () => runRequest("Latest Report", "/reports/latest", null, "GET"));
  document.getElementById("listRecordsBtn").addEventListener("click", () => {
    const recordType = document.getElementById("recordType").value.trim();
    runRequest("Storage Records", recordType ? `/storage/records/${encodeURIComponent(recordType)}` : "/storage/records", null, "GET");
  });
}

async function bootstrap() {
  const apiBase = document.createElement("input");
  apiBase.id = "apiBaseUrl";
  apiBase.className = "input";
  apiBase.value = state.apiBase;
  apiBase.style.minWidth = "280px";
  const topbarActions = document.querySelector(".topbar-actions");
  topbarActions.insertBefore(apiBase, topbarActions.firstChild);

  apiBase.addEventListener("change", () => {
    state.apiBase = apiBase.value.trim() || "http://127.0.0.1:8000";
    localStorage.setItem("apiBaseUrl", state.apiBase);
  });

  wireTabs();
  wireForms();
  wireTools();

  try {
    const health = await callApi("/health", null, "GET");
    const config = await callApi("/config", null, "GET");
    const env = config.data?.app_env || "development";
    document.getElementById("envBadge").textContent = env;
    setStatus("online", "success");
    setResult("API Ready", { health, config }, { markdown: "# API Ready\n\nThe local API is available.", badge: "success" });
  } catch (error) {
    setStatus("offline", "error");
    setResult("API Unavailable", {}, { warnings: [], errors: [error.message], badge: "error" });
  }
}

bootstrap();
