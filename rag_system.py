import os
import google.generativeai as genai
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

class BusinessRAG:
    def __init__(self):
        # Initialize Supabase (your existing setup)
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        
        # Initialize Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def search_documents(self, query: str, limit: int = 5) -> List[Dict]:
        """Search your existing Supabase vector database"""
        try:
            # Search in both title and content columns
            response = self.supabase.table("documents").select(
                "id, title, content, file_type, file_path, metadata"
            ).or_(
                f"title.ilike.%{query}%,content.ilike.%{query}%"
            ).limit(limit).execute()
            
            return response.data if response.data else []
        
        except Exception as e:
            print(f"Search error: {e}")
            # Fallback to simple content search
            try:
                response = self.supabase.table("documents").select(
                    "id, title, content, file_type, file_path, metadata"
                ).ilike("content", f"%{query}%").limit(limit).execute()
                return response.data if response.data else []
            except:
                return []
    
    def classify_query(self, question: str) -> str:
        """Simple query classification"""
        simple_keywords = ["what", "who", "when", "where", "contact", "email", "phone", "price"]
        complex_keywords = ["compare", "analyze", "recommend", "strategy", "approach", "best", "how should"]
        
        question_lower = question.lower()
        
        if any(keyword in question_lower for keyword in complex_keywords):
            return "complex"
        elif any(keyword in question_lower for keyword in simple_keywords):
            return "simple"
        else:
            return "medium"
    
    def generate_response(self, question: str, context_docs: List[Dict], query_type: str) -> str:
        """Generate business-focused response using Gemini"""
        try:
            # Prepare context from documents
            if context_docs:
                context = "\n\n".join([
                    f"Document: {doc.get('title', doc.get('file_path', 'Unknown'))}\n"
                    f"Content: {doc.get('content', '')[:1000]}..."  # Limit content length
                    for doc in context_docs[:3]  # Use top 3 documents
                ])
            else:
                context = "No specific documents found. Use general business knowledge."
            
            # Business-focused prompt based on query type
            if query_type == "simple":
                prompt = f"""
                You are a business assistant. Provide a direct, factual answer.
                
                Context from business documents:
                {context}
                
                Question: {question}
                
                Provide a direct answer. If the context doesn't contain the answer, say so clearly.
                """
            else:
                prompt = f"""
                You are a senior business consultant with access to comprehensive business knowledge.
                
                Context from business documents:
                {context}
                
                Question: {question}
                
                Provide a strategic business response with:
                1. IMMEDIATE_ANSWER (direct response to the question)
                2. KEY_INSIGHTS (relevant information from the context)
                3. RECOMMENDED_ACTIONS (specific next steps)
                4. BUSINESS_IMPACT (potential implications)
                
                Be direct, actionable, and business-focused. If the context is insufficient, recommend gathering more information.
                """
            
            # Generate response
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"Error generating response: {str(e)}. Please check your API keys and try again."
    
    def ask(self, question: str) -> Dict:
        """Main method for business questions"""
        if not question.strip():
            return {
                "question": question,
                "response": "Please ask a specific business question.",
                "query_type": "empty",
                "sources": [],
                "source_count": 0
            }
        
        try:
            # Classify query
            query_type = self.classify_query(question)
            
            # Search for relevant documents
            relevant_docs = self.search_documents(question, 3 if query_type == "simple" else 5)
            
            # Generate response
            response = self.generate_response(question, relevant_docs, query_type)
            
            return {
                "question": question,
                "response": response,
                "query_type": query_type,
                "sources": [doc.get('title', doc.get('file_path', 'Unknown')) for doc in relevant_docs],
                "source_count": len(relevant_docs)
            }
        
        except Exception as e:
            return {
                "question": question,
                "response": f"System error: {str(e)}. Please check your configuration.",
                "query_type": "error",
                "sources": [],
                "source_count": 0
            }

# Test function
if __name__ == "__main__":
    rag = BusinessRAG()
    result = rag.ask("What projects have we worked on?")

    print("Response:", result["response"])
