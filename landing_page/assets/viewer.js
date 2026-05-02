const state = {
  base: defaultRegistryBase(),
  root: null,
  status: null,
  packages: null,
  intents: null,
  capabilities: [],
  activePath: "status/index.json",
  activeKind: "status",
  activeId: null,
  payload: null,
  errors: []
};

const endpoints = [
  { id: "root", title: "GET /v0", path: "index.json", description: "Registry root entrypoint" },
  { id: "status", title: "GET /v0/status", path: "status/index.json", description: "Availability and counts" },
  { id: "packages", title: "GET /v0/packages", path: "packages/index.json", description: "Package index" },
  { id: "package-template", title: "GET /v0/packages/{package_id}", description: "Select a package to load this endpoint" },
  { id: "version-template", title: "GET /v0/packages/{package_id}/versions/{version}", description: "Select a package version to load this endpoint" },
  { id: "capability-template", title: "GET /v0/capabilities/{capability_id}/packages", description: "Select a capability to load this endpoint" },
  { id: "intents", title: "GET /v0/intents", path: "intents/index.json", description: "Observed intent catalog" },
  { id: "intent-template", title: "GET /v0/intents/{intent_id}", description: "Select an intent to load this endpoint" },
  { id: "intent-packages-template", title: "GET /v0/intents/{intent_id}/packages", description: "Select an intent, then open package matches" }
];

const form = document.querySelector("#registry-form");
const baseInput = document.querySelector("#registry-base");
const loadStatus = document.querySelector("#load-status");
const endpointList = document.querySelector("#endpoint-list");
const packageList = document.querySelector("#package-list");
const intentList = document.querySelector("#intent-list");
const capabilityList = document.querySelector("#capability-list");
const detailPanel = document.querySelector("#detail-panel");
const jsonOutput = document.querySelector("#json-output");
const jsonTitle = document.querySelector("#json-title");
const rawLink = document.querySelector("#raw-link");

document.addEventListener("DOMContentLoaded", () => {
  baseInput.value = state.base;
  bindFilters();
  bindActions();
  loadRegistry();
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  state.base = normalizeRegistryBase(baseInput.value);
  baseInput.value = state.base;
  loadRegistry();
});

function defaultRegistryBase() {
  const params = new URLSearchParams(window.location.search);
  const registry = params.get("registry");
  if (registry) {
    return normalizeRegistryBase(registry);
  }
  if (window.location.protocol === "file:") {
    return "https://0al-spec.github.io/SpecPM/v0/";
  }
  return new URL("../v0/", window.location.href).href;
}

function normalizeRegistryBase(value) {
  const fallback = "https://0al-spec.github.io/SpecPM/v0/";
  const trimmed = String(value || "").trim();
  if (!trimmed) {
    return fallback;
  }
  try {
    const url = new URL(trimmed, window.location.href);
    const marker = url.pathname.indexOf("/v0");
    if (marker >= 0) {
      url.pathname = url.pathname.slice(0, marker + 3) + "/";
    } else {
      url.pathname = url.pathname.replace(/\/?$/, "/v0/");
    }
    url.search = "";
    url.hash = "";
    return url.href;
  } catch (_error) {
    return fallback;
  }
}

async function loadRegistry() {
  state.errors = [];
  setLoadStatus("loading", "Loading static registry metadata...");
  renderEndpointList();
  try {
    const [root, status, packages, intents] = await Promise.all([
      fetchOptional("index.json"),
      fetchRequired("status/index.json"),
      fetchRequired("packages/index.json"),
      fetchOptional("intents/index.json")
    ]);

    state.root = root;
    state.status = status;
    state.packages = packages;
    state.intents = intents || emptyIntentIndex();
    state.capabilities = collectCapabilities(state.packages);
    state.payload = state.status;
    state.activePath = "status/index.json";
    state.activeKind = "status";
    state.activeId = null;

    setLoadStatus("ok", `Loaded ${state.base}`);
    renderAll();
  } catch (error) {
    state.errors.push(error.message);
    setLoadStatus("error", error.message);
    renderAll();
  }
}

