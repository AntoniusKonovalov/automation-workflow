// Fetch eval run object documentation
import { DOMParser } from "linkedom";

async function fetchEvalRunDoc() {
  const url = "https://platform.openai.com/docs/api-reference/evals/run-object";
  
  try {
    console.log(`Fetching: ${url}\n`);
    
    const response = await fetch(url, {
      headers: {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.5",
        "cache-control": "no-cache"
      }
    });
    
    console.log(`Response status: ${response.status}`);
    
    if (!response.ok) {
      console.log(`Error: ${response.status} ${response.statusText}`);
      
      // Try with a different approach - using curl via command line
      console.log("\nTrying with curl command...");
      return;
    }
    
    const html = await response.text();
    const { document } = new DOMParser().parseFromString(html, "text/html");
    
    // Extract title
    const title = document.querySelector("h1")?.textContent?.trim() || 
                  document.querySelector("title")?.textContent?.trim() || 
                  "Eval Run Object";
    
    console.log(`Title: ${title}\n`);
    
    // Extract description/summary
    const description = document.querySelector('meta[name="description"]')?.getAttribute("content") ||
                       document.querySelector("p")?.textContent?.trim() || "";
    
    if (description) {
      console.log(`Description: ${description}\n`);
    }
    
    // Look for code blocks with JSON schema
    console.log("Looking for object structure...\n");
    
    const codeBlocks = document.querySelectorAll("pre, code");
    codeBlocks.forEach((block, i) => {
      const content = block.textContent?.trim();
      if (content && (content.includes('"id"') || content.includes('eval_id') || content.includes('"status"'))) {
        console.log(`Code block ${i + 1}:`);
        console.log("```json");
        console.log(content);
        console.log("```\n");
      }
    });
    
    // Look for property definitions
    const propertyHeaders = document.querySelectorAll("h3, h4, strong");
    const properties = [];
    
    propertyHeaders.forEach(header => {
      const text = header.textContent?.trim();
      if (text && (text.includes("id") || text.includes("status") || text.includes("created") || 
                   text.includes("eval") || text.includes("model"))) {
        properties.push(text);
      }
    });
    
    if (properties.length > 0) {
      console.log("Found properties:");
      properties.forEach(prop => console.log(`  - ${prop}`));
    }
    
  } catch (error) {
    console.error("Error fetching documentation:", error.message);
    
    // Suggest alternative
    console.log("\nNote: The OpenAI docs may require authentication or have CORS restrictions.");
    console.log("You can visit the URL directly in your browser:");
    console.log(`  ${url}`);
  }
}

// Also try fetching related endpoints
async function fetchRelatedDocs() {
  const urls = [
    "https://platform.openai.com/docs/api-reference/evals/getRun",
    "https://platform.openai.com/docs/api-reference/evals/createRun",
    "https://platform.openai.com/docs/api-reference/evals/run-output-item-object"
  ];
  
  console.log("\n=== Related Documentation ===\n");
  
  for (const url of urls) {
    console.log(`Checking: ${url}`);
    try {
      const response = await fetch(url, {
        method: 'HEAD',
        headers: {
          "user-agent": "Mozilla/5.0"
        }
      });
      console.log(`  Status: ${response.status} ${response.ok ? '✓' : '✗'}`);
    } catch (e) {
      console.log(`  Error: ${e.message}`);
    }
  }
}

async function main() {
  await fetchEvalRunDoc();
  await fetchRelatedDocs();
}

main();