import ollama

# Skill display name lookup - handles abbreviations correctly
SKILL_DISPLAY_NAMES = {
    "aws": "AWS",
    "sql": "SQL",
    "nlp": "NLP",
    "git": "Git",
    "python": "Python",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
}

def format_skill(skill):
    return SKILL_DISPLAY_NAMES.get(skill.lower(), skill.title())


def generate_evaluation(candidate_name, match_result, semantic_score, final_score, fit_category):

    matched = match_result['matched_skills']
    missing = match_result['missed_skills']

    # Format skill names properly
    matched_display = ", ".join([format_skill(s) for s in matched]) if matched else "None"
    missing_display = ", ".join([format_skill(s) for s in missing]) if missing else "None"

    # Build Recommendation in Python - no LLM, no hallucination
    if fit_category == "Strong Fit":
        recommendation = (f"The candidate is a strong match for this role. "
                         f"All key technical skills are well represented. "
                         f"Recommended for immediate interview.")
    elif fit_category == "Moderate Fit":
        recommendation = (f"The candidate is suitable for interview if the role emphasizes "
                         f"{matched_display}. "
                         f"Additional experience in {missing_display} would strengthen the profile.")
    else:
        recommendation = (f"The candidate currently lacks several key requirements: {missing_display}. "
                         f"Consider for junior roles or reassess after skill development.")

    # LLM only for Overall Summary - simple and focused
    prompt = f"""
Write 2-3 sentences summarizing this candidate's alignment with the job.

Fit Category: {fit_category}
Skill Match: {match_result['match_percent']}%
Matched Skills: {matched_display}
Missing Skills: {missing_display}

RULES:
- Do NOT mention any skill not listed above.
- Do NOT invent experience or qualifications.
- Be factual and concise.
"""

    response = ollama.chat(
        model="qwen2.5:0.5b",
        messages=[
            {"role": "system", "content": "You are a strict hiring evaluator. Never invent information. Only use data provided."},
            {"role": "user", "content": prompt}
        ]
    )

    summary = response["message"]["content"].strip()

    # Build structured output entirely in Python
    strengths_block = "\n".join([f"  ✓ {format_skill(s)}" for s in matched]) if matched else "  None"
    gaps_block = "\n".join([f"  ✗ {format_skill(s)}" for s in missing]) if missing else "  None"

    output = f"""
Candidate: {candidate_name}

Overall Summary
{summary}

Strengths
{strengths_block}

Skill Gaps
{gaps_block}

Recommendation
{recommendation}
"""
    return output


def generate_improvement_suggestions(match_result):

    missing = match_result['missed_skills']

    if not missing:
        return "No missing skills identified. Candidate matches all required skills."

    missing_display = ", ".join([format_skill(s) for s in missing])

    # Build Skills to Learn in Python - no LLM needed
    skills_to_learn = "\n".join([
        f"  {i+1}. {format_skill(s)} — Search for beginner courses on Coursera, YouTube, or Kaggle."
        for i, s in enumerate(missing)
    ])

    # Build Resume Modifications in Python - no LLM needed
    resume_mods = f"""  1. Add a 'Skills' section explicitly listing any exposure to {missing_display}.
  2. Include personal or academic projects that demonstrate use of {missing_display}.
  3. Mention relevant certifications or online courses completed for {missing_display}."""

    # LLM only for Project Ideas - it handles this well
    prompt = f"""Suggest exactly 3 project ideas using only these skills: {missing_display}
Each project must use only the skills listed. No other technologies.
Keep each idea to 2-3 sentences maximum."""

    project_ideas = ollama.chat(
        model="qwen2.5:0.5b",
        messages=[
            {"role": "system", "content": f"Only use these skills: {missing_display}. Never mention anything else."},
            {"role": "user", "content": prompt}
        ]
    )["message"]["content"].strip()

    output = f"""
1. Skills to Learn
{skills_to_learn}

2. Resume Modifications
{resume_mods}

3. Project Ideas
{project_ideas}
"""
    return output