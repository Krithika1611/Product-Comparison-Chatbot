from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langchain_community.utilities import SerpAPIWrapper
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from langchain_community.vectorstores.supabase import SupabaseVectorStore
from supabase.client import create_client
import os
import json
import datetime
import sys

SERPAPI_API_KEY = "your_serpapi_key"
GROQ_API_KEY = "your_groq_key"
GOOGLE_API_KEY = "your_google_api_key"
SUPABASE_URL = "your_supabase_url"
SUPABASE_KEY = "your_supabase_service_key" # Your Supabase service role key

# Define constants
USER_CONTEXT_PATH = "user_context.json"
COLLECTION_NAME = "product_info"

# Initialize search tool
search = SerpAPIWrapper(serpapi_api_key=SERPAPI_API_KEY)

# Initialize language model
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    max_tokens=1024
)

# Initialize Gemini embeddings
try:
    embeddings = GoogleGenerativeAIEmbeddings(
        google_api_key=GOOGLE_API_KEY,
        model="models/embedding-001"
    )
except Exception as e:
    print(f"Error initializing Gemini embeddings: {e}")
    print("Using mock embeddings for demonstration")
    
    # Create a simple mock embedding function
    class MockEmbeddings:
        def embed_documents(self, texts):
            # Return mock embeddings (simple hash-based)
            return [[hash(text) % 1024 / 1024 for _ in range(768)] for text in texts]
        
        def embed_query(self, text):
            # Return mock embedding (simple hash-based)
            return [hash(text) % 1024 / 1024 for _ in range(768)]
    
    embeddings = MockEmbeddings()

# Initialize Supabase client
try:
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Error connecting to Supabase: {e}")
    supabase_client = None  # Will be handled in vector_store initialization

# Initialize vector store with Supabase
def init_supabase_vector_store():
    """Initialize Supabase vector store"""
    if not supabase_client:
        print("Supabase client not available. Using mock vector store.")
        return MockVectorStore()
    
    try:
        # Create vector store with Supabase
        vector_store = SupabaseVectorStore(
            client=supabase_client,
            embedding=embeddings,
            table_name=COLLECTION_NAME,
            query_name="match_documents"
        )
        return vector_store
    except Exception as e:
        print(f"Error initializing Supabase vector store: {e}")
        return MockVectorStore()

# Mock vector store for fallback
class MockVectorStore:
    def add_documents(self, docs):
        print(f"Added {len(docs)} documents to mock store")
        return True
    
    def similarity_search(self, query, k=3):
        print(f"Searching for: {query}")
        return [Document(
            page_content=f"Mock result for {query}", 
            metadata={"product_name": query, "source": "mock"}
        )]

# Function to load or create user context
def get_user_context():
    if os.path.exists(USER_CONTEXT_PATH):
        try:
            with open(USER_CONTEXT_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading user context: {e}")
            return create_new_user_context()
    else:
        return create_new_user_context()

def create_new_user_context():
    return {
        "previous_products": [],
        "user_preferences": {},
        "comparison_criteria": []
    }

def save_user_context(user_context):
    with open(USER_CONTEXT_PATH, "w") as f:
        json.dump(user_context, f)

# Simple in-memory chat history store to avoid deprecation warnings
class SimpleMemory:
    def __init__(self):
        self.buffer = []
    
    def add_message(self, role, content):
        self.buffer.append({"role": role, "content": content})
    
    def get_messages(self):
        return self.buffer

# Initialize memory
memory = SimpleMemory()

# Initialize vector store
vector_store = init_supabase_vector_store()

# Create prompt templates
from langchain.prompts import ChatPromptTemplate

comparison_prompt = ChatPromptTemplate.from_template("""
You are a helpful AI assistant specialized in product research and comparisons for business professionals.
Your goal is to provide brief, actionable insights about products and comparisons between them.

Only use the vector database if the user's prompt explicitly refers to a product found in it. Avoid unnecessary retrievals.

If the user has mentioned fewer than two products, politely ask them to provide at least two products for comparison.
Don't output lines like "I've researched".
Respond to simple user interactions like hi, bye, etc. Remember the last 5 messages received and generated and answer to 
follow-up messages when asked.

Product being researched: {product}

SEARCH RESULTS:
{search_results}

ADDITIONAL CONTEXT:
Chat history: {chat_history}
Previously researched products: {previous_products}
Known user preferences: {user_preferences}
Relevant vector database info (if applicable): {vector_db_results}

Your output must follow these rules strictly:
- Output a table with 5 rows, each comparing the two products across a specific aspect.
- The first row must be the header: "Aspect | Product 1 | Product 2" with `|` as the delimiter.
- Product 1 and Product 2 must be the names of the two products being compared (e.g., iPhone 11 and iPhone 12).
- Each subsequent row must contain exactly three segments separated by `|` with no extra spaces.
- Each row must be on a new line.
- After the table, add a marker "SUMMARY:" followed by a 2-line summary on separate lines.
- Do NOT use markdown, bullet points, or any special formatting beyond the `|` delimiter.
- Keep each cell content concise (under 50 characters).
- Write in plain text, structured for easy parsing.

Use these exact aspect labels for the table rows:
1. Key features
2. Comparison
3. Pricing
4. Strengths
5. Suitability

Example output format:
Aspect | iPhone 11 | iPhone 12
Key features | A13, 10hr play | A14, OLED, 11hr
Comparison | Similar to 11 | Beats flagships
Pricing | Budget-friendly | Higher value
Strengths | Good value | Better battery
Suitability | Cost-focused | Power-focused
SUMMARY:
iPhone 12 suits power users.
iPhone 11 fits budget needs.

Be clear and business-oriented. Avoid unnecessary technical jargon.
""")

def extract_product_info(product, search_results):
    """Extract structured information about a product from search results"""
    product_info = {
        "product_name": product,
        "features": [],
        "price_info": "",
        "reviews": [],
        "competitors": [],
        "timestamp": str(datetime.datetime.now())
    }
    
    # This would ideally use an LLM to extract structured info from search results
    # For now, we'll just use the raw search results
    doc = Document(
        page_content=f"Product information for {product}: {search_results}",
        metadata=product_info
    )
    
    return doc

def update_user_context(product, chat_history, user_context):
    """Update the user context with new information"""
    # Track researched products
    if product and product not in user_context["previous_products"]:
        user_context["previous_products"].append(product)
    
    # Extract preferences from chat history
    chat_str = str(chat_history).lower()
    preference_keywords = ["prefer", "like", "want", "need", "looking for", "important", "priority"]
    
    for keyword in preference_keywords:
        if keyword in chat_str:
            # Find sentences containing preference keywords
            # This is a simplified approach - a real implementation would use NLP
            sentences = chat_str.split('.')
            for sentence in sentences:
                if keyword in sentence:
                    preference = sentence.strip()
                    if "preferences" not in user_context["user_preferences"]:
                        user_context["user_preferences"]["preferences"] = []
                    if preference not in user_context["user_preferences"]["preferences"]:
                        user_context["user_preferences"]["preferences"].append(preference)
    
    return user_context

def research_product(product_query):
    """Main function to research and compare products"""
    # Load user context
    user_context = get_user_context()
    
    # Get search results
    search_results = search.run(product_query)
    
    # Extract and store product information
    product_doc = extract_product_info(product_query, search_results)
    
    # Generate numeric IDs for Supabase (which expects int8)
    import hashlib
    import time
    
    # Create a deterministic but unique numeric ID
    numeric_id = int(hashlib.md5((product_query + str(time.time())).encode()).hexdigest(), 16) % (2**63 - 1)
    
    # Pass the numeric ID when adding documents
    vector_store.add_documents([product_doc], ids=[numeric_id])
    
    # Get relevant product information from vector store
    vector_results = vector_store.similarity_search(product_query, k=3)
    vector_db_results = "\n".join([doc.page_content for doc in vector_results])
    
    # Update memory and context
    memory.add_message("user", product_query)
    chat_history = memory.get_messages()
    user_context = update_user_context(product_query, chat_history, user_context)
    save_user_context(user_context)
    
    # Create chain
    chain = (
        {"product": RunnablePassthrough(), 
         "search_results": lambda x: search.run(x["product"]),
         "chat_history": lambda x: memory.get_messages(),
         "previous_products": lambda x: user_context["previous_products"],
         "user_preferences": lambda x: user_context["user_preferences"],
         "vector_db_results": lambda x: vector_db_results
        }
        | comparison_prompt
        | llm
        | StrOutputParser()
    )
    
    # Run chain
    response = chain.invoke({"product": product_query})
    
    # Save response to memory
    #memory.add_message("assistant", response)
    
    return response



if __name__ == "__main__":
    input_data = sys.stdin.read()
    data = json.loads(input_data)
    product_query = data.get("product")
    chat_history = data.get("chat_history", [])

    # Initialize memory with chat history
    memory = SimpleMemory()
    for msg in chat_history:
        memory.add_message(msg["role"], msg["content"])

    response = research_product(product_query)
    sys.stdout.write(response)