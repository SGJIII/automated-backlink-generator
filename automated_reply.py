from anthropic import Anthropic
import os
from models import User
from email_sender import send_email

anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def process_reply(website, reply_content, user_id):
    prompt = f"""
    Analyze the following reply to our backlink request for {website.url}:
    
    {reply_content}
    
    If it's a confirmation that they will add the backlink, respond with a thank you message.
    If not, craft a persuasive response to encourage them to add the backlink.
    If it's unclear, ask for clarification politely.
    """
    
    try:
        response = anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = response.content[0].text.strip()
        
        # Send the response
        user = User.query.get(user_id)
        if user:
            send_email(user.id, website.author_email, "Re: Backlink Request", response_text)
        
        return response_text
    except Exception as e:
        print(f"Error processing reply with Anthropic API: {str(e)}")
        return "An error occurred while processing the reply. Please check the response manually."
