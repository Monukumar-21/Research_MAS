"""Streamlit frontend for the Multi-Agent Research Platform."""

import time
import requests
import streamlit as st

# --- Configuration ---
API_BASE = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="Multi-Agent Research Platform",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS ---
st.markdown("""
<style>
    .agent-card {
        padding: 10px 15px;
        border-radius: 8px;
        margin: 5px 0;
        border-left: 4px solid;
        color: #333 !important; /* Force dark text regardless of dark mode */
    }
    .agent-supervisor { border-left-color: #FF6B6B; background: #FFF5F5; }
    .agent-planner { border-left-color: #4ECDC4; background: #F0FFFE; }
    .agent-retrieval { border-left-color: #45B7D1; background: #F0F9FC; }
    .agent-memory_agent { border-left-color: #96CEB4; background: #F5FBF8; }
    .agent-writer { border-left-color: #FFEAA7; background: #FFFEF5; }
    .agent-critic { border-left-color: #DDA0DD; background: #FDF5FD; }
    .agent-citation { border-left-color: #98D8C8; background: #F5FCFA; }
    .agent-system { border-left-color: #95A5A6; background: #F8F9F9; }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea, #764ba2);
    }
</style>
""", unsafe_allow_html=True)

# --- Session State ---
if "research_result" not in st.session_state:
    st.session_state.research_result = None
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "history" not in st.session_state:
    st.session_state.history = []

# --- Sidebar ---
with st.sidebar:
    st.title("🔬 Research Platform")
    st.markdown("---")

    st.subheader("⚙️ Settings")
    api_url = st.text_input("API URL", value=API_BASE)
    provider_map = {
        "Gemini": "gemini",
        "OpenAI (ChatGPT)": "openai",
        "Anthropic (Claude)": "anthropic",
        "xAI (Grok)": "grok",
        "Groq (Mixtral)": "groq"
    }
    selected_provider_ui = st.selectbox("LLM Provider", list(provider_map.keys()))
    llm_provider = provider_map[selected_provider_ui]
    api_key = st.text_input(f"{selected_provider_ui.split(' ')[0]} API Key (Required)", type="password", placeholder="sk-...")
    max_revisions = st.slider("Max Revisions", 0, 5, 2)

    st.markdown("---")
    st.subheader("📜 Research History")

    try:
        resp = requests.get(f"{api_url}/research/history", timeout=5)
        if resp.status_code == 200:
            history = resp.json()
            for item in history[:10]:
                if st.button(f"📄 {item['topic'][:40]}...", key=item["run_id"]):
                    try:
                        detail = requests.get(f"{api_url}/research/{item['run_id']}", timeout=10)
                        if detail.status_code == 200:
                            st.session_state.research_result = detail.json()
                    except Exception:
                        st.error("Failed to load research run")
    except Exception:
        st.info("Connect to API to see history")

    st.markdown("---")
    st.markdown("**Built with:**")
    st.markdown("🦜 LangGraph + LangChain")
    st.markdown("🤖 Google Gemini")
    st.markdown("🗄️ MongoDB + Pinecone + SQLite")
    st.markdown("🔌 Model Context Protocol")

# --- Main Content ---
st.title("🔬 Multi-Agent Academic Research Platform")
st.markdown("Enter a research topic and let our AI agents collaborate to produce a comprehensive report.")

# --- Input Section ---
col1, col2 = st.columns([4, 1])
with col1:
    topic = st.text_input(
        "Research Topic",
        placeholder="e.g., Latest advancements in Small Language Models",
        label_visibility="collapsed",
    )
with col2:
    is_disabled = st.session_state.is_running or not api_key
    run_button = st.button("🚀 Research", type="primary", use_container_width=True, disabled=is_disabled)
    
    if run_button and not api_key:
        st.warning("Please provide an API Key in the sidebar.")

# --- Example Topics ---
st.markdown("**Try these:**")
example_cols = st.columns(4)
examples = [
    "Latest advancements in Small Language Models",
    "Multi-Agent Systems in AI",
    "Retrieval Augmented Generation techniques",
    "Transformer architecture innovations 2024",
]
for i, ex in enumerate(examples):
    with example_cols[i]:
        if st.button(ex[:35] + "...", key=f"ex_{i}"):
            topic = ex
            run_button = True

