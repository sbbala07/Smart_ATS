# PDF TEXT EXTRACTOR

import pdfplumber   # python library used to read and extract texts,tables from pdf

def extract_text_from_pdf(pdf_path: str)->str:   # define a function to extract text from pdf through pdf path likely string, return string(->)
    text = ""     # intialize an empty string
    with pdfplumber.open(pdf_path) as pdf:    # Open pdf files from pdf_path using pdfplumber
        for page in pdf.pages:                # Loop through each pages
            page_text = page.extract_text()   # Extract text from current page 
            if page_text:                     # If found any string,prevents error if page empty or images
                text += page_text + '\n'      # Adding page's text to main text variable, adds new line
    return text.strip()                       # Remove extra spaces
