import os
from anthropic import Anthropic
from models import Website, User

anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def generate_outreach_email_content(website, user_id, sender_name, company_name, company_profile, article_url, is_followup=False):
    user = User.query.get(user_id)
    if not user:
        print(f"User with id {user_id} not found")
        return None

    prompt = f"""
    Create an {'follow-up ' if is_followup else ''}outreach email for the website {website.url}.
    Recipient Name: {website.author_name.split()[0]}
    Recipient Email: {website.author_email}
    Sender Name: {sender_name}
    Sender Email: {user.email}
    Company Name: {company_name}
    Company Profile: {company_profile}
    Article URL: {article_url}
    
    The email should be personalized, friendly, and focused on suggesting that the recipient's readers might find the article helpful or interesting. Do not mention the word "backlink" explicitly.
    
    Keep the tone professional yet approachable, and use only the recipient's first name when addressing them.
    
    {'If this is a follow-up email, politely remind them about the previous email and express continued interest in collaboration.' if is_followup else ''}
    
    The email should:
    1. Start with a brief introduction and mention something specific about the recipient's website or recent content.
    2. Introduce your company and article briefly.
    3. Suggest how the article might be valuable to the recipient's readers.
    4. Politely ask if they would consider mentioning or linking to your article if they find it relevant.
    5. Offer to provide any additional information if needed.
    6. Thank them for their time and consideration.
    """
    
    try:
        response = anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text.strip()
    except Exception as e:
        print(f"Error generating email with Anthropic API: {str(e)}")
        return generate_fallback_email(website, sender_name, company_name, company_profile, article_url, is_followup)

def generate_fallback_email(website, sender_name, company_name, company_profile, article_url, is_followup=False):
    recipient_first_name = website.author_name.split()[0]
    followup_intro = "I hope this email finds you well. I'm following up on my previous message regarding " if is_followup else ""
    
    return f"""
    Dear {recipient_first_name},

    {followup_intro}I hope this email finds you well. My name is {sender_name}, and I recently came across your excellent content on {website.url}. I was particularly impressed by your insights on [mention a specific topic or article from their website].

    I'm reaching out because I work with {company_name}, a company that {company_profile}. We've recently published an article that I believe would be valuable to your readers. The article discusses [brief description of your article topic] and can be found here: {article_url}

    Given your expertise in [related field], I thought you might be interested in taking a look. If you find the content relevant and helpful, we'd be honored if you'd consider mentioning or referencing it in one of your future posts.

    I'd be happy to provide any additional information or answer any questions you might have about the article or our company.

    Thank you for your time and consideration. I look forward to hearing from you.

    Best regards,
    {sender_name}
    {company_name}
    """