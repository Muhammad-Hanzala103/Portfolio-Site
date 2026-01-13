# Muhammad Hanzala Portfolio

A production-grade portfolio and freelancing platform built with Flask.

## Features

- 🎨 **Digital Alchemy Design** - Glassmorphism UI with dark theme
- 📱 **Responsive** - Mobile-first with hamburger menu
- 🔐 **Authentication** - Login, registration, password reset
- 📁 **Media Uploads** - Image thumbnails, WebP, video support
- 💳 **Stripe Payments** - Service checkout integration
- 📊 **Analytics** - Visit tracking and dashboard charts
- 📝 **Blog** - CKEditor rich text, categories, tags
- 📧 **Contact** - Spam-protected contact form

## Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd Portfolio-Site

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your settings

# Initialize database
flask db upgrade

# Seed with sample data
flask seed

# Run development server
flask run
```

## Environment Variables

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost:5432/portfolio
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
STRIPE_PUBLIC_KEY=pk_test_xxx
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STORAGE_BACKEND=local  # or 's3'
# For S3:
S3_BUCKET=your-bucket
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
```

## CLI Commands

```bash
flask create-admin  # Create admin user interactively
flask seed          # Seed database with sample data
flask db upgrade    # Run migrations
```

## Admin Credentials (Default)

```
Username: hanzala
Email: hani75384@gmail.com
Password: ChangeMe!2025
```

## Deployment

### Option A: Render (Recommended)

1. Create account at [render.com](https://render.com)
2. Connect GitHub repository
3. Create new Web Service:
   - Build Command: `pip install -r requirements.txt && flask db upgrade`
   - Start Command: `gunicorn app:app`
4. Add Postgres database addon
5. Set environment variables
6. Deploy!

### Option B: Docker

```bash
docker build -t portfolio .
docker run -p 5000:5000 --env-file .env portfolio
```

### Option C: Railway/Fly.io

Similar to Render - connect repo, set env vars, deploy.

## Stripe Webhook Setup

1. Install Stripe CLI: https://stripe.com/docs/stripe-cli
2. Forward webhooks locally:
   ```bash
   stripe listen --forward-to localhost:5000/payment/stripe/webhook
   ```
3. Use the webhook secret in `.env`

For production: Add webhook endpoint in Stripe Dashboard pointing to:
`https://your-domain.com/payment/stripe/webhook`

## Project Structure

```
Portfolio-Site/
├── app.py              # Main Flask application
├── models.py           # SQLAlchemy models
├── routes/
│   ├── main.py         # Public routes
│   ├── admin.py        # Admin dashboard
│   ├── api.py          # REST API
│   └── payment.py      # Stripe integration
├── templates/          # Jinja2 templates
├── static/
│   ├── css/            # Stylesheets
│   └── uploads/        # User uploads
├── utils/
│   └── uploads.py      # Media processing
└── tests/              # Pytest tests
```

## Testing

```bash
pytest tests/ -v
pytest tests/ --cov=. --cov-report=html
```

## Owner

**Muhammad Hanzala**  
Some people call me Hani.

---

© 2025 Muhammad Hanzala. All Rights Reserved.
