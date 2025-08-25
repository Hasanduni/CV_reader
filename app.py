import streamlit as st
import re
from PyPDF2 import PdfReader
from dateutil import parser
from datetime import datetime

# --- Extract text from PDF ---
def extract_text_from_pdf(uploaded_file):
    pdf_reader = PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"
    return text

# --- Parse CV text ---
def parse_cv(text):
    # --- Universities + Degrees ---
    uni_patterns = re.findall(r"([A-Za-z ]+(University|Institute)[^\n]+)", text)

    # --- Experience lines with roles + dates ---
    exp_patterns = re.findall(
        r"([A-Za-z ]*(Intern|Engineer|Scientist|Analyst)[^\n]*\d{4} ?[–-] ?(Present|\d{4}))", text
    )

    # --- Skills & Tools ---
    skills = re.findall(r"(Python|Java|SQL|Machine Learning|Deep Learning|Data Science|R|C\+\+)", text, re.IGNORECASE)
    tools = re.findall(r"(TensorFlow|PyTorch|Pandas|NumPy|Excel|Git|Docker|Spark|scikit-learn)", text, re.IGNORECASE)

    # --- Calculate experience years from dates ---
    total_exp_years = 0
    for exp_line in exp_patterns:
        line = exp_line[0]
        dates = re.findall(r"(\w+ \d{4}|\d{4}|Present)", line)
        if len(dates) >= 1:
            start = dates[0]
            end = dates[1] if len(dates) > 1 else "Present"
            try:
                start_date = parser.parse(start)
            except:
                continue
            end_date = datetime.today() if end.lower() == "present" else parser.parse(end)
            total_exp_years += (end_date - start_date).days / 365.0

    total_exp_years = round(total_exp_years, 1)

    # --- Prepare parsed data ---
    parsed_data = {
        "Universities": [u[0] for u in uni_patterns],
        "Experiences": [e[0] for e in exp_patterns],
        "Skills": list(set(skills + tools)),
        "Total_Experience_Years": total_exp_years
    }

    return parsed_data

# --- Streamlit UI ---
st.title("📄 CV Parser → Readable Vertical Format")
st.write("Upload a CV (PDF) → extract structured info → display top-to-bottom, compute experience automatically")

uploaded_file = st.file_uploader("Upload CV (PDF only)", type=["pdf"])

if uploaded_file is not None:
    text = extract_text_from_pdf(uploaded_file)
    parsed_data = parse_cv(text)

    st.subheader("✅ Extracted CV Information (Vertical Layout)")

    # --- Display vertically ---
    if parsed_data["Universities"]:
        st.markdown("**🎓 Universities / Degrees**")
        for u in parsed_data["Universities"]:
            st.write(u)

    if parsed_data["Experiences"]:
        st.markdown("**💼 Experience**")
        for e in parsed_data["Experiences"]:
            st.write(e)

    if parsed_data["Skills"]:
        st.markdown("**🛠️ Skills & Tools**")
        st.write(", ".join(parsed_data["Skills"]))

    st.markdown(f"**📊 Total Experience (Years):** {parsed_data['Total_Experience_Years']}")
