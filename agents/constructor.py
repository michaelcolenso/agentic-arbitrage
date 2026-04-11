"""
The Constructor (Build Agent)

Generates complete SEO sites in < 5 minutes:
- Database schema (Drizzle migrations)
- Scraping adapters
- SEO content templates
- Comparison tools
"""
import asyncio
import aiohttp
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

from core.models import Opportunity, Site, SiteStatus, OpportunityStatus, Evidence
from core.storage import Storage
from config.settings import config


@dataclass
class BuildResult:
    """Result of build process"""
    success: bool
    site_id: str
    repo_url: Optional[str]
    deploy_url: Optional[str]
    build_time_seconds: float
    pages_generated: int
    errors: List[str]


class SchemaGenerator:
    """Generates database schemas from data sources"""
    
    def generate(self, opportunity: Opportunity) -> Dict[str, Any]:
        """Generate Drizzle schema from data sources"""
        print("  Generating database schema...")
        
        schema = {
            "tables": [],
            "relations": [],
            "indexes": []
        }
        
        main_table = self._generate_main_table(opportunity)
        schema["tables"].append(main_table)
        
        for data_source in opportunity.data_sources:
            table = self._generate_source_table(data_source)
            if table:
                schema["tables"].append(table)
        
        schema["relations"] = self._generate_relations(schema["tables"])
        schema["indexes"] = self._generate_indexes()
        
        return schema
    
    def _generate_main_table(self, opportunity: Opportunity) -> Dict:
        niche = opportunity.niche
        entity_name = self._to_pascal_case(niche)
        
        fields = [
            {"name": "id", "type": "serial", "primary": True},
            {"name": "name", "type": "varchar(255)", "indexed": True},
            {"name": "slug", "type": "varchar(255)", "unique": True, "indexed": True},
            {"name": "description", "type": "text"},
            {"name": "location", "type": "varchar(255)", "indexed": True},
            {"name": "state", "type": "varchar(50)", "indexed": True},
            {"name": "status", "type": "varchar(50)", "indexed": True},
            {"name": "metadata", "type": "jsonb"},
            {"name": "createdAt", "type": "timestamp", "default": "now()"},
            {"name": "updatedAt", "type": "timestamp", "default": "now()"},
        ]
        
        return {
            "name": self._to_snake_case(niche),
            "entity": entity_name,
            "fields": fields
        }
    
    def _generate_source_table(self, data_source: Any) -> Optional[Dict]:
        if not data_source.schema or not data_source.schema.get("fields"):
            return None
        
        table_name = self._to_snake_case(data_source.name)
        
        fields = [
            {"name": "id", "type": "serial", "primary": True},
            {"name": "sourceId", "type": "varchar(255)", "indexed": True},
            {"name": "rawData", "type": "jsonb"},
            {"name": "lastUpdated", "type": "timestamp"},
        ]
        
        for field_name in data_source.schema.get("fields", [])[:5]:
            fields.append({
                "name": self._to_camel_case(field_name),
                "type": "varchar(255)",
                "indexed": True
            })
        
        return {
            "name": table_name,
            "entity": self._to_pascal_case(data_source.name),
            "fields": fields
        }
    
    def _generate_relations(self, tables: List[Dict]) -> List[Dict]:
        relations = []
        if len(tables) > 1:
            main_table = tables[0]
            for related in tables[1:]:
                relations.append({
                    "from": main_table["name"],
                    "to": related["name"],
                    "type": "one-to-many",
                    "field": related["name"] + "Id"
                })
        return relations
    
    def _generate_indexes(self) -> List[Dict]:
        return [
            {"table": "main", "fields": ["state", "location"]},
            {"table": "main", "fields": ["location", "status"]},
            {"table": "main", "fields": ["status", "createdAt"]},
        ]
    
    def _to_pascal_case(self, s: str) -> str:
        return "".join(word.capitalize() for word in s.replace("_", " ").split())
    
    def _to_snake_case(self, s: str) -> str:
        return s.lower().replace(" ", "_").replace("-", "_")
    
    def _to_camel_case(self, s: str) -> str:
        parts = s.replace("_", " ").replace("-", " ").split()
        return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])


