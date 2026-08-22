# 🎯 Job Market Intelligence Dashboard

An automated job market monitoring and analysis system for cybersecurity/IAM opportunities in Portugal. This tool scrapes multiple job boards, enriches job descriptions, applies intelligent scoring, and delivers a weekly HTML dashboard with actionable insights.

![Dashboard Preview](docs/dashboard-preview.png)

## 🚀 Features

- **Multi-Source Scraping**: Aggregates jobs from 4 sources (LinkedIn/Indeed via JobSpy, ITJobs.pt, Net-Empregos.com, Landing.jobs)
- **Intelligent Enrichment**: Automatically fetches full job descriptions from ITJobs using JSON-LD structured data
- **Smart Scoring**: 50+ security keywords with contextual weighting (title vs description, IAM-specific bonuses)
- **Application Tracking**: Persistent tracking of submitted applications with deterministic hashing
- **Interactive Dashboard**: HTML dashboard with filtering by priority, source, and search
- **Automated Delivery**: Weekly email notifications with CSV export and HTML dashboard
- **Cron Integration**: Scheduled execution every Friday at 19:00 (Portugal time)
- **Auto-Cleanup**: Automatically removes files older than 30 days

## 📊 How It Works

The system runs as an automated pipeline:

1. **Cron Trigger** → Executes every Friday at 19:00 (Portugal time)
2. **Scrape JobSpy** → Collects jobs from LinkedIn and Indeed (5 search terms × 20 jobs)
3. **Scrape ITJobs.pt** → Custom scraper for Portuguese IT job board (4 terms × 30 jobs)
4. **Enrich Descriptions** → Fetches full job descriptions via JSON-LD structured data (max 25)
5. **Scrape Net-Empregos** → Portuguese general job board (5 terms × 30 jobs, with pagination)
6. **Scrape Landing.jobs** → Tech-focused job board (4 terms × 30 jobs)
7. **Deduplicate Jobs** → Uses deterministic MD5 hashing to remove duplicates across sources
8. **Apply Scoring Algorithm** → Evaluates each job based on 50+ security keywords
9. **Filter & Prioritize** → Classifies jobs into High/Medium/Low priority
10. **Generate Outputs** → Creates CSV export and interactive HTML dashboard
11. **Send Email** → Delivers dashboard with attachments via Resend API
12. **Cleanup Old Files** → Removes CSV/HTML files older than 30 days

## 🎯 Scoring System

The scoring algorithm evaluates jobs based on:

### Positive Signals (Points Added)

**IAM Keywords:**
- Identity and Access Management: +25 points
- SAML: +15 points
- OIDC: +15 points
- OAuth: +12 points
- Single Sign-On/SSO: +15-20 points
- Active Directory: +12 points
- Azure AD/Entra ID: +15 points
- Okta: +12 points
- Ping Identity: +20 points
- CyberArk: +15 points
- Privileged Access/PAM: +12-18 points
- Identity Governance: +18 points

**Security Operations:**
- Incident Response: +15 points
- Security Operations: +12 points
- SOC: +10 points
- SIEM: +12 points
- Sentinel: +15 points
- Splunk: +12 points
- Threat Detection: +12 points
- Vulnerability Management: +10 points
- Security Engineer: +15 points

**Automation:**
- Python: +10 points
- PowerShell: +10 points
- Bash: +10 points
- Automation: +8 points
- REST API: +8 points
- Scripting: +8 points

**Structural Bonuses:**
- Remote work: +15 points
- Hybrid work: +8 points
- Portugal location: +10 points
- IAM in title: +15 points (additional)
- Keywords in title: 1.5x multiplier

### Negative Signals (Points Deducted)

**Seniority Mismatch:**
- "Director", "VP", "Head of": -20 points
- 7-10 years experience required: -20 points

**Junior Roles:**
- "Junior", "Intern", "Trainee": -15 points

**Wrong Domain:**
- AML: -30 points
- KYC: -30 points
- SAP: -30 points
- Mainframe: -30 points
- Help Desk: -30 points
- Service Desk: -30 points

### Priority Classification

- 🟢 **ALTA** (70-100 points): Apply today - high priority
- 🟡 **MÉDIA** (40-69 points): Apply this week - medium priority
- 🔴 **BAIXA** (0-39 points): Ignore - low priority

## 🛠️ Tech Stack

- **Language**: Python 3.13
- **Scraping**: BeautifulSoup4, requests
- **Job APIs**: JobSpy (LinkedIn/Indeed aggregator)
- **Data Processing**: pandas
- **Email Delivery**: Resend API
- **Dashboard**: HTML/CSS/JavaScript (vanilla)
- **Scheduling**: cron (Linux)
- **Web Server**: Python http.server (local dashboard)

## 📦 Installation

### Prerequisites

- Python 3.11+
- pip
- Linux environment (cron support)

### Setup

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/job-market-intelligence.git
cd job-market-intelligence
```


2.  **Create virtual environment**

```bash
python -m venv jobspy-env
source jobspy-env/bin/activate
```

3.  **Install dependencies**

```bash
pip install jobspy pandas beautifulsoup4 requests resend
```

4.  **Configure environment**

```bash
cp config.example.py config.py
# Edit config.py with your Resend API key and email
```

5.  **Test the system**

```bash
python job_radar.py
```

6.  **Set up cron job**

```bash
crontab -e
# Add: 0 19 * * 5 cd /path/to/job-market-intelligence && /path/to/python job_radar.py
```

## 🖥️ Local Dashboard Server

Start a local web server to access the dashboard:

```bash
python dashboard_server.py
```

Access at: `http://localhost:8080`

The server automatically redirects to the most recent dashboard file.

## 📁 Project Structure


job-market-intelligence/
├── job_radar.py              # Main scraping and scoring script
├── dashboard_server.py       # Local web server for dashboard
├── applications.json         # Persistent application tracking
├── config.py                 # Configuration (API keys, email)
├── config.example.py         # Configuration template
├── jobs_*.csv               # Generated CSV exports
├── jobs_*.html              # Generated HTML dashboards
└── README.md                # This file

## 🔐 Configuration

Create a `config.py` file based on `config.example.py`:

```python
# Email configuration
RESEND_API_KEY = "your_resend_api_key"
EMAIL_RECIPIENT = "your@email.com"
EMAIL_FROM = "Job Radar <onboarding@resend.dev>"

# Scraping configuration
MAX_RESULTS_PER_SOURCE = 30
MAX_ENRICH_DESCRIPTIONS = 25
RATE_LIMIT_DELAY = 1.5  # seconds between requests
```


## 🎓 Learning Outcomes

Building this project taught me:

*   **Web Scraping Best Practices**: Rate limiting, user-agent rotation, anti-bot detection
*   **HTML Parsing Strategies**: Different sites require different approaches (JSON-LD, CSS selectors, encoding handling)
*   **Scoring System Design**: How to weight features, handle missing data, avoid bias
*   **Automation & Scheduling**: Cron jobs, error handling, idempotent operations
*   **Data Persistence**: Deterministic hashing for tracking across executions
*   **API Integration**: Email delivery services, structured data extraction

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome! Feel free to:

*   Open an issue for bugs or feature requests
*   Submit a pull request for improvements
*   Fork and adapt for your own job search

## 📄 License

MIT License - feel free to use and modify for your own purposes.

## ⚠️ Disclaimer

This tool is for personal use in job market research. Please respect:

*   Terms of service of job boards
*   Rate limits and robots.txt
*   Privacy of job seekers and employers
*   Anti-scraping measures

## 🔗 Connect

*   **LinkedIn**: [linkedin.com/in/gonçalo-marçalo-57a996190](https://www.linkedin.com/in/gon%C3%A7alo-mar%C3%A7alo-57a996190)
*   **Email**: [gonsaloam@outlook.pt](mailto:gonsaloam@outlook.pt)

* * *

**Built with ❤️ for the cybersecurity community**
