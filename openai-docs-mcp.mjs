// openai-docs-mcp.mjs
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { XMLParser } from "fast-xml-parser";
import { DOMParser } from "linkedom";
import { fetch } from "undici";
import { z } from "zod";

const BASE = "https://platform.openai.com";
const DOCS = `${BASE}/docs`;
const SITEMAP_URL = `${BASE}/sitemap.xml`;

const server = new McpServer({ name: "openai-docs", version: "0.1.0" });

// ---- helpers ----
function normalizePathOrUrl(input) {
  if (/^https?:\/\//i.test(input)) return input;
  if (input.startsWith("/docs/")) return `${BASE}${input}`;
  if (input.startsWith("docs/")) return `${BASE}/${input}`;
  if (input.startsWith("api-reference")) return `${DOCS}/${input}`;
  return `${DOCS}/${input.replace(/^\/+/, "")}`;
}

async function fetchText(url) {
  const res = await fetch(url, {
    headers: { "user-agent": "openai-docs-mcp/0.1 (+https://example.local)" },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText} for ${url}`);
  return await res.text();
}

const squash = (s) => (s || "").replace(/\s+/g, " ").trim();

function parseDocHtml(html, url) {
  const { document } = new DOMParser().parseFromString(html, "text/html");

  const title =
    document.querySelector("h1")?.textContent?.trim() ||
    document.querySelector("title")?.textContent?.trim() ||
    null;

  const summary =
    document.querySelector('meta[name="description"]')?.getAttribute("content") ||
    document.querySelector("p")?.textContent?.trim() ||
    null;

  const text = document.body?.textContent || "";
  const methodPathMatches = Array.from(
    text.matchAll(/\b(GET|POST|PUT|PATCH|DELETE)\s+(\/[^\s]+)/g)
  );

  const examples = [];
  document.querySelectorAll("pre, code").forEach((el) => {
    const t = el.textContent?.trim();
    if (t && examples.length < 8) examples.push(t);
  });

  const endpoints = [];
  const seen = new Set();
  for (const m of methodPathMatches) {
    const method = m[1];
    const path = m[2];
    const key = `${method} ${path}`;
    if (!seen.has(key)) {
      seen.add(key);
      endpoints.push({
        method,
        path,
        title: null,
        summary: null,
        params: [],
        examples: [],
      });
    }
  }

  if (endpoints.length && examples.length) {
    endpoints[endpoints.length - 1].examples = examples.slice(0, 2);
  }

  return { url, title, summary: squash(summary), endpoints };
}

function toMarkdown(doc) {
  const lines = [];
  lines.push(`# ${doc.title || "OpenAI API"}`);
  lines.push(`*URL:* ${doc.url}`);
  if (doc.summary) {
    lines.push("");
    lines.push(doc.summary);
  }
  if (doc.endpoints?.length) {
    lines.push("\n## Endpoints");
    for (const ep of doc.endpoints) {
      lines.push(`- **${ep.method || "?"} ${ep.path || ""}**`);
      if (ep.params?.length) {
        lines.push("  - **Parameters:**");
        for (const p of ep.params) {
          lines.push(`    - \`${p.name}\`${p.required ? " (required)" : ""}`);
        }
      }
      if (ep.examples?.length) {
        lines.push("  - **Example(s):**");
        for (const ex of ep.examples.slice(0, 2)) {
          lines.push("    ```");
          lines.push(ex);
          lines.push("    ```");
        }
      }
    }
  }
  return lines.join("\n");
}

// ---- tools ----

// 1) Fetch + parse a doc page
server.registerTool(
  "get_openai_doc",
  {
    description:
      "Fetch and parse an OpenAI docs page. Accepts full URL or docs path like 'api-reference/evals/deleteRun'.",
    inputSchema: z.object({
      path_or_url: z.string(),
      format: z.enum(["structured", "markdown"]).default("structured"),
    }),
  },
  async ({ path_or_url, format = "structured" }) => {
    try {
      const url = normalizePathOrUrl(path_or_url);
      const html = await fetchText(url);
      const parsed = parseDocHtml(html, url);
      if (format === "markdown") {
        return { content: [{ type: "text", text: toMarkdown(parsed) }] };
      }
      return { content: [{ type: "json", json: parsed }] };
    } catch (err) {
      return { content: [{ type: "text", text: `Error: ${err?.message || String(err)}` }] };
    }
  }
);

// 2) Search docs via sitemap
server.registerTool(
  "search_openai_docs",
  {
    description: "Search OpenAI docs using the sitemap. Returns URLs that contain the query.",
    inputSchema: z.object({
      query: z.string(),
      limit: z.number().int().min(1).max(50).default(10),
    }),
  },
  async ({ query, limit = 10 }) => {
    try {
      const xml = await fetchText(SITEMAP_URL);
      const parser = new XMLParser({ ignoreAttributes: false });
      const parsed = parser.parse(xml);
      const urls =
        parsed?.urlset?.url?.map((u) => (typeof u === "string" ? u : u.loc))?.filter(Boolean) ||
        [];
      const hits = urls
        .filter(
          (u) =>
            typeof u === "string" &&
            u.includes("/docs/") &&
            u.toLowerCase().includes(query.toLowerCase())
        )
        .slice(0, limit);
      return { content: [{ type: "json", json: { results: hits } }] };
    } catch (err) {
      return { content: [{ type: "text", text: `Error: ${err?.message || String(err)}` }] };
    }
  }
);

// 3) List /docs/api-reference/* URLs
server.registerTool(
  "list_openai_api_paths",
  {
    description: "List '/docs/api-reference/...' URLs from the sitemap for quick navigation.",
    inputSchema: z.object({
      limit: z.number().int().min(1).max(200).default(50),
    }),
  },
  async ({ limit = 50 }) => {
    try {
      const xml = await fetchText(SITEMAP_URL);
      const parser = new XMLParser({ ignoreAttributes: false });
      const parsed = parser.parse(xml);
      const urls =
        parsed?.urlset?.url?.map((u) => (typeof u === "string" ? u : u.loc))?.filter(Boolean) ||
        [];
      const apiUrls = urls.filter(
        (u) => typeof u === "string" && u.includes("/docs/api-reference/")
      );
      return { content: [{ type: "json", json: { results: apiUrls.slice(0, limit) } }] };
    } catch (err) {
      return { content: [{ type: "text", text: `Error: ${err?.message || String(err)}` }] };
    }
  }
);

// start
try {
  await server.connect(new StdioServerTransport());
  console.log("[openai-docs] MCP server ready (stdio)");
} catch (e) {
  console.error("MCP connect failed:", e);
  process.exit(1);
}
