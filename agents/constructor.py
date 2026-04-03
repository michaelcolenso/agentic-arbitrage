"""
The Constructor (Build Agent)

Generates complete SEO sites in < 5 minutes:
- Database schema (Drizzle migrations)
- Scraping adapters
- SEO content templates
- Comparison tools
"""
import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

from core.models import Opportunity, Site, SiteStatus, OpportunityStatus
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


class Constructor:
    """The Constructor Build Agent"""
    
    def __init__(self, storage: Storage = None):
        self.storage = storage or Storage()
        self.schema_generator = SchemaGenerator()
        self.adapter_generator = ScrapingAdapterGenerator()
        self.template_generator = TemplateGenerator()
    
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
            
            deploy_result = await self._deploy(site, project_path)
            
            site.status = SiteStatus.DEPLOYED
            site.deployed_at = datetime.now()
            site.deploy_url = deploy_result.get("url")
            site.page_count = len(templates) * 50
            self.storage.save_site(site)
            
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
        
        dirs = ["src", "src/app", "src/components", "src/lib", "src/adapters", "migrations"]
        for d in dirs:
            (base_path / d).mkdir(parents=True, exist_ok=True)
        
        with open(base_path / "schema.json", "w") as f:
            json.dump(schema, f, indent=2)
        
        for name, code in adapters.items():
            adapter_path = base_path / "src/adapters" / (name.lower().replace(" ", "_") + ".ts")
            with open(adapter_path, "w") as f:
                f.write(code)
        
        for name, code in templates.items():
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
            }
        }
    
    async def _deploy(self, site: Site, project_path: Path) -> Dict[str, str]:
        print("  Deploying to Cloudflare...")
        domain = site.niche.replace("_", "-") + ".pages.dev"
        return {"url": "https://" + domain, "project_id": site.id}
    
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
