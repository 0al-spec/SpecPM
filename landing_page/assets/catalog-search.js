/* Browser-local, field-weighted BM25 over the loaded registry metadata. */
(function (root) {
  "use strict";

  const weights = { id: 5, title: 4, keywords: 3, summary: 1, identifiers: 2, details: 0.5 };
  const k1 = 1.2;
  const b = 0.75;
  // Bump when tokenization, field weights, projection or scoring changes.
  const engineVersion = 2;

  function catalogItems(packageIndex, intentIndex) {
    const capabilities = new Map();
    const packages = (packageIndex?.packages || []).map((pkg) => {
      for (const capability of pkg.capabilities || []) {
        if (!capabilities.has(capability)) capabilities.set(capability, []);
        capabilities.get(capability).push(pkg.package_id);
      }
      return {
        type: pkg.subject?.kind === "package_set" ? "package-set" : pkg.subject?.scope || "package",
        action: "package",
        id: pkg.package_id,
        meta: `${pkg.name || ""} - ${pkg.summary || ""}`,
        searchFields: {
          title: pkg.name,
          summary: pkg.summary,
          keywords: (pkg.keywords || []).join(" "),
          identifiers: [...(pkg.capabilities || []), ...(pkg.intents || [])].join(" "),
          details: [pkg.latest_version, pkg.license].join(" ")
        }
      };
    });
    const intents = (intentIndex?.intents || []).map((intent) => ({
      type: "intent",
      action: "intent",
      id: intent.intent_id,
      meta: `${intent.package_count || 0} package(s), ${intent.capability_count || 0} capability match(es)`,
      searchFields: {
        identifiers: [...(intent.package_ids || []), ...(intent.capabilities || [])].join(" "),
        details: intent.status
      }
    }));
    const capabilityItems = [...capabilities].map(([id, packageIds]) => ({
      type: "capability",
      action: "capability",
      id,
      meta: `${packageIds.length} package source(s)`,
      searchFields: { identifiers: packageIds.join(" ") }
    }));
    const rank = { "package-set": 0, package: 1, intent: 2, capability: 3 };
    return [...packages, ...intents, ...capabilityItems].sort((left, right) =>
      (rank[left.type] ?? 9) - (rank[right.type] ?? 9)
      || (left.id < right.id ? -1 : left.id > right.id ? 1 : 0)
    );
  }

  async function corpusHash(items) {
    const bytes = new TextEncoder().encode(JSON.stringify(items));
    const hash = await root.crypto.subtle.digest("SHA-256", bytes);
    return [...new Uint8Array(hash)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
  }

  function normalize(text) {
    return String(text ?? "").normalize("NFKC").toLowerCase().trim();
  }

  function tokenize(text) {
    const words = String(text ?? "").normalize("NFKC").match(/[\p{L}\p{N}]+/gu) || [];
    return words.flatMap((word) => {
      const parts = normalize(word
        .replace(/([A-Z]+)([A-Z][a-z])/g, "$1 $2")
        .replace(/([a-z])([A-Z])/g, "$1 $2")).split(" ");
      // Keep the whole word so lowercase and uppercase compound queries still match.
      return parts.length > 1 ? [normalize(word), ...parts] : parts;
    });
  }

  function createIndex(items) {
    const postings = new Map();
    const averages = Object.fromEntries(Object.keys(weights).map((field) => [field, 0]));
    const documents = items.map((item, position) => {
      const fields = { ...item.searchFields, id: item.id };
      const lengths = {};
      for (const field of Object.keys(weights)) {
        const tokens = tokenize(fields[field]);
        lengths[field] = tokens.length;
        averages[field] += tokens.length;
        for (const token of tokens) {
          if (!postings.has(token)) postings.set(token, new Map());
          const matches = postings.get(token);
          if (!matches.has(position)) matches.set(position, {});
          const frequencies = matches.get(position);
          frequencies[field] = (frequencies[field] || 0) + 1;
        }
      }
      return { item, lengths, id: normalize(item.id), title: normalize(fields.title) };
    });
    for (const field of Object.keys(weights)) {
      averages[field] /= documents.length || 1;
    }
    return makeIndex(items, documents, averages, postings, "local");
  }

  function restoreIndex(payload, items, hash) {
    if (payload?.kind !== "SpecPMCatalogSearchIndex" || payload.schemaVersion !== 1
      || payload.engineVersion !== engineVersion || payload.corpusHash !== hash
      || !Array.isArray(payload.documents) || payload.documents.length !== items.length
      || !Array.isArray(payload.postings)) {
      throw new Error("Incompatible catalog search index");
    }
    const documents = payload.documents.map((doc, position) => {
      if (doc.id !== normalize(items[position].id)
        || doc.title !== normalize(items[position].searchFields?.title)
        || Object.keys(weights).some((field) =>
          !Number.isSafeInteger(doc.lengths?.[field]) || doc.lengths[field] < 0)) {
        throw new Error("Invalid catalog search document");
      }
      return { ...doc, item: items[position] };
    });
    const averages = payload.averages;
    for (const field of Object.keys(weights)) {
      const expected = documents.reduce((sum, doc) => sum + doc.lengths[field], 0)
        / (documents.length || 1);
      if (!Number.isFinite(averages?.[field]) || averages[field] !== expected) {
        throw new Error("Invalid catalog search statistics");
      }
    }
    const postings = new Map();
    const totals = documents.map(() => Object.fromEntries(Object.keys(weights).map((f) => [f, 0])));
    for (const [term, entries] of payload.postings) {
      if (typeof term !== "string" || !term || postings.has(term)
        || !Array.isArray(entries) || !entries.length) {
        throw new Error("Invalid catalog search postings");
      }
      const matches = new Map();
      for (const [position, frequencies] of entries) {
        if (!Number.isSafeInteger(position) || position < 0 || position >= documents.length
          || matches.has(position) || !frequencies || !Object.keys(frequencies).length
          || Object.entries(frequencies).some(([field, tf]) =>
            !Object.hasOwn(weights, field) || !Number.isSafeInteger(tf) || tf <= 0
            || tf > documents[position].lengths[field])) {
          throw new Error("Invalid catalog search frequencies");
        }
        matches.set(position, frequencies);
        for (const [field, tf] of Object.entries(frequencies)) totals[position][field] += tf;
      }
      postings.set(term, matches);
    }
    if (documents.some((doc, position) => Object.keys(weights).some((field) =>
      totals[position][field] !== doc.lengths[field]))) {
      throw new Error("Incomplete catalog search postings");
    }
    return makeIndex(items, documents, averages, postings, "prebuilt");
  }

  async function loadIndex(items, fetchIndex) {
    try {
      const payload = await fetchIndex();
      return restoreIndex(payload, items, await corpusHash(items));
    } catch {
      // A third-party registry may have no index, or deployment/cache versions may differ.
      return createIndex(items);
    }
  }

  function makeIndex(items, documents, averages, postings, source) {

    function search(query) {
      const text = normalize(query);
      if (!text) return items.slice();
      const queryTokens = tokenize(query).slice(0, 32);
      const tokens = [...new Set(queryTokens)];
      if (!tokens.length) return [];
      const terms = new Map(tokens.map((token) => [token, 1]));
      // Complete the final word while typing; exact terms retain their full weight.
      const prefix = queryTokens[queryTokens.length - 1];
      if (prefix.length >= 2) {
        for (const term of postings.keys()) {
          if (term.startsWith(prefix) && !terms.has(term)) terms.set(term, 0.35);
        }
      }
      const scores = new Map();
      for (const [term, boost] of terms) {
        const matches = postings.get(term);
        if (!matches) continue;
        const idf = Math.log(1 + (documents.length - matches.size + 0.5) / (matches.size + 0.5));
        for (const [position, frequencies] of matches) {
          let score = scores.get(position) || 0;
          for (const [field, tf] of Object.entries(frequencies)) {
            const length = documents[position].lengths[field];
            const norm = 1 - b + b * length / averages[field];
            score += boost * weights[field] * idf * tf * (k1 + 1) / (tf + k1 * norm);
          }
          scores.set(position, score);
        }
      }
      return [...scores].map(([position, score]) => ({
        position,
        score,
        exact: documents[position].id === text ? 2 : documents[position].title === text ? 1 : 0
      })).sort((left, right) =>
        right.exact - left.exact || right.score - left.score || left.position - right.position
      ).map(({ position }) => documents[position].item);
    }

    function toJSON(hash) {
      return {
        kind: "SpecPMCatalogSearchIndex",
        schemaVersion: 1,
        engineVersion,
        corpusHash: hash,
        documents: documents.map(({ id, title, lengths }) => ({ id, title, lengths })),
        averages,
        postings: [...postings].map(([term, matches]) => [term, [...matches]])
      };
    }

    return { search, toJSON, source };
  }

  root.SpecPMCatalogSearch = { catalogItems, corpusHash, createIndex, restoreIndex, loadIndex, tokenize };
  if (typeof module !== "undefined" && module.exports) module.exports = root.SpecPMCatalogSearch;
})(globalThis);
