"""Section 6.4: Lead Gen — scrape, enrich, score, personalize."""
from flow import create_lead_gen_flow

shared = {}
create_lead_gen_flow().run(shared)

print("Scores:")
for l in shared["leads"]:
    print(f"  {l['name']}: {l['score']}/10 — {l['score_reason']}")

for e in shared.get("emails", []):
    lead = e["lead"]
    print(f"\n--- {lead['name']} (score: {lead['score']}) ---")
    print(e["email"])
