Smart ATS

A resume screening tool I built to understand how ATS (Applicant Tracking Systems) work under the hood. It takes a job description and multiple resumes as PDF inputs, scores and ranks candidates, and generates an AI-powered evaluation — all running locally on your machine.


Why I Built This

I wanted a hands-on project that combines NLP, semantic similarity, and LLMs in a real-world use case. Resume screening felt like a natural fit — it's something every company does, and building it from scratch helped me understand the full pipeline from raw PDF to ranked output.


What It Does


Extracts text from PDF resumes and job descriptions
Matches skills against a predefined skill list
Computes semantic similarity between resume and JD using sentence-transformers
Scores candidates using a hybrid formula (60% skill match + 40% semantic similarity)
Ranks all candidates with a fit category (Strong / Moderate / Weak Fit)
Generates an AI evaluation and resume improvement suggestions using a local LLM (Ollama)
Displays everything in a Streamlit web UI with charts and an Excel export



Tech Stack

ComponentToolPDF ExtractionpdfplumberText CleaningPython regexSkill MatchingCSV keyword matchingSemantic Similaritysentence-transformers (all-MiniLM-L6-v2)Local LLMOllama (qwen2.5:0.5b)Web UIStreamlitChartsPlotlyExportpandas + openpyxl


Project Structure

Smart_ATS/
│
├── version_1/
│   ├── main.py                  # Core pipeline (CLI version)
│   ├── streamlit_app.py         # Web UI
│   │
│   ├── src/
│   │   ├── pdf_loader.py        # PDF text extraction
│   │   ├── preprocessing.py     # Text cleaning
│   │   ├── skill_extractor.py   # Skill matching
│   │   ├── scoring.py           # Skill match + semantic scoring
│   │   └── llm_reasoning.py     # LLM evaluation + suggestions
│   │
│   └── data/
│       ├── resumes/             # Place resume PDFs here
│       ├── job_descriptions/    # Place JD PDFs here
│       └── skills.csv           # Skill keyword list
│
└── requirements.txt


How to Run

1. Clone the repo

bashgit clone https://github.com/sbbala-7/Smart_ATS.git
cd Smart_ATS

2. Create a virtual environment and install dependencies

bashpython -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

pip install -r requirements.txt

3. Install and start Ollama

Download Ollama from https://ollama.com and then pull the model:

bashollama pull qwen2.5:0.5b
ollama serve

4. Run the Streamlit app

bashcd version_1
streamlit run streamlit_app.py

Then open your browser at http://localhost:8501, upload a JD and resumes, and click Run Analysis.


Scoring Logic

The final score is a weighted combination of two signals:

Final Score = (Skill Match % × 0.6) + (Semantic Score × 0.4)
Confidence  = (Skill Match % + Semantic Score) / 2


Skill Match — exact keyword matching between resume and JD against a skills.csv list
Semantic Score — cosine similarity between sentence-transformer embeddings of the full resume and JD text



Screenshots



What I Learned


How to build a multi-stage NLP pipeline from scratch
How semantic similarity works using transformer embeddings
How to integrate a local LLM for structured evaluation
How to build and structure a Streamlit app for a real use case
The gap between keyword matching and actual semantic understanding



Limitations


Skill extraction depends on the skills.csv list — it won't catch skills not in the list
The LLM used (qwen2.5:0.5b) is a very small model, so the generated text quality varies
Only supports PDF format currently



Future Improvements


Add support for DOCX resumes
Expand the skills.csv with a larger, domain-specific list
Try a larger LLM for better evaluation quality
Add multi-JD support for batch hiring workflows



Author

Built by Balachandran as a portfolio project while learning AI/ML engineering.