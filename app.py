import streamlit as st
from rag_system import BusinessRAG
import time

# Page config
st.set_page_config(
    page_title="BrandedAI Business Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional look
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
    }
    .response-box {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1f4e79;
        margin: 1rem 0;
    }
    .source-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .stButton > button {
        width: 100%;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize RAG system
@st.cache_resource
def init_rag_system():
    try:
        return BusinessRAG()
    except Exception as e:
        st.error(f"Failed to initialize system: {e}")
        return None

def main():
    # Header
    st.markdown('<h1 class="main-header">🚀 BrandedAI Business Assistant</h1>', unsafe_allow_html=True)
    st.markdown("**Powered by Gemini 2.5 Pro + Your Knowledge Base**")
    
    # Initialize system
    rag = init_rag_system()
    
    if rag is None:
        st.error("❌ System initialization failed. Please check your .env file and credentials.")
        st.stop()
    else:
        st.success("✅ System Ready - Connected to your knowledge base")
    
    # Sidebar with quick actions
    with st.sidebar:
        st.header("🎯 Quick Actions")
        
        quick_questions = {
            "📧 Client Response": "How should I respond to the latest client inquiry?",
            "💰 Project Pricing": "What's our typical pricing for automation projects?",
            "🔧 Tool Recommendations": "What tools have we recommended for similar projects?",
            "📋 Project Status": "What's the status of current projects?",
            "🎯 Strategy Advice": "What's our approach for new automation clients?",
            "📞 Contact Info": "Who are the key contacts for recent projects?",
            "⚡ Quick Update": "What are the latest project updates?"
        }
        
        for label, question in quick_questions.items():
            if st.button(label, key=f"quick_{label}"):
                st.session_state.question = question
        
        st.markdown("---")
        st.markdown("**💡 Tips:**")
        st.markdown("- Be specific in your questions")
        st.markdown("- Reference client names for better context")
        st.markdown("- Ask for strategic advice")
        st.markdown("- Use the quick actions for common queries")
    
    # Main interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Question input
        question = st.text_area(
            "**Ask me anything about your business:**",
            placeholder="e.g., 'How should I respond to Slumberjack's production planning inquiry?'",
            height=120,
            key="question",
            value=st.session_state.get("question", "")
        )
        
        # Options row
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            urgency = st.selectbox("Priority", ["Normal", "High", "Urgent"])
        with col_b:
            include_technical = st.checkbox("Include Technical Details")
        with col_c:
            detailed_analysis = st.checkbox("Detailed Analysis")
        
        # Submit button
        if st.button("🚀 Get Business Insight", type="primary", use_container_width=True) and question:
            # Modify question based on options
            enhanced_question = question
            if include_technical:
                enhanced_question += " Include technical implementation details."
            if detailed_analysis:
                enhanced_question += " Provide detailed analysis and multiple options."
            if urgency in ["High", "Urgent"]:
                enhanced_question += f" This is {urgency.lower()} priority - provide immediate actionable steps."
            
            # Show processing
            with st.spinner("🧠 Analyzing your question..."):
                start_time = time.time()
                result = rag.ask(enhanced_question)
                response_time = time.time() - start_time
            
            # Display results
            st.markdown("### 💡 Business Insight")
            st.markdown(f'<div class="response-box">{result["response"]}</div>', unsafe_allow_html=True)
            
            # Metadata
            col_meta1, col_meta2, col_meta3 = st.columns(3)
            with col_meta1:
                st.metric("Query Type", result["query_type"].title())
            with col_meta2:
                st.metric("Sources Found", result["source_count"])
            with col_meta3:
                st.metric("Response Time", f"{response_time:.1f}s")
            
            # Sources
            if result["sources"] and result["source_count"] > 0:
                st.markdown("### 📚 Sources")
                for i, source in enumerate(result["sources"], 1):
                    st.markdown(f'<div class="source-box">{i}. {source}</div>', unsafe_allow_html=True)
            else:
                st.info("💡 Response based on general business knowledge - no specific documents found for this query.")
    
    with col2:
        st.markdown("### 📊 System Status")
        st.success("🟢 Gemini 2.5 Pro")
        st.success("🟢 Supabase Connected")
        st.info("📁 Knowledge Base Active")
        
        # System info
        st.markdown("### ℹ️ System Info")
        st.markdown("- **Model:** Gemini 2.0 Flash Exp")
        st.markdown("- **Context:** 2M tokens")
        st.markdown("- **Database:** Supabase")
        st.markdown("- **Search:** Text matching")
        
        st.markdown("### 🎯 Example Questions")
        examples = [
            "What did Hannah say about pricing?",
            "How did we approach the Birkdale project?",
            "What tools do we recommend for HubSpot?",
            "Who should I contact at Quantum?",
            "What's our automation pricing strategy?"
        ]
        
        for example in examples:
            if st.button(f"💭 {example[:30]}...", key=f"example_{example[:15]}"):
                st.session_state.question = example
                st.rerun()

if __name__ == "__main__":
    main()