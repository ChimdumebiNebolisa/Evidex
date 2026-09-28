import { writeFile } from "node:fs/promises";
import { Cursor } from "@cursor/sdk";

const locked = [
  {
    legacy_id: "cursor-grok-4.6-high-fast",
    selection: {
      id: "grok-4.6",
      params: [
        { id: "effort", value: "high" },
        { id: "fast", value: "true" },
      ],
    },
  },
  {
    legacy_id: "claude-opus-5-thinking-high",
    selection: {
      id: "claude-opus-5",
      params: [
        { id: "cyber", value: "false" },
        { id: "thinking", value: "true" },
        { id: "context", value: "1m" },
        { id: "effort", value: "high" },
        { id: "fast", value: "false" },
      ],
    },
  },
];

const auth = await Cursor.auth.status();
if (auth.status !== "logged-in") {
  throw new Error("Cursor SDK is not authenticated");
}

const [account, models] = await Promise.all([
  Cursor.me(),
  Cursor.models.list(),
]);

const available = new Set();
for (const entry of models) {
  available.add(entry.id);
  for (const alias of entry.aliases ?? []) available.add(alias);
}

function sameParams(left, right) {
  const normalize = (params) => [...params].sort((a, b) => a.id.localeCompare(b.id));
  return JSON.stringify(normalize(left)) === JSON.stringify(normalize(right));
}

const report = {
  retrieved_at_utc: new Date().toISOString(),
  sdk_authentication: "logged-in",
  api_key_name: account.apiKeyName,
  account_identity_present: Boolean(account.userId || account.userEmail),
  locked_models: locked.map(({ legacy_id, selection }) => {
    const model = models.find((item) => item.id === selection.id);
    return {
      legacy_id,
      legacy_id_listed_literally: available.has(legacy_id),
      canonical_selection: selection,
      canonical_configuration_available: Boolean(model?.variants?.some(
        (variant) => sameParams(variant.params, selection.params),
      )),
    };
  }),
  models,
};

await writeFile(
  new URL("./account_model_catalog.json", import.meta.url),
  `${JSON.stringify(report, null, 2)}\n`,
  { encoding: "utf8", flag: "w" },
);

console.log(JSON.stringify({
  authenticated: true,
  api_key_name: account.apiKeyName,
  catalog_size: models.length,
  locked_models: report.locked_models,
}));