class ScrapingAdapterGenerator:
    """Generates scraping adapters for data sources"""
    
    def generate(self, opportunity: Opportunity) -> Dict[str, str]:
        print("  Generating scraping adapters...")
        adapters = {}
        
        for data_source in opportunity.data_sources:
            if data_source.type == "api":
                adapter = self._generate_api_adapter(data_source)
            else:
                adapter = self._generate_scrape_adapter(data_source)
            adapters[data_source.name] = adapter
        
        return adapters
    
    def _generate_api_adapter(self, data_source: Any) -> str:
        class_name = self._to_pascal_case(data_source.name) + "Adapter"
        
        template = '''export class {class_name} {{
  constructor(apiKey) {{
    this.baseUrl = '{base_url}';
    this.apiKey = apiKey;
  }}

  async fetchAll(params = {{}}) {{
    const url = new URL(this.baseUrl);
    Object.entries(params).forEach(([key, value]) => {{
      if (value) url.searchParams.append(key, String(value));
    }});

    const response = await fetch(url.toString(), {{
      headers: {{
        'Authorization': `Bearer ${{this.apiKey}}`,
        'Accept': 'application/json',
      }},
    }});

    if (!response.ok) {{
      throw new Error(`API error: ${{response.status}}`);
    }}

    const data = await response.json();
    return this.transform(data);
  }}

  transform(data) {{
    if (Array.isArray(data)) return data.map(d => this.transformSingle(d));
    if (data.results) return data.results.map(d => this.transformSingle(d));
    if (data.data) return data.data.map(d => this.transformSingle(d));
    return [this.transformSingle(data)];
  }}

  transformSingle(item) {{
    return {{
      sourceId: item.id || item.uuid,
      rawData: item,
      lastUpdated: new Date(),
    }};
  }}
}}
'''
        return template.format(class_name=class_name, base_url=data_source.url)
    
    def _generate_scrape_adapter(self, data_source: Any) -> str:
        class_name = self._to_pascal_case(data_source.name) + "Scraper"
        
        template = '''export class {class_name} {{
  constructor() {{
    this.baseUrl = '{base_url}';
  }}

  async scrapeList(page = 1) {{
    const url = `${{this.baseUrl}}?page=${{page}}`;
    
    const response = await fetch(url, {{
      headers: {{
        'User-Agent': 'Mozilla/5.0 (compatible; SEOBot/1.0)',
      }},
    }});

    const html = await response.text();
    return this.parseList(html);
  }}

  parseList(html) {{
    // Implement parsing logic based on page structure
    const items = [];
    return items;
  }}
}}
'''
        return template.format(class_name=class_name, base_url=data_source.url)
    
    def _to_pascal_case(self, s: str) -> str:
        return "".join(word.capitalize() for word in s.replace("_", " ").split())


