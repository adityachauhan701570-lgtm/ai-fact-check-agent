import streamlit as st
import requests
import re
import importlib
import time

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="AI Fact-Check Agent",
    page_icon="🔍",
    layout="wide"
)

# ---------------- STYLING ----------------
st.markdown("""
    <style>
    .main {
        background-color: #0E1117;
        color: white;
    }
    .card {
        padding: 15px;
        border-radius: 12px;
        background-color: #1c1f26;
        margin-bottom: 15px;
    }
    .claim {
        font-size: 16px;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------- TITLE ----------------
st.title("🔍 AI Fact-Check Agent")
st.caption("Upload PDF → Extract Claims → Verify using Local AI (Ollama)")

# ---------------- LOAD PDF LIB ----------------
pdfplumber = None
try:
    pdfplumber = importlib.import_module("pdfplumber")
except:
    pdfplumber = None

try:
    from PyPDF2 import PdfReader
except:
    PdfReader = None

# ---------------- OLLAMA ----------------
def ask_ollama(prompt):
    url = "http://localhost:11434/api/generate"
    
    data = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    }

    try:
        res = requests.post(url, json=data)

        if res.status_code == 200:
            return res.json().get("response", "No response")
        else:
            return f"⚠️ Error {res.status_code}"

    except Exception as e:
        return "⚠️ Ollama not running. Run: ollama run llama3"


# ---------------- PDF TEXT ----------------
def extract_pdf_text(file):
    text = []

    if pdfplumber:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                text.append(t if t else "")

    elif PdfReader:
        reader = PdfReader(file)
        for page in reader.pages:
            t = page.extract_text()
            text.append(t if t else "")

    return "\n".join(text)


# ---------------- CLAIM EXTRACTION ----------------
def split_sentences(text):
    return re.split(r'(?<=[.!?])\s+', text.replace('\n', ' '))


def extract_claims(text):
    sentences = split_sentences(text)
    return [s.strip() for s in sentences if len(s) > 40][:8]


# ---------------- VERIFY ----------------
def verify_claim(claim):
    prompt = f"""
    Verify the claim:

    {claim}

    Give:
    Verdict: True / False / Uncertain
    Reason: short explanation
    """
    return ask_ollama(prompt)


# ---------------- UI ----------------
uploaded_file = st.file_uploader("📄 Upload your PDF", type=["pdf"])

if uploaded_file:
    st.success("✅ PDF Uploaded Successfully")

    text = extract_pdf_text(uploaded_file)

    if st.button("🚀 Extract & Verify Claims"):

        with st.spinner("🔎 Analyzing document..."):

            text = text[:3000]  # limit for speed
            claims = extract_claims(text)

            progress = st.progress(0)

            for i, claim in enumerate(claims):

                progress.progress((i + 1) / len(claims))
                time.sleep(0.3)

                with st.container():
                    st.markdown('<div class="card">', unsafe_allow_html=True)

                    st.markdown(f"### 🧾 Claim {i+1}")
                    st.markdown(f'<p class="claim">{claim}</p>', unsafe_allow_html=True)

                    with st.expander("🔍 View Verification"):
                        result = verify_claim(claim)
                        st.info(result)

                    st.markdown('</div>', unsafe_allow_html=True)

            st.success("✅ Verification Completed!")