"""
Configuration template for Job Market Intelligence Dashboard
Copy this file to config.py and fill in your values
DO NOT commit config.py to version control!
"""

# Email configuration
RESEND_API_KEY = "your_resend_api_key_here"
EMAIL_RECIPIENT = "your.email@example.com"
EMAIL_FROM = "Job Radar <onboarding@resend.dev>"

# Scraping configuration
MAX_RESULTS_PER_SOURCE = 30
MAX_ENRICH_DESCRIPTIONS = 25
RATE_LIMIT_DELAY = 1.5  # seconds between requests
MAX_PAGES = 3  # max pages to scrape per term

# Application tracking
APPLICATIONS_FILE = 'applications.json'
