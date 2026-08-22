"""Section 6.4: Lead Gen — scrape → enrich → score → personalize → send"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pocketflow import Node, Flow
from call_llm import call_llm
import yaml

PRODUCT = "PocketFlow — a 100-line LLM framework for building AI apps with zero dependencies"

SAMPLE_LEADS = [
    {"name": "Sarah Chen", "title": "CTO", "company": "DataStack AI",
     "enrichment": "DataStack AI raised $12M Series A, building LLM-powered analytics. 45 employees, hiring ML engineers. Uses Python, AWS, Postgres."},
    {"name": "Marcus Johnson", "title": "VP Engineering", "company": "CloudNine Labs",
     "enrichment": "CloudNine Labs, 120 employees, Series B. Building cloud dev tools. Recently launched AI code assistant. Uses TypeScript, GCP."},
    {"name": "Priya Patel", "title": "Head of AI", "company": "FinBot",
     "enrichment": "FinBot, 30 employees, seed stage. AI chatbot for financial advisors. Just pivoted to LLM-based approach. Uses Python, OpenAI API."},
]

class ScrapeLeads(Node):
    """In production: API calls to LinkedIn, Apollo, or a lead database."""
    def prep(self, shared):
        return shared.get("leads", SAMPLE_LEADS)
    def exec(self, leads):
        return leads
    def post(self, shared, prep_res, exec_res):
        shared["leads"] = exec_res
        print(f"  Loaded {len(exec_res)} leads")

class EnrichLeads(Node):
    """In production: API calls to Clearbit, Apollo, or web search per lead."""
    def prep(self, shared):
        return shared["leads"]
    def exec(self, leads):
        return leads  # already enriched in sample data
    def post(self, shared, prep_res, exec_res):
        shared["leads"] = exec_res
        print(f"  Enriched {len(exec_res)} leads")

class ScoreLeads(Node):
    def prep(self, shared):
        return shared["leads"]
    def exec(self, leads):
        leads_text = "\n".join(
            f"- {l['name']}, {l['title']} at {l['company']}: {l.get('enrichment', '')}"
            for l in leads
        )
        prompt = f"""Score each lead 1-10 for selling "{PRODUCT}".
Score based on: likely need for LLM tooling, seniority, technical role.

Leads:
{leads_text}

Output ONLY yaml:
```yaml
scores:
  - name: "Sarah Chen"
    score: 8
    reason: "one sentence why"
  - name: "Marcus Johnson"
    score: 7
    reason: "one sentence why"
  - name: "Priya Patel"
    score: 9
    reason: "one sentence why"
```"""
        resp = call_llm(prompt)
        yaml_str = resp.split("```yaml")[1].split("```")[0].strip()
        return yaml.safe_load(yaml_str)["scores"]
    def post(self, shared, prep_res, exec_res):
        score_map = {s["name"]: s for s in exec_res}
        for lead in shared["leads"]:
            match = score_map.get(lead["name"], {})
            lead["score"] = match.get("score", 0)
            lead["score_reason"] = match.get("reason", "")
        shared["leads"].sort(key=lambda x: x["score"], reverse=True)
        print("  Scores:")
        for l in shared["leads"]:
            print(f"    {l['name']}: {l['score']}/10 — {l['score_reason']}")

class PersonalizeEmails(Node):
    def prep(self, shared):
        return [l for l in shared["leads"] if l["score"] >= 6]
    def exec(self, hot_leads):
        emails = []
        for lead in hot_leads:
            prompt = f"""Write a 3-sentence cold email to {lead['name']}, {lead['title']} at {lead['company']}.

Product: {PRODUCT}
About them: {lead.get('enrichment', '')}

Rules:
- Reference something specific about their company
- Connect to a problem they likely have
- End with a specific ask (15 min call)
- No "I hope this finds you well" or filler
- Subject line first"""
            emails.append({"lead": lead, "email": call_llm(prompt)})
        return emails
    def post(self, shared, prep_res, exec_res):
        shared["emails"] = exec_res

scrape = ScrapeLeads()
enrich = EnrichLeads()
score = ScoreLeads()
personalize = PersonalizeEmails()
scrape >> enrich >> score >> personalize
flow = Flow(start=scrape)

shared = {}
flow.run(shared)

for e in shared.get("emails", []):
    lead = e["lead"]
    print(f"\n--- {lead['name']} (score: {lead['score']}) ---")
    print(e["email"])
