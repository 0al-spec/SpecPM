const assert = require("node:assert/strict");
const { test } = require("node:test");
const { createIndex, tokenize } = require("../landing_page/assets/catalog-search.js");

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
