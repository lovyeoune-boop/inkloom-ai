import os
from google import genai
from google.genai import types

# Initialize the Gemini client
# Note: Ensure your GEMINI_API_KEY is set in your environment variables
client = genai.Client()

def review_content_compliance(draft_content: str, brand_guidelines: str):
    """
    Evaluates draft content against company brand guidelines and returns 
    explainable feedback, rule violations, and suggested corrections.
    """
    prompt = f"""
    You are an AI brand governance and compliance officer for Inkloom AI. 
    Your task is to review the following draft content against the provided company guidelines.
    
    === COMPANY GUIDELINES ===
    {brand_guidelines}
    
    === CONTENT TO REVIEW ===
    {draft_content}
    
    === INSTRUCTIONS ===
    1. Check for tone consistency, terminology errors, unverified promotional claims, or off-board phrasing.
    2. If violations are found, explain clearly why it was flagged and cite the guideline involved.
    3. Provide constructive, smart correction suggestions that preserve the creator's original intent.
    """

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2, # Lower temperature for analytical, objective compliance reviews
        )
    )
    
    return response.text

# --- Example Local Test ---
if __name__ == "__main__":
    # Mock rulebook (In your full app, this will be retrieved via your vector database / RAG)
    sample_rulebook = """
    Rule 1: Never use unverified superlatives like 'guaranteed 100% risk-free' or 'cheapest on earth'.
    Rule 2: Maintain a professional, authoritative, yet approachable tone of voice. Always refer to our product as an 'intelligent governance assistant'.
    """
    
    # Mock draft content submitted by a creator
    sample_draft = "Our new software tool is the cheapest on earth and gives you guaranteed 100% risk-free profits!"
    
    print("Running Inkloom AI Brand Compliance Audit...\n")
    audit_results = review_content_compliance(sample_draft, sample_rulebook)
    print(audit_results)
