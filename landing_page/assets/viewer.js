const state = {
  base: defaultRegistryBase(),
  root: null,
  status: null,
  packages: null,
  intents: null,
  capabilities: [],
  catalogItems: [],
  activePath: "status/index.json",
  activeKind: "status",
  activeId: null,
  routePrompt: null,
  routeError: null,
  catalogMode: "all",
  payload: null,
  errors: []
};

const catalogVisibleLimit = 80;

const endpointGroups = [
  {
    title: "Registry",
    items: [
      { id: "root", title: "GET /v0", path: "index.json", description: "Registry root entrypoint" },
      { id: "status", title: "GET /v0/status", path: "status/index.json", description: "Availability and counts" }
    ]
  },
  {
    title: "Packages",
    items: [
      { id: "packages", title: "GET /v0/packages", path: "packages/index.json", description: "Browse package index" },
      { id: "package-template", title: "GET /v0/packages/{package_id}", description: "Select a package from catalog search" },
      { id: "version-template", title: "GET /v0/packages/{package_id}/versions/{version}", description: "Select a package version" }
    ]
  },
  {
    title: "Capabilities",
    items: [
      { id: "capability-template", title: "GET /v0/capabilities/{capability_id}/packages", description: "Select a capability from catalog search" }
    ]
  },
  {
    title: "Observed Intents",
    items: [
      { id: "intents", title: "GET /v0/intents", path: "intents/index.json", description: "Browse observed intent catalog" },
      { id: "intent-template", title: "GET /v0/intents/{intent_id}", description: "Select an intent from catalog search" },
      { id: "intent-packages-template", title: "GET /v0/intents/{intent_id}/packages", description: "Select an intent, then open package matches" }
    ]
  }
];

const endpoints = endpointGroups.flatMap((group) => group.items);
const defaultViewerRoute = { type: "endpoint", kind: "status" };

const routeTemplates = {
  "package-template": {
    title: "GET /v0/packages/{package_id}",
    description: "Build a concrete package metadata endpoint.",
    parts: ["/v0/packages/", { param: "package_id" }]
  },
  "version-template": {
    title: "GET /v0/packages/{package_id}/versions/{version}",
    description: "Build a concrete package version endpoint.",
    parts: ["/v0/packages/", { param: "package_id" }, "/versions/", { param: "version" }]
  },
  "capability-template": {
    title: "GET /v0/capabilities/{capability_id}/packages",
    description: "Build a concrete capability reverse lookup endpoint.",
    parts: ["/v0/capabilities/", { param: "capability_id" }, "/packages"]
  },
  "intent-template": {
    title: "GET /v0/intents/{intent_id}",
    description: "Build a concrete observed intent endpoint.",
    parts: ["/v0/intents/", { param: "intent_id" }]
  },
  "intent-packages-template": {
    title: "GET /v0/intents/{intent_id}/packages",
    description: "Build a concrete observed intent package lookup endpoint.",
    parts: ["/v0/intents/", { param: "intent_id" }, "/packages"]
  }
};

const form = document.querySelector("#registry-form");
const baseInput = document.querySelector("#registry-base");
const loadStatus = document.querySelector("#load-status");
const endpointTree = document.querySelector("#endpoint-tree");
const catalogFilter = document.querySelector("#catalog-filter");
const catalogList = document.querySelector("#catalog-list");
const catalogCount = document.querySelector("#catalog-count");
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

window.addEventListener("popstate", async (event) => {
  if (!state.status) {
    return;
  }
  const route = event.state?.specpmViewerRoute || routeFromLocation();
  try {
    await navigateToRoute(route, { historyMode: "none" });
  } catch (error) {
    state.payload = { status: "invalid", error: { message: error.message } };
    state.errors.push(error.message);
    setLoadStatus("error", error.message);
    renderAll();
  }
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
    if (url.protocol !== "http:" && url.protocol !== "https:") {
      return fallback;
    }
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
  clearLoadedRegistryState();
  setLoadStatus("loading", "Loading static registry metadata...");
  renderAll();
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
    state.catalogItems = buildCatalogItems();
    state.payload = state.status;
    state.activePath = "status/index.json";
    state.activeKind = "status";
    state.activeId = null;
    clearRoutePrompt();

    setLoadStatus("ok", `Loaded ${state.base}`);
    try {
      await navigateToRoute(routeFromLocation(), { historyMode: "replace" });
    } catch (routeError) {
      state.errors.push(routeError.message);
      setLoadStatus("error", routeError.message);
      await showEndpoint("status", "status/index.json", { historyMode: "replace" });
    }
  } catch (error) {
    state.errors.push(error.message);
    state.payload = {
      apiVersion: "specpm.registry/viewer",
      kind: "RemoteRegistryLoadError",
      status: "invalid",
      errors: [...state.errors]
    };
    setLoadStatus("error", error.message);
    renderAll();
  }
}