class TemplateGenerator:
    """Generates SEO content templates"""
    
    def generate(self, opportunity: Opportunity) -> Dict[str, str]:
        print("  Generating SEO templates...")
        
        if opportunity.niche == "ev_charger_rebates":
            return EVChargerTemplateGenerator().generate()
        
        templates = {}
        niche_title = opportunity.niche.replace("_", " ").title()
        niche_lower = opportunity.niche.replace("_", " ").lower()
        
        templates["home"] = self._generate_home_template(niche_title, niche_lower)
        templates["list"] = self._generate_list_template(niche_title, niche_lower)
        templates["detail"] = self._generate_detail_template(niche_title, niche_lower)
        templates["compare"] = self._generate_compare_template(niche_title, niche_lower)
        
        return templates
    
    def _generate_home_template(self, niche_title: str, niche_lower: str) -> str:
        return f'''export default function Home({{ stats, featured }}) {{
  return (
    <Layout
      title="{niche_title} Database | Find & Compare"
      description="Comprehensive database of {niche_lower}. Search, filter, and compare."
    >
      <Hero
        title="Find the Best {niche_title}"
        subtitle="Search thousands of {niche_lower} in our database"
      />
      <Stats stats={{stats}} />
      <FeaturedList items={{featured}} />
    </Layout>
  );
}}

export async function getStaticProps() {{
  const [stats, featured] = await Promise.all([
    getStats(),
    getFeatured(6),
  ]);
  return {{ props: {{ stats, featured }}, revalidate: 3600 }};
}}
'''
    
    def _generate_list_template(self, niche_title: str, niche_lower: str) -> str:
        return f'''export default function ListPage({{ entities, filters }}) {{
  return (
    <Layout
      title="All {niche_title} - Complete Database"
      description="Browse our complete database of {niche_lower}."
    >
      <div className="container">
        <h1>All {niche_title}</h1>
        <FilterBar filters={{filters}} />
        <EntityList entities={{entities}} />
      </div>
    </Layout>
  );
}}
'''
    
    def _generate_detail_template(self, niche_title: str, niche_lower: str) -> str:
        return '''export default function DetailPage({ entity }) {
  return (
    <Layout
      title={`${entity.name} - ''' + niche_title + ''' Details`}
      description={entity.description}
    >
      <div className="container">
        <EntityDetail entity={entity} />
      </div>
    </Layout>
  );
}
'''
    
    def _generate_compare_template(self, niche_title: str, niche_lower: str) -> str:
        return f'''export default function ComparePage({{ entities }}) {{
  return (
    <Layout
      title="Compare {niche_title} Side by Side"
      description="Compare {niche_lower} side by side."
    >
      <div className="container">
        <h1>Compare {niche_title}</h1>
        <CompareTable entities={{entities}} />
      </div>
    </Layout>
  );
}}
'''


