from config import require_groq_api_key, GROQ_MODEL
from groq import Groq

try:
    api_key = require_groq_api_key()
    print(f"API Key found: {api_key[:10]}...{api_key[-10:] if len(api_key) > 20 else ''}")
    print(f"API Key length: {len(api_key)}")
    
    client = Groq(api_key=api_key)
    
    # Test with a simple API call
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": "Say 'API key is valid' if you receive this."}],
        max_tokens=10
    )
    
    result = response.choices[0].message.content
    print(f"API Response: {result}")
    print("✓ API key is VALID")
    
except Exception as e:
    print(f"✗ API key is INVALID or error occurred: {e}")
