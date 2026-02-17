import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load your API Key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ Error: GOOGLE_API_KEY not found in .env")
else:
    print(f"✅ Found API Key: {api_key[:5]}...")
    
    try:
        genai.configure(api_key=api_key)
        print("\n🔍 Checking available models for your key...")
        
        available_models = []
        for m in genai.list_models():
            # We only care about models that can generate text (content)
            if 'generateContent' in m.supported_generation_methods:
                print(f"  - {m.name}")
                available_models.append(m.name)
        
        if not available_models:
            print("\n⚠️ No text generation models found. Your key might be restricted.")
        else:
            print(f"\n🚀 SUCCESS! You have access to {len(available_models)} models.")
            print("Copy one of the names above (e.g., 'models/gemini-2.0-flash') into your agent.py")
            
    except Exception as e:
        print(f"\n❌ API Error: {str(e)}")