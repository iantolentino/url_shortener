# URL Shortener Service

A feature-rich, self-hosted URL shortener service built with Flask and SQLAlchemy. This application allows you to create shortened URLs, track analytics, and manage your links through a web interface or REST API.

## Features 

- **URL Shortening**: Convert long URLs into short, manageable links
- **Custom Aliases**: Create custom short codes for your URLs
- **Analytics Dashboard**: Track clicks, referrers, and user agents
- **REST API**: Programmatic access to all features
- **Click Tracking**: Detailed click analytics with geographic data
- **URL Validation**: Automatic URL formatting and validation
- **Title Extraction**: Automatic page title extraction
- **Responsive Design**: Mobile-friendly web interface

## Installation

### Prerequisites

- Python 3.7+
- pip (Python package manager)
- SQLite (default) or other supported database

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd url-shortener

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configuration

Create a `config.py` file in the root directory:

```python
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///urls.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
```

### Step 3: Initialize Database

```bash
python app.py
```

The database will be automatically created when you first run the application.

## Usage

### Web Interface

1. Start the server:
```bash
python app.py
```

2. Open your browser to `http://localhost:5000`

3. Enter a URL to shorten:
   - Paste your long URL in the input field
   - Optionally provide a custom alias
   - Click "Shorten URL"

### API Usage

The service provides a REST API for programmatic access:

#### Shorten a URL

```bash
curl -X POST http://localhost:5000/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/very-long-url"}'
```

Response:
```json
{
  "original_url": "https://example.com/very-long-url",
  "short_url": "http://localhost:5000/abc123",
  "short_code": "abc123",
  "clicks": 0,
  "title": "Example Domain"
}
```

#### With Custom Alias

```bash
curl -X POST http://localhost:5000/api/shorten \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/very-long-url",
    "custom_alias": "my-link"
  }'
```

#### Get Analytics

```bash
curl http://localhost:5000/api/analytics/abc123
```

#### Get Overall Statistics

```bash
curl http://localhost:5000/api/stats
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/shorten` | Shorten URL (web form) |
| POST | `/api/shorten` | Shorten URL (API) |
| GET | `/<short_code>` | Redirect to original URL |
| GET | `/dashboard` | View all shortened URLs |
| GET | `/analytics/<short_code>` | View analytics for a short URL |
| GET | `/api/analytics/<short_code>` | Get analytics data (API) |
| GET | `/api/stats` | Get overall statistics (API) |

## Database Models

### ShortenedURL
- `id`: Primary key
- `original_url`: The original long URL
- `short_code`: Unique short code for redirection
- `custom_alias`: Optional custom alias
- `clicks`: Total click count
- `created_at`: Creation timestamp
- `last_accessed`: Last access timestamp
- `title`: Extracted page title
- `is_custom`: Whether a custom alias was used

### ClickEvent
- `id`: Primary key
- `short_code`: Associated short code
- `ip_address`: Visitor IP address
- `user_agent`: Visitor browser/device info
- `referrer`: Referral source
- `timestamp`: Click timestamp
- `country`: Geographic location (if available)

## URL Validation

The service automatically:
- Validates URL format
- Adds `https://` prefix if missing
- Ensures URLs use http or https protocols
- Checks domain validity

## Custom Alias Rules

- 2-30 characters long
- Only letters, numbers, hyphens, and underscores
- Must be unique

## Deployment

### Production Deployment

For production deployment, consider:

1. **Use a production WSGI server**:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

2. **Set a strong secret key**:
```bash
export SECRET_KEY='your-very-secure-secret-key'
```

3. **Use a production database**:
```bash
export DATABASE_URL='postgresql://username:password@localhost/url_shortener'
```

4. **Configure reverse proxy** (nginx example):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Environment Variables

- `SECRET_KEY`: Flask secret key for session security
- `DATABASE_URL`: Database connection URL
- `DEBUG`: Enable debug mode (not recommended for production)

## Security Features

- URL validation and sanitization
- SQL injection protection through SQLAlchemy
- XSS protection through template escaping
- Secure redirects with validation

## Error Handling

- 404: URL not found
- 500: Internal server error
- Custom error pages for better user experience

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For support and questions:
1. Check the API documentation
2. Review the code comments
3. Create an issue in the repository

## Roadmap

- [ ] User authentication and private URLs
- [ ] QR code generation
- [ ] Bulk URL shortening
- [ ] Advanced analytics with charts
- [ ] URL expiration dates
- [ ] API rate limiting
- [ ] Export analytics data

---

Built with Flask, SQLAlchemy, and modern web standards.

