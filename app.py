import re
import io
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

import streamlit as st

try:
    import pdfplumber
except Exception:
    pdfplumber = None

try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

try:
    import docx2txt
except Exception:
    docx2txt = None


# ------------------------------ Helpers ------------------------------

MONTHS = [
    "jan","feb","mar","apr","may","jun","jul","aug","sep","sept","oct","nov","dec",
    "january","february","march","april","june","july","august","september","october","november","december"
]

DEGREE_PATTERNS = [
    r"\bB\.?Sc\.?\b", r"\bM\.?Sc\.?\b", r"\bMBA\b", r"\bPh\.?D\.?\b", r"\bB\.?Eng\.?\b",
    r"\bM\.?Eng\.?\b", r"\bB\.?Tech\b", r"\bM\.?Tech\b", r"\bDiploma\b", r"\bHigher Diploma\b"
]

INSTITUTION_HINTS = [
    "university","institute","college","campus","faculty of","academy","polytechnic"
]

TOOLS_TECH = {
    "python","java","c++","c#","javascript","typescript","r","matlab","sql","mysql","postgresql",
    "mongodb","html","css","bash","powershell","pandas","numpy","scikit-learn","tensorflow","pytorch",
    "keras","opencv","matplotlib","plotly","spark","hadoop","tableau","power bi","excel","jupyter",
    "docker","kubernetes","aws","azure","gcp","git","github","jenkins","terraform","ansible","autocad"
}

SOFT_SKILLS = {
    "communication","leadership","teamwork","problem solving","analytical","time management","adaptability",
    "creativity","critical thinking","collaboration","presentation","public speaking","decision making"
}

def normalize_spaces(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text)


def read_pdf(file) -> str:
    if pdfplumber:
        try:
            with pdfplumber.open(file) as pdf:
                return "\n".join([page.extract_text() or "" for page in pdf.pages])
        except Exception:
            pass
    if PdfReader:
        try:
            reader = PdfReader(file)
            return "\n".join([p.extract_text() or "" for p in reader.pages])
        except Exception:
            pass
    return ""


def read_docx(path: str) -> str:
    if docx2txt:
        try:
            return docx2txt.process(path) or ""
        except Exception:
            pass
    try:
        from docx import Document
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""


def extract_degrees(text: str) -> List[str]:
    degrees = set()
    for pat in DEGREE_PATTERNS:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            degrees.add(m.group(0))
    return sorted(degrees)


def extract_institutions(text: str) -> List[str]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    found = set()
    for line in lines:
        if any(h in line.lower() for h in INSTITUTION_HINTS):
            found.add(normalize_spaces(line))
    return sorted(found)


def extract_skills_and_tools(text: str) -> (List[str], List[str]):
    skills, tools = set(), set()
    for token in re.split(r"[,\n;/]+", text):
        t = token.strip().lower()
        if not t:
            continue
        if t in TOOLS_TECH:
            tools.add(token.strip())
        elif t in SOFT_SKILLS:
            skills.add(token.strip())
    return sorted(skills), sorted(tools)


def extract_internships(text: str) -> List[str]:
    return [line for line in text.splitlines() if re.search(r"\bintern(ship)?\b", line, re.IGNORECASE)]


def _parse_date(tok: str) -> Optional[datetime]:
    tok = tok.strip().lower()
    if tok in {"present","current"}:
        return datetime.now()
    for fmt in ["%b %Y","%B %Y","%Y"]:
        try:
            return datetime.strptime(tok.title(), fmt)
        except Exception:
            pass
    return None


def extract_total_experience_years(text: str) -> float:
    total_months = 0
    pattern = re.compile(
        r"(?P<s>(?:\b(?:%s)\b\s+\d{4}|\b\d{4}\b))\s*[-–to]+\s*(?P<e>(?:\b(?:%s)\b\s+\d{4}|\b\d{4}\b|present|current))"
        % ("|".join(MONTHS), "|".join(MONTHS)), re.IGNORECASE
    )
    for m in pattern.finditer(text):
        s_dt, e_dt = _parse_date(m.group("s")), _parse_date(m.group("e"))
        if s_dt and e_dt:
            total_months += (e_dt.year - s_dt.year) * 12 + (e_dt.month - s_dt.month)
    return round(total_months/12, 2)


def extract_current_role(text: str) -> Optional[str]:
    pat = re.compile(r"([A-Za-z ]{2,40})\s+(?:at|@)\s+([A-Za-z ]{2,60}).*?(present|current)", re.IGNORECASE)
    m = pat.search(text)
    if m:
        return f"{m.group(1).strip()} at {m.group(2).strip()}"
    return None


def extract_structured(text: str) -> Dict[str, Any]:
    degrees = extract_degrees(text)
    institutions = extract_institutions(text)
    skills, tools = extract_skills_and_tools(text)
    internships = extract_internships(text)
    exp_years = extract_total_experience_years(text)
    role = extract_current_role(text)
    return {
        "University / Educational Institution": institutions or None,
        "Qualifications / Degrees": degrees or None,
        "Skills": skills or None,
        "Tools & Technologies": tools or None,
        "Internships": internships or None,
        "Previous Experience (years)": exp_years,
        "Current Role": role
    }


# ------------------------------ Streamlit UI ------------------------------

st.set_page_config(page_title="CV Parser", layout="wide")
st.title("📄 CV Parser — Extract Structured Data")

uploaded_files = st.file_uploader("Upload CVs", type=["pdf","docx"], accept_multiple_files=True)

if uploaded_files:
    results = []
    for f in uploaded_files:
        text = ""
        if f.name.lower().endswith(".pdf"):
            text = read_pdf(f)
        elif f.name.lower().endswith(".docx"):
            import tempfile, os
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                tmp.write(f.read())
                tmp.flush()
                text = read_docx(tmp.name)
                os.remove(tmp.name)
        structured = extract_structured(text)
        structured["File Name"] = f.name
        results.append(structured)

    st.subheader("Results")
    for r in results:
        with st.expander(r["File Name"], expanded=False):
            st.json(r)

    if st.button("Download JSON"):
        st.download_button(
            label="Save Results",
            file_name="cv_results.json"