class EVChargerTemplateGenerator:
    """Generates EV charger incentives Next.js App Router templates"""
    
    STATES = [
        "California", "Texas", "Florida", "New York", "Pennsylvania",
        "Illinois", "Ohio", "Georgia", "North Carolina", "Michigan"
    ]
    
    def generate(self) -> Dict[str, str]:
        templates = {}
        templates["layout"] = self._layout()
        templates["page"] = self._home_page()
        templates["ev-charger-rebates/page"] = self._rebates_list_page()
        templates["ev-charger-rebates/[state]/page"] = self._state_page()
        templates["ev-charger-tax-credit/page"] = self._tax_credit_page()
        templates["level-2-charger-rebate-checklist/page"] = self._checklist_page()
        templates["api/health/route"] = self._health_route()
        templates["robots"] = self._robots()
        templates["sitemap"] = self._sitemap()
        templates["next-config"] = self._next_config()
        return templates
    
    def _layout(self) -> str:
        return '''export const metadata = {
  title: {
    default: "EV Charger Rebates & Tax Credits",
    template: "%s | EV Charger Rebates",
  },
  description: "Find EV charger rebates, tax credits, and incentives by state and utility. Updated for the federal 30C credit deadline.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, sans-serif", margin: 0, padding: 0 }}>
        <header style={{ padding: "1rem", borderBottom: "1px solid #eee" }}>
          <nav>
            <a href="/" style={{ marginRight: "1rem" }}>Home</a>
            <a href="/ev-charger-rebates" style={{ marginRight: "1rem" }}>Rebates by State</a>
            <a href="/ev-charger-tax-credit" style={{ marginRight: "1rem" }}>Tax Credit</a>
            <a href="/level-2-charger-rebate-checklist">Checklist</a>
          </nav>
        </header>
        <main style={{ padding: "1rem" }}>{children}</main>
        <footer style={{ padding: "1rem", borderTop: "1px solid #eee", marginTop: "2rem" }}>
          <p>© {new Date().getFullYear()} EV Charger Rebates Database</p>
        </footer>
      </body>
    </html>
  );
}
'''
    
    def _home_page(self) -> str:
        return '''import Link from "next/link";

export default function HomePage() {
  return (
    <div>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "WebSite",
            name: "EV Charger Rebates Database",
            url: "/",
          }),
        }}
      />
      <h1>EV Charger Rebates & Incentives Database</h1>
      <p>Find money-back programs for installing a Level 2 EV charger at home before the June 30, 2026 federal credit deadline.</p>
      
      <section style={{ marginTop: "1.5rem" }}>
        <h2>Quick Links</h2>
        <ul>
          <li><Link href="/ev-charger-rebates">Browse rebates by state</Link></li>
          <li><Link href="/ev-charger-tax-credit">Federal 30C tax credit</Link></li>
          <li><Link href="/level-2-charger-rebate-checklist">Get your personalized checklist</Link></li>
        </ul>
      </section>
    </div>
  );
}
'''
    
    def _rebates_list_page(self) -> str:
        states_str = ", ".join([f'"{s}"' for s in self.STATES])
        return f'''import Link from "next/link";

export default function RebatesListPage() {{
  const states = [{states_str}];
  return (
    <div>
      <h1>EV Charger Rebates by State</h1>
      <p>Browse state and utility rebates for home EV charger installation.</p>
      <ul>
        {{states.map((state) => (
          <li key={{state}}>
            <Link href={{`/ev-charger-rebates/${{state.toLowerCase().replace(/\\s/g, "-")}}`}}>
              {{state}} EV Charger Rebates
            </Link>
          </li>
        ))}}
      </ul>
      <p><Link href="/ev-charger-tax-credit">→ See the federal 30C tax credit</Link></p>
    </div>
  );
}}
'''
    
    def _state_page(self) -> str:
        return '''export default function StatePage({ params }) {
  const state = params.state;
  const stateTitle = state.replace(/-/g, " ").replace(/\\b\\w/g, (l) => l.toUpperCase());
  return (
    <div>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "GovernmentService",
            name: `${stateTitle} EV Charger Rebates`,
            serviceType: "Rebate Program",
            areaServed: { "@type": "State", name: stateTitle },
          }),
        }}
      />
      <h1>{stateTitle} EV Charger Rebates</h1>
      <p>State and utility rebates for {stateTitle} residents installing a Level 2 home EV charger.</p>
      <p><a href="/ev-charger-tax-credit">→ Federal 30C tax credit details</a></p>
      <p><a href="/level-2-charger-rebate-checklist">→ Get your rebate checklist</a></p>
    </div>
  );
}
'''
    
    def _tax_credit_page(self) -> str:
        return '''export default function TaxCreditPage() {
  return (
    <div>
      <h1>Federal EV Charger Tax Credit (30C)</h1>
      <p>
        The federal 30C tax credit covers 30% of the cost to install a qualified EV charger at your
        primary residence, up to $1,000. <strong>Deadline: June 30, 2026.</strong>
      </p>
      <h2>Who Qualifies</h2>
      <ul>
        <li>Property must be in a low-income community or non-urban census tract</li>
        <li>Charger must be Level 2 or higher and installed at a primary residence</li>
      </ul>
      <p><a href="/level-2-charger-rebate-checklist">→ Check if you qualify</a></p>
    </div>
  );
}
'''
    
    def _checklist_page(self) -> str:
        return '''export default function ChecklistPage() {
  return (
    <div>
      <h1>Level 2 Charger Rebate Checklist</h1>
      <p>Enter your ZIP code and email to get a personalized rebate checklist.</p>
      <form action="/api/lead" method="POST" style={{ maxWidth: 400 }}>
        <div style={{ marginBottom: "1rem" }}>
          <label htmlFor="zip">ZIP Code</label>
          <input id="zip" name="zip" type="text" maxLength={10} required style={{ width: "100%" }} />
        </div>
        <div style={{ marginBottom: "1rem" }}>
          <label htmlFor="email">Email</label>
          <input id="email" name="email" type="email" required style={{ width: "100%" }} />
        </div>
        <button type="submit">Get My Checklist</button>
      </form>
      <p style={{ marginTop: "1rem" }}><a href="/ev-charger-rebates">← Back to rebates by state</a></p>
    </div>
  );
}
'''
    
    def _health_route(self) -> str:
        return '''export async function GET() {
  return Response.json({ status: "ok", timestamp: new Date().toISOString() });
}
'''
    
    def _robots(self) -> str:
        return "User-agent: *\\nAllow: /\\n\\nSitemap: /sitemap.xml\\n"
    
    def _sitemap(self) -> str:
        return '''export default function sitemap() {
  const base = "https://example.com";
  const routes = [
    "",
    "/ev-charger-rebates",
    "/ev-charger-tax-credit",
    "/level-2-charger-rebate-checklist",
  ];
  return routes.map((route) => ({
    url: `${base}${route}`,
    lastModified: new Date(),
  }));
}
'''
    
    def _next_config(self) -> str:
        return '''/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  distDir: 'dist',
};
module.exports = nextConfig;
'''


