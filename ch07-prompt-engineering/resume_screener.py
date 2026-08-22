"""Section 7.3 — Resume screener prompt iteration. Shows 5 techniques stacking."""
import sys
sys.path.append("..")
from call_llm import call_llm

RESUME = """John Smith
john.smith@email.com | San Francisco, CA

EXPERIENCE
Senior Software Engineer, Acme Corp (2021-Present)
- Led initiatives to improve team processes and engineering standards
- Built microservices handling 10K+ requests/second using Python and FastAPI
- Migrated legacy monolith to distributed architecture on AWS

Software Engineer, StartupXYZ (2018-2021)
- Developed REST APIs and internal tools
- Worked with various databases and cloud services
- Participated in code reviews and mentored junior developers

EDUCATION
BS Computer Science, UC Berkeley (2018)

SKILLS
Python, JavaScript, FastAPI, PostgreSQL, Redis, Docker, AWS, Kubernetes"""

JOB = "Senior Backend Engineer: 5+ years backend experience, Python expert, system design, team leadership, PostgreSQL"

# v1: No schema
prompt_v1 = f"""Evaluate this resume for the following role.

Role: {JOB}

Resume:
{RESUME}"""

# v2: With schema
prompt_v2 = f"""Evaluate this resume for the following role.

Role: {JOB}

Resume:
{RESUME}

Respond in this exact format:
technical_skills:
  rating: strong / partial / weak
  evidence: ...
experience_level:
  rating: strong / partial / weak
  evidence: ...
leadership:
  rating: strong / partial / weak
  evidence: ...
overall: strong / partial / weak"""

# v3: Schema + numbers + rubrics
prompt_v3 = f"""Evaluate this resume for the following role.

Role: {JOB}

Resume:
{RESUME}

Respond in this exact format:
technical_skills:
  rating: strong / partial / weak
  - strong: 4+ required technologies with project evidence
  - partial: 2-3 required technologies with evidence
  - weak: 0-1, or claims without project evidence
  evidence: list exactly the matching technologies with years of experience. Max 3 sentences.
experience_level:
  rating: strong / partial / weak
  - strong: 5+ years backend, built production systems
  - partial: 3-5 years, mostly individual contributor
  - weak: <3 years or unrelated domain
  evidence: total years, specific systems built. Max 2 sentences.
leadership:
  rating: strong / partial / weak
  - strong: managed team or led major technical initiative with measurable outcome
  - partial: mentored others or led small projects
  - weak: no evidence of leadership
  evidence: specific examples only. Max 2 sentences.
overall: strong / partial / weak
gaps: list missing requirements"""

# v4: + uncertainty handling
prompt_v4 = f"""Evaluate this resume for the following role.

Role: {JOB}

Resume:
{RESUME}

If a dimension cannot be clearly assessed from the resume, rate as "unclear" rather than guessing. Do NOT infer skills or experience that aren't explicitly stated. "Led initiatives" without specifics is NOT evidence of leadership.

Respond in this exact format:
technical_skills:
  rating: strong / partial / weak / unclear
  - strong: 4+ required technologies with project evidence
  - partial: 2-3 required technologies with evidence
  - weak: 0-1, or claims without project evidence
  evidence: list exactly the matching technologies with years of experience. Max 3 sentences.
experience_level:
  rating: strong / partial / weak / unclear
  - strong: 5+ years backend, built production systems
  - partial: 3-5 years, mostly individual contributor
  - weak: <3 years or unrelated domain
  evidence: total years, specific systems built. Max 2 sentences.
leadership:
  rating: strong / partial / weak / unclear
  - strong: managed team or led major technical initiative with measurable outcome
  - partial: mentored others or led small projects
  - weak: no evidence of leadership
  evidence: specific examples only. Max 2 sentences.
overall: strong / partial / weak
gaps: list missing requirements"""

for label, prompt in [("v1: No schema", prompt_v1),
                      ("v2: + schema", prompt_v2),
                      ("v3: + numbers and rubrics", prompt_v3),
                      ("v4: + uncertainty handling", prompt_v4)]:
    print(f"\n{'=' * 60}\n{label}\n{'=' * 60}")
    print(call_llm(prompt))
