from pathlib import Path
from pydantic import BaseModel, Field

MASTER_PROFILE_MARKDOWN = Path("master_profile.md").read_text(encoding="utf-8")







def resume_creator(client, ats_keys, profile=MASTER_PROFILE_MARKDOWN):
    TAILORING_PROMPT = f"""
    You are an expert technical resume engineer.
    Tailor the candidate's verified master profile to target the extracted job taxonomy.

    TARGET TAXONOMY:
    - Seniority Tier: {ats_keys.role_level}
    - Required Language: {", ".join(ats_keys.core_languages)}
    - Target Algorithms: {", ".join(ats_keys.domain_algorithms)}
    - Core Infrastructure: {", ".join(ats_keys.tools_and_infrastructure)}
    - Bonus Technologies: {", ".join(ats_keys.bonus_or_nice_to_have)}

    TARGET RESPONSIBILITIES:
    {chr(10).join(f"- {r}" for r in ats_keys.key_responsibilities)}

    CANDIDATE MASTER PROFILE:
    <master_profile>
    {profile}
    </master_profile>

    EXECUTION CONSTRAINTS:
    1. Strict Grounding: Use ONLY verified tools, metrics, roles, and achievements present in the candidate profile. Do not invent unverified tools (e.g., if ROS or LiDAR is in the taxonomy but absent in the profile, omit it).
    2. ATS Action Phrasing: Format every bullet using the formula: [Strong Action Verb] + [Context/Problem] + [Technical Tool/Method] + [Quantifiable Impact/Result].
    3. Prioritize Alignment: Align the project bullets directly with experimental design, benchmarking, Python tooling, and visualization.
    
    CRITICAL FORMATTING & SYNTAX RULES:
    1. Do NOT bold the first word or action verb of bullet points. Start bullets with standard unbolded text.
       - CORRECT: `- Formulated continuous fuzzy logic rule sets in C#...`
       - FORBIDDEN: `- **Formulated** continuous fuzzy logic...`
    2. Never put project titles, job titles, or institutions into bullet points. Only concrete accomplishments/duties use bullet points (-), ONLY USE - FOR BULLET POINTS exclusively
    3. Do not include introductory text, greetings, code fences (```markdown), or sign-offs. Start directly with the `# Full Name` header.
    4. Keep the entire document within a strict 1-page visual budget (2 projects, 3 bullets each; 2 roles, 2 bullets each).
    
    REQUIRED SECTION ORDER & LAYOUT SKELETON:
    
    # [Full Name]
    [City, State] • [Email] • [Phone]
    
    ### PROFESSIONAL SUMMARY
    [2–3 concise sentences summarizing technical domain focus, core programming/engineering stack, and target alignment. Do not use bullets.]
    
    ### EDUCATION
    **[University Name]** | [City, State] | [Graduation Month Year]
    *[Degree Name]* — [Focus/Specialization if applicable] | GPA: x.x
    
    ### WORK EXPERIENCE
    **[Company Name]** — [City, State] | [Start Month Year – End Month Year or Present]
    *[Job Title]*
    - [Action Verb] [Core operational or technical duty with specific tools, metrics, or impact].
    - [Action Verb] [Core operational or technical duty with specific tools, metrics, or impact].
    
    ### Projects
    **[Project Title]** | *[Core Languages, Frameworks, and Tools]*
    - [Action Verb] [Technical architecture, algorithm implementation, or experimental setup].
    - [Action Verb] [Trajectory tracking, simulation, control loop, or state estimation detail].
    - [Action Verb] [Testing framework, empirical validation, or benchmark performance metric].
    
    ### TECHNICAL SKILLS
    - **Programming Languages:** [Comma-separated list]
    - **Autonomy, Simulation & Controls:** [Comma-separated list]
    - **Data Science, AI & Tooling:** [Comma-separated list]
    - **Developer Tools & Environments:** [Comma-separated list]
    """

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=TAILORING_PROMPT,
    )

    return response.text