import streamlit as st
from utils.resume_parser import parse_resume
from utils.jd_parser import parse_jd
from utils.groq_client import call_llama
from utils.memory import compress_memory

from prompts.system_prompt import SYSTEM_PROMPT
from prompts.dsa import dsa_prompt
from prompts.system_design import system_design_prompt
from prompts.technical import technical_prompt
from prompts.projects import projects_prompt
from prompts.internships import internships_prompt
from prompts.hr import hr_prompt
from prompts.judge import judge_prompt

# Page config
st.set_page_config(page_title="AI Interviewer", layout="wide")

# Custom CSS for colors, background, and cards
st.markdown("""
<style>
body {
    background-image: url('https://images.unsplash.com/photo-1542831371-29b0f74f9713');
    background-size: cover;
    background-attachment: fixed;
    color: #ffffff;
}

h1 {
    color: royalblue;
    text-align: center;
}

.card {
    background-color: rgba(0,0,0,0.7);
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 10px;
}

.button-red {
    background-color: red;
    color: white;
    font-weight: bold;
}

.button-blue {
    background-color: royalblue;
    color: white;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st.title("AI INTERVIEWER")

# ======================
# SESSION STATE SETUP
# ======================
if "llm_messages" not in st.session_state:
    st.session_state.llm_messages = []

if "chat_ui" not in st.session_state:
    st.session_state.chat_ui = []

if "resume" not in st.session_state:
    st.session_state.resume = ""

if "jd" not in st.session_state:
    st.session_state.jd = ""

if "interview_started" not in st.session_state:
    st.session_state.interview_started = False

# ======================
# INPUTS
# ======================
with st.container():
    st.subheader("Candidate & Job Info")
    col1, col2 = st.columns([1,2])
    with col1:
        company = st.selectbox("Company", ["Google", "Amazon", "Microsoft", "Startup"])
        designation = st.radio(
            "Recruiter Designation",
            ["HR Recruiter", "Technical Recruiter", "Hiring Manager", "Engineering Manager"]
        )
        round_type = st.selectbox(
            "Interview Round",
            ["DSA", "System Design", "Technical", "Projects", "Internships", "HR"]
        )
    with col2:
        resume_file = st.file_uploader("Upload Resume")
        jd_text = st.text_area("Job Description", height=200)

# ======================
# START INTERVIEW
# ======================
if st.button("Start Interview", key="start_btn") and not st.session_state.interview_started:
    if resume_file and jd_text:
        st.session_state.resume = parse_resume(resume_file)
        st.session_state.jd = parse_jd(jd_text)
        st.session_state.chat_ui = []

        resume_short = st.session_state.resume[:2000]
        jd_short = st.session_state.jd[:2000]

        if round_type == "DSA":
            starter = dsa_prompt(resume_short, jd_short, designation, company)
        elif round_type == "System Design":
            starter = system_design_prompt(resume_short, jd_short, designation, company)
        elif round_type == "Technical":
            starter = technical_prompt(resume_short, jd_short, designation, company)
        elif round_type == "Projects":
            starter = projects_prompt(resume_short, jd_short, designation, company)
        elif round_type == "Internships":
            starter = internships_prompt(resume_short, jd_short, designation, company)
        else:
            starter = hr_prompt(resume_short, jd_short, designation, company)

        st.session_state.llm_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": starter}
        ]

        question = call_llama(st.session_state.llm_messages)
        st.session_state.llm_messages.append({"role": "assistant", "content": question})
        st.session_state.chat_ui.append({"role": "Interviewer", "content": question})
        st.session_state.interview_started = True

# ======================
# DISPLAY CHAT
# ======================
st.subheader("Interview Conversation")
for msg in st.session_state.chat_ui:
    if msg["role"] == "Interviewer":
        st.markdown(f"<div class='card'><b>Interviewer:</b> {msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='card' style='background-color: rgba(65,105,225,0.7);'><b>You:</b> {msg['content']}</div>", unsafe_allow_html=True)

# ======================
# ANSWER INPUT
# ======================
answer = st.text_area("Your Answer", height=150)

if st.button("Submit Answer", key="submit_btn"):
    if answer.strip():
        st.session_state.chat_ui.append({"role": "Candidate", "content": answer})
        st.session_state.llm_messages.append({"role": "user", "content": answer})
        st.session_state.llm_messages = compress_memory(st.session_state.llm_messages, max_turns=4)

        next_question = call_llama(st.session_state.llm_messages)
        st.session_state.llm_messages.append({"role": "assistant", "content": next_question})
        st.session_state.chat_ui.append({"role": "Interviewer", "content": next_question})

# ======================
# FINAL EVALUATION
# ======================
if st.button("End Interview & Evaluate", key="evaluate_btn"):
    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in st.session_state.chat_ui)
    judge_prompt_text = judge_prompt(
        st.session_state.resume[:1500],
        st.session_state.jd[:1500],
        transcript
    )

    evaluation = call_llama([
        {"role": "system", "content": "You are a senior technical interviewer."},
        {"role": "user", "content": judge_prompt_text}
    ])

    st.subheader("Final Interview Feedback")
    st.markdown(f"<div class='card' style='background-color: rgba(255,0,0,0.5);'>{evaluation}</div>", unsafe_allow_html=True)



