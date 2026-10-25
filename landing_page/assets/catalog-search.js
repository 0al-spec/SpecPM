/* Browser-local, field-weighted BM25 over the loaded registry metadata. */
(function (root) {
  "use strict";

  const weights = { id: 5, title: 4, keywords: 3, summary: 1, identifiers: 2, details: 0.5 };
  const k1 = 1.2;
  const b = 0.75;

  function normalize(text) {
    return String(text ?? "").normalize("NFKC").toLowerCase().trim();
  }

  function tokenize(text) {
    return normalize(String(text ?? "")
      .replace(/([A-Z]+)([A-Z][a-z])/g, "$1 $2")
      .replace(/([a-z])([A-Z])/g, "$1 $2"))
      .match(/[\p{L}\p{N}]+/gu) || [];
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

    return { search };
  }

  root.SpecPMCatalogSearch = { createIndex, tokenize };
  if (typeof module !== "undefined" && module.exports) module.exports = root.SpecPMCatalogSearch;
})(globalThis);
