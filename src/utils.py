import tiktoken

def calculate_cost(text, model="gemini"):
    """
    Estimates token count. Cost is 0 for Gemini Free Tier.
    """
    # Tiktoken is for OpenAI, but it gives a good enough estimate of text length
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = len(encoding.encode(text))
    
    if model == "gemini":
        cost = 0.00  # Free Tier
    else:
        # Fallback for other models
        cost = (tokens / 1_000_000) * 10.00
    
    return tokens, cost

def format_error(e):
    return f"System error: {str(e)}. Please try refining your query."