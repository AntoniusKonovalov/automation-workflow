// Direct search for eval documentation
import { XMLParser } from "fast-xml-parser";

async function searchEvalDocs() {
  const SITEMAP_URL = "https://platform.openai.com/sitemap.xml";
  
  try {
    // Fetch sitemap
    console.log("Fetching OpenAI sitemap...");
    const response = await fetch(SITEMAP_URL, {
      headers: { 
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" 
      }
    });
    
    if (!response.ok) {
      console.log(`Error fetching sitemap: ${response.status} ${response.statusText}`);
      return;
    }
    
    const xml = await response.text();
    
    // Parse XML
    const parser = new XMLParser({ ignoreAttributes: false });
    const parsed = parser.parse(xml);
    
    // Extract URLs
    const urls = parsed?.urlset?.url?.map(u => (typeof u === 'string' ? u : u.loc))?.filter(Boolean) || [];
    
    // Search for eval-related URLs
    console.log("\nSearching for eval-related documentation...");
    const evalUrls = urls.filter(url => 
      url.toLowerCase().includes('eval') && 
      url.includes('/docs/')
    );
    
    console.log(`\nFound ${evalUrls.length} eval-related URLs:`);
    evalUrls.forEach(url => console.log(`  - ${url}`));
    
    // Also search for "run" in API reference
    console.log("\nSearching for 'run' in API reference...");
    const runUrls = urls.filter(url => 
      url.toLowerCase().includes('run') && 
      url.includes('/docs/api-reference/')
    );
    
    console.log(`\nFound ${runUrls.length} run-related API URLs:`);
    runUrls.forEach(url => console.log(`  - ${url}`));
    
    // Search specifically for eval run combinations
    console.log("\nSearching for eval AND run URLs...");
    const evalRunUrls = urls.filter(url => {
      const lower = url.toLowerCase();
      return (lower.includes('eval') && lower.includes('run')) || 
             lower.includes('evalrun');
    });
    
    console.log(`\nFound ${evalRunUrls.length} eval-run related URLs:`);
    evalRunUrls.forEach(url => console.log(`  - ${url}`));
    
  } catch (error) {
    console.error("Error:", error.message);
  }
}

searchEvalDocs();