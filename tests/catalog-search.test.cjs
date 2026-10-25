const assert = require("node:assert/strict");
const { test } = require("node:test");
const { catalogItems, corpusHash, createIndex, restoreIndex, loadIndex, tokenize } =
  require("../landing_page/assets/catalog-search.js");

function item(id, fields = {}) {
  return { id, searchFields: fields };
}

function ids(index, query) {
  return index.search(query).map((entry) => entry.id);
}

test("splits identifiers, camel case and Unicode without losing numbers", () => {
  assert.deepEqual(tokenize("HTTPClient email_to.Markdown v1.19 ПОИСК"),
    ["httpclient", "http", "client", "email", "to", "markdown", "v1", "19", "поиск"]);
});

test("compound names match whole words regardless of query capitalization", () => {
  const index = createIndex([
    item("example.client", { title: "HTTPClient", summary: "SwiftDecision integration" })
  ]);
  for (const query of ["HTTPClient", "httpclient", "HTTPCLIENT", "http client",
    "SwiftDecision", "swiftdecision", "SWIFTDECISION", "swift decision"]) {
    assert.deepEqual(ids(index, query), ["example.client"]);
  }
});

test("empty query preserves browse order and empty indexes are searchable", () => {
  const entries = [item("b"), item("a")];
  assert.deepEqual(createIndex(entries).search("  "), entries);
  assert.deepEqual(createIndex([]).search("http"), []);
  assert.deepEqual(createIndex(entries).search("*** : ()"), []);
});

test("multiple words rank matches even when the phrase is absent or reversed", () => {
  const index = createIndex([
    item("single", { summary: "client library" }),
    item("both", { summary: "HTTP requests from a browser client" }),
    item("other", { summary: "image conversion" })
  ]);
  assert.deepEqual(ids(index, "http client"), ["both", "single"]);
  assert.deepEqual(ids(index, "client http"), ["both", "single"]);
});

test("an exact ID wins over stronger lexical matches and is case insensitive", () => {
  const index = createIndex([
    item("other", { title: "Axios HTTP Client", keywords: "axios http client" }),
    item("axios.http_client", { summary: "Requests" })
  ]);
  assert.equal(ids(index, "AXIOS.HTTP_CLIENT")[0], "axios.http_client");
});

test("exact titles precede partial title matches", () => {
  const index = createIndex([
    item("other", { title: "HTTP Client Tools", keywords: "http client" }),
    item("target", { title: "HTTP Client" })
  ]);
  assert.equal(ids(index, "http client")[0], "target");
});

test("titles and keywords outweigh the same word in a summary", () => {
  const index = createIndex([
    item("summary", { summary: "retry" }),
    item("title", { title: "retry mechanism" }),
    item("keyword", { keywords: "retry" })
  ]);
  const result = ids(index, "retry");
  assert.ok(result.indexOf("title") < result.indexOf("summary"));
  assert.ok(result.indexOf("keyword") < result.indexOf("summary"));
});

test("rare terms contribute more than common terms", () => {
  const index = createIndex([
    item("a", { summary: "common neutral" }),
    item("b", { summary: "unusual neutral" }),
    item("c", { summary: "common neutral" }),
    item("d", { summary: "common neutral" })
  ]);
  assert.equal(ids(index, "common unusual")[0], "b");
});

test("normalizes document length and saturates repeated terms", () => {
  const index = createIndex([
    item("long", { summary: "retry " + "neutral ".repeat(100) }),
    item("short", { summary: "retry neutral" })
  ]);
  assert.equal(ids(index, "retry")[0], "short");
  const saturated = createIndex([
    item("repeated", { summary: "retry ".repeat(1000) }),
    item("title", { title: "retry support" })
  ]);
  assert.equal(ids(saturated, "retry")[0], "title");
});

test("completes the last word while typing with lower weight than an exact term", () => {
  const index = createIndex([
    item("completion", { summary: "HTTP client" }),
    item("exact", { summary: "HTTP cli" })
  ]);
  assert.deepEqual(ids(index, "http cli"), ["exact", "completion"]);
});

test("unmatched text returns nothing; hostile query text stays literal", () => {
  const index = createIndex([item("axios.http_client", { summary: "HTTP requests" })]);
  assert.deepEqual(ids(index, "nonexistentword"), []);
  assert.deepEqual(ids(index, '<script>alert("xss")</script>'), []);
});

test("ties are deterministic and a new registry index has no old documents", () => {
  const entries = [item("b", { summary: "retry" }), item("a", { summary: "retry" })];
  assert.deepEqual(ids(createIndex(entries), "retry"), ["b", "a"]);
  assert.deepEqual(ids(createIndex([item("new")]), "retry"), []);
});

test("serialized postings preserve ranking, exact IDs, prefixes and Unicode", async () => {
  const entries = [
    item("axios.http_client", { title: "Axios HTTPClient", summary: "HTTP requests" }),
    item("email_tools", { title: "Email Tools", keywords: "markdown поиск" }),
    item("other", { summary: "client support" })
  ];
  const hash = await corpusHash(entries);
  const local = createIndex(entries);
  const payload = JSON.parse(JSON.stringify(local.toJSON(hash)));
  const restored = restoreIndex(payload, entries, hash);
  assert.equal(restored.source, "prebuilt");
  for (const query of ["", "http client", "client http", "axios.http_client", "http cli",
    "HTTPClient", "httpclient", "HTTPCLIENT", "ПОИСК", "missing"]) {
    assert.deepEqual(ids(restored, query), ids(local, query));
  }
  assert.deepEqual(createIndex(entries).toJSON(hash), payload);
});

test("valid prebuilt metadata is loaded without falling back", async () => {
  const entries = [item("a", { summary: "retry" })];
  const payload = createIndex(entries).toJSON(await corpusHash(entries));
  const index = await loadIndex(entries, async () => payload);
  assert.equal(index.source, "prebuilt");
  assert.deepEqual(ids(index, "retry"), ["a"]);
});

test("changed, deleted or reordered documents reject an old snapshot", async () => {
  const old = [item("a", { summary: "oldword" }), item("b")];
  const payload = createIndex(old).toJSON(await corpusHash(old));
  for (const current of [[item("a", { summary: "newword" }), item("b")], [item("b")],
    [old[1], old[0]]]) {
    const index = await loadIndex(current, async () => payload);
    assert.equal(index.source, "local");
    assert.deepEqual(ids(index, ""), current.map((entry) => entry.id));
  }
  const changed = await loadIndex([item("a", { summary: "newword" })], async () => payload);
  assert.deepEqual(ids(changed, "oldword"), []);
  assert.deepEqual(ids(changed, "newword"), ["a"]);
});

test("missing index and invalid JSON fall back for third-party registries", async () => {
  const entries = [item("target", { summary: "client" })];
  for (const fetch of [async () => { throw new Error("404"); },
    async () => JSON.parse("broken"), async () => null]) {
    const index = await loadIndex(entries, fetch);
    assert.equal(index.source, "local");
    assert.deepEqual(ids(index, "client"), ["target"]);
  }
});

test("unsupported versions and invalid statistics or postings fall back", async () => {
  const entries = [item("a", { summary: "retry" })];
  const original = createIndex(entries).toJSON(await corpusHash(entries));
  const corruptions = [
    (p) => { p.schemaVersion += 1; },
    (p) => { p.engineVersion += 1; },
    (p) => { p.engineVersion = 1; },
    (p) => { p.averages.summary = 999; },
    (p) => { p.documents[0].id = "another"; },
    (p) => { p.documents[0].lengths.summary = -1; },
    (p) => { p.postings[0][1][0][0] = 100; },
    (p) => { p.postings[0][1][0][1].id = 999; },
    (p) => { p.postings.push(p.postings[0]); },
    (p) => { p.postings = []; },
    (p) => { p.postings.pop(); }
  ];
  for (const corrupt of corruptions) {
    const payload = structuredClone(original);
    corrupt(payload);
    const index = await loadIndex(entries, async () => payload);
    assert.equal(index.source, "local");
    assert.deepEqual(ids(index, "retry"), ["a"]);
  }
});

test("shared projection includes packages, package sets, intents and capabilities", () => {
  const entries = catalogItems({ packages: [
    { package_id: "b", name: "HTTP Client", capabilities: ["http.request"] },
    { package_id: "a", subject: { kind: "package_set" }, capabilities: ["http.request"] }
  ] }, { intents: [{ intent_id: "intent.http", package_ids: ["b"], package_count: 1 }] });
  assert.deepEqual(entries.map(({ type, id }) => [type, id]),
    [["package-set", "a"], ["package", "b"], ["intent", "intent.http"],
      ["capability", "http.request"]]);
  assert.equal(entries[3].meta, "2 package source(s)");
});

test("hash changes with searchable metadata while equivalent JSON stays identical", async () => {
  const entries = [item("a", { title: "Search", summary: "old" })];
  assert.equal(await corpusHash(entries), await corpusHash(JSON.parse(JSON.stringify(entries))));
  assert.notEqual(await corpusHash(entries), await corpusHash([item("a", { summary: "new" })]));
});

test("build script publishes a deterministic index and refreshes changed metadata", async (t) => {
  const fs = require("node:fs/promises");
  const path = require("node:path");
  const os = require("node:os");
  const { buildCatalogSearch } = require("../scripts/build_catalog_search.cjs");
  const site = await fs.mkdtemp(path.join(os.tmpdir(), "specpm-search-"));
  t.after(() => fs.rm(site, { recursive: true, force: true }));
  await fs.mkdir(path.join(site, "v0/packages"), { recursive: true });
  await fs.mkdir(path.join(site, "v0/intents"), { recursive: true });
  const packageFile = path.join(site, "v0/packages/index.json");
  const packages = { kind: "RemotePackageIndex", status: "ok", packages: [
    { package_id: "a", name: "HTTP Client", summary: "Requests", capabilities: ["http.request"] }
  ] };
  const intents = { kind: "RemoteIntentIndex", status: "ok", intents: [] };
  await fs.writeFile(packageFile, JSON.stringify(packages));
  await fs.writeFile(path.join(site, "v0/intents/index.json"), JSON.stringify(intents));
  const first = await buildCatalogSearch(site);
  const bytes = await fs.readFile(first.output, "utf8");
  assert.equal(first.documents, 2);
  await buildCatalogSearch(site);
  assert.equal(await fs.readFile(first.output, "utf8"), bytes);
  const items = catalogItems(packages, intents);
  assert.equal((await loadIndex(items, async () => JSON.parse(bytes))).source, "prebuilt");
  packages.packages[0].summary = "New description";
  await fs.writeFile(packageFile, JSON.stringify(packages));
  assert.notEqual((await buildCatalogSearch(site)).corpusHash, first.corpusHash);
  await fs.writeFile(packageFile, JSON.stringify({ status: "invalid" }));
  await assert.rejects(buildCatalogSearch(site), /Expected generated/);
});
