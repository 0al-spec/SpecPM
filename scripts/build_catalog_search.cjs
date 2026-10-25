#!/usr/bin/env node
"use strict";

const fs = require("node:fs/promises");
const path = require("node:path");
const { catalogItems, corpusHash, createIndex } = require("../landing_page/assets/catalog-search.js");

async function buildCatalogSearch(site) {
  const registry = path.join(site, "v0");
  const [packages, intents] = await Promise.all([
    fs.readFile(path.join(registry, "packages/index.json"), "utf8").then(JSON.parse),
    fs.readFile(path.join(registry, "intents/index.json"), "utf8").then(JSON.parse)
  ]);
  if (packages.kind !== "RemotePackageIndex" || packages.status !== "ok"
    || !Array.isArray(packages.packages) || intents.kind !== "RemoteIntentIndex"
    || intents.status !== "ok" || !Array.isArray(intents.intents)) {
    throw new Error("Expected generated package and intent indexes");
  }
  const items = catalogItems(packages, intents);
  const hash = await corpusHash(items);
  const payload = JSON.stringify(createIndex(items).toJSON(hash)) + "\n";
  const output = path.join(registry, "search/catalog-index.json");
  await fs.mkdir(path.dirname(output), { recursive: true });
  await fs.writeFile(output, payload);
  return { output, documents: items.length, corpusHash: hash, bytes: Buffer.byteLength(payload) };
}

if (require.main === module) {
  const site = process.argv[2];
  if (!site || process.argv.length !== 3) {
    console.error("Usage: node scripts/build_catalog_search.cjs <generated-site-directory>");
    process.exitCode = 1;
  } else {
    buildCatalogSearch(site).then((report) => console.log(JSON.stringify(report))).catch((error) => {
      console.error(error.message);
      process.exitCode = 1;
    });
  }
}

module.exports = { buildCatalogSearch };
