import streamlit as st
import tempfile
import os
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

from src.pdf_loader import extract_text_from_pdf
from src.preprocessing import clean_text
from src.skill_extractor import load_skills, extract_skills
from src.scoring import compute_skill_match, compute_semantic_similarity
from src.llm_reasoning import generate_evaluation, generate_improvement_suggestions

# ─────────────────────────────────────────────
# SKILL DISPLAY NAME LOOKUP
# ─────────────────────────────────────────────
SKILL_DISPLAY_NAMES = {
    "aws": "AWS", "sql": "SQL", "nlp": "NLP",
    "git": "Git", "python": "Python", "pytorch": "PyTorch",
    "tensorflow": "TensorFlow", "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
}

def format_skill(skill):
    return SKILL_DISPLAY_NAMES.get(skill.lower(), skill.title())

def sentence_case(text):
    """Convert ALL CAPS lines to sentence case, preserving skill proper names."""
    result = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            result.append("")
            continue
        letters = [c for c in line if c.isalpha()]
        if letters and sum(1 for c in letters if c.isupper()) / len(letters) > 0.7:
            words = line.split()
            converted = []
            for i, word in enumerate(words):
                clean_word = word.strip(".,;:()")
                lower_word = clean_word.lower()
                if lower_word in SKILL_DISPLAY_NAMES:
                    converted.append(word.replace(clean_word, SKILL_DISPLAY_NAMES[lower_word]))
                elif i == 0:
                    converted.append(word.capitalize())
                else:
                    converted.append(word.lower())
            result.append(" ".join(converted))
        else:
            result.append(line)
    return "\n".join(result)

def fix_skill_names(text):
    """Fix lowercase skill names in improvement suggestions."""
    for skill_lower, skill_display in SKILL_DISPLAY_NAMES.items():
        for sep in [", ", ". ", "\n", " and ", " or "]:
            text = text.replace(
                skill_lower + sep.rstrip(),
                skill_display + sep.rstrip()
            )
    return text

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Smart ATS",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }

    .ats-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border-radius: 16px; padding: 2.5rem 3rem;
        margin-bottom: 2rem; border-left: 4px solid #6366f1;
    }
    .ats-header h1 { color: #f8fafc; font-size: 2.2rem; font-weight: 700; margin: 0; letter-spacing: -0.5px; }
    .ats-header p { color: #94a3b8; font-size: 1rem; margin: 0.4rem 0 0 0; }

    .upload-card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; }
    .upload-card h3 { color: #e2e8f0; font-size: 0.95rem; font-weight: 600; margin: 0 0 0.8rem 0; text-transform: uppercase; letter-spacing: 0.5px; }

    .rank-card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 1.2rem 1.5rem; margin-bottom: 0.8rem; }
    .rank-card.top { border-left: 3px solid #6366f1; }
    .rank-number { font-family: 'JetBrains Mono', monospace; font-size: 1.4rem; font-weight: 600; color: #6366f1; }
    .candidate-name { color: #f1f5f9; font-weight: 600; font-size: 1rem; }
    .score-label { color: #64748b; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; }
    .score-value { color: #e2e8f0; font-family: 'JetBrains Mono', monospace; font-size: 1rem; font-weight: 600; }

    .badge-strong { background: #064e3b; color: #6ee7b7; border: 1px solid #065f46; padding: 3px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; }
    .badge-moderate { background: #78350f; color: #fcd34d; border: 1px solid #92400e; padding: 3px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; }
    .badge-weak { background: #7f1d1d; color: #fca5a5; border: 1px solid #991b1b; padding: 3px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 600; }

    .section-title { color: #94a3b8; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid #1e293b; }

    .skill-matched { display: inline-block; background: #064e3b; color: #6ee7b7; border: 1px solid #065f46; padding: 4px 12px; border-radius: 20px; font-size: 0.82rem; margin: 3px; font-weight: 500; }
    .skill-missing { display: inline-block; background: #1e293b; color: #94a3b8; border: 1px dashed #475569; padding: 4px 12px; border-radius: 20px; font-size: 0.82rem; margin: 3px; font-weight: 500; }

    .eval-panel { background: #0f172a; border: 1px solid #1e293b; border-radius: 12px; padding: 1.8rem; margin-top: 1rem; }
    .eval-summary { color: #cbd5e1; font-size: 0.95rem; line-height: 1.7; margin-bottom: 1.5rem; padding-bottom: 1.5rem; border-bottom: 1px solid #1e293b; }
    .eval-recommendation { color: #a5b4fc; font-size: 0.9rem; line-height: 1.6; font-style: italic; background: #1e1b4b; border-left: 3px solid #6366f1; padding: 1rem 1.2rem; border-radius: 0 8px 8px 0; margin-top: 1rem; }

    .improvement-box { background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 1.2rem 1.5rem; margin-bottom: 1rem; }
    .improvement-box h4 { color: #a5b4fc; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin: 0 0 0.8rem 0; }
    .improvement-box p { color: #94a3b8; font-size: 0.9rem; line-height: 1.7; }

    .metric-box { background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 1rem; text-align: center; }
    .metric-box .metric-val { font-family: 'JetBrains Mono', monospace; font-size: 1.6rem; font-weight: 700; color: #6366f1; }
    .metric-box .metric-lbl { color: #64748b; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 0.2rem; }

    .custom-divider { border: none; border-top: 1px solid #1e293b; margin: 2rem 0; }
    .stProgress > div > div > div > div { background: linear-gradient(90deg, #6366f1, #8b5cf6); }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────
def fit_badge(category):
    if category == "Strong Fit":
        return '<span class="badge-strong">⬆ Strong Fit</span>'
    elif category == "Moderate Fit":
        return '<span class="badge-moderate">◆ Moderate Fit</span>'
    else:
        return '<span class="badge-weak">⬇ Weak Fit</span>'

def save_uploaded_file(uploaded_file):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(uploaded_file.read())
    tmp.close()
    return tmp.name

def process_pdf(uploaded_file, skills):
    path = save_uploaded_file(uploaded_file)
    raw = extract_text_from_pdf(path)
    text = clean_text(raw)
    os.unlink(path)
    extracted = extract_skills(text, skills)
    return text, extracted

def export_to_excel(ranked_results):
    rows = []
    for i, c in enumerate(ranked_results, 1):
        rows.append({
            "Rank": i,
            "Candidate": c["filename"],
            "Skill Match %": c["match_percent"],
            "Semantic Score": c["semantic_score"],
            "Final Score": c["final_score"],
            "Confidence Score": c["confidence_score"],
            "Fit Category": c["fit_category"],
            "Matched Skills": " | ".join(sorted(c["match_result"]["matched_skills"])),
            "Missing Skills": " | ".join(sorted(c["match_result"]["missed_skills"])),
        })
    df = pd.DataFrame(rows)
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="ATS Results")
    return buf.getvalue()

def parse_evaluation(evaluation):
    """Parse the evaluation text output into structured sections."""
    lines = evaluation.strip().split("\n")
    summary, strengths, gaps, recommendation = "", [], [], ""
    section = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line == "Overall Summary":
            section = "summary"
        elif line == "Strengths":
            section = "strengths"
        elif line == "Skill Gaps":
            section = "gaps"
        elif line == "Recommendation":
            section = "recommendation"
        elif line.startswith("Candidate:"):
            continue
        elif line.startswith("✓"):
            strengths.append(line)
        elif line.startswith("✗"):
            gaps.append(line)
        elif section == "summary" and not line.startswith("<"):
            summary += line + " "
        elif section == "recommendation" and not line.startswith("<"):
            recommendation += line + " "
    return summary.strip(), strengths, gaps, recommendation.strip()

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="ats-header">
    <h1>🎯 Smart ATS</h1>
    <p>AI-powered resume screening · Skill matching · Candidate ranking</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# UPLOAD SECTION
# ─────────────────────────────────────────────
col_jd, col_res = st.columns([1, 1])

with col_jd:
    st.markdown('<div class="upload-card"><h3>📄 Job Description</h3>', unsafe_allow_html=True)
    jd_file = st.file_uploader("Upload JD PDF", type=["pdf"], key="jd", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

with col_res:
    st.markdown('<div class="upload-card"><h3>📁 Resumes</h3>', unsafe_allow_html=True)
    resume_files = st.file_uploader("Upload Resume PDFs", type=["pdf"], accept_multiple_files=True, key="resumes", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# RUN ANALYSIS
# ─────────────────────────────────────────────
if jd_file and resume_files:
    if st.button("▶  Run Analysis", use_container_width=True, type="primary"):

        with st.spinner("Loading skills database..."):
            skills = load_skills()

        with st.spinner("Reading job description..."):
            jd_text, jd_skills = process_pdf(jd_file, skills)

        results = []
        progress = st.progress(0, text="Analysing resumes...")

        for i, resume_file in enumerate(resume_files):
            progress.progress(i / len(resume_files), text=f"Processing {resume_file.name}...")
            resume_text, resume_skills = process_pdf(resume_file, skills)
            match_result = compute_skill_match(resume_skills, jd_skills)
            semantic_score = compute_semantic_similarity(resume_text, jd_text)
            final_score = round((match_result["match_percent"] * 0.6) + (semantic_score * 0.4), 2)
            confidence_score = round((match_result["match_percent"] + semantic_score) / 2, 2)

            if final_score >= 70:
                fit_category = "Strong Fit"
            elif final_score >= 40:
                fit_category = "Moderate Fit"
            else:
                fit_category = "Weak Fit"

            results.append({
                "filename": resume_file.name,
                "match_percent": match_result["match_percent"],
                "semantic_score": semantic_score,
                "final_score": final_score,
                "confidence_score": confidence_score,
                "fit_category": fit_category,
                "match_result": match_result,
                "resume_text": resume_text,
            })

        progress.progress(1.0, text="Ranking candidates...")
        ranked_results = sorted(results, key=lambda x: x["final_score"], reverse=True)
        st.session_state["ranked_results"] = ranked_results
        st.session_state["jd_skills"] = jd_skills
        progress.empty()
        st.success(f"✅ Analysis complete — {len(ranked_results)} candidates ranked.")

# ─────────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────────
if "ranked_results" in st.session_state:
    ranked_results = st.session_state["ranked_results"]
    jd_skills = st.session_state["jd_skills"]

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["🏆  Rankings", "📊  Charts", "🤖  AI Evaluation"])

    # ════════════════════════════════
    # TAB 1 — RANKINGS
    # ════════════════════════════════
    with tab1:
        col_rank, col_detail = st.columns([1, 1.2])

        with col_rank:
            st.markdown('<p class="section-title">Candidate Rankings</p>', unsafe_allow_html=True)
            for rank, candidate in enumerate(ranked_results, 1):
                card_class = "rank-card top" if rank == 1 else "rank-card"
                badge = fit_badge(candidate["fit_category"])
                st.markdown(f"""
                <div class="{card_class}">
                    <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.8rem;">
                        <span class="rank-number">#{rank}</span>
                        <span class="candidate-name">{candidate['filename']}</span>
                        <span style="margin-left:auto">{badge}</span>
                    </div>
                    <div style="display:flex;gap:2rem;">
                        <div><div class="score-label">Skill Match</div><div class="score-value">{candidate['match_percent']}%</div></div>
                        <div><div class="score-label">Semantic</div><div class="score-value">{candidate['semantic_score']}%</div></div>
                        <div><div class="score-label">Final Score</div><div class="score-value">{candidate['final_score']}</div></div>
                        <div><div class="score-label">Confidence</div><div class="score-value">{candidate['confidence_score']}</div></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with col_detail:
            st.markdown('<p class="section-title">Skill Breakdown</p>', unsafe_allow_html=True)
            for candidate in ranked_results:
                with st.expander(f"🔍 {candidate['filename']}", expanded=(candidate == ranked_results[0])):
                    matched = sorted(candidate["match_result"]["matched_skills"])
                    missing = sorted(candidate["match_result"]["missed_skills"])

                    st.markdown("**Matched Skills**")
                    if matched:
                        pills = "".join([f'<span class="skill-matched">✓ {format_skill(s)}</span>' for s in matched])
                        st.markdown(pills, unsafe_allow_html=True)
                    else:
                        st.markdown('<span style="color:#64748b">None matched</span>', unsafe_allow_html=True)

                    st.markdown("<br>**Missing Skills**", unsafe_allow_html=True)
                    if missing:
                        pills = "".join([f'<span class="skill-missing">✗ {format_skill(s)}</span>' for s in missing])
                        st.markdown(pills, unsafe_allow_html=True)
                    else:
                        st.markdown('<span style="color:#6ee7b7">All skills matched!</span>', unsafe_allow_html=True)

                    st.markdown("<br>**Score Breakdown**", unsafe_allow_html=True)
                    st.markdown("Skill Match")
                    st.progress(candidate["match_percent"] / 100)
                    st.markdown("Semantic Similarity")
                    st.progress(candidate["semantic_score"] / 100)
                    st.markdown("Final Score")
                    st.progress(candidate["final_score"] / 100)

        st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
        excel_data = export_to_excel(ranked_results)
        st.download_button(
            label="⬇  Download Results as Excel",
            data=excel_data,
            file_name="smart_ats_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    # ════════════════════════════════
    # TAB 2 — CHARTS
    # ════════════════════════════════
    with tab2:
        names = [c["filename"].replace(".pdf", "") for c in ranked_results]
        skill_scores = [c["match_percent"] for c in ranked_results]
        semantic_scores = [c["semantic_score"] for c in ranked_results]
        final_scores = [c["final_score"] for c in ranked_results]

        col_c1, col_c2 = st.columns(2)

        with col_c1:
            st.markdown('<p class="section-title">Final Score Comparison</p>', unsafe_allow_html=True)
            fig = go.Figure(go.Bar(
                x=final_scores, y=names, orientation="h",
                marker=dict(color=final_scores, colorscale=[[0, "#334155"], [0.5, "#6366f1"], [1, "#8b5cf6"]], showscale=False),
                text=[f"{s}" for s in final_scores], textposition="outside", textfont=dict(color="#e2e8f0")
            ))
            fig.update_layout(
                paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                font=dict(color="#94a3b8", family="Inter"),
                xaxis=dict(showgrid=False, zeroline=False, range=[0, 110]),
                yaxis=dict(showgrid=False, autorange="reversed"),
                margin=dict(l=10, r=40, t=10, b=10), height=300
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_c2:
            st.markdown('<p class="section-title">Skill vs Semantic Score</p>', unsafe_allow_html=True)
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(name="Skill Match", x=names, y=skill_scores, marker_color="#6366f1"))
            fig2.add_trace(go.Bar(name="Semantic", x=names, y=semantic_scores, marker_color="#8b5cf6"))
            fig2.update_layout(
                barmode="group", paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
                font=dict(color="#94a3b8", family="Inter"),
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=False, range=[0, 110]),
                legend=dict(bgcolor="#1e293b", bordercolor="#334155"),
                margin=dict(l=10, r=10, t=10, b=10), height=300
            )
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown('<p class="section-title">Top Candidate — Radar Profile</p>', unsafe_allow_html=True)
        top = ranked_results[0]
        categories = ["Skill Match", "Semantic Score", "Final Score", "Confidence"]
        values = [top["match_percent"], top["semantic_score"], top["final_score"], top["confidence_score"]]
        fig3 = go.Figure(go.Scatterpolar(
            r=values + [values[0]], theta=categories + [categories[0]],
            fill="toself", fillcolor="rgba(99,102,241,0.2)",
            line=dict(color="#6366f1", width=2), marker=dict(color="#6366f1", size=6)
        ))
        fig3.update_layout(
            polar=dict(
                bgcolor="#1e293b",
                radialaxis=dict(visible=True, range=[0, 100], color="#475569", gridcolor="#334155"),
                angularaxis=dict(color="#94a3b8", gridcolor="#334155")
            ),
            paper_bgcolor="#0f172a", font=dict(color="#94a3b8", family="Inter"),
            showlegend=False, height=380, margin=dict(l=60, r=60, t=30, b=30)
        )
        st.plotly_chart(fig3, use_container_width=True)

    # ════════════════════════════════
    # TAB 3 — AI EVALUATION
    # ════════════════════════════════
    with tab3:
        top_candidate = ranked_results[0]

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f'<div class="metric-box"><div class="metric-val">{top_candidate["match_percent"]}%</div><div class="metric-lbl">Skill Match</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="metric-box"><div class="metric-val">{top_candidate["semantic_score"]}%</div><div class="metric-lbl">Semantic Score</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="metric-box"><div class="metric-val">{top_candidate["final_score"]}</div><div class="metric-lbl">Final Score</div></div>', unsafe_allow_html=True)
        with m4:
            st.markdown(f'<div class="metric-box"><div class="metric-val">{top_candidate["confidence_score"]}</div><div class="metric-lbl">Confidence</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_eval, col_improve = st.columns([1, 1])

        # ── AI EVALUATION PANEL ──
        with col_eval:
            st.markdown('<p class="section-title">AI Evaluation — Top Candidate</p>', unsafe_allow_html=True)
            with st.spinner("Generating AI evaluation..."):
                evaluation = generate_evaluation(
                    top_candidate["filename"],
                    top_candidate["match_result"],
                    top_candidate["semantic_score"],
                    top_candidate["final_score"],
                    top_candidate["fit_category"]
                )

            summary, strengths, gaps, recommendation = parse_evaluation(evaluation)

            strengths_html = "".join([
                f'<div style="color:#6ee7b7;font-size:0.9rem;margin-bottom:0.4rem">{s}</div>'
                for s in strengths
            ]) if strengths else '<span style="color:#64748b">None identified</span>'

            gaps_html = "".join([
                f'<div style="color:#fca5a5;font-size:0.9rem;margin-bottom:0.4rem">{g}</div>'
                for g in gaps
            ]) if gaps else '<span style="color:#6ee7b7">All skills matched!</span>'

            eval_html = (
                '<div class="eval-panel">'
                '<p class="section-title" style="margin-top:0">Overall Summary</p>'
                f'<div class="eval-summary">{summary}</div>'
                '<div style="display:flex;gap:2rem;margin-bottom:1.5rem;">'
                '<div style="flex:1">'
                '<p class="section-title">Strengths</p>'
                + strengths_html +
                '</div>'
                '<div style="flex:1">'
                '<p class="section-title">Skill Gaps</p>'
                + gaps_html +
                '</div>'
                '</div>'
                '<p class="section-title">Recommendation</p>'
                f'<div class="eval-recommendation">{recommendation}</div>'
                '</div>'
            )
            st.markdown(eval_html, unsafe_allow_html=True)

        # ── RESUME IMPROVEMENT SUGGESTIONS ──
        with col_improve:
            st.markdown('<p class="section-title">Resume Improvement Suggestions</p>', unsafe_allow_html=True)
            with st.spinner("Generating improvement suggestions..."):
                improvements = generate_improvement_suggestions(top_candidate["match_result"])

            # Clean up LLM output
            improvements = improvements.replace("**", "")
            improvements = fix_skill_names(improvements)

            # Split into sections by double newline
            sections = improvements.strip().split("\n\n")

            for sec in sections:
                sec = sec.strip()
                if not sec:
                    continue
                lines = sec.split("\n")
                title = lines[0].strip()
                body_lines = lines[1:] if len(lines) > 1 else []

                # Apply sentence case to each body line
                cleaned_body_lines = []
                for line in body_lines:
                    line = line.strip()
                    if not line:
                        continue
                    cleaned_body_lines.append(sentence_case(line))

                body = "\n".join(cleaned_body_lines)

                if title and body:
                    box_html = (
                        '<div class="improvement-box">'
                        f'<h4>{title}</h4>'
                        f'<p style="white-space:pre-line">{body}</p>'
                        '</div>'
                    )
                    st.markdown(box_html, unsafe_allow_html=True)
                elif title and not body:
                    # Some sections have content as part of title block
                    box_html = (
                        '<div class="improvement-box">'
                        f'<p style="white-space:pre-line;color:#94a3b8">{sentence_case(title)}</p>'
                        '</div>'
                    )
                    st.markdown(box_html, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="text-align:center;padding:4rem 2rem;color:#475569;">
        <div style="font-size:3rem;margin-bottom:1rem;">📂</div>
        <div style="font-size:1.1rem;font-weight:600;color:#64748b;">Upload a Job Description and Resumes to get started</div>
        <div style="font-size:0.9rem;margin-top:0.5rem;">Supports multiple resume PDFs · AI-powered ranking · Instant skill analysis</div>
    </div>
    """, unsafe_allow_html=True)