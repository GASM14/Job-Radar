# ============================================
# JOB RADAR CONFIGURATION
# ============================================

# Email configuration
RESEND_API_KEY = "your_resend_api_key"
EMAIL_RECIPIENT = "marianajacobleitao@gmail.com"  # ou o teu se for tu a receber
EMAIL_FROM = "Job Radar <onboarding@resend.dev>"

# ============================================
# ACTIVE PROFILE - change to switch profiles
# ============================================
ACTIVE_PROFILE = "mariana"  # "goncalo" or "mariana"

# ============================================
# PROFILE: Gonçalo (IAM/Cybersecurity)
# ============================================
PROFILES = {
    "goncalo": {
        "name": "Gonçalo - IAM & Cybersecurity",
		"email_recipient": "gonsaloam@outlook.pt",
        "search_terms": [
            "Identity and Access Management",
            "IAM Engineer",
            "CyberArk",
            "Entra ID",
            "SAML OIDC",
            "Privileged Access Management",
            "Security Operations",
        ],
        "locations": ["Portugal", "Lisbon", "Porto", "Remote"],
        "scoring": {
            "positive_keywords": {
                "Identity and Access Management": 25,
                "SAML": 15, "OIDC": 15, "OAuth": 12,
                "Single Sign-On": 15, "SSO": 15,
                "Active Directory": 12, "Azure AD": 15, "Entra ID": 15,
                "Okta": 12, "Ping Identity": 20, "CyberArk": 15,
                "Privileged Access": 18, "PAM": 15,
                "Identity Governance": 18,
                "Incident Response": 15, "SOC": 10, "SIEM": 12,
                "Sentinel": 15, "Splunk": 12,
                "Python": 10, "PowerShell": 10, "Bash": 10,
                "REST API": 8, "Scripting": 8,
            },
            "negative_keywords": {
                "AML": -30, "KYC": -30, "SAP": -30,
                "Mainframe": -30, "Help Desk": -30, "Service Desk": -30,
                "Director": -20, "VP": -20, "Head of": -20,
                "Junior": -15, "Intern": -15, "Trainee": -15,
            },
        },
    },

    # ============================================
    # PROFILE: Mariana (Healthcare Project Coordination)
    # ============================================
    "mariana": {
        "name": "Mariana - Healthcare Project Coordination & Operations",
       	"email_recipient": "marianajacobleitao@gmail.com", 
        "search_terms": [
            "Project Coordinator Healthcare",
            "Coordenador de Projetos Saúde",
            "Operations Coordinator Health",
            "Clinical Operations",
            "Process Improvement Healthcare",
            "Melhoria Processos Saúde",
            "Project Management Office Healthcare",
            "Junior Project Manager Pharma",
            "Clinical Trial Assistant",
            "Healthcare Consultant",
            "Hospital Operations",
            "Pharmaceutical Operations",
        ],
        "locations": [
            "Portugal", "Lisboa", "Lisbon", "Oeiras", "Amadora",
            "Cascais", "Setúbal", "Porto", "Remote", "Remoto",
        ],
        "target_companies": [
            # Tier 1 - Multinacionais Pharma (salários altos, inglês)
            "Roche", "Novartis", "GSK", "AstraZeneca", "MSD", "Merck",
            "Pfizer", "Sanofi", "Bayer", "Bristol-Myers Squibb", "BMS",
            "IQVIA", "Syneos Health", "ICON plc", "Parexel", "PRA Health",
            # Tier 2 - Grupos de saúde privados PT
            "CUF", "Lusíadas", "Luz Saúde", "HPA Saúde", "Holon",
            "Unilabs", "Jaba Recordati", "Bial", "Bluepharma",
            # Tier 3 - Consultoria Life Sciences
            "Deloitte", "PwC", "EY", "KPMG", "Accenture",
        ],
        "scoring": {
            # Keywords positivas (soma pontos)
            "positive_keywords": {
                # Core roles (ALTA relevância)
                "Project Coordinator": 30,
                "Coordenador de Projetos": 30,
                "Project Management": 25,
                "Gestão de Projetos": 25,
                "PMO": 25,
                "Project Management Office": 25,
                "Operations Coordinator": 28,
                "Coordenador de Operações": 28,
                "Process Improvement": 25,
                "Melhoria de Processos": 25,
                "Continuous Improvement": 22,
                "Lean": 18,
                
                # Healthcare-specific (bonus setor)
                "Healthcare": 20,
                "Saúde": 20,
                "Hospital": 18,
                "Clínica": 15, "Clinic": 15,
                "Pharmaceutical": 20,
                "Farmacêutica": 20,
                "Pharma": 18,
                "Clinical Operations": 25,
                "Clinical Trial": 22,
                "CTA": 20,
                "Clinical Research": 22,
                "CRO": 20,
                "Life Sciences": 18,
                
                # Transferable skills
                "Stakeholder": 12,
                "Stakeholder Management": 15,
                "Project Planning": 15,
                "Risk Management": 12,
                "Gestão de Riscos": 12,
                "Agile": 10,
                "Scrum": 10,
                "Kanban": 8,
                "MS Project": 10,
                "Jira": 8,
                "Confluence": 8,
                "ServiceNow": 10,
                "SAP": 8,  # apenas em contexto PM/ops, não functional
                "Supply Chain": 15,
                "Inventory Management": 12,
                "Quality Management": 12,
                "GCP": 15,  # Good Clinical Practice (pharma)
                "GMP": 15,  # Good Manufacturing Practice
                
                # Coordination skills
                "Coordination": 12,
                "Coordenação": 12,
                "Multidisciplinary": 10,
                "Cross-functional": 12,
                "Team Leadership": 12,
                "Problem Solving": 8,
            },
            
            # Keywords NEGATIVAS (subtrai pontos ou descarta)
            "negative_keywords": {
                # Laboratorial (NÃO quer)
                "Laboratório": -100,
                "Lab Technician": -100,
                "Laboratory Technician": -100,
                "Análises Clínicas": -100,
                "Técnico de Laboratório": -100,
                "Quality Control Lab": -100,
                "Wet Lab": -100,
                "Bench Scientist": -100,
                
                # Atendimento puro (NÃO quer)
                "Atendimento ao Público": -80,
                "Customer Service": -60,
                "Balção": -80,
                "Rececionista": -80,
                "Front Desk": -70,
                "Call Center": -80,
                "Contact Center": -70,
                
                # Finanças/Contabilidade (NÃO quer)
                "Contabilista": -80,
                "Accountant": -80,
                "Controller": -60,
                "Tesouraria": -80,
                "Treasury": -70,
                "Bookkeeper": -80,
                "Audit Senior": -50,
                
                # Assuntos Regulamentares PUROS (NÃO quer)
                "Regulatory Affairs": -60,
                "Assuntos Regulamentares": -60,
                "Regulatory Submission": -70,
                "Regulatory Specialist": -60,
                "Drug Registration": -70,
                
                # IT/Programação (NÃO quer)
                "Software Engineer": -100,
                "Developer": -90,
                "Programador": -90,
                "Backend Developer": -100,
                "Frontend Developer": -100,
                "Full Stack": -100,
                "Data Scientist": -80,
                "DevOps": -90,
                
                # Farmácia de balcão (NÃO quer - é o que está a sair)
                "Farmacêutico de Oficina": -50,
                "Community Pharmacist": -50,
                "Dispensing Pharmacist": -50,
                "Retail Pharmacist": -50,
                
                # Vendas comerciais (NÃO quer)
                "Sales Representative": -70,
                "Medical Delegate": -70,
                "Delegado de Informação Médica": -70,
                "DIM": -60,
                "Sales Manager": -60,
                "Account Manager Pharma": -50,
                
                # Seniority mismatch
                "Director": -30,
                "VP": -40,
                "Head of": -30,
                "C-Level": -40,
                "10+ years": -25,
                "10 years experience": -25,
                "15 years": -30,
            },
        },
        
        # Bónus estruturais
        "structural_bonuses": {
            "remote": 15,
            "hybrid": 10,
            "portugal": 12,
            "target_company": 30,  # Trabalhar em Tier 1/Tier 2 company
            "keyword_in_title": 1.5,  # Multiplicador
        },
    },
}

# ============================================
# Scraping configuration
# ============================================
MAX_RESULTS_PER_SOURCE = 30
MAX_ENRICH_DESCRIPTIONS = 25
RATE_LIMIT_DELAY = 1.5

# ============================================
# Scoring thresholds
# ============================================
THRESHOLD_HIGH = 70      # 🟢 ALTA - Apply today
THRESHOLD_MEDIUM = 40    # 🟡 MÉDIA - Apply this week
THRESHOLD_LOW = 0        # 🔴 BAIXA - Ignore