function clearLoadedRegistryState() {
  state.root = null;
  state.status = null;
  state.packages = null;
  state.intents = null;
  state.capabilities = [];
  state.catalogItems = [];
  state.activePath = "status/index.json";
  state.activeKind = "status";
  state.activeId = null;
  state.payload = {
    apiVersion: "specpm.registry/viewer",
    kind: "RemoteRegistryLoading",
    status: "loading",
    message: "Loading static registry metadata..."
  };
  clearRoutePrompt();
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
  renderEndpointTree();
  renderCatalog();
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

function renderEndpointTree() {
  endpointTree.innerHTML = endpointGroups.map((group) => `
    <div class="tree-group">
      <div class="tree-group-title">${escapeHtml(group.title)}</div>
      ${group.items.map((endpoint) => {
        const active = isEndpointActive(endpoint.id) ? "active" : "";
        if (routeTemplates[endpoint.id]) {
          return `
            <button class="tree-item ${active}" data-action="route-template" data-kind="${escapeAttr(endpoint.id)}">
              <span class="tree-path">${escapeHtml(endpoint.title)}</span>
              <span class="tree-desc">${escapeHtml(endpoint.description)}</span>
            </button>
          `;
        }
        if (!endpoint.path) {
          return `
            <div class="tree-item static ${active}">
              <span class="tree-path">${escapeHtml(endpoint.title)}</span>
              <span class="tree-desc">${escapeHtml(endpoint.description)}</span>
            </div>
          `;
        }
        return `
          <button class="tree-item ${active}" data-action="endpoint" data-path="${escapeAttr(endpoint.path)}" data-kind="${escapeAttr(endpoint.id)}">
            <span class="tree-path">${escapeHtml(endpoint.title)}</span>
            <span class="tree-desc">${escapeHtml(endpoint.description)}</span>
          </button>
        `;
      }).join("")}
    </div>
  `).join("");
}

function renderCatalog() {
  const filter = catalogFilter.value.trim().toLowerCase();
  const results = state.catalogItems.filter((item) => {
    if (state.catalogMode !== "all" && item.type !== state.catalogMode) {
      return false;
    }
    return matchesCatalogFilter(item, filter);
  });
  const visible = results.slice(0, catalogVisibleLimit);
  catalogCount.textContent = String(results.length);
  document.querySelectorAll("[data-action='catalog-mode']").forEach((button) => {
    button.classList.toggle("active", button.dataset.mode === state.catalogMode);
  });
  catalogList.innerHTML = visible.length ? `
    ${visible.map((item) => `
      <button class="list-item ${isCatalogItemActive(item) ? "active" : ""}" data-action="${escapeAttr(item.action)}" data-id="${escapeAttr(item.id)}">
        <span class="list-type">${escapeHtml(item.type)}</span>
        <span class="list-id">${escapeHtml(item.id)}</span>
        <span class="list-meta">${escapeHtml(item.meta)}</span>
      </button>
    `).join("")}
    ${results.length > visible.length ? `<div class="list-note">Showing ${escapeHtml(String(visible.length))} of ${escapeHtml(String(results.length))}. Narrow the search to see more.</div>` : ""}
  ` : `<div class="empty">No catalog items match this search.</div>`;
}

function renderRouteTemplateDetail() {
  const template = routeTemplates[state.routePrompt.kind];
  if (!template) {
    renderEndpointDetail();
    return;
  }
  detailPanel.innerHTML = `
    <form class="route-template-form" data-route-template="${escapeAttr(state.routePrompt.kind)}">
      <div class="detail-head">
        <div class="detail-title">
          <span class="pill live">Route Template</span>
          <h2>${escapeHtml(template.title)}</h2>
          <p>${escapeHtml(template.description)}</p>
        </div>
      </div>
      <div class="route-builder" aria-label="Endpoint URL builder">
        ${template.parts.map((part) => renderRoutePart(part)).join("")}
        <button class="btn primary" type="submit">Open Endpoint</button>
      </div>
      ${state.routeError ? `
        <div class="route-error">
          <span class="pill warn">Issue</span>
          <span>${escapeHtml(state.routeError)}</span>
        </div>
      ` : ""}
    </form>
  `;
}

function renderRoutePart(part) {
  if (typeof part === "string") {
    return `<span class="route-literal">${escapeHtml(part)}</span>`;
  }
  return `
    <label class="route-field">
      <span>{${escapeHtml(part.param)}}</span>
      <input
        name="${escapeAttr(part.param)}"
        placeholder="${escapeAttr(routePlaceholder(part.param))}"
        autocomplete="off"
        required
      />
    </label>
  `;
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

  if (state.routePrompt) {
    renderRouteTemplateDetail();
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
  if (state.activeKind === "packages") {
    renderPackageIndexDetail();
    return;
  }
  if (state.activeKind === "intents") {
    renderIntentIndexDetail();
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

function renderPackageIndexDetail() {
  const packages = packageItems();
  const visible = packages.slice(0, catalogVisibleLimit);
  detailPanel.innerHTML = `
    <div class="detail-head">
      <div class="detail-title">
        <span class="pill live">Package Index</span>
        <h2>Browse packages</h2>
        <p>Static package index from <code>GET /v0/packages</code>. Select a package to load its exact metadata endpoint.</p>
      </div>
      <div class="actions">
        <a class="btn small" href="${escapeAttr(resourceUrl(state.activePath))}" target="_blank" rel="noopener">Open Raw</a>
      </div>
    </div>
    <div class="facts">
      <div class="fact"><span>Packages</span><strong>${escapeHtml(String(packages.length))}</strong></div>
      <div class="fact"><span>Rendered</span><strong>${escapeHtml(String(visible.length))}</strong></div>
      <div class="fact"><span>Endpoint</span><strong>GET /v0/packages</strong></div>
      <div class="fact"><span>Next</span><strong>GET /v0/packages/{package_id}</strong></div>
    </div>
    <div class="catalog-grid">
      ${visible.map((pkg) => `
        <button class="catalog-row" data-action="package" data-id="${escapeAttr(pkg.package_id)}">
          <span class="catalog-row-head">
            <span class="list-type">package</span>
            <span class="catalog-row-id">${escapeHtml(pkg.package_id)}</span>
          </span>
          <span class="catalog-row-meta">${escapeHtml(pkg.name || "")} - ${escapeHtml(pkg.summary || "")}</span>
          <span class="catalog-row-meta">${escapeHtml(String(pkg.capabilities?.length || 0))} capability ID(s), ${escapeHtml(String(pkg.intents?.length || 0))} observed intent ID(s), latest ${escapeHtml(pkg.latest_version || "")}</span>
        </button>
      `).join("") || `<div class="empty">No packages are published in this registry.</div>`}
    </div>
    ${packages.length > visible.length ? `<div class="list-note">Showing ${escapeHtml(String(visible.length))} of ${escapeHtml(String(packages.length))}. Use catalog search to narrow the list.</div>` : ""}
  `;
}

function renderIntentIndexDetail() {
  const intents = intentItems();
  const visible = intents.slice(0, catalogVisibleLimit);
  const catalog = state.intents?.catalog || {};
  detailPanel.innerHTML = `
    <div class="detail-head">
      <div class="detail-title">
        <span class="pill live">Observed Intent Catalog</span>
        <h2>Browse observed intents</h2>
        <p>Static observed intent catalog from <code>GET /v0/intents</code>. These IDs are observed metadata, not canonical semantic authority.</p>
      </div>
      <div class="actions">
        <a class="btn small" href="${escapeAttr(resourceUrl(state.activePath))}" target="_blank" rel="noopener">Open Raw</a>
      </div>
    </div>
    <div class="facts">
      <div class="fact"><span>Intents</span><strong>${escapeHtml(String(intents.length))}</strong></div>
      <div class="fact"><span>Rendered</span><strong>${escapeHtml(String(visible.length))}</strong></div>
      <div class="fact"><span>Authority</span><strong>${escapeHtml(catalog.authority || "observed_metadata_only")}</strong></div>
      <div class="fact"><span>Canonical</span><strong>${escapeHtml(String(catalog.canonical ?? false))}</strong></div>
    </div>
    <div class="catalog-grid">
      ${visible.map((intent) => `
        <button class="catalog-row" data-action="intent" data-id="${escapeAttr(intent.intent_id)}">
          <span class="catalog-row-head">
            <span class="list-type">intent</span>
            <span class="catalog-row-id">${escapeHtml(intent.intent_id)}</span>
          </span>
          <span class="catalog-row-meta">${escapeHtml(String(intent.package_count || 0))} package match(es), ${escapeHtml(String(intent.capability_count || 0))} capability match(es)</span>
          <span class="catalog-row-meta">${escapeHtml((intent.capabilities || []).slice(0, 4).join(", ") || "No capability matches listed.")}</span>
        </button>
      `).join("") || `<div class="empty">No observed intents are published in this registry.</div>`}
    </div>
    ${intents.length > visible.length ? `<div class="list-note">Showing ${escapeHtml(String(visible.length))} of ${escapeHtml(String(intents.length))}. Use catalog search to narrow the list.</div>` : ""}
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
  rawLink.hidden = !state.activePath;
  rawLink.href = state.activePath ? resourceUrl(state.activePath) : "#";
}

function bindFilters() {
  catalogFilter.addEventListener("input", renderCatalog);
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
      } else if (action === "route-template") {
        showRoutePrompt(target.dataset.kind);
      } else if (action === "catalog-mode") {
        state.catalogMode = target.dataset.mode || "all";
        renderCatalog();
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

  document.body.addEventListener("submit", async (event) => {
    const routeForm = event.target.closest(".route-template-form");
    if (!routeForm) {
      return;
    }
    event.preventDefault();
    try {
      await submitRoutePrompt(routeForm);
    } catch (error) {
      state.routePrompt = { kind: routeForm.dataset.routeTemplate };
      state.routeError = error.message;
      renderEndpointTree();
      renderDetail();
      renderJson();
    }
  });
}

function showRoutePrompt(kind, options = {}) {
  if (!routeTemplates[kind]) {
    return;
  }
  state.routePrompt = { kind };
  state.routeError = null;
  state.activeKind = kind;
  state.activeId = null;
  state.activePath = null;
  state.payload = routeTemplatePayload(kind);
  renderAll();
  commitViewerRoute({ type: "route-template", kind }, options);
  const input = detailPanel.querySelector("input");
  if (input) {
    input.focus();
  }
}

async function submitRoutePrompt(routeForm) {
  const kind = routeForm.dataset.routeTemplate;
  const template = routeTemplates[kind];
  if (!template) {
    throw new Error("Unknown endpoint template.");
  }
  const values = Object.fromEntries([...new FormData(routeForm).entries()].map(([key, value]) => [
    key,
    String(value || "").trim()
  ]));
  const missing = template.parts
    .filter((part) => typeof part !== "string" && !values[part.param])
    .map((part) => part.param);
  if (missing.length) {
    throw new Error(`Missing required id: ${missing.join(", ")}`);
  }
  if (kind === "package-template") {
    await showPackage(values.package_id);
  } else if (kind === "version-template") {
    await showVersion(values.package_id, values.version);
  } else if (kind === "capability-template") {
    await showCapability(values.capability_id);
  } else if (kind === "intent-template") {
    await showIntent(values.intent_id);
  } else if (kind === "intent-packages-template") {
    await showIntentPackages(values.intent_id);
  }
}

async function showEndpoint(kind, path, options = {}) {
  clearRoutePrompt();
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
  commitViewerRoute({ type: "endpoint", kind }, options);
}

async function showPackage(packageId, options = {}) {
  clearRoutePrompt();
  state.activeKind = "package";
  state.activeId = packageId;
  state.activePath = `packages/${segment(packageId)}/index.json`;
  state.payload = await fetchRequired(state.activePath);
  renderAll();
  commitViewerRoute({ type: "package", packageId }, options);
}

async function showVersion(packageId, version, options = {}) {
  clearRoutePrompt();
  state.activeKind = "version";
  state.activeId = `${packageId}@${version}`;
  state.activePath = `packages/${segment(packageId)}/versions/${segment(version)}/index.json`;
  state.payload = await fetchRequired(state.activePath);
  renderAll();
  commitViewerRoute({ type: "version", packageId, version }, options);
}

async function showCapability(capabilityId, options = {}) {
  clearRoutePrompt();
  state.activeKind = "capability";
  state.activeId = capabilityId;
  state.activePath = `capabilities/${segment(capabilityId)}/packages/index.json`;
  state.payload = await fetchRequired(state.activePath);
  renderAll();
  commitViewerRoute({ type: "capability", capabilityId }, options);
}

async function showIntent(intentId, options = {}) {
  clearRoutePrompt();
  state.activeKind = "intent";
  state.activeId = intentId;
  state.activePath = `intents/${segment(intentId)}/index.json`;
  state.payload = await fetchRequired(state.activePath);
  renderAll();
  commitViewerRoute({ type: "intent", intentId }, options);
}

async function showIntentPackages(intentId, options = {}) {
  clearRoutePrompt();
  state.activeKind = "intent-packages";
  state.activeId = intentId;
  state.activePath = `intents/${segment(intentId)}/packages/index.json`;
  state.payload = await fetchRequired(state.activePath);
  renderAll();
  commitViewerRoute({ type: "intent-packages", intentId }, options);
}

async function navigateToRoute(route, options = {}) {
  const next = normalizeViewerRoute(route);
  if (next.type === "route-template") {
    showRoutePrompt(next.kind, options);
    return;
  }
  if (next.type === "endpoint") {
    const endpoint = endpoints.find((item) => item.id === next.kind && item.path);
    if (!endpoint) {
      throw new Error(`Unknown endpoint route: ${next.kind}`);
    }
    await showEndpoint(endpoint.id, endpoint.path, options);
    return;
  }
  if (next.type === "package") {
    await showPackage(next.packageId, options);
    return;
  }
  if (next.type === "version") {
    await showVersion(next.packageId, next.version, options);
    return;
  }
  if (next.type === "capability") {
    await showCapability(next.capabilityId, options);
    return;
  }
  if (next.type === "intent") {
    await showIntent(next.intentId, options);
    return;
  }
  if (next.type === "intent-packages") {
    await showIntentPackages(next.intentId, options);
    return;
  }
  await showEndpoint("status", "status/index.json", options);
}

function commitViewerRoute(route, options = {}) {
  const mode = options.historyMode || "push";
  if (mode === "none" || !window.history?.pushState) {
    return;
  }
  const normalized = normalizeViewerRoute(route);
  const nextUrl = new URL(window.location.href);
  nextUrl.hash = routeToHash(normalized);
  if (nextUrl.href === window.location.href && mode !== "replace") {
    return;
  }
  const historyState = { specpmViewerRoute: normalized };
  if (mode === "replace") {
    window.history.replaceState(historyState, "", nextUrl);
  } else {
    window.history.pushState(historyState, "", nextUrl);
  }
}

function routeFromLocation() {
  const hash = window.location.hash.replace(/^#\/?/, "");
  if (!hash) {
    return { ...defaultViewerRoute };
  }
  const parts = hash.split("/").filter(Boolean).map(decodeRouteSegment);
  if (parts[0] === "endpoint" && parts[1]) {
    return { type: "endpoint", kind: parts[1] };
  }
  if (parts[0] === "route" && parts[1]) {
    return { type: "route-template", kind: parts[1] };
  }
  if (parts[0] === "package" && parts[1]) {
    return { type: "package", packageId: parts[1] };
  }
  if (parts[0] === "version" && parts[1] && parts[2]) {
    return { type: "version", packageId: parts[1], version: parts[2] };
  }
  if (parts[0] === "capability" && parts[1]) {
    return { type: "capability", capabilityId: parts[1] };
  }
  if (parts[0] === "intent" && parts[1]) {
    return { type: "intent", intentId: parts[1] };
  }
  if (parts[0] === "intent-packages" && parts[1]) {
    return { type: "intent-packages", intentId: parts[1] };
  }
  return { ...defaultViewerRoute };
}

function normalizeViewerRoute(route) {
  const next = route || defaultViewerRoute;
  if (next.type === "route-template" && routeTemplates[next.kind]) {
    return { type: "route-template", kind: next.kind };
  }
  if (next.type === "endpoint" && endpoints.some((item) => item.id === next.kind && item.path)) {
    return { type: "endpoint", kind: next.kind };
  }
  if (next.type === "package" && next.packageId) {
    return { type: "package", packageId: String(next.packageId) };
  }
  if (next.type === "version" && next.packageId && next.version) {
    return { type: "version", packageId: String(next.packageId), version: String(next.version) };
  }
  if (next.type === "capability" && next.capabilityId) {
    return { type: "capability", capabilityId: String(next.capabilityId) };
  }
  if (next.type === "intent" && next.intentId) {
    return { type: "intent", intentId: String(next.intentId) };
  }
  if (next.type === "intent-packages" && next.intentId) {
    return { type: "intent-packages", intentId: String(next.intentId) };
  }
  return { ...defaultViewerRoute };
}

function routeToHash(route) {
  if (route.type === "route-template") {
    return `route/${encodeRouteSegment(route.kind)}`;
  }
  if (route.type === "package") {
    return `package/${encodeRouteSegment(route.packageId)}`;
  }
  if (route.type === "version") {
    return `version/${encodeRouteSegment(route.packageId)}/${encodeRouteSegment(route.version)}`;
  }
  if (route.type === "capability") {
    return `capability/${encodeRouteSegment(route.capabilityId)}`;
  }
  if (route.type === "intent") {
    return `intent/${encodeRouteSegment(route.intentId)}`;
  }
  if (route.type === "intent-packages") {
    return `intent-packages/${encodeRouteSegment(route.intentId)}`;
  }
  return `endpoint/${encodeRouteSegment(route.kind || defaultViewerRoute.kind)}`;
}

function buildCatalogItems() {
  const packages = packageItems().map((pkg) => ({
    type: "package",
    action: "package",
    id: pkg.package_id,
    meta: `${pkg.name || ""} - ${pkg.summary || ""}`,
    search: [
      pkg.name,
      pkg.summary,
      pkg.latest_version,
      pkg.license,
      ...(pkg.capabilities || []),
      ...(pkg.intents || []),
      ...(pkg.keywords || [])
    ].join(" ")
  }));
  const intents = intentItems().map((intent) => ({
    type: "intent",
    action: "intent",
    id: intent.intent_id,
    meta: `${intent.package_count || 0} package(s), ${intent.capability_count || 0} capability match(es)`,
    search: [
      intent.status,
      ...(intent.package_ids || []),
      ...(intent.capabilities || [])
    ].join(" ")
  }));
  const capabilities = state.capabilities.map((capability) => ({
    type: "capability",
    action: "capability",
    id: capability.id,
    meta: `${capability.packages.length} package source(s)`,
    search: capability.packages.join(" ")
  }));
  return [...packages, ...intents, ...capabilities]
    .map((item) => ({
      ...item,
      searchText: `${item.id || ""} ${item.search || ""}`.toLowerCase()
    }))
    .sort((left, right) => {
      if (left.type === right.type) {
        return left.id.localeCompare(right.id);
      }
      return typeRank(left.type) - typeRank(right.type);
    });
}

function typeRank(type) {
  return { package: 0, intent: 1, capability: 2 }[type] ?? 9;
}

function isCatalogItemActive(item) {
  return state.activeKind === item.type && state.activeId === item.id;
}

function isEndpointActive(endpointId) {
  if (state.routePrompt?.kind === endpointId) {
    return true;
  }
  if (state.activeKind === endpointId) {
    return true;
  }
  if (endpointId === "package-template") {
    return state.activeKind === "package";
  }
  if (endpointId === "version-template") {
    return state.activeKind === "version";
  }
  if (endpointId === "capability-template") {
    return state.activeKind === "capability";
  }
  if (endpointId === "intent-template") {
    return state.activeKind === "intent";
  }
  if (endpointId === "intent-packages-template") {
    return state.activeKind === "intent-packages";
  }
  return false;
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

function encodeRouteSegment(value) {
  return encodeURIComponent(String(value || ""));
}

function decodeRouteSegment(value) {
  try {
    return decodeURIComponent(value || "");
  } catch (_error) {
    return "";
  }
}

function routePlaceholder(param) {
  if (param === "package_id") {
    return packageItems()[0]?.package_id || "specpm.core";
  }
  if (param === "version") {
    return packageItems()[0]?.latest_version || "0.1.0";
  }
  if (param === "capability_id") {
    return state.capabilities[0]?.id || "specpm.registry.search";
  }
  if (param === "intent_id") {
    return intentItems()[0]?.intent_id || "intent.registry.intent_lookup";
  }
  return param;
}

function routeTemplatePayload(kind) {
  const template = routeTemplates[kind] || {};
  return {
    apiVersion: "specpm.registry/viewer",
    kind: "RemoteRouteTemplate",
    status: "local_template",
    title: template.title || "Route template",
    description: template.description || "",
    parameters: (template.parts || [])
      .filter((part) => typeof part !== "string")
      .map((part) => part.param)
  };
}

function clearRoutePrompt() {
  state.routePrompt = null;
  state.routeError = null;
}

function matchesCatalogFilter(item, filter) {
  if (!filter) {
    return true;
  }
  return item.searchText.includes(filter);
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