class DeploymentAdapter:
    """Base deployment adapter"""
    
    async def deploy(self, site: Site, project_path: Path) -> Dict[str, str]:
        raise NotImplementedError
    
    async def health_check(self, deploy_url: str) -> bool:
        if deploy_url.startswith("file://"):
            local_path = Path(deploy_url.replace("file://", ""))
            return local_path.exists() and (local_path / "index.html").exists()
        
        health_url = deploy_url.rstrip("/") + "/api/health"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(health_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    return resp.status == 200
        except Exception:
            # Fallback: check root URL
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(deploy_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        return resp.status == 200
            except Exception:
                return False


class DemoDeploymentAdapter(DeploymentAdapter):
    """Fake deployment for demo mode"""
    
    async def deploy(self, site: Site, project_path: Path) -> Dict[str, str]:
        domain = site.niche.replace("_", "-") + ".pages.dev"
        return {"url": "https://" + domain, "project_id": site.id, "adapter": "demo"}
    
    async def health_check(self, deploy_url: str) -> bool:
        return True


class LocalDeploymentAdapter(DeploymentAdapter):
    """Local file deployment for tests and staging"""
    
    async def deploy(self, site: Site, project_path: Path) -> Dict[str, str]:
        import shutil
        deploy_dir = project_path.parent / "deployments" / site.id
        deploy_dir.mkdir(parents=True, exist_ok=True)
        
        dist_dir = project_path / "dist"
        if dist_dir.exists():
            shutil.copytree(dist_dir, deploy_dir, dirs_exist_ok=True)
        else:
            # Copy project files as fallback
            shutil.copytree(project_path, deploy_dir, dirs_exist_ok=True)
        
        return {"url": "file://" + str(deploy_dir), "project_id": site.id, "adapter": "local"}


class CloudflareDeploymentAdapter(DeploymentAdapter):
    """Production Cloudflare Pages deployment"""
    
    async def deploy(self, site: Site, project_path: Path) -> Dict[str, str]:
        if not config.cloudflare_api_token:
            raise RuntimeError("CloudflareDeploymentAdapter requires CLOUDFLARE_API_TOKEN")
        
        # Try wrangler CLI deployment if available
        wrangler_check = subprocess.run(
            ["npx", "wrangler", "--version"],
            capture_output=True,
            timeout=30
        )
        
        if wrangler_check.returncode != 0:
            raise RuntimeError(
                "CloudflareDeploymentAdapter requires wrangler CLI. "
                "Install with: npm install -g wrangler"
            )
        
        # For this MVP, we run wrangler pages deploy
        # In a full implementation, this would use the Cloudflare API directly
        deploy_result = subprocess.run(
            ["npx", "wrangler", "pages", "deploy", "dist", "--project-name", site.niche.replace("_", "-")],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300,
            env={**os.environ, "CLOUDFLARE_API_TOKEN": config.cloudflare_api_token}
        )
        
        if deploy_result.returncode != 0:
            raise RuntimeError(f"Wrangler deploy failed: {deploy_result.stderr[:500]}")
        
        # Extract URL from wrangler output (best-effort)
        url = f"https://{site.niche.replace('_', '-')}.pages.dev"
        return {"url": url, "project_id": site.id, "adapter": "cloudflare"}


class Constructor:
    """The Constructor Build Agent"""
    
    def __init__(self, storage: Storage = None):
        self.storage = storage or Storage()
        self.schema_generator = SchemaGenerator()
        self.adapter_generator = ScrapingAdapterGenerator()
        self.template_generator = TemplateGenerator()
    
    def _get_deployment_adapter(self) -> DeploymentAdapter:
        if config.is_demo:
            return DemoDeploymentAdapter()
        if config.is_production:
            return CloudflareDeploymentAdapter()
        return LocalDeploymentAdapter()
    
    async def build(self, opportunity: Opportunity) -> BuildResult:
        print("\\nBuilding " + opportunity.niche + "...")
        
        start_time = datetime.now()
        errors = []
        site = None
        
        try:
            site = Site(
                opportunity_id=opportunity.id,
                name=opportunity.niche.replace("_", " ").title(),
                niche=opportunity.niche,
                status=SiteStatus.BUILDING
            )
            self.storage.save_site(site)
            
            schema = self.schema_generator.generate(opportunity)
            site.data_schema = schema
            
            adapters = self.adapter_generator.generate(opportunity)
            templates = self.template_generator.generate(opportunity)
            
            project_path = await self._create_project_files(
                site, opportunity, schema, adapters, templates
            )
            
            # Build gate
            build_output = await self._run_build(project_path)
            
            if not build_output["success"]:
                raise RuntimeError(f"Build failed: {build_output['output'][:500]}")
            
            deploy_result = await self._deploy(site, project_path)
            
            site.deploy_url = deploy_result.get("url")
            
            # Health check before marking DEPLOYED
            adapter = self._get_deployment_adapter()
            healthy = await adapter.health_check(site.deploy_url)
            
            if not healthy:
                raise RuntimeError(f"Health check failed for {site.deploy_url}")
            
            site.status = SiteStatus.DEPLOYED
            site.deployed_at = datetime.now()
            site.page_count = len(templates) * 50
            self.storage.save_site(site)
            
            # Record deployment evidence
            self.storage.save_evidence(Evidence(
                evidence_type="deployment",
                opportunity_id=opportunity.id,
                site_id=site.id,
                data={
                    "build_status": "success",
                    "build_output": build_output["output"][:1000],
                    "deployment_adapter": deploy_result.get("adapter", "unknown"),
                    "deployment_url": site.deploy_url,
                    "health_check_status": "passed",
                    "checked_timestamp": datetime.now().isoformat(),
                }
            ))
            
            opportunity.status = OpportunityStatus.DEPLOYED
            opportunity.site_id = site.id
            opportunity.deployed_url = site.deploy_url
            opportunity.built_at = datetime.now()
            self.storage.save_opportunity(opportunity)
            
            build_time = (datetime.now() - start_time).total_seconds()
            
            print("Built " + opportunity.niche + " in " + str(int(build_time)) + "s")
            print("   URL: " + site.deploy_url)
            
            return BuildResult(
                success=True,
                site_id=site.id,
                repo_url=site.repo_url,
                deploy_url=site.deploy_url,
                build_time_seconds=build_time,
                pages_generated=site.page_count,
                errors=[]
            )
            
        except Exception as e:
            errors.append(str(e))
            print("Build failed: " + str(e))
            
            build_time = (datetime.now() - start_time).total_seconds()
            
            if site:
                site.status = SiteStatus.FAILED
                self.storage.save_site(site)
                
                self.storage.save_evidence(Evidence(
                    evidence_type="deployment",
                    opportunity_id=opportunity.id,
                    site_id=site.id,
                    data={
                        "build_status": "failed",
                        "error": str(e),
                        "checked_timestamp": datetime.now().isoformat(),
                    }
                ))
            
            # Update opportunity to failed status
            if opportunity.status == OpportunityStatus.BUILDING:
                opportunity.status = OpportunityStatus.BUILD_FAILED
            else:
                opportunity.status = OpportunityStatus.DEPLOYMENT_FAILED
            self.storage.save_opportunity(opportunity)
            
            return BuildResult(
                success=False,
                site_id=site.id if site else "",
                repo_url=None,
                deploy_url=None,
                build_time_seconds=build_time,
                pages_generated=0,
                errors=errors
            )
    
    async def _create_project_files(self, site, opportunity, schema, adapters, templates):
        print("  Creating project files...")
        
        base_path = config.sites_dir / site.id
        base_path.mkdir(parents=True, exist_ok=True)
        
        dirs = ["src", "src/app", "src/components", "src/lib", "src/adapters", "migrations", "public"]
        for d in dirs:
            (base_path / d).mkdir(parents=True, exist_ok=True)
        
        with open(base_path / "schema.json", "w") as f:
            json.dump(schema, f, indent=2)
        
        for name, code in adapters.items():
            adapter_path = base_path / "src/adapters" / (name.lower().replace(" ", "_") + ".ts")
            with open(adapter_path, "w") as f:
                f.write(code)
        
        for name, code in templates.items():
            if name == "robots":
                with open(base_path / "public" / "robots.txt", "w") as f:
                    f.write(code)
            elif name == "next-config":
                with open(base_path / "next.config.js", "w") as f:
                    f.write(code)
            elif "/" in name:
                # Nested app router paths like ev-charger-rebates/page.tsx
                ext = ".ts" if name.endswith("/route") else ".tsx"
                template_path = base_path / "src/app" / (name + ext)
                template_path.parent.mkdir(parents=True, exist_ok=True)
                with open(template_path, "w") as f:
                    f.write(code)
            else:
                template_path = base_path / "src/app" / (name + ".tsx")
                with open(template_path, "w") as f:
                    f.write(code)
        
        package_json = self._generate_package_json(site)
        with open(base_path / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)
        
        return base_path
    
    def _generate_package_json(self, site: Site) -> Dict:
        return {
            "name": site.niche.replace("_", "-"),
            "version": "1.0.0",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "deploy": "wrangler deploy"
            },
            "dependencies": {
                "next": "^14.0.0",
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            },
            "devDependencies": {
                "@types/node": "^20.0.0",
                "@types/react": "^18.2.0",
                "typescript": "^5.0.0"
            }
        }
    
    async def _run_build(self, project_path: Path) -> Dict[str, Any]:
        """Run npm install and npm build in the project directory."""
        if config.is_demo:
            return {"success": True, "output": "skipped in demo mode"}
        
        print("  Running npm install...")
        install_result = subprocess.run(
            ["npm", "install"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if install_result.returncode != 0:
            return {
                "success": False,
                "output": install_result.stdout + install_result.stderr
            }
        
        print("  Running npm run build...")
        build_result = subprocess.run(
            ["npm", "run", "build"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return {
            "success": build_result.returncode == 0,
            "output": build_result.stdout + build_result.stderr
        }
    
    async def _deploy(self, site: Site, project_path: Path) -> Dict[str, str]:
        adapter = self._get_deployment_adapter()
        print(f"  Deploying with {adapter.__class__.__name__}...")
        return await adapter.deploy(site, project_path)
    
    async def build_queue(self) -> List[BuildResult]:
        opportunities = self.storage.get_opportunities_by_status(OpportunityStatus.VALIDATED)
        
        print("\\nBuilding " + str(len(opportunities)) + " sites...")
        
        results = []
        for opp in opportunities:
            result = await self.build(opp)
            results.append(result)
        
        successful = sum(1 for r in results if r.success)
        print("\\n" + str(successful) + "/" + str(len(results)) + " sites built successfully")
        
        return results


if __name__ == "__main__":
    async def main():
        constructor = Constructor()
        results = await constructor.build_queue()
        
        print("\\nBUILD RESULTS")
        for result in results:
            status = "SUCCESS" if result.success else "FAILED"
            print(status + " - " + result.site_id)
    
    asyncio.run(main())
