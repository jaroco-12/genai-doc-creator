from pathlib import Path
from google import genai
from google.genai import types
import textwrap

MASTER_PROFILE_MARKDOWN = Path("master_profile.md").read_text(encoding="utf-8")







def resume_creator(client, ats_keys, profile=MASTER_PROFILE_MARKDOWN):
    responsibilities_block = "\n".join(f"- {r}" for r in ats_keys.key_responsibilities)

    TAILORING_PROMPT = textwrap.dedent(f"""\
            You are a technical resume writer specializing in defensible, interview-ready resumes for {ats_keys.role_level} software engineering and machine learning candidates.
            Tailor the candidate's verified master profile to align with the extracted job taxonomy without inflating scope or inventing claims.

            TARGET TAXONOMY:
            - Seniority Tier: {ats_keys.role_level}
            - Required Languages: {", ".join(ats_keys.core_languages)}
            - Target Algorithms / Concepts: {", ".join(ats_keys.domain_algorithms)}
            - Core Infrastructure & Frameworks: {", ".join(ats_keys.tools_and_infrastructure)}
            - Bonus Technologies: {", ".join(ats_keys.bonus_or_nice_to_have)}

            TARGET RESPONSIBILITIES:
            {responsibilities_block}

            CANDIDATE MASTER PROFILE:
            <master_profile>
            {profile}
            </master_profile>

            EXECUTION & DEFENSIBILITY CONSTRAINTS:
            1. Strict Grounding & Anti-Inflation: Use ONLY verified tools, metrics, roles, and facts from `<master_profile>`. Never upgrade academic, retail, or student software usage into enterprise infrastructure claims.
               - FORBIDDEN INFLATIONS: Do NOT claim "zero data loss", "eliminating schema drift", "immutable audit trails", "strict HIPAA compliance", "high-throughput streaming", or "core transactional database administration" unless explicitly stated verbatim in `<master_profile>`.
               - Describe retail/banking roles accurately as operational and compliance workflows without disguising teller/CRM UI usage as SQL or backend database engineering.
            2. Honest Impact Phrasing: Format bullets using `[Strong Action Verb] + [Specific Technical Implementation/Workflow] + [Verified Tooling] + [Concrete Outcome or Purpose]`. Only include numbers/percentages that exist verbatim in `<master_profile>`; otherwise, end with the functional engineering outcome.
            3. ATS Keyword Mirroring: Where a skill or concept is verified in `<master_profile>`, mirror the exact naming from `TARGET TAXONOMY` across the Summary, Projects, and Technical Skills.
            4. Summary-to-Project Consistency: Every technical domain or tool highlighted in the Professional Summary MUST be backed by at least one of the 2 selected projects or roles below it.
            5. Dynamic Selection: Select the 2 projects and 4 technical skill category headers that best fit `{ats_keys.role_level}` and `TARGET TAXONOMY`.

            CRITICAL FORMATTING & 1-PAGE BUDGET RULES:
            1. Do NOT bold the first word or action verb of bullet points. Start bullets with standard unbolded text.
               - CORRECT: `- Engineered vectorized feature extraction pipelines in Python...`
               - FORBIDDEN: `- **Engineered** vectorized feature extraction pipelines...`
            2. Never put project titles, job titles, or institutions into bullet points. Use `- ` exclusively for accomplishments/duties and skill categories.
            3. Do not include introductory text, greetings, code fences (```markdown), or sign-offs. Start directly with `# Full Name` at column 0.
            4. Strict 1-Page Budget: 2 roles (2 bullets each), 2 projects (3 bullets each). Keep every bullet to 15–22 words (max 2 lines) and every skill category to 6–10 items.

            REQUIRED SECTION ORDER & LAYOUT SKELETON:

            # [Full Name]
            [City, State] • [Email] • [Phone]

            ### PROFESSIONAL SUMMARY
            [2–3 concise sentences summarizing academic standing, core languages, and verified experience directly reflected in the selected projects. No bullets.]

            ### EDUCATION
            **[University Name]** | [City, State] | [Graduation Month Year]
            *[Degree Name]* — [Focus/Specialization if applicable] | GPA: x.x

            ### WORK EXPERIENCE
            **[Company Name]** — [City, State] | [Start Month Year – End Month Year or Present]
            *[Job Title]*
            - [Action Verb] [Operational or technical duty with verified tools and metrics].
            - [Action Verb] [Operational or technical duty with verified tools and metrics].

            ### Projects
            **[Project Title]** | *[Core Languages, Frameworks, and Tools]*
            - [Action Verb] [System architecture, API design, or model/algorithm implementation].
            - [Action Verb] [Core technical mechanism, data pipeline, or state/control logic].
            - [Action Verb] [Testing, cross-validation, or functional verification outcome].

            ### TECHNICAL SKILLS
            - **[Relevant Category 1, e.g., Programming Languages]:** [6–10 comma-separated items]
            - **[Relevant Category 2, e.g., Web & API Engineering or Autonomy & Simulation]:** [6–10 comma-separated items]
            - **[Relevant Category 3, e.g., Data Science, AI & Databases]:** [6–10 comma-separated items]
            - **[Relevant Category 4, e.g., Developer Tools & Environments]:** [6–10 comma-separated items]
        """)

    response = client.models.generate_content(
        model="gemini-4-hydrogen",
        contents=TAILORING_PROMPT,
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are a technical resume writer specializing in defensible, "
                "interview-ready resumes. Strictly follow all grounding, anti-inflation, "
                "1-page word budget, and Markdown skeleton rules. Output raw Markdown only."
            ),
            thinking_config=types.ThinkingConfig(
                thinking_level="LOW",  # Cuts latency & billed output tokens; use "MEDIUM" if layout drifts
            ),
            max_output_tokens=4096,  # Leaves plenty of headroom for both thinking tokens and the ~600-token resume
        ),
    )
    return response.text