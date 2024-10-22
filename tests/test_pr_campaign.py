from flask import jsonify, request
from models import db, Campaign, Author, OutreachAttempt

@app.route('/create_pr_campaign', methods=['POST'])
def create_pr_campaign():
    data = request.json
    new_campaign = Campaign(
        user_id=data['user_id'],
        campaign_type='pr',
        name=data['name'],
        topic=data['topic'],
        press_release_url=data.get('press_release_url'),
        press_release_content=data.get('press_release_content')
    )
    db.session.add(new_campaign)
    db.session.commit()

    # Create an author
    new_author = Author(
        website_id=data['website_id'],
        name=data['author_name'],
        email=data['author_email']
    )
    db.session.add(new_author)
    db.session.commit()

    # Create an outreach attempt
    new_outreach = OutreachAttempt(
        campaign_id=new_campaign.id,
        website_id=data['website_id'],
        author_id=new_author.id
    )
    db.session.add(new_outreach)
    db.session.commit()

    return jsonify({
        'message': 'PR campaign created successfully',
        'campaign_id': new_campaign.id,
        'author_id': new_author.id,
        'outreach_attempt_id': new_outreach.id
    }), 201