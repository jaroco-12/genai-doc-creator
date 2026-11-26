import hashlib
from pathlib import Path
from pydantic import BaseModel, Field
from google.genai import types

CACHE_DIR = Path(".ats_cache")
CACHE_DIR.mkdir(exist_ok=True)


class KeywordsOutput(BaseModel):
    role_level: str = Field(description="e.g. Intern, Junior, Mid, Senior")
    core_languages: list[str] = Field(description="Strict programming languages required, e.g. Python, Java, TypeScript, C++")
    domain_algorithms: list[str] = Field(
        description="CS concepts, ML/math techniques, or domain paradigms, e.g. REST APIs, Reinforcement Learning, Distributed Systems, Kalman Filters"
    )
    tools_and_infrastructure: list[str] = Field(
        description="Required platforms, databases, and frameworks, e.g. PostgreSQL, Docker, React, Linux, SQL"
    )
    bonus_or_nice_to_have: list[str] = Field(
        description="Tools explicitly marked as preferred or optional, e.g. Snowflake, Cursor, Kubernetes"
    )
    key_responsibilities: list[str] = Field(description="Top 3–5 concrete technical problems this person will solve")


EXTRACTION_SYSTEM_INSTRUCTION = """\
You are an expert technical recruiter and ATS parser.
Deconstruct the job posting into the structured technical taxonomy.

Extraction Rules:
1. role_level: Determine the seniority tier (e.g., Intern, Early Career/Junior, Mid, Senior).
2. core_languages: Extract ONLY required programming languages (e.g., Python, Java, TypeScript, C++). Route SQL, markup languages, and frameworks to tools_and_infrastructure.
3. domain_algorithms: Extract core CS concepts, ML/math techniques, and architectural patterns.
4. tools_and_infrastructure: Extract required frameworks, databases, runtime environments, and platforms (e.g., PostgreSQL, Docker, Git, Linux, SQL).
5. bonus_or_nice_to_have: Isolate technologies explicitly marked Preferred, Bonus, Plus, or Nice to have.
6. key_responsibilities: Synthesize the top 3–5 concrete technical actions the candidate will perform daily.
"""


def extract_keywords(client, job_text: str) -> KeywordsOutput:
    job_hash = hashlib.sha256(job_text.strip().encode("utf-8")).hexdigest()[:16]
    cache_file = CACHE_DIR / f"{job_hash}.json"

    if cache_file.exists():
        return KeywordsOutput.model_validate_json(cache_file.read_text(encoding="utf-8"))

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=f"Analyze the job description below and map its technical requirements into the taxonomy schema.\n\n<job_description>\n{job_text}\n</job_description>",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=KeywordsOutput,
            temperature=0.1,
            system_instruction=EXTRACTION_SYSTEM_INSTRUCTION,
            thinking_config=types.ThinkingConfig(thinking_level="LOW"),
        ),
    )

    data = KeywordsOutput.model_validate_json(response.text)
    cache_file.write_text(data.model_dump_json(indent=2), encoding="utf-8")
    return data