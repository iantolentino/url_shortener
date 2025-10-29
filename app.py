import os
import secrets
import re
from datetime import datetime, timezone
from urllib.parse import urlparse
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import requests

app = Flask(__name__)
app.config.from_object('config.Config')

# Initialize database
db = SQLAlchemy(app)

class ShortenedURL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(2048), nullable=False)
    short_code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    custom_alias = db.Column(db.String(50), unique=True, nullable=True)
    clicks = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_accessed = db.Column(db.DateTime, nullable=True)
    title = db.Column(db.String(200), nullable=True)
    is_custom = db.Column(db.Boolean, default=False)

class ClickEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    short_code = db.Column(db.String(10), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    referrer = db.Column(db.String(500), nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    country = db.Column(db.String(100), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'short_code': self.short_code,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'referrer': self.referrer,
            'timestamp': self.timestamp.isoformat(),
            'country': self.country
        }

def generate_short_code(length=6):
    """Generate a random short code"""
    return secrets.token_urlsafe(length)[:length]

def is_valid_url(url):
    """
    Validate URL format
    """
    try:
        result = urlparse(url)
        
        # Basic checks
        if not result.scheme and not result.netloc:
            # If no scheme and no netloc, try adding https://
            url = 'https://' + url
            result = urlparse(url)
        
        # Check if we have at least scheme and netloc
        if not all([result.scheme, result.netloc]):
            return False, "Invalid URL format"
        
        # Check scheme
        if result.scheme not in ['http', 'https']:
            return False, "URL must start with http:// or https://"
        
        # Check netloc (domain)
        if not result.netloc:
            return False, "Invalid domain"
        
        # Basic domain validation
        if '.' not in result.netloc:
            return False, "Invalid domain name"
        
        return True, url
        
    except Exception as e:
        return False, f"Invalid URL: {str(e)}"

def get_url_title(url):
    """Extract title from URL (optional feature)"""
    try:
        response = requests.get(url, timeout=5)
        if '<title>' in response.text:
            title_start = response.text.find('<title>') + 7
            title_end = response.text.find('</title>', title_start)
            if title_end > title_start:
                title = response.text[title_start:title_end].strip()
                return title[:197] + '...' if len(title) > 200 else title
    except:
        pass
    return 'No Title'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/shorten', methods=['POST'])
def shorten_url():
    original_url = request.form.get('url', '').strip()
    custom_alias = request.form.get('custom_alias', '').strip()
    
    if not original_url:
        flash('Please enter a URL', 'error')
        return redirect(url_for('index'))
    
    # Validate URL
    is_valid, validated_url_or_error = is_valid_url(original_url)
    if not is_valid:
        flash(validated_url_or_error, 'error')
        return redirect(url_for('index'))
    
    original_url = validated_url_or_error  # This now contains the properly formatted URL
    
    # Validate custom alias if provided
    if custom_alias:
        if not re.match(r'^[a-zA-Z0-9_-]+$', custom_alias):
            flash('Custom alias can only contain letters, numbers, hyphens, and underscores', 'error')
            return redirect(url_for('index'))
        
        if len(custom_alias) < 2 or len(custom_alias) > 30:
            flash('Custom alias must be between 2 and 30 characters', 'error')
            return redirect(url_for('index'))
        
        if ShortenedURL.query.filter_by(custom_alias=custom_alias).first():
            flash('Custom alias already exists. Please choose another one.', 'error')
            return redirect(url_for('index'))
        
        short_code = custom_alias
        is_custom = True
    else:
        # Generate unique short code
        short_code = generate_short_code()
        while ShortenedURL.query.filter_by(short_code=short_code).first():
            short_code = generate_short_code()
        is_custom = False
    
    # Get page title (optional)
    title = get_url_title(original_url)
    
    # Create new shortened URL
    new_url = ShortenedURL(
        original_url=original_url,
        short_code=short_code,
        custom_alias=custom_alias if custom_alias else None,
        title=title,
        is_custom=is_custom
    )
    
    try:
        db.session.add(new_url)
        db.session.commit()
        
        short_url = f"{request.host_url}{short_code}"
        return render_template('index.html', short_url=short_url, original_url=original_url)
    
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while creating the short URL. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/<short_code>')
def redirect_to_original(short_code):
    url_entry = ShortenedURL.query.filter_by(short_code=short_code).first()
    
    if not url_entry:
        flash('URL not found', 'error')
        return redirect(url_for('index'))
    
    # Update click count and last accessed time
    url_entry.clicks += 1
    url_entry.last_accessed = datetime.now(timezone.utc)
    
    # Log click event
    click_event = ClickEvent(
        short_code=short_code,
        ip_address=request.environ.get('HTTP_X_REAL_IP', request.remote_addr),
        user_agent=request.headers.get('User-Agent'),
        referrer=request.headers.get('Referer')
    )
    
    try:
        db.session.add(click_event)
        db.session.commit()
    except:
        db.session.rollback()
    
    return redirect(url_entry.original_url)

@app.route('/api/shorten', methods=['POST'])
def api_shorten_url():
    """API endpoint for URL shortening"""
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400
    
    original_url = data['url'].strip()
    custom_alias = data.get('custom_alias', '').strip()
    
    # Validate URL
    is_valid, validated_url_or_error = is_valid_url(original_url)
    if not is_valid:
        return jsonify({'error': validated_url_or_error}), 400
    
    original_url = validated_url_or_error
    
    # Validate custom alias if provided
    if custom_alias:
        if not re.match(r'^[a-zA-Z0-9_-]+$', custom_alias):
            return jsonify({'error': 'Custom alias can only contain letters, numbers, hyphens, and underscores'}), 400
        
        if len(custom_alias) < 2 or len(custom_alias) > 30:
            return jsonify({'error': 'Custom alias must be between 2 and 30 characters'}), 400
        
        if ShortenedURL.query.filter_by(custom_alias=custom_alias).first():
            return jsonify({'error': 'Custom alias already exists'}), 400
        
        short_code = custom_alias
        is_custom = True
    else:
        short_code = generate_short_code()
        while ShortenedURL.query.filter_by(short_code=short_code).first():
            short_code = generate_short_code()
        is_custom = False
    
    title = get_url_title(original_url)
    
    new_url = ShortenedURL(
        original_url=original_url,
        short_code=short_code,
        custom_alias=custom_alias if custom_alias else None,
        title=title,
        is_custom=is_custom
    )
    
    try:
        db.session.add(new_url)
        db.session.commit()
        
        short_url = f"{request.host_url}{short_code}"
        
        return jsonify({
            'original_url': original_url,
            'short_url': short_url,
            'short_code': short_code,
            'clicks': 0,
            'title': title
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create short URL'}), 500

@app.route('/dashboard')
def dashboard():
    """Dashboard to view all shortened URLs"""
    urls = ShortenedURL.query.order_by(ShortenedURL.created_at.desc()).all()
    total_clicks = db.session.query(func.sum(ShortenedURL.clicks)).scalar() or 0
    total_urls = ShortenedURL.query.count()
    
    return render_template('dashboard.html', 
                         urls=urls, 
                         total_clicks=total_clicks, 
                         total_urls=total_urls)

@app.route('/analytics/<short_code>')
def analytics(short_code):
    """Analytics for a specific short URL"""
    url_entry = ShortenedURL.query.filter_by(short_code=short_code).first()
    
    if not url_entry:
        flash('URL not found', 'error')
        return redirect(url_for('dashboard'))
    
    # Get click events for this short code
    click_events = ClickEvent.query.filter_by(short_code=short_code)\
                                  .order_by(ClickEvent.timestamp.desc())\
                                  .limit(100)\
                                  .all()
    
    # Basic analytics data
    clicks_by_day = db.session.query(
        func.date(ClickEvent.timestamp),
        func.count(ClickEvent.id)
    ).filter_by(short_code=short_code)\
     .group_by(func.date(ClickEvent.timestamp))\
     .all()
    
    return render_template('analytics.html',
                         url_entry=url_entry,
                         click_events=click_events,
                         clicks_by_day=clicks_by_day)

@app.route('/api/analytics/<short_code>')
def api_analytics(short_code):
    """API endpoint for analytics data"""
    url_entry = ShortenedURL.query.filter_by(short_code=short_code).first()
    
    if not url_entry:
        return jsonify({'error': 'URL not found'}), 404
    
    # Get recent click events
    recent_clicks = ClickEvent.query.filter_by(short_code=short_code)\
                                   .order_by(ClickEvent.timestamp.desc())\
                                   .limit(50)\
                                   .all()
    
    return jsonify({
        'short_code': url_entry.short_code,
        'original_url': url_entry.original_url,
        'total_clicks': url_entry.clicks,
        'created_at': url_entry.created_at.isoformat(),
        'last_accessed': url_entry.last_accessed.isoformat() if url_entry.last_accessed else None,
        'title': url_entry.title,
        'recent_clicks': [click.to_dict() for click in recent_clicks]
    })

@app.route('/api/stats')
def api_stats():
    """API endpoint for overall statistics"""
    total_urls = ShortenedURL.query.count()
    total_clicks = db.session.query(func.sum(ShortenedURL.clicks)).scalar() or 0
    most_popular = ShortenedURL.query.order_by(ShortenedURL.clicks.desc()).first()
    
    stats = {
        'total_urls': total_urls,
        'total_clicks': total_clicks,
        'most_popular': {
            'short_code': most_popular.short_code if most_popular else None,
            'clicks': most_popular.clicks if most_popular else 0,
            'original_url': most_popular.original_url if most_popular else None
        }
    }
    
    return jsonify(stats)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)