# --- Run Research ---
if run_button and topic:
    if not api_key:
        st.warning("Please provide an API Key in the sidebar to start the research.")
        st.stop()
        
    st.session_state.is_running = True
    st.session_state.research_result = None

    progress_bar = st.progress(0, text="Initializing research workflow...")
    status_container = st.container()

    agent_steps = [
        ("🎯 Supervisor", "Analyzing topic and planning workflow...", 10),
        ("📋 Planner", "Breaking topic into subtopics...", 25),
        ("🔍 Retrieval", "Searching for relevant sources...", 45),
        ("🧠 Memory", "Storing findings in knowledge base...", 55),
        ("✍️ Writer", "Generating research report...", 70),
        ("🔎 Critic", "Reviewing report quality...", 85),
        ("📚 Citation", "Formatting references...", 95),
    ]

    with status_container:
        for emoji_name, desc, pct in agent_steps:
            progress_bar.progress(pct / 100, text=f"{emoji_name}: {desc}")
            time.sleep(0.3)

    try:
        response = requests.post(
            f"{api_url}/research",
            json={
                "topic": topic, 
                "max_revisions": max_revisions, 
                "api_key": api_key, 
                "provider": llm_provider
            },
            timeout=300,
        )

        if response.status_code == 200:
            st.session_state.research_result = response.json()
            progress_bar.progress(1.0, text="✅ Research complete!")
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            progress_bar.progress(1.0, text="❌ Research failed")

    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to the API. Make sure the backend is running.")
        progress_bar.progress(1.0, text="❌ Connection failed")
    except requests.exceptions.Timeout:
        st.error("Request timed out. The research may still be processing.")
        progress_bar.progress(1.0, text="⏰ Timed out")
    except Exception as e:
        st.error(f"Error: {str(e)}")
        progress_bar.progress(1.0, text="❌ Error")

    st.session_state.is_running = False

# --- Display Results ---
result = st.session_state.research_result
if result:
    st.markdown("---")

    if result.get("status") == "quota_exceeded":
        st.error("⚠️ **API Quota Exceeded!** Your API key has run out of credits or hit a rate limit.")
        st.warning("The research workflow was interrupted. Please provide a new API Key in the sidebar to run further research. Below is the mid-research summary of what was found before the quota was reached:")


    # Metrics row
    mcols = st.columns(4)
    with mcols[0]:
        st.metric("Status", result.get("status", "N/A").title())
    with mcols[1]:
        st.metric("Citations", len(result.get("citations", [])))
    with mcols[2]:
        st.metric("Agent Steps", len(result.get("agent_activity", [])))
    with mcols[3]:
        review = result.get("critic_review") or {}
        st.metric("Quality Score", f"{review.get('overall_score', 'N/A')}")

    # Tabs
    tab_report, tab_agents, tab_citations, tab_review, tab_raw = st.tabs(
        ["📄 Report", "🤖 Agent Activity", "📚 Citations", "🔎 Review", "📊 Raw Data"]
    )

    with tab_report:
        report = result.get("final_report", "No report generated.")
        st.markdown(report)
        st.download_button(
            "📥 Download Report",
            data=report,
            file_name=f"research_report_{result.get('run_id', 'report')}.md",
            mime="text/markdown",
        )

    with tab_agents:
        activities = result.get("agent_activity", [])
        if activities:
            for act in activities:
                agent = act.get("agent", "unknown")
                css_class = f"agent-{agent}"
                st.markdown(
                    f'<div class="agent-card {css_class}">'
                    f'<strong>Step {act.get("step", "?")}:</strong> '
                    f'<em>{agent.replace("_", " ").title()}</em> — {act.get("action", "")}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No agent activity recorded.")

    with tab_citations:
        citations = result.get("citations", [])
        if citations:
            for cit in citations:
                with st.expander(f"[{cit.get('index', '?')}] {cit.get('title', 'Untitled')}"):
                    st.write(f"**Authors:** {cit.get('authors', 'N/A')}")
                    st.write(f"**Year:** {cit.get('year', 'N/A')}")
                    url = cit.get("url", "")
                    if url:
                        st.write(f"**URL:** [{url}]({url})")
        else:
            st.info("No citations available.")

    with tab_review:
        review = result.get("critic_review")
        if review:
            st.subheader(f"Verdict: {review.get('verdict', 'N/A').upper()}")

            scores = review.get("scores", {})
            if scores:
                score_cols = st.columns(len(scores))
                for i, (k, v) in enumerate(scores.items()):
                    with score_cols[i]:
                        st.metric(k.title(), f"{v}/10")

            st.markdown("**Feedback:**")
            st.write(review.get("feedback", "No feedback."))

            issues = review.get("issues", [])
            if issues:
                st.markdown("**Issues:**")
                for issue in issues:
                    st.warning(issue)
        else:
            st.info("No review available.")

    with tab_raw:
        st.json(result)

elif not st.session_state.is_running:
    # Landing state
    st.markdown("---")
    st.markdown("### How it works")
    cols = st.columns(4)
    steps = [
        ("1️⃣", "Plan", "Supervisor & Planner break your topic into subtopics"),
        ("2️⃣", "Research", "Retrieval agent searches web & knowledge base"),
        ("3️⃣", "Write", "Writer generates a structured academic report"),
        ("4️⃣", "Review", "Critic reviews quality, Citation agent adds references"),
    ]
    for i, (icon, title, desc) in enumerate(steps):
        with cols[i]:
            st.markdown(f"### {icon} {title}")
            st.markdown(desc)
