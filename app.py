import streamlit as st
import re
import pandas as pd
from PyPDF2 import PdfReader

# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    text = ""
    pdf_reader = PdfReader(uploaded_file)
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text

# Function to parse CV details
def parse_cv(text):
    details = {}

    # Extract Name (first line assumption)
    details["Name"] = text.split("\n")[0].strip()

    # Extract Email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+', text)
    details["Email"] = email_match.group(0) if email_match else "Not Found"

    # Extract Phone
    phone_match = re.search(r'\+?\d[\d -]{8,}\d', text)
    details["Phone"] = phone_match.group(0) if phone_match else "Not Found"

    # Extract Skills (basic keyword match)
    skills_keywords = ["Python", "Java", "SQL", "C++", "Machine Learning", "Data Analysis", "Excel", "TensorFlow"]
    skills_found = [skill for skill in skills_keywords if re.search(skill, text, re.IGNORECASE)]
    details["Skills"] = ", ".join(skills_found) if skills_found else "Not Found"

    # Extract Education (keywords search)
    education_match = re.findall(r"(B\.Sc|M\.Sc|Bachelor|Master|PhD|Degree|Diploma).*", text, re.IGNORECASE)
    details["Education"] = ", ".join(education_match) if education_match else "Not Found"

    return details


# Streamlit App
st.title("📄 CV Parser App")

uploaded_file = st.file_uploader("Upload a CV (PDF only)", type=["pdf"])

if uploaded_file is not None:
    st.success("✅ File uploaded successfully!")

    # Extract text
    text = extract_text_from_pdf(uploaded_file)

    # Parse CV
    parsed_details = parse_cv(text)

    # Show Results
    st.subheader("🔎 Extracted Information")
    for key, value in parsed_details.items():
        st.write(f"**{key}:** {value}")

    # Convert to DataFrame for table view
    df = pd.DataFrame(parsed_details.items(), columns=["Field", "Value"])
    st.subheader("📊 CV Data Table")
    st.table(df)
