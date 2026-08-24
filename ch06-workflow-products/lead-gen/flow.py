from pocketflow import Flow
from nodes import ScrapeLeads, EnrichLeads, ScoreLeads, PersonalizeEmails

def create_lead_gen_flow():
    scrape = ScrapeLeads()
    enrich = EnrichLeads()
    score = ScoreLeads()
    personalize = PersonalizeEmails()

    scrape >> enrich >> score >> personalize
    return Flow(start=scrape)
