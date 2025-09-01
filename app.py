import streamlit as st
import os
from rag_system import BusinessRAG

# Page configuration
st.set_page_config(
    page_title="BrandedAI Business Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

def initialize_rag():
    """Initialize RAG system with error handling"""
    try:
        if 'rag_system' not in st.session_state:
            with st.spinner("🔄 Initializing AI system..."):
                st.session_state.rag_system = BusinessRAG()
        return st.session_state.rag_system
    except Exception as e:
        st.error(f"❌ Failed to initialize system: {str(e)}")
        return None

def main():
    """Main application interface"""
    
    # Header
    st.markdown('<h1 class="main-header">🚀 BrandedAI Business Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Powered by Gemini 2.5 Pro • Your Knowledge Base</p>', unsafe_allow_html=True)
    
    # Initialize RAG system
    rag_system = initialize_rag()
    
    if not rag_system:
        st.error("❌ System initialization failed. Please refresh the page.")
        return
    
    # Sidebar with Quick Actions
    with st.sidebar:
        st.markdown("## 🎯 Quick Actions")
        
        # Quick action buttons
        if st.button("📧 Client Response", key="client_response"):
            st.session_state.query = "Help me draft a professional client response"
        
        if st.button("💰 Project Pricing", key="project_pricing"):
            st.session_state.query = "What are our standard project pricing guidelines?"
        
        if st.button("🔧 Tool Recommendations", key="tool_recommendations"):
            st.session_state.query = "What tools do we recommend for automation projects?"
        
        if st.button("📋 Project Status", key="project_status"):
            st.session_state.query = "What are the current project statuses?"
        
        if st.button("🎯 Strategy Advice", key="strategy_advice"):
            st.session_state.query = "Provide strategic advice for our business"
        
        if st.button("📞 Contact Info", key="contact_info"):
            st.session_state.query = "What are our key contact details and processes?"
        
        if st.button("⚡ Quick Update", key="quick_update"):
            st.session_state.query = "Give me a quick business update"
        
        # Tips section
        st.markdown("## 💡 Tips:")
        st.markdown("""
        • Be specific in your questions
        • Reference client names for better context
        • Ask for strategic advice
        • Use the quick actions for common queries
        """)
        
        # System status
        st.markdown("## 📊 System Status")
        st.markdown('<div class="status-box success-box">✅ Gemini 2.5 Pro Connected</div>', unsafe_allow_html=True)
        st.markdown('<div class="status-box success-box">✅ Supabase Connected</div>', unsafe_allow_html=True)
        st.markdown('<div class="status-box info-box">📚 Knowledge Base Active</div>', unsafe_allow_html=True)
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Main chat interface
        st.markdown("### Ask me anything about your business:")
        
        # Initialize query in session state
        if 'query' not in st.session_state:
            st.session_state.query = ""
        
        # Text input for questions
        user_question = st.text_area(
            "Your question:",
            value=st.session_state.query,
            height=100,
            placeholder="e.g., What projects have we worked on? How did we approach the Birkdale project? What are our pricing strategies?"
        )
        
        # Priority and options
        col_priority, col_options = st.columns([1, 2])
        
        with col_priority:
            priority = st.selectbox("Priority:", ["Normal", "High", "Urgent"])
        
        with col_options:
            include_technical = st.checkbox("Include Technical Details")
            detailed_analysis = st.checkbox("Detailed Analysis")
        
        # Submit button
        if st.button("🔍 Get Business Insight", type="primary", use_container_width=True):
            if user_question.strip():
                with st.spinner("🔄 Analyzing your business knowledge..."):
                    try:
                        # Get response from RAG system
                        result = rag_system.ask(user_question)
                        
                        # Display response
                        st.markdown("### 💡 Response:")
                        st.markdown(result["response"])
                        
                        # Display sources if found
                        if result["source_count"] > 0:
                            st.markdown(f"### 📚 Sources ({result['source_count']} documents):")
                            for i, source in enumerate(result["sources"][:3], 1):
                                st.markdown(f"**{i}.** {source}")
                        else:
                            st.info("ℹ️ Response based on general business knowledge")
                        
                        # Clear the query from session state
                        st.session_state.query = ""
                        
                    except Exception as e:
                        st.error(f"❌ Error processing question: {str(e)}")
            else:
                st.warning("⚠️ Please enter a question")
    
    with col2:
        # System information panel
        st.markdown("### 📊 System Info")
        
        # Model information
        st.markdown("**Model:** Gemini 2.0 Flash Exp")
        st.markdown("**Context:** 2M tokens")
        st.markdown("**Database:** Supabase")
        st.markdown("**Search:** Vector matching")
        
        # Example questions
        st.markdown("### 🔍 Example Questions")
        
        example_questions = [
            "What did Hannah say about pricing?",
            "How did we approach the Birkdale project?",
            "What tools do we recommend for clients?",
            "Who should I contact at Quantum Security?",
            "What are our current automation strategies?"
        ]
        
        for question in example_questions:
            if st.button(f"💭 {question}", key=f"example_{hash(question)}", use_container_width=True):
                st.session_state.query = question
                st.rerun()

if __name__ == "__main__":
    main()
