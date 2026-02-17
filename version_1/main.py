# Main file to connect everything

from src.pdf_loader import extract_text_from_pdf      # import custom modules reads texts from PDF's
from src.preprocessing import clean_text              # Clean and normalize extracted text
from src.skill_extractor import load_skills, extract_skills   # load and extract skills from text
from src.scoring import compute_skill_match                   # compute skill match
from src.scoring import compute_semantic_similarity
import os                                             # interact with file system to list files, build paths

RESUME_DIR = "data/resumes"                           # Folder path of resumes
JD_DIR = "data/job_descriptions"                      # Folder path of JD's

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

    print("\n----SAMPLE RESUME TEXT---\n")
    print(list(resumes.values())[0][:1000])           # all resume texts, first resume and print first 1000 characters

    print("\n----SAMPLE JOB DESCRIPTION TEXT---\n")
    print(list(jd.values())[0][:1000])

    skills = load_skills()

    print("\n--- RESUME SKILLS ---")
    print(extract_skills(list(resumes.values())[0], skills))

    print("\n--- JD SKILLS ---")
    print(extract_skills(list(jd.values())[0], skills))

    resume_skills = extract_skills(list(resumes.values())[0], skills)
    jd_skills = extract_skills(list(jd.values())[0], skills)

    match_result = compute_skill_match(resume_skills, jd_skills)

    print("\n----- MATCH RESULT -----")
    print(match_result)

    semantic_score = compute_semantic_similarity(
        list(resumes.values())[0],
        list(jd.values())[0])
    
    print("\n------SEMANTIC SIMILARITY(%)-----")
    print(semantic_score)

    final_score = round(
        (match_result["match_percent"]*0.6) + 
        (semantic_score*0.4), 2)
    
    print("\n----- FINAL SCORE-----")
    print(final_score)