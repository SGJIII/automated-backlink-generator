import os
from anthropic import Anthropic
from models import Website, User

anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def generate_outreach_email_content(website, user_id, sender_name, company_name, company_profile, campaign, author_name, is_followup=False):
    user = User.query.get(user_id)
    if not user:
        print(f"User with id {user_id} not found")
        return None

    recipient_first_name = author_name.split()[0]

    if campaign.campaign_type == 'seo':
        prompt = f"""
        Create an {'follow-up ' if is_followup else ''}outreach email for the website {website.url}.
        Recipient Name: {recipient_first_name}
        Sender Name: {sender_name}
        Sender Email: {user.email}
        Company Name: {company_name}
        Company Profile: {company_profile}
        Article URL: {campaign.target_url}
        
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
    else:  # PR campaign
        prompt = f"""
        Create an {'follow-up ' if is_followup else ''}outreach email for a PR campaign targeting {website.author_name} from {website.url}.
        Recipient Name: {recipient_first_name}
        Sender Name: {sender_name}
        Sender Email: {user.email}
        Company Name: {company_name}
        Company Profile: {company_profile}
        Press Release: {campaign.press_release}
        
        The email should be personalized, friendly, and focused on pitching the press release to the journalist or news outlet.
        
        Keep the tone professional yet approachable, and use only the recipient's first name when addressing them.
        
        {'If this is a follow-up email, politely remind them about the previous email and express continued interest in coverage.' if is_followup else ''}
        
        The email should:
        1. Start with a brief introduction and mention something specific about the recipient's recent articles or their area of coverage.
        2. Introduce your company briefly.
        3. Pitch the press release, highlighting its newsworthiness and relevance to the recipient's audience.
        4. Offer additional information, interviews, or resources if needed.
        5. Thank them for their time and consideration.
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
        return generate_fallback_email(website, sender_name, company_name, company_profile, campaign, author_name, is_followup)

def generate_fallback_email(website, sender_name, company_name, company_profile, campaign, author_name, is_followup=False):
    recipient_first_name = author_name.split()[0]
    followup_intro = "I hope this email finds you well. I'm following up on my previous message regarding " if is_followup else ""
    
    if campaign.campaign_type == 'seo':
        return f"""
        Dear {recipient_first_name},

        {followup_intro}I hope this email finds you well. My name is {sender_name}, and I recently came across your excellent content on {website.url}. I was particularly impressed by your insights on [mention a specific topic or article from their website].

        I'm reaching out because I work with {company_name}, a company that {company_profile}. We've recently published an article that I believe would be valuable to your readers. The article discusses [brief description of your article topic] and can be found here: {campaign.target_url}

        Given your expertise in [related field], I thought you might be interested in taking a look. If you find the content relevant and helpful, we'd be honored if you'd consider mentioning or referencing it in one of your future posts.

        I'd be happy to provide any additional information or answer any questions you might have about the article or our company.

        Thank you for your time and consideration. I look forward to hearing from you.

        Best regards,
        {sender_name}
        {company_name}
        """
    else:  # PR campaign
        return f"""
        Dear {recipient_first_name},

        {followup_intro}I hope this email finds you well. My name is {sender_name}, and I've been following your insightful coverage of [mention a relevant topic or recent article].

        I'm reaching out on behalf of {company_name}, a company that {company_profile}. We have some exciting news that I believe would be of interest to your readers:

        [Brief summary of the press release]

        Given your expertise in [related field], I thought you might be interested in covering this story. We'd be happy to provide additional information, arrange interviews with key personnel, or offer any other resources you might need for your article.

        If you'd like to learn more, I'd be glad to schedule a brief call or send you our full press release.

        Thank you for your time and consideration. I look forward to the possibility of working with you on this story.

        Best regards,
        {sender_name}
        {company_name}
        """