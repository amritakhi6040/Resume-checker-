# app.py
import streamlit as st
import os
import re
import json
from io import BytesIO

# PDF / DOCX parsing
from PyPDF2 import PdfReader
from docx import Document

# Gemini client
from google import genai

st.set_page_config(page_title="Resume Reviewer (Gemini)", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for enhanced styling
st.markdown("""
<style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    body {
        background: #1a1a2e;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .main {
        background: #1a1a2e;
    }
    
    .stApp {
        background: #1a1a2e;
    }
    
    /* Header Styling */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        margin-bottom: 10px;
        font-size: 2.5rem;
    }
    
    h2, h3 {
        color: #667eea;
        font-weight: 700;
        margin-top: 20px;
        margin-bottom: 15px;
    }
    
    /* Container Styling */
    .stContainer {
        background: #2d2d3d;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    
    /* Input Fields */
    .stFileUploader, .stTextArea, .stTextInput {
        background: #2d2d3d;
    }
    
    .stFileUploader > div {
        border: 2px dashed #667eea;
        border-radius: 8px;
        padding: 20px;
        transition: all 0.3s ease;
        background: #1a1a2e;
    }
    
    .stFileUploader > div:hover {
        border-color: #764ba2;
        background: #252535;
    }
    
    .stTextArea > div > textarea {
        border: 2px solid #444;
        border-radius: 8px;
        padding: 15px;
        font-size: 14px;
        transition: border 0.3s ease;
        background: #2d2d3d;
        color: #fff;
    }
    
    .stTextArea > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .stTextInput > div > input {
        border: 2px solid #444;
        border-radius: 8px;
        padding: 12px 15px;
        transition: border 0.3s ease;
        background: #2d2d3d;
        color: #fff;
    }
    
    .stTextInput > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 12px 30px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 16px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    .stDownloadButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 14px;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    /* Alert Messages */
    .stAlert {
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 4px solid;
    }
    
    .stSuccess {
        background: #d4edda;
        border-left-color: #28a745;
        color: #155724;
    }
    
    .stError {
        background: #f8d7da;
        border-left-color: #dc3545;
        color: #721c24;
    }
    
    .stWarning {
        background: #fff3cd;
        border-left-color: #ffc107;
        color: #856404;
    }
    
    .stInfo {
        background: #d1ecf1;
        border-left-color: #17a2b8;
        color: #0c5460;
    }
    
    /* Result Cards */
    .result-card {
        background: #2d2d3d;
        border-radius: 12px;
        padding: 25px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        border-left: 4px solid #667eea;
    }
    
    .strength-item {
        background: #1a3a1a;
        border-left: 4px solid #4caf50;
        padding: 12px 15px;
        border-radius: 4px;
        margin-bottom: 10px;
        font-size: 14px;
        color: #a8d5a8;
    }
    
    .weakness-item {
        background: #3a1a1a;
        border-left: 4px solid #f44336;
        padding: 12px 15px;
        border-radius: 4px;
        margin-bottom: 10px;
        font-size: 14px;
        color: #f8a5a5;
    }
    
    .bullet-item {
        background: #1a2a3a;
        border-left: 4px solid #2196f3;
        padding: 12px 15px;
        border-radius: 4px;
        margin-bottom: 10px;
        font-size: 14px;
        line-height: 1.6;
        color: #a8d5f8;
    }
    
    .interview-question {
        background: #2a1a3a;
        border: 1px solid #764ba2;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
    }
    
    .interview-question .question {
        font-weight: 600;
        color: #b388ff;
        margin-bottom: 8px;
    }
    
    .interview-question .type {
        display: inline-block;
        background: #764ba2;
        color: white;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 8px;
    }
    
    .interview-question .answer {
        color: #ccc;
        font-size: 14px;
        line-height: 1.5;
        font-style: italic;
    }
    
    /* Column Layout */
    .column-title {
        font-weight: 700;
        color: #667eea;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 2px solid #667eea;
    }
    
    /* Markdown Styling */
    .markdown-text {
        color: #ddd;
        line-height: 1.6;
    }
    
    /* Divider */
    hr {
        border: none;
        border-top: 1px solid #444;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Title and Description
st.markdown("<h1>📄 Resume Reviewer & Interview Coach</h1>", unsafe_allow_html=True)
st.markdown("""
<p style="font-size: 16px; color: #666; margin-bottom: 20px;">
Powered by Gemini AI • Get personalized resume feedback and interview preparation
</p>
""", unsafe_allow_html=True)

# Input Section
st.markdown("<div class='stContainer'>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("<h3>Step 1: Upload or Paste Your Resume</h3>", unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload resume (PDF / DOCX / TXT)", type=["pdf", "docx", "txt"])
    
with col2:
    st.markdown("<h3>Step 2: Target Role (Optional)</h3>", unsafe_allow_html=True)
    role = st.text_input("Enter your target role (e.g., Data Analyst, Product Manager)")

pasted = st.text_area("Or paste resume text directly", height=180, placeholder="Paste your resume content here...")
st.markdown("</div>", unsafe_allow_html=True)

analyze = st.button("🚀 Analyze Resume", use_container_width=True)

def extract_text_from_pdf_bytes(b: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(b))
        pages = []
        for p in reader.pages:
            txt = p.extract_text()
            if txt:
                pages.append(txt)
        return "\n\n".join(pages)
    except Exception as e:
        return ""

def extract_text_from_docx_bytes(b: bytes) -> str:
    try:
        doc = Document(BytesIO(b))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        return ""

def build_prompt(resume_text: str, role: str) -> str:
    return f"""
You are an expert career coach and professional resume writer.

Given the resume text below and an optional target role, produce ONLY a valid JSON object (nothing else) with these keys:
- "profile_summary": string (1-2 lines summarizing the candidate)
- "strengths": list of short strings (3-6 items)
- "weaknesses": list of short strings (3-6 items / gaps to address)
- "improved_bullets": list of up to 8 rewritten resume bullet points (each short, action + result when possible)
- "interview_questions": list of objects with keys: "question", "ideal_answer" (short), "type" (one of 'behavioral','technical','system')

Tailor wording to the target role: {role if role else "No specific role provided"}.

Return strictly one JSON object and nothing else.

Resume text:
\"\"\"{resume_text}\"\"\"
""".strip()

if analyze:
    # Gather resume text
    resume_text = ""
    if uploaded:
        raw = uploaded.getvalue()
        name = uploaded.name.lower()
        if name.endswith(".pdf"):
            resume_text = extract_text_from_pdf_bytes(raw)
        elif name.endswith(".docx"):
            resume_text = extract_text_from_docx_bytes(raw)
        elif name.endswith(".txt"):
            try:
                resume_text = raw.decode("utf-8")
            except:
                resume_text = raw.decode("latin-1", errors="ignore")
    
    if pasted and pasted.strip():
        resume_text = (resume_text + "\n\n" + pasted.strip()) if resume_text else pasted.strip()

    if not resume_text.strip():
        st.error("❌ Please upload a resume file or paste resume text.")
    else:
        st.info("⏳ Analyzing your resume with Gemini AI... This may take a few seconds.")
        try:
            client = genai.Client()
            prompt = build_prompt(resume_text, role)
            response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            text = response.text if hasattr(response, "text") else str(response)

            json_match = re.search(r"\{[\s\S]*\}", text)
            if not json_match:
                st.warning("⚠️ Could not parse response. Showing raw output:")
                st.code(text)
            else:
                payload = None
                try:
                    payload = json.loads(json_match.group(0))
                except Exception as e:
                    st.warning("⚠️ Failed to parse JSON response:")
                    st.code(text)

                if payload:
                    st.success("✅ Analysis Complete!")
                    
                    # Left Column - Main Feedback
                    col1, col2 = st.columns([2, 1.5])

                    with col1:
                        st.markdown("<div class='result-card'>", unsafe_allow_html=True)
                        st.markdown("<h2>👤 Profile Summary</h2>", unsafe_allow_html=True)
                        st.markdown(f"<p style='font-size: 16px; color: #333; line-height: 1.6;'>{payload.get('profile_summary', '—')}</p>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                        st.markdown("<div class='result-card'>", unsafe_allow_html=True)
                        st.markdown("<h2>✅ Strengths</h2>", unsafe_allow_html=True)
                        for s in payload.get("strengths", []):
                            st.markdown(f"<div class='strength-item'>• {s}</div>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                        st.markdown("<div class='result-card'>", unsafe_allow_html=True)
                        st.markdown("<h2>⚠️ Areas for Improvement</h2>", unsafe_allow_html=True)
                        for w in payload.get("weaknesses", []):
                            st.markdown(f"<div class='weakness-item'>• {w}</div>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                        st.markdown("<div class='result-card'>", unsafe_allow_html=True)
                        st.markdown("<h2>✨ Improved Resume Bullets</h2>", unsafe_allow_html=True)
                        for b in payload.get("improved_bullets", []):
                            st.markdown(f"<div class='bullet-item'>• {b}</div>", unsafe_allow_html=True)
                        
                        download_text = "\n".join(payload.get("improved_bullets", []))
                        if download_text:
                            st.download_button(
                                "📥 Download Improved Bullets",
                                download_text,
                                file_name="improved_bullets.txt",
                                use_container_width=True
                            )
                        st.markdown("</div>", unsafe_allow_html=True)

                    # Right Column - Interview Questions
                    with col2:
                        st.markdown("<div class='result-card'>", unsafe_allow_html=True)
                        st.markdown("<h2>🎤 Interview Prep</h2>", unsafe_allow_html=True)
                        for q in payload.get("interview_questions", []):
                            st.markdown(f"""
                            <div class='interview-question'>
                                <div class='question'>Q: {q.get('question', '')}</div>
                                <span class='type'>{q.get('type', '').upper()}</span>
                                <div class='answer'>💡 {q.get('ideal_answer', '')}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.markdown("**Troubleshooting:** Ensure GEMINI_API_KEY is set in your environment variables.")