async function fetchRequired(path) {
  const response = await fetch(resourceUrl(path), { headers: { Accept: "application/json" } });
  if (!response.ok) {
    throw new Error(`${path} returned HTTP ${response.status}`);
  }
  return response.json();
}

async function fetchOptional(path) {
  try {
    return await fetchRequired(path);
  } catch (error) {
    state.errors.push(`${path}: ${error.message}`);
    return null;
  }
}

function resourceUrl(path) {
  return new URL(path, state.base).href;
}

function emptyIntentIndex() {
  return {
    apiVersion: "specpm.registry/v0",
    schemaVersion: 1,
    kind: "RemoteIntentIndex",
    status: "ok",
    catalog: {
      authority: "observed_metadata_only",
      canonical: false,
      description: "No observed intent catalog was found at this registry."
    },
    intent_count: 0,
    intents: []
  };
}

function collectCapabilities(packageIndex) {
  const seen = new Map();
  for (const pkg of packageIndex?.packages || []) {
    for (const capability of pkg.capabilities || []) {
      const entry = seen.get(capability) || { id: capability, packages: [] };
      entry.packages.push(pkg.package_id);
      seen.set(capability, entry);
    }
  }
  return [...seen.values()].sort((left, right) => left.id.localeCompare(right.id));
}

function renderAll() {
  renderSummary();
  renderEndpointList();
  renderPackageList();
  renderIntentList();
  renderCapabilityList();
  renderDetail();
  renderJson();
}

function setLoadStatus(kind, message) {
  const className = kind === "ok" ? "live" : "warn";
  const label = kind === "ok" ? "Live" : kind === "loading" ? "Loading" : "Issue";
  loadStatus.innerHTML = `<span class="pill ${className}">${escapeHtml(label)}</span><span class="status-message">${escapeHtml(message)}</span>`;
}

function renderSummary() {
  const registry = state.status?.registry || {};
  const cards = [
    ["Packages", registry.package_count ?? packageItems().length],
    ["Versions", registry.version_count ?? 0],
    ["Capabilities", registry.capability_count ?? state.capabilities.length],
    ["Observed intents", registry.intent_count ?? intentItems().length]
  ];
  document.querySelector("#summary-grid").innerHTML = cards.map(([label, value]) => `
    <article class="summary-card">
      <span class="panel-title">${escapeHtml(label)}</span>
      <div class="value">${escapeHtml(String(value))}</div>
    </article>
  `).join("");
}

function renderEndpointList() {
  endpointList.innerHTML = endpoints.map((endpoint) => `
    ${endpoint.path ? `<button class="list-item ${state.activeKind === endpoint.id ? "active" : ""}" data-action="endpoint" data-path="${escapeAttr(endpoint.path)}" data-kind="${escapeAttr(endpoint.id)}">` : `<div class="list-item static">`}
      <span class="list-id">${escapeHtml(endpoint.title)}</span>
      <span class="list-meta">${escapeHtml(endpoint.description)}</span>
    ${endpoint.path ? `</button>` : `</div>`}
  `).join("");
}

function renderPackageList() {
  const filter = getFilter("#package-filter");
  const packages = packageItems().filter((pkg) => matchesFilter(pkg.package_id, pkg.name, filter));
  document.querySelector("#package-count").textContent = String(packageItems().length);
  packageList.innerHTML = packages.length ? packages.map((pkg) => `
    <button class="list-item ${state.activeKind === "package" && state.activeId === pkg.package_id ? "active" : ""}" data-action="package" data-id="${escapeAttr(pkg.package_id)}">
      <span class="list-id">${escapeHtml(pkg.package_id)}</span>
      <span class="list-meta">${escapeHtml(pkg.name || "")} - ${escapeHtml(pkg.latest_version || "")}</span>
    </button>
  `).join("") : `<div class="empty">No packages match this filter.</div>`;
}

