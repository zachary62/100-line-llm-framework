import sys, os, yaml
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from pocketflow import Node
from call_llm import call_llm

PRODUCT = "PocketFlow, an LLM framework for developers"
SAMPLE_LEADS = [
    {"name": "Priya Patel",    "title": "Head of AI",            "company": "Acme Corp"},
    {"name": "Sarah Chen",     "title": "CTO",                   "company": "Stripe"},
    {"name": "Marcus Johnson", "title": "Engineering Manager",   "company": "Stark Inc."},
]
FAKE_COMPANY_DB = {
    "Acme Corp":  {"industry": "SaaS",     "size": "200-500",  "funding": "Series B"},
    "Stripe":     {"industry": "Fintech",  "size": "5000+",    "funding": "Public"},
    "Stark Inc.": {"industry": "Hardware", "size": "1000-5000","funding": "Public"},
}

class ScrapeLeads(Node):
    def prep(self, shared):
        return shared.get("leads", SAMPLE_LEADS)
    def exec(self, leads):
        return [{"name": l["name"], "title": l["title"],
                 "company": l["company"]} for l in leads]
    def post(self, shared, prep_res, exec_res):
        shared["leads"] = exec_res

class EnrichLeads(Node):
    def prep(self, shared):
        return shared["leads"]
    def exec(self, leads):
        out = []
        for l in leads:
            data = FAKE_COMPANY_DB.get(l["company"], {})
            summary = ", ".join(f"{k}: {v}" for k, v in data.items())
            out.append({**l, **data, "enrichment": summary})
        return out
    def post(self, shared, prep_res, exec_res):
        shared["leads"] = exec_res

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
  - name: "..."
    score: 8
    reason: "one sentence why"
```"""
        resp = call_llm(prompt)
        yaml_str = resp.split("```yaml")[1].split("```")[0]
        return yaml.safe_load(yaml_str)["scores"]
    def post(self, shared, prep_res, exec_res):
        score_map = {s["name"]: s for s in exec_res}
        for lead in shared["leads"]:
            match = score_map.get(lead["name"], {})
            lead["score"] = match.get("score", 0)
            lead["score_reason"] = match.get("reason", "")
        shared["leads"].sort(key=lambda x: x["score"], reverse=True)

class PersonalizeEmails(Node):
    def prep(self, shared):
        return [l for l in shared["leads"] if l["score"] >= 6]
    def exec(self, hot_leads):
        emails = []
        for lead in hot_leads:
            prompt = f"""Write a 3-sentence cold email to {lead['name']},
{lead['title']} at {lead['company']}.

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
