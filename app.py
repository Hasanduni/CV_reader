import streamlit as st
import re
import os
from PyPDF2 import PdfReader
import pandas as pd

# --- Function to extract text from uploaded PDF ---
def extract_text_from_pdf(uploaded_file):
    pdf_reader = PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"
    return text

# --- Function to parse CV text ---
def parse_cv(text, candidate_id=9999):
    # Universities + inline degrees
    uni_patterns = re.findall(
        r"([A-Za-z ]+(University|Institute)[^\n]+)", text
    )

    # Experience lines with roles + dates
    exp_patterns = re.findall(
        r"([A-Za-z ]*(Intern|Engineer|Scientist|Analyst)[^\n]*\d{4} ?[–-] ?(Present|\d{4}))", text
    )

    # Skills and tools (simple list, extendable)
    skills = re.findall(r"(Python|Java|SQL|Machine Learning|Deep Learning|Data Science|R|C\+\+)", text, re.IGNORECASE)
    tools = re.findall(r"(TensorFlow|PyTorch|Pandas|NumPy|Excel|Git|Docker|Spark)", text, re.IGNORECASE)

    # Years of experience
    exp_years = re.findall(r"(\d+)\+?\s+years", text)
    exp_years = float(exp_years[0]) if exp_years else 0.0

    # Combine results
    parsed_data = {
        "Candidate_ID": candidate_id,
        "Universities": [u[0] for u in uni_patterns],
        "Experiences": [e[0] for e in exp_patterns],
        "Skills": list(set(skills + tools)),
        "Experience_Years": exp_years
    }
    return parsed_data

# --- Streamlit UI ---
st.title("📄 CV Parser → Job Dataset Aligner")
st.write("Upload a CV (PDF) → extract structured info → download as CSV/Excel (for dataset building)")

uploaded_file = st.file_uploader("Upload CV (PDF only)", type=["pdf"])

if uploaded_file is not None:
    text = extract_text_from_pdf(uploaded_file)
    parsed_data = parse_cv(text)

    st.subheader("✅ Extracted CV Information")

    # Display as text instead of table
    if parsed_data["Universities"]:
        st.markdown("**🎓 Universities / Degrees**")
        for u in parsed_data["Universities"]:
            st.write("- " + u)

    if parsed_data["Experiences"]:
        st.markdown("**💼 Experience**")
        for e in parsed_data["Experiences"]:
            st.write("- " + e)

    if parsed_data["Skills"]:
        st.markdown("**🛠️ Skills & Tools**")
        st.write(", ".join(parsed_data["Skills"]))

    st.markdown(f"**📊 Total Experience (Years):** {parsed_data['Experience_Years']}")

    # Save structured row for dataset
    row = {
        "Candidate_ID": parsed_data["Candidate_ID"],
        "Universities": "; ".join(parsed_data["Universities"]),
        "Experiences": "; ".join(parsed_data["Experiences"]),
        "Skills": ", ".join(parsed_data["Skills"]),
        "Experience_Years": parsed_data["Experience_Years"]
    }
    df = pd.DataFrame([row])

    # --- Download options ---
    csv = df.to_csv(index=False).encode("utf-8")
    excel_file = "cv_aligned.xlsx"
    df.to_excel(excel_file, index=False)

    st.download_button(
        label="📥 Download CSV (aligned row)",
        data=csv,
        file_name="cv_aligned.csv",
        mime="text/csv",
    )

    with open(excel_file, "rb") as f:
        st.download_button(
            label="📥 Download Excel (aligned row)",
            data=f,
            file_name="cv_aligned.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    if os.path.exists(excel_file):
        os.remove(excel_file)
