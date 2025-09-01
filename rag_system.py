import os
import google.generativeai as genai
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import List, Dict, Optional
import streamlit as st
import json

load_dotenv()

class BusinessRAG:
    def __init__(self):
        """Initialize with comprehensive error handling and debugging"""
        try:
            # Initialize Supabase
            self.supabase_url = os.getenv("SUPABASE_URL")
            self.supabase_key = os.getenv("SUPABASE_KEY")
            self.gemini_key = os.getenv("GEMINI_API_KEY")
            
            # Validate environment variables
            if not all([self.supabase_url, self.supabase_key, self.gemini_key]):
                st.error("❌ Missing environment variables!")
                st.write(f"Supabase URL: {'✅' if self.supabase_url else '❌'}")
                st.write(f"Supabase Key: {'✅' if self.supabase_key else '❌'}")
                st.write(f"Gemini Key: {'✅' if self.gemini_key else '❌'}")
                return
            
            # Initialize clients
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            genai.configure(api_key=self.gemini_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            # Test and detect table structure
            self.table_info = self.detect_table_structure()
            
        except Exception as e:
            st.error(f"❌ Initialization failed: {str(e)}")
            self.table_info = {"error": str(e)}
    
    def detect_table_structure(self) -> Dict:
        """Detect actual table structure and available columns"""
        try:
            st.write("🔍 **Detecting your table structure...**")
            
            # Test basic connection first
            response = self.supabase.table("documents").select("*").limit(1).execute()
            
            if not response.data:
                st.write("❌ **No documents found in 'documents' table**")
                
                # Try alternative table names
                for table_name in ["document", "files", "content", "knowledge"]:
                    try:
                        st.write(f"🔄 Trying table: '{table_name}'")
                        response = self.supabase.table(table_name).select("*").limit(1).execute()
                        if response.data:
                            st.write(f"✅ **Found data in table: '{table_name}'**")
                            break
                    except:
                        continue
                else:
                    return {"error": "No accessible tables found"}
            
            if response.data:
                sample_doc = response.data[0]
                columns = list(sample_doc.keys())
                
                st.write(f"✅ **Table structure detected:**")
                st.write(f"**Available columns:** {columns}")
                
                # Show sample data
                st.write("**Sample document structure:**")
                for key, value in sample_doc.items():
                    value_preview = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                    st.write(f"- **{key}:** {value_preview}")
                
                # Identify searchable columns
                text_columns = []
                for col in columns:
                    if col.lower() in ['content', 'text', 'body', 'description', 'summary', 'title', 'name', 'filename', 'file_path']:
                        text_columns.append(col)
                
                st.write(f"**Searchable columns identified:** {text_columns}")
                
                return {
                    "columns": columns,
                    "text_columns": text_columns,
                    "sample": sample_doc,
                    "table_name": "documents"
                }
            
            return {"error": "No data found"}
            
        except Exception as e:
            st.write(f"❌ **Table detection failed:** {str(e)}")
            return {"error": str(e)}
    
    def search_documents(self, query: str, limit: int = 5) -> List[Dict]:
        """Vector search - uses your existing vector infrastructure"""
        try:
            st.write(f"🔍 **Vector searching 254K+ documents for:** '{query}'")
            
            # Generate embedding for query using OpenAI
            try:
                import openai
                openai.api_key = os.getenv("OPENAI_API_KEY")
                
                response = openai.Embedding.create(
                    input=query[:8000],  # Limit query length
                    model="text-embedding-3-small"
                )
                query_embedding = response['data'][0]['embedding']
                
                st.write("✅ **Query embedding generated**")
                
            except Exception as e:
                st.write(f"❌ **Embedding generation failed:** {str(e)}")
                return self.fallback_search(limit)
            
            # Vector search using your existing match_documents function
            try:
                results = self.supabase.rpc('match_documents', {
                    'query_embedding': query_embedding,
                    'match_threshold': 0.3,
                    'match_count': limit
                }).execute()
                
                if results.data:
                    st.write(f"✅ **Found {len(results.data)} highly relevant documents**")
                    st.write(f"📊 **Similarity scores:** {[f'{r.get('similarity', 0):.2f}' for r in results.data]}")
                    return results.data
                else:
                    st.write("⚠️ **No documents found above similarity threshold - trying fallback**")
                    return self.fallback_search(limit)
                    
            except Exception as e:
                st.write(f"❌ **Vector search failed:** {str(e)}")
                return self.fallback_search(limit)
                
        except Exception as e:
            st.write(f"❌ **Search error:** {str(e)}")
            return self.fallback_search(limit)
    
    def fallback_search(self, limit: int = 5) -> List[Dict]:
        """Fallback to recent documents if vector search fails"""
        try:
            st.write("🔄 **Using fallback: recent documents**")
            response = self.supabase.table("documents").select(
                "id, title, content, file_type, file_path"
            ).order("id", desc=True).limit(limit).execute()
            
            if response.data:
                st.write(f"✅ **Using {len(response.data)} recent documents**")
                return response.data
            return []
        except Exception as e:
            st.write(f"❌ **Fallback failed:** {str(e)}")
            return []
    
    def extract_content(self, doc: Dict) -> tuple:
        """Extract title and content from document using detected structure"""
        text_columns = self.table_info.get("text_columns", [])
        
        # Try to find title
        title = "Unknown Document"
        for title_field in ['title', 'name', 'filename', 'file_path']:
            if title_field in doc and doc[title_field]:
                title = str(doc[title_field])
                break
        
        # Try to find content
        content = "No content available"
        for content_field in ['content', 'text', 'body', 'description']:
            if content_field in doc and doc[content_field]:
                content = str(doc[content_field])[:1500]  # Limit length
                break
        
        return title, content
    
    def generate_response(self, question: str, context_docs: List[Dict]) -> str:
        """Generate business response using found documents"""
        try:
            if context_docs:
                context_parts = []
                for doc in context_docs[:3]:  # Use top 3 documents
                    title, content = self.extract_content(doc)
                    context_parts.append(f"Document: {title}\nContent: {content}")
                
                context = "\n\n".join(context_parts)
                st.write(f"📄 **Using {len(context_docs)} documents for context**")
            else:
                context = "No specific documents found in your knowledge base."
                st.write("⚠️ **No documents found - using general knowledge**")
            
            # Generate response
            prompt = f"""
            You are a business assistant with access to comprehensive business knowledge.
            
            Context from business documents:
            {context}
            
            Question: {question}
            
            Provide a helpful business response with:
            1. **DIRECT ANSWER** - Address the question directly
            2. **KEY INSIGHTS** - Relevant information from the context
            3. **NEXT STEPS** - Recommended actions
            
            If the context doesn't contain relevant information, provide general business guidance and suggest gathering more specific information.
            """
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def ask(self, question: str) -> Dict:
        """Main method for business questions with comprehensive debugging"""
        if not question.strip():
            return {
                "question": question,
                "response": "Please ask a specific business question.",
                "sources": [],
                "source_count": 0
            }
        
        try:
            # Show system status
            st.write("🔧 **System Status Check:**")
            st.write(f"- Environment variables: ✅")
            st.write(f"- Supabase connection: ✅")
            st.write(f"- Gemini API: ✅")
            
            # Search for relevant documents
            relevant_docs = self.search_documents(question, 5)
            
            # Generate response
            response = self.generate_response(question, relevant_docs)
            
            # Extract source names
            sources = []
            for doc in relevant_docs:
                title, _ = self.extract_content(doc)
                sources.append(title)
            
            return {
                "question": question,
                "response": response,
                "sources": sources,
                "source_count": len(relevant_docs)
            }
        
        except Exception as e:
            st.write(f"❌ **System error:** {str(e)}")
            return {
                "question": question,
                "response": f"System error: {str(e)}",
                "sources": [],
                "source_count": 0
            }

# Test function for debugging
if __name__ == "__main__":
    rag = BusinessRAG()
    result = rag.ask("What projects have we worked on?")
    print("Response:", result["response"])
    print("Sources:", result["sources"])