function renderIntentList() {
  const filter = getFilter("#intent-filter");
  const intents = intentItems().filter((intent) => matchesFilter(intent.intent_id, intent.capabilities?.join(" "), filter));
  document.querySelector("#intent-count").textContent = String(intentItems().length);
  intentList.innerHTML = intents.length ? intents.map((intent) => `
    <button class="list-item ${state.activeKind === "intent" && state.activeId === intent.intent_id ? "active" : ""}" data-action="intent" data-id="${escapeAttr(intent.intent_id)}">
      <span class="list-id">${escapeHtml(intent.intent_id)}</span>
      <span class="list-meta">${escapeHtml(String(intent.package_count || 0))} package(s), ${escapeHtml(String(intent.capability_count || 0))} capability match(es)</span>
    </button>
  `).join("") : `<div class="empty">No intents match this filter.</div>`;
}

function renderCapabilityList() {
  const filter = getFilter("#capability-filter");
  const capabilities = state.capabilities.filter((capability) => matchesFilter(capability.id, capability.packages.join(" "), filter));
  document.querySelector("#capability-count").textContent = String(state.capabilities.length);
  capabilityList.innerHTML = capabilities.length ? capabilities.map((capability) => `
    <button class="list-item ${state.activeKind === "capability" && state.activeId === capability.id ? "active" : ""}" data-action="capability" data-id="${escapeAttr(capability.id)}">
      <span class="list-id">${escapeHtml(capability.id)}</span>
      <span class="list-meta">${escapeHtml(String(capability.packages.length))} package source(s)</span>
    </button>
  `).join("") : `<div class="empty">No capabilities match this filter.</div>`;
}

function renderDetail() {
  if (state.errors.length && !state.status) {
    detailPanel.innerHTML = `
      <div class="detail-head">
        <div class="detail-title">
          <span class="pill warn">Unavailable</span>
          <h2>Registry metadata could not be loaded.</h2>
          <p>${escapeHtml(state.errors.join(" "))}</p>
        </div>
      </div>
    `;
    return;
  }

  if (state.activeKind === "package") {
    renderPackageDetail();
    return;
  }
  if (state.activeKind === "version") {
    renderVersionDetail();
    return;
  }
  if (state.activeKind === "capability") {
    renderCapabilityDetail();
    return;
  }
  if (state.activeKind === "intent") {
    renderIntentDetail();
    return;
  }
  if (state.activeKind === "intent-packages") {
    renderIntentPackagesDetail();
    return;
  }
  renderEndpointDetail();
}

function renderEndpointDetail() {
  const registry = state.status?.registry || {};
  detailPanel.innerHTML = `
    <div class="detail-head">
      <div class="detail-title">
        <span class="pill live">Static JSON</span>
        <h2>${escapeHtml(endpointTitle(state.activeKind))}</h2>
        <p>${escapeHtml(endpointDescription(state.activeKind))}</p>
      </div>
      <div class="actions">
        <a class="btn small" href="${escapeAttr(resourceUrl(state.activePath))}" target="_blank" rel="noopener">Open Raw</a>
      </div>
    </div>
    <div class="facts">
      <div class="fact"><span>Profile</span><strong>${escapeHtml(registry.profile || "unknown")}</strong></div>
      <div class="fact"><span>Authority</span><strong>${escapeHtml(registry.authority || "metadata_only")}</strong></div>
      <div class="fact"><span>API Version</span><strong>${escapeHtml(registry.api_version || "v0")}</strong></div>
      <div class="fact"><span>Read Only</span><strong>${escapeHtml(String(registry.read_only ?? true))}</strong></div>
    </div>
    ${state.errors.length ? `<div class="error">${escapeHtml(state.errors.join(" "))}</div>` : ""}
  `;
}

