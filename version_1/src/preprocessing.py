# BASIC TEXT CLEANING

import re    # python regex module used for pattern matching, search,replace and text normalization

def clean_text(text: str)->str:        # Define a function to clean text, getting string input and return cleaned string
    text = re.sub(r'\(cid:\d+\)','',text) # Fix common PDF encoding artifacts
    text = re.sub(r'\s+',' ',text)     # matches tabs, spaces,newlines,multiple lines to single space
    text = re.sub(r'•|●|▪|', '-', text) # matches different bullet points to single '-'
    text = text.replace('\x0c','')     # remove form feed character often appears when extracting text from PDF's to single space
    return text.strip()                # Remove leading and trailing spaces