import os
import docx2txt
import PyPDF2
import textract
import string
from patterns import patterns
from skills import skills
import re
import json
import sys
from utils import generate_parsed_filename
from pymongo import MongoClient
    # Create a MongoDB client and connect to the database
client = MongoClient('mongodb+srv://skillscout:37UXk2ZC0Qx5nDQg@cluster0.gnzpa5b.mongodb.net/')
db = client['Applicant']  # Assuming 'applicant' is the database name
collection = db['resume']  # Assuming 'resume' is the collection name

#filepath = ('storage/inputresume/emily.docx')

filename = sys.argv[1] if len(sys.argv) > 1 else ''
filepath = os.path.join('storage/inputresume', filename)
""" 
    This extract_text function will extract text from a file using its file extension, 
    split the extracted text into paragraphs using newline characters as delimiters,
    Remove unnecessary punctuations from the extracted text.
"""
def extract_text(filepath):
    extension = os.path.splitext(filepath)[1][1:]
    if extension == 'txt':
        with open(filepath, 'r') as f:
            text = f.read()
    elif extension == 'docx':
        text = docx2txt.process(filepath)
    elif extension == 'pdf':
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f, strict=False)
            pages = [page.extract_text() for page in reader.pages]
            text = '\n'.join(pages)
    else:
        text = textract.process(filepath).decode('utf-8')
    
    # Splitting text into paragraphs using newline characters as delimiters
    paragraphs = text.split('\n\n') # Split by double newline to represent paragraphs
    
    # Removing unnecessary punctuations from the extracted text.
    translator = str.maketrans('', '', string.punctuation)
    paragraphs = [paragraph.translate(translator) for paragraph in paragraphs]
    
    return paragraphs

def extract_text_nm(filepath):
    """
    Extract text from a file using its file extension.
    """
    extension = os.path.splitext(filepath)[1][1:].lower()
    if extension == 'txt':
        with open(filepath, 'r') as f:
            text = f.read()
    elif extension == 'docx':
        text = docx2txt.process(filepath)
    elif extension == 'pdf':
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f, strict=False)
            pages = [reader.pages[i].extract_text() for i in range(len(reader.pages))]
            text = '\n'.join(pages)
    else:
        text = textract.process(filepath).decode('utf-8')
    return text.lower()

#------------------------------------------------------------
'''
    Defining a function whose funciton would be to consider the paragraph or sentence as the content under that heading when match is found!
'''

def extract_content(paragraphs, patterns_dict):
    '''
    Extract headings and content based on the provided patterns.
    '''
    extracted_data = {}
    current_heading = None
    
    for paragraph in paragraphs:
        for heading, keywords in patterns_dict["titles"].items():
            for keyword in keywords:
                if keyword.lower() in paragraph.lower():
                    current_heading = heading
                    break
        
        if current_heading:
            # Store the paragraph as content under the current heading
            if current_heading not in extracted_data:
                extracted_data[current_heading] = paragraph
            else:
                extracted_data[current_heading] += '\n' + paragraph
        
        current_heading = None  # Reset the current_heading
    
    return extracted_data


#-----------------------------------------

'''This function is extracting name from the resume using the regulare expression 
defined in the patterns dictionary in the patterns.py module.''' 
def extract_name(text):
    name = ""
    # Extract name using the pattern
    name_matches = re.findall(patterns['regular']['name'][0], text, re.IGNORECASE)
    if name_matches:
        name = ' '.join(name_matches[0])
    return name

#-------------------------------------

'''This function is extracting email from the resume using the email_pattern logic
defined in this function itself!'''
def extract_email(text):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, text)
    if matches:
        return matches[0]
    else:
        return ""

#----------------------------------------
'''
    Defining function to extract phone/mobile no.
'''
def extract_phone(text):
    phone = ""
    phone_matches = re.findall(patterns['regular']['phone'][0], text, re.IGNORECASE)
    if phone_matches:
        phone = ' '.join(filter(str.isdigit,phone_matches[0]))

    return phone

'''
def extract_skills(text, skills_dict):
    extracted_skills = {}  # Initialize as a dictionary
    for category, skill_list in skills_dict.items():
        extracted_skills[category] = []  # Initialize an empty list for each category
        for skill in skill_list:
            if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
                extracted_skills[category].append(skill)  # Append skill to the corresponding category
    
    return extracted_skills
'''

def extract_linkedin(text):
    linkedin = ""
    linkedin_matches = re.findall(patterns['regular']['linkedin'][0], text, re.IGNORECASE)
    if linkedin_matches:
        linkedin = ' '.join(filter(str.isdigit,linkedin_matches[0]))

    return linkedin

def extract_github(text):
    github = ""
    github_matches = re.findall(patterns['regular']['github'][0], text, re.IGNORECASE)
    if github_matches:
        github = ' '.join(filter(str.isdigit,github_matches[0]))
    return github

def parser(filepath):
    paragraphs = extract_text(filepath)
    resume_text = extract_text_nm(filepath)
    name = extract_name(resume_text)
    email = extract_email(resume_text)
    phone = extract_phone(resume_text)
    content = extract_content(paragraphs, patterns)
    linkedin = extract_linkedin(resume_text)
    github = extract_github(resume_text)

    output_data = {
    "name": name,
    "email": email,
    "phone": phone,
    "linkedin": linkedin,
    "github": github,
    "objective": content.get("objective", ""),
    "summary": content.get("summary", ""),
    "technology": content.get("technology", ""),
    "skills": content.get("skills", ""),
    "experience": content.get("experience", ""),
    "education": content.get("education", ""),
    "languages": content.get("language", ""),
    "courses": content.get("courses", ""),
    "projects": content.get("projects", ""),
    "links":  content.get("links", ""),
    "contacts": content.get("contacts", ""),
    "positions": content.get("positions", ""),
    "profiles": content.get("profiles", ""),
    "awards": content.get("awards", ""),
    "honors": content.get("honors", ""),
    "additional": content.get("additional", ""),
    "certification": content.get("certifications", ""),
    "interests": content.get("interests", "")
    }
    collection.insert_one(output_data)
    
    
    '''output_filepath, output_filename = os.path.split(filepath)  # Using the input file's directory and filename
    output_filename_without_extension, _ = os.path.splitext(output_filename)  # Removing the extension
    parsed_filename = generate_parsed_filename(output_filename)
    output_filepath = os.path.join('storage/output', parsed_filename)
        # Convert the output_data dictionary to a JSON string
    output_json = json.dumps(output_data, indent=4)
    with open(output_filepath, 'w') as json_file:
        json.dump(output_data, json_file, indent=4)'''
    return output_data #, parsed_filename, output_filepath, output_json   

output_data = parser(filepath)
#output_data, parsed_filename, output_filepath, output_json = parser(filepath)
    # Insert the JSON data into the MongoDB collection
#with open (output_filepath) as file:
#    file_data = json.load(file)
#collection.insert_one(output_data)

print(f"Resume data parsed and saved to MongoDB collection.")