function renderPackageDetail() {
  const pkg = state.payload?.package || state.payload;
  const versions = pkg?.versions || [];
  detailPanel.innerHTML = `
    <div class="detail-head">
      <div class="detail-title">
        <span class="pill live">Package</span>
        <h2>${escapeHtml(pkg?.package_id || state.activeId || "Package")}</h2>
        <p>${escapeHtml(pkg?.summary || "")}</p>
      </div>
      <div class="actions">
        <a class="btn small" href="${escapeAttr(resourceUrl(state.activePath))}" target="_blank" rel="noopener">Open Raw</a>
      </div>
    </div>
    <div class="facts">
      <div class="fact"><span>Name</span><strong>${escapeHtml(pkg?.name || "")}</strong></div>
      <div class="fact"><span>Latest</span><strong>${escapeHtml(pkg?.latest_version || "")}</strong></div>
      <div class="fact"><span>License</span><strong>${escapeHtml(pkg?.license || "")}</strong></div>
      <div class="fact"><span>Versions</span><strong>${escapeHtml(String(versions.length))}</strong></div>
    </div>
    <h3>Versions</h3>
    <div class="token-list">
      ${versions.map((version) => `<button class="token" data-action="version" data-package="${escapeAttr(pkg.package_id)}" data-version="${escapeAttr(version.version)}">${escapeHtml(version.version)}</button>`).join("")}
    </div>
    <h3 style="margin-top: 24px;">Capabilities</h3>
    <div class="token-list">
      ${(pkg?.capabilities || []).map((capability) => `<button class="token" data-action="capability" data-id="${escapeAttr(capability)}">${escapeHtml(capability)}</button>`).join("") || `<span class="empty">No capabilities listed.</span>`}
    </div>
    <h3 style="margin-top: 24px;">Observed Intents</h3>
    <div class="token-list">
      ${(pkg?.intents || []).map((intent) => `<button class="token" data-action="intent" data-id="${escapeAttr(intent)}">${escapeHtml(intent)}</button>`).join("") || `<span class="empty">No observed intents listed.</span>`}
    </div>
  `;
}

function renderVersionDetail() {
  const pkg = state.payload?.package || {};
  detailPanel.innerHTML = `
    <div class="detail-head">
      <div class="detail-title">
        <span class="pill live">Version</span>
        <h2>${escapeHtml(pkg.package_id || "")}@${escapeHtml(pkg.version || "")}</h2>
        <p>${escapeHtml(pkg.summary || "")}</p>
      </div>
      <div class="actions">
        <a class="btn small" href="${escapeAttr(resourceUrl(state.activePath))}" target="_blank" rel="noopener">Open Raw</a>
      </div>
    </div>
    <div class="facts">
      <div class="fact"><span>Digest</span><strong>${escapeHtml(pkg.source?.digest?.value || "")}</strong></div>
      <div class="fact"><span>Archive Size</span><strong>${escapeHtml(String(pkg.source?.size || 0))}</strong></div>
      <div class="fact"><span>Yanked</span><strong>${escapeHtml(String(pkg.state?.yanked ?? false))}</strong></div>
      <div class="fact"><span>Deprecated</span><strong>${escapeHtml(String(pkg.state?.deprecated ?? false))}</strong></div>
    </div>
    <div class="actions">
      <a class="btn small" href="${escapeAttr(pkg.source?.url || "#")}" target="_blank" rel="noopener">Archive</a>
      <button class="btn small" data-action="package" data-id="${escapeAttr(pkg.package_id || "")}">Back to package</button>
    </div>
  `;
}

