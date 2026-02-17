# Create skill extractor

import pandas as pd                                     # Pandas to resad structured data

def load_skills(skill_file = "data/skills.csv"):        # function to load skill from file path
    skills = pd.read_csv(skill_file, header= None)      # read file from path, header->none, CSV has no column
    return [s.lower() for s in skills[0].tolist()]      # select first column and convert to python list of skills

def extract_skills(text, skill_list):                   # Extract skills from resume
    text = text.lower()                                 # convert to lower case for case sensitive matching
    found_skills = set()                                # Create empty set to avoid duplicates, add skills one by one.

    for skill in skill_list:                            # Loop through every predefined skill in csv
        if skill.lower() in text:                       # if found on resume text
            found_skills.add(skill)                     # add it to the empty set

    return sorted(found_skills)                         # Convert to sorted list



