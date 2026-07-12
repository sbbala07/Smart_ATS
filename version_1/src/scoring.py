# Skill matching logic

from sentence_transformers import SentenceTransformer   # convert text into dense vector embeddings and capture semantic meaning
from sklearn.metrics.pairwise import cosine_similarity  # measure similarity between two vectors ranges from 0 to 1

def compute_skill_match(resume_skills, jd_skills):  # function to finding match, Getting input from resume and JD skills 

    resume_set = set(resume_skills)   # set of resume skills(to avoid duplicates)
    jd_set= set(jd_skills)            # set of JD skills

    matched = resume_set.intersection(jd_set)   # common skills b/w resume and jd skill set
    missing = jd_set - resume_set               # missing skill from jd set that are required by the job

    if len(jd_set)==0:                          # To avoid error dividing by zero
        match_percent = 0
    else:
        match_percent = (len(matched)/len(jd_set))*100   # Give percentage score

    return {
        "matched_skills": list(matched),
        "missed_skills": list(missing),
        "match_percent": round(match_percent,2)

    }

# Wrap model loading in a class to avoid model everytime running when imported
model = None
def get_model():
    global model
    if model is None:
        model = SentenceTransformer("all-MiniLM-L6-v2")   # Loading pretrained embedding model.  
    return model

def compute_semantic_similarity(resume_text, jd_text): # Resume content, JD content and gives simarlity content
    model = get_model()                                # Load the model if it hasn't been loaded yet 
    resume_embedding, jd_embedding = model.encode([resume_text, jd_text])  # Generate embeddings with a list of two texts
    similarity = cosine_similarity([resume_embedding], [jd_embedding])[0][0]  # Cosine similarity b/w resume embedding, JD embedding
    return round(float(similarity)*100, 2)                               # convert to percentage