function renderCapabilityDetail() {
  const results = state.payload?.results || [];
  detailPanel.innerHTML = `
    <div class="detail-head">
      <div class="detail-title">
        <span class="pill live">Capability Lookup</span>
        <h2>${escapeHtml(state.activeId || "")}</h2>
        <p>Exact reverse lookup for packages that provide this capability.</p>
      </div>
      <div class="actions">
        <a class="btn small" href="${escapeAttr(resourceUrl(state.activePath))}" target="_blank" rel="noopener">Open Raw</a>
      </div>
    </div>
    <div class="facts">
      <div class="fact"><span>Match</span><strong>exact</strong></div>
      <div class="fact"><span>Results</span><strong>${escapeHtml(String(results.length))}</strong></div>
    </div>
    <div class="token-list">
      ${results.map((result) => `<button class="token" data-action="package" data-id="${escapeAttr(result.package_id)}">${escapeHtml(result.package_id)}@${escapeHtml(result.version)}</button>`).join("") || `<span class="empty">No package matches.</span>`}
    </div>
  `;
}

function renderIntentDetail() {
  const intent = state.payload?.intent || {};
  detailPanel.innerHTML = `
    <div class="detail-head">
      <div class="detail-title">
        <span class="pill live">Observed Intent</span>
        <h2>${escapeHtml(intent.intent_id || state.activeId || "")}</h2>
        <p>Observed metadata from accepted packages. This is not a canonical dictionary entry.</p>
      </div>
      <div class="actions">
        <a class="btn small" href="${escapeAttr(resourceUrl(state.activePath))}" target="_blank" rel="noopener">Open Raw</a>
        <button class="btn small" data-action="intent-packages" data-id="${escapeAttr(intent.intent_id || state.activeId || "")}">Packages</button>
      </div>
    </div>
    <div class="facts">
      <div class="fact"><span>Status</span><strong>${escapeHtml(intent.status || "observed")}</strong></div>
      <div class="fact"><span>Canonical</span><strong>${escapeHtml(String(intent.canonical ?? false))}</strong></div>
      <div class="fact"><span>Packages</span><strong>${escapeHtml(String(intent.package_count || 0))}</strong></div>
      <div class="fact"><span>Capabilities</span><strong>${escapeHtml(String(intent.capability_count || 0))}</strong></div>
    </div>
    <h3>Capability Matches</h3>
    <div class="token-list">
      ${(intent.capabilities || []).map((capability) => `<button class="token" data-action="capability" data-id="${escapeAttr(capability)}">${escapeHtml(capability)}</button>`).join("") || `<span class="empty">No capability matches.</span>`}
    </div>
  `;
}

function renderIntentPackagesDetail() {
  const results = state.payload?.results || [];
  detailPanel.innerHTML = `
    <div class="detail-head">
      <div class="detail-title">
        <span class="pill live">Intent Package Lookup</span>
        <h2>${escapeHtml(state.activeId || "")}</h2>
        <p>Exact reverse lookup for packages that declare this observed intent.</p>
      </div>
      <div class="actions">
        <a class="btn small" href="${escapeAttr(resourceUrl(state.activePath))}" target="_blank" rel="noopener">Open Raw</a>
      </div>
    </div>
    <div class="facts">
      <div class="fact"><span>Match</span><strong>exact</strong></div>
      <div class="fact"><span>Results</span><strong>${escapeHtml(String(results.length))}</strong></div>
    </div>
    <div class="token-list">
      ${results.map((result) => `<button class="token" data-action="package" data-id="${escapeAttr(result.package_id)}">${escapeHtml(result.package_id)}@${escapeHtml(result.version)}</button>`).join("") || `<span class="empty">No package matches.</span>`}
    </div>
  `;
}

function renderJson() {
  jsonTitle.textContent = formatPayloadKind(state.payload?.kind);
  jsonOutput.textContent = JSON.stringify(state.payload || { errors: state.errors }, null, 2);
  rawLink.href = resourceUrl(state.activePath || "status/index.json");
}

function bindFilters() {
  for (const selector of ["#package-filter", "#intent-filter", "#capability-filter"]) {
    document.querySelector(selector).addEventListener("input", () => {
      renderPackageList();
      renderIntentList();
      renderCapabilityList();
    });
  }
}

function bindActions() {
  document.body.addEventListener("click", async (event) => {
    const target = event.target.closest("[data-action]");
    if (!target) {
      return;
    }
    const action = target.dataset.action;
    try {
      if (action === "endpoint") {
        await showEndpoint(target.dataset.kind, target.dataset.path);
      } else if (action === "package") {
        await showPackage(target.dataset.id);
      } else if (action === "version") {
        await showVersion(target.dataset.package, target.dataset.version);
      } else if (action === "capability") {
        await showCapability(target.dataset.id);
      } else if (action === "intent") {
        await showIntent(target.dataset.id);
      } else if (action === "intent-packages") {
        await showIntentPackages(target.dataset.id);
      }
    } catch (error) {
      state.payload = { status: "invalid", error: { message: error.message } };
      state.errors.push(error.message);
      setLoadStatus("error", error.message);
      renderDetail();
      renderJson();
    }
  });
}

async function showEndpoint(kind, path) {
  state.activeKind = kind;
  state.activeId = null;
  state.activePath = path;
  if (kind === "root") {
    state.payload = state.root || await fetchRequired(path);
  } else if (kind === "status") {
    state.payload = state.status;
  } else if (kind === "packages") {
    state.payload = state.packages;
  } else if (kind === "intents") {
    state.payload = state.intents;
  } else {
    state.payload = await fetchRequired(path);
  }
  renderAll();
}

async function showPackage(packageId) {
  state.activeKind = "package";
  state.activeId = packageId;
  state.activePath = `packages/${segment(packageId)}/index.json`;
  state.payload = await fetchRequired(state.activePath);
  renderAll();
}

async function showVersion(packageId, version) {
  state.activeKind = "version";
  state.activeId = `${packageId}@${version}`;
  state.activePath = `packages/${segment(packageId)}/versions/${segment(version)}/index.json`;
  state.payload = await fetchRequired(state.activePath);
  renderAll();
}

async function showCapability(capabilityId) {
  state.activeKind = "capability";
  state.activeId = capabilityId;
  state.activePath = `capabilities/${segment(capabilityId)}/packages/index.json`;
  state.payload = await fetchRequired(state.activePath);
  renderAll();
}

async function showIntent(intentId) {
  state.activeKind = "intent";
  state.activeId = intentId;
  state.activePath = `intents/${segment(intentId)}/index.json`;
  state.payload = await fetchRequired(state.activePath);
  renderAll();
}

async function showIntentPackages(intentId) {
  state.activeKind = "intent-packages";
  state.activeId = intentId;
  state.activePath = `intents/${segment(intentId)}/packages/index.json`;
  state.payload = await fetchRequired(state.activePath);
  renderAll();
}

function packageItems() {
  return state.packages?.packages || [];
}

function intentItems() {
  return state.intents?.intents || [];
}

function segment(value) {
  return encodeURIComponent(String(value || ""));
}

function getFilter(selector) {
  return document.querySelector(selector).value.trim().toLowerCase();
}

function matchesFilter(primary, secondary, filter) {
  if (!filter) {
    return true;
  }
  return `${primary || ""} ${secondary || ""}`.toLowerCase().includes(filter);
}

function endpointTitle(kind) {
  const endpoint = endpoints.find((item) => item.id === kind);
  return endpoint ? endpoint.title : "Registry Endpoint";
}

function endpointDescription(kind) {
  const endpoint = endpoints.find((item) => item.id === kind);
  return endpoint ? endpoint.description : "Static registry payload.";
}

function formatPayloadKind(kind) {
  if (!kind) {
    return "Raw payload";
  }
  return String(kind)
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/[_-]+/g, " ")
    .toLowerCase()
    .replace(/^./, (first) => first.toUpperCase());
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value);
}