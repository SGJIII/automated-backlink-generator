import os
from anthropic import Anthropic
from models import Website, Content, db, User  # Updated import to include User model

anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def generate_content(website):
    prompt = f"Write a personalized outreach email for the website {website.url}. The email should be friendly, professional, and briefly explain the benefits of backlinking. Mention '[some crypto currency] IRA' as the topic."
    
    try:
        response = anthropic.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        generated_content = response.content[0].text.strip()
        
        new_content = Content(website_id=website.id, content_text=generated_content)
        db.session.add(new_content)
        db.session.commit()
        
        return generated_content
    except Exception as e:
        print(f"Error generating content with Anthropic API: {str(e)}")
        # Fallback to a template
        return generate_fallback_content(website)

def generate_fallback_content(website):
    return f"""
    Dear {website.author_name},

    I hope this email finds you well. My name is [Your Name], and I recently came across your excellent article on {website.url}. I was impressed by your insights on [topic].

    I'm reaching out because I've written an article about [some crypto currency] IRAs that I believe would be valuable to your readers. Given your expertise in [related field], I thought you might be interested in linking to it.

    If you're open to the idea, I'd be happy to share the article with you. It could provide your readers with additional information on [specific aspect of crypto IRAs].

    Thank you for your time and consideration. I look forward to hearing from you.

    Best regards,
    [Your Name]
    """

def generate_follow_up(website, attempt):
    prompt = f"Write a follow-up email for the website {website.url}. This is follow-up attempt number {attempt}. Be polite and remind them about the previous email regarding '[some crypto currency] IRA' backlink request."
    
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
        print(f"Error generating follow-up email with Anthropic API: {str(e)}")
        # Fallback to a template
        return generate_fallback_follow_up(website, attempt)

def generate_fallback_follow_up(website, attempt):
    return f"""
    Dear {website.author_name},

    I hope this email finds you well. My name is [Your Name], and I recently came across your excellent article on {website.url}. I was impressed by your insights on [topic].

    I'm reaching out because I've written an article about [some crypto currency] IRAs that I believe would be valuable to your readers. Given your expertise in [related field], I thought you might be interested in linking to it.

    If you're open to the idea, I'd be happy to share the article with you. It could provide your readers with additional information on [specific aspect of crypto IRAs].

    Thank you for your time and consideration. I look forward to hearing from you.

    Best regards,
    [Your Name]
    """

def generate_outreach_email(website, user_id):
    user = User.query.get(user_id)
    if not user:
        print(f"User with id {user_id} not found")
        return None

    prompt = f"""
    Create an outreach email for the website {website.url}.
    Author Name: {website.author_name}
    Email: {website.author_email}
    Sender Name: {user.name}
    Sender Email: {user.email}
    
    The email should be personalized, friendly, and focused on requesting a backlink for a '[some crypto currency] IRA' related article.
    Highlight the mutual benefits of backlinking and keep the tone professional yet approachable.
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
        # Fallback to a template
        return generate_fallback_email(website, user)

def generate_fallback_email(website, user):
    return f"""
    Dear {website.author_name},

    I hope this email finds you well. My name is {user.name}, and I recently came across your excellent article on {website.url}. I was impressed by your insights on [topic].

    I'm reaching out because I've written an article about [some crypto currency] IRAs that I believe would be valuable to your readers. Given your expertise in [related field], I thought you might be interested in linking to it.

    If you're open to the idea, I'd be happy to share the article with you. It could provide your readers with additional information on [specific aspect of crypto IRAs].

    Thank you for your time and consideration. I look forward to hearing from you.

    Best regards,
    {user.name}
    """

def generate_followup_email(website, attempt, user_id):
    user = User.query.get(user_id)
    if not user:
        print(f"User with id {user_id} not found")
        return None

    prompt = f"""
    Create a follow-up email for the website {website.url}.
    Author Name: {website.author_name}
    Email: {website.author_email}
    Attempt: {attempt}
    Sender Name: {user.name}
    Sender Email: {user.email}
    
    This is a follow-up to our previous request for a backlink for a '[some crypto currency] IRA' related article.
    Be polite, remind them of the previous email, and emphasize the mutual benefits.
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
        print(f"Error generating follow-up email with Anthropic API: {str(e)}")
        # Fallback to a template
        return generate_fallback_followup_email(website, attempt, user)

def generate_fallback_followup_email(website, attempt, user):
    return f"""
    Dear {website.author_name},

    I hope this email finds you well. My name is {user.name}, and I recently came across your excellent article on {website.url}. I was impressed by your insights on [topic].

    I'm reaching out because I've written an article about [some crypto currency] IRAs that I believe would be valuable to your readers. Given your expertise in [related field], I thought you might be interested in linking to it.

    If you're open to the idea, I'd be happy to share the article with you. It could provide your readers with additional information on [specific aspect of crypto IRAs].

    Thank you for your time and consideration. I look forward to hearing from you.

    Best regards,
    {user.name}
    """
