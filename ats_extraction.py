from pydantic import BaseModel, Field




class KeywordsOutput(BaseModel):
    role_level: str = Field(description="e.g. Intern, Junior, Mid, Senior")
    core_languages: list[str] = Field(description="Strict programming languages required, e.g. C++, Python")
    domain_algorithms: list[str] = Field(
        description="Math, controls, or domain concepts, e.g. Kalman Filters, MPC, Point Clouds")
    tools_and_infrastructure: list[str] = Field(description="Platforms and frameworks, e.g. ROS, Linux, BigQuery")
    bonus_or_nice_to_have: list[str] = Field(
        description="Tools mentioned as preferred or optional, e.g. Cursor, Streamlit")
    key_responsibilities: list[str] = Field(description="Top 5 active problems this person will be solving")


EXTRACTION_SYSTEM_INSTRUCTION = """
    You are an expert technical recruiter and ATS parser. 
    Your objective is to deconstruct a job posting into a structured technical taxonomy.

    Extraction Rules:
    1. role_level: Determine the seniority tier (e.g., Intern, Early Career/Junior, Mid, Senior, Lead).
    2. core_languages: Extract ONLY strict, non-negotiable programming languages explicitly listed as requirements (e.g., Python, C++, Java). Do not place markup languages, frameworks, or SQL here.
    3. domain_algorithms: Extract fundamental computer science concepts, mathematical techniques, control systems, and algorithmic domains (e.g., State Estimation, Kalman Filters, Point Clouds).
    4. tools_and_infrastructure: Extract foundational runtime environments, containerization systems, operating systems, and developer platforms explicitly marked as required (e.g., Linux, Docker, Git).
    5. bonus_or_nice_to_have: Isolate all technologies, libraries, and tools explicitly categorized under 'Preferred', 'Bonus', 'Plus', or 'Nice to have'. If a skill is optional, it MUST be placed here, not in the core lists.
    6. key_responsibilities: Synthesize the top 3 core technical problems the candidate will solve daily, focusing on concrete technical actions rather than generic corporate statements.
    """

def extract_keywords(client, job_text):
    response = client.models.generate_content(
        model = "gemini-3.8-flash",
        contents = f"Analyze the job description delimited below and map its technical requirements into the taxonomy schema.{job_text}",
        config={
            "response_mime_type": "application/json",
            "response_schema": KeywordsOutput,
            "temperature": 0.1,
            "system_instruction": EXTRACTION_SYSTEM_INSTRUCTION,
        }
    )
    data = KeywordsOutput.model_validate_json(response.text)
    return data
