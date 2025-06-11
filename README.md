# 🛍️ Product Comparison Chatbot

An intelligent, LLM-powered chatbot that compares products using real-time web search, semantic understanding, and contextual memory. Built using LangChain, Groq, Supabase, and Gemini embeddings.

## Features

- Real-time product search via SerpAPI  
- Structured LLM-based comparison  
- Remembers user preferences & chat context  
- Embedding-powered Supabase vector search  
- Fallbacks for offline/mock testing  
- Outputs 5-row comparison table + summary  

## Setup Instructions

### 1. Clone the Repository

git clone https://github.com/your-username/product-comparison-chatbot.git  
cd product-comparison-chatbot

### 2. Install Dependencies

pip install -r requirements.txt

### 3. Add API Keys

Open `app.py` and replace these with your own:

SERPAPI_API_KEY = "your_serpapi_key"  
GROQ_API_KEY = "your_groq_api_key"  
GOOGLE_API_KEY = "your_google_api_key"  
SUPABASE_URL = "your_supabase_url"  
SUPABASE_KEY = "your_supabase_service_role_key"

## Run the Application

Use command-line to run:
\`\`\`bash
cd product-comparison-frontend
npm run dev
\`\`\`

The script will output a product comparison table and a summary in plain text.

## Sample Output

![Screenshot 2025-04-16 193923](https://github.com/user-attachments/assets/ae0806e4-b396-43bf-bb92-4f11138b1c03)

![image](https://github.com/user-attachments/assets/3e66d33e-2cf6-46d6-b537-f9737a9baf55)

## Project Structure

app.py                      → Backend code (LangChain, Groq, Supabase)  
requirements.txt            → Python dependencies  
user_context.json           → Chat context memory  
product-comparison-frontend → Frontend folder

## Notes

- Works even if Supabase or Gemini fail (mock fallback used)  
- Change table fields/aspects inside the `comparison_prompt`  
- Secure API keys using .env (optional)

## License

MIT License
