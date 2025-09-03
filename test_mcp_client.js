// Test MCP client to search for eval run object
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { spawn } from "child_process";

async function main() {
  const transport = new StdioClientTransport({
    command: "node",
    args: ["openai-docs-mcp.mjs"],
  });

  const client = new Client({
    name: "test-client",
    version: "1.0.0",
  }, {
    capabilities: {},
  });

  await client.connect(transport);
  
  console.log("Connected to MCP server");
  
  // Search for eval run object
  console.log("\nSearching for 'eval run' in OpenAI docs...");
  const searchResult = await client.callTool({
    name: "search_openai_docs",
    arguments: {
      query: "eval run",
      limit: 20
    }
  });
  
  console.log("Search results:", JSON.stringify(searchResult, null, 2));
  
  // Also search for just "eval"
  console.log("\nSearching for 'eval' in OpenAI docs...");
  const evalSearchResult = await client.callTool({
    name: "search_openai_docs",
    arguments: {
      query: "eval",
      limit: 10
    }
  });
  
  console.log("Eval search results:", JSON.stringify(evalSearchResult, null, 2));
  
  // List API paths to see what's available
  console.log("\nListing API reference paths...");
  const apiPaths = await client.callTool({
    name: "list_openai_api_paths",
    arguments: {
      limit: 100
    }
  });
  
  console.log("API paths (filtered for eval):");
  const paths = apiPaths.content?.[0]?.json?.results || [];
  const evalPaths = paths.filter(p => p.toLowerCase().includes('eval'));
  console.log(evalPaths);
  
  // If we found eval-related paths, fetch one
  if (evalPaths.length > 0) {
    console.log("\nFetching first eval-related doc...");
    const docResult = await client.callTool({
      name: "get_openai_doc",
      arguments: {
        path_or_url: evalPaths[0],
        format: "markdown"
      }
    });
    console.log("Doc content:", docResult.content?.[0]?.text);
  }
  
  await client.close();
}

main().catch(console.error);