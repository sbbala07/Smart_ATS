# Main file to connect everything

from src.pdf_loader import extract_text_from_pdf      # import custom modules reads texts from PDF's
from src.preprocessing import clean_text              # Clean and normalize extracted text
from src.skill_extractor import load_skills, extract_skills   # load and extract skills from text
from src.scoring import compute_skill_match                   # compute skill match
from src.scoring import compute_semantic_similarity
from src.llm_reasoning import generate_evaluation, generate_improvement_suggestions
import os                                             # interact with file system to list files, build paths

RESUME_DIR = "C:/Smart_ATS/data/resumes"                           # Folder path of resumes
JD_DIR = "C:/Smart_ATS/data/job_descriptions"                      # Folder path of JD's

def load_documents(directory):                        # Function to takes folder path and returns clean text form

    documents = {}                                    # Create empty dictionery to store key and value for easy lookup and scoring/ranking

    for file in os.listdir(directory):                # Loops through files in directory, all files inside the folder
        if file.endswith(".pdf"):                     # Check for PDF's
            path = os.path.join(directory,file)       # Build full file path, combines folder path and filename
            raw_text = extract_text_from_pdf(path)    # Extract raw text from PDF's
            documents[file]= clean_text(raw_text)     # Clean the extracted text and stores in the dict with key and values
    return documents                                  # returns dictionery of all resumes and JD's


if __name__ == "__main__":                            # Ensures this code runs only when this file is executed directly
    resumes = load_documents(RESUME_DIR)              # Read all resume PDF's, extracts and clean text
    jd = load_documents(JD_DIR)                       # Read all JD PDF's, extracts and clean text

    skills = load_skills()

    jd_skills = extract_skills(list(jd.values())[0],skills)   # Since only one JD is there, so we are keep outside loop

    results = []                                               # Create empty list to store all resumes scores

    for filename, resume_text in resumes.items():              # Loop through all resumes

        resume_skills = extract_skills(resume_text, skills)     # Extract resume skills from matching skills.csv

        match_result = compute_skill_match(resume_skills, jd_skills)  # Skill match calculation with resume and jd skills

        semantic_score = compute_semantic_similarity(resume_text, list(jd.values())[0]) # Computes cosine semantic similarity

        final_score = round(
            (match_result["match_percent"]*0.6) +
            (semantic_score*0.4),
            2
        )                                                           # Hybrid scoring 60% skill match, 40% semantic similarity

        
        confidence_score = round(
            100 - abs(match_result["match_percent"] - semantic_score),
            2
        )                                                           # Calculate confidence score based on result

        results.append({                                            # Store structured result per candidate
            "filename":filename,
            "match_percent": match_result["match_percent"],
            "semantic_score": semantic_score,
            "final_score": final_score,
            "confidence_score": confidence_score,
            "match_result": match_result
            
        })

    # Sort candidates by final score descending

    ranked_results = sorted(results, key=lambda x : x["final_score"], reverse=True)  # Sort list by final_Score descending

    print("\n====== RANKED CANDIDATES ======")

    for rank, candidate in enumerate(ranked_results,1):    # loops through sorted list and assign rank starting from 1
        print(f" Rank {rank} : {candidate["filename"]}")
        print(f" Skill Match % : {candidate["match_percent"]}")
        print(f" Semantic Score : {candidate["semantic_score"]}")
        print(f" Final Score : {candidate["final_score"]}")
        print(f" Confidence Score: {candidate['confidence_score']}")
        print("-" * 40)

    print("\n====== CANDIDATE SKILL COMPARISON ======")

    for candidate in ranked_results:
        filename = candidate["filename"]
        matched = sorted(candidate["match_result"]["matched_skills"])
        missing = sorted(candidate["match_result"]["missed_skills"])

        print(f"\nCandidate: {filename}")
        print("Matched Skills:", " | ".join(matched))
        print("Missing Skills:", " | ".join(missing))

top_candidate = ranked_results[0]

if top_candidate["final_score"] >= 70:
    fit_category = "Strong Fit"
elif top_candidate["final_score"] >= 40:
    fit_category = "Moderate Fit"
else:
    fit_category = "Weak Fit"   

print(f" Fit Category : {fit_category}")

resume_text = resumes[top_candidate["filename"]]
resume_skills = extract_skills(resume_text, skills)
jd_skills = extract_skills(list(jd.values())[0], skills)

match_result = compute_skill_match(resume_skills, jd_skills)

evaluation = generate_evaluation(
    top_candidate["filename"],
    match_result,
    top_candidate["semantic_score"],
    top_candidate["final_score"],
    fit_category
)

improvements = generate_improvement_suggestions(match_result)

print("\n======== AI EVALUATION ========\n")
print(evaluation)

print("\n======== RESUME IMPROVEMENT SUGGESTIONS ========\n")
print(improvements)