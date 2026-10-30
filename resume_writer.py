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
    """





    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=TAILORING_PROMPT,
    )

    return response.text