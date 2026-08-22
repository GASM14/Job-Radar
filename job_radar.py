from jobspy import scrape_jobs
import pandas as pd
from datetime import datetime
import resend
import base64
import requests
from bs4 import BeautifulSoup
import re
import json
import os
import glob
import time  # ⭐ ADICIONAR AQUI
import hashlib # ⭐ ADICIONA NO TOPO DO FICHEIRO (junto aos outros imports)

try:
    import config
except ImportError:
    print("❌ config.py não encontrado! Copia config.example.py para config.py")
    exit(1)

# ========================================
# APPLICATION TRACKING
# ========================================

APPLICATIONS_FILE = config.APPLICATIONS_FILE

def load_applications():
    """Carrega lista de candidaturas já enviadas"""
    try:
        with open(APPLICATIONS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('applied_jobs', [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_applications(applications):
    """Guarda lista de candidaturas"""
    with open(APPLICATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'applied_jobs': applications}, f, indent=2, ensure_ascii=False)

def is_applied(job_id):
    """Verifica se uma vaga já foi candidata"""
    applications = load_applications()
    return any(app['job_id'] == job_id for app in applications)

def get_application_status(job_id):
    """Retorna status da candidatura se existir"""
    applications = load_applications()
    for app in applications:
        if app['job_id'] == job_id:
            return app.get('status', 'applied')
    return None

# ========================================
# ITJOBS.PT SCRAPER (VERSÃO CORRIGIDA)
# ========================================

def scrape_itjobs_pt(search_terms, max_results=50):
    """Scraper customizado para ITJobs.pt"""
    all_jobs = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for term in search_terms:
        try:
            # ⭐ FIX: Adicionado &date=7d para filtrar últimos 7 dias
            search_url = f"https://www.itjobs.pt/pesquisa?q={term.replace(' ', '+')}&search_type=job&date=7d"
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_blocks = soup.find_all('div', class_='block borderless')
            current_date = None
            job_count = 0
            
            for block in job_blocks:
                date_box = block.find('div', class_='date-box')
                if date_box:
                    day = date_box.find('div', class_='d-d')
                    month = date_box.find('div', class_='d-m')
                    if day and month:
                        current_date = f"{day.text.strip()} {month.text.strip()}"
                
                listing = block.find('ul', class_='listing')
                if not listing:
                    continue
                
                job_items = listing.find_all('li')
                
                for item in job_items:
                    if job_count >= max_results:
                        break
                    
                    try:
                        title_elem = item.find('div', class_='list-title')
                        if not title_elem:
                            continue
                        
                        title_link = title_elem.find('a', class_='title')
                        if not title_link:
                            continue
                        
                        title = title_link.get_text(strip=True)
                        job_path = title_link.get('href', '')
                        job_url = f"https://www.itjobs.pt{job_path}" if job_path.startswith('/') else job_path
                        
                        company_elem = item.find('div', class_='list-name')
                        company_link = company_elem.find('a') if company_elem else None
                        company = company_link.get_text(strip=True) if company_link else "Unknown"
                        
                        details_elem = item.find('div', class_='list-details')
                        location = "Portugal"
                        is_remote = False
                        work_model = ""
                        
                        if details_elem:
                            details_text = details_elem.get_text(separator='|', strip=True)
                            location_match = re.search(r'fa-map-marker.*?\|([^|]+)\|', details_text)
                            if location_match:
                                location = location_match.group(1).strip()
                            
                            if 'Remoto' in details_text:
                                work_model = 'Remoto'
                                is_remote = True
                            elif 'Híbrido' in details_text:
                                work_model = 'Híbrido'
                            elif 'Presencial' in details_text:
                                work_model = 'Presencial'
                        
                        job_id = f"itjobs-{hashlib.md5(job_url.encode('utf-8')).hexdigest()[:12]}"
                        all_jobs.append({
                            'id': job_id,
                            'site': 'itjobs',
                            'job_url': job_url,
                            'title': title,
                            'company': company,
                            'location': location,
                            'date_posted': current_date,
                            'is_remote': is_remote,
                            'work_model': work_model,
                            'description': '',
                        })
                        job_count += 1
                    
                    except Exception as e:
                        print(f"⚠️  Erro ao extrair vaga ITJobs: {e}")
                        continue
            
            print(f"✅ ITJobs.pt ({term}): {job_count} vagas encontradas")
        
        except Exception as e:
            print(f"❌ Erro ao fazer scrape do ITJobs.pt ({term}): {e}")
    
    return pd.DataFrame(all_jobs)


# ========================================
# NET-EMPREGOS.COM SCRAPER
# ========================================

def scrape_net_empregos(search_terms, max_results=30):
    """Scraper customizado para Net-Empregos.com com proteção anti-loop"""
    all_jobs = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    for term in search_terms:
        page = 1
        job_count = 0
        max_pages = 3  # ⭐ Limite máximo de páginas para evitar loops
        
        try:
            while job_count < max_results and page <= max_pages:
                print(f"   📄 Página {page} de {term}...")
                search_url = f"https://www.net-empregos.com/pesquisa-empregos.asp?chaves={term.replace(' ', '+')}&categoria=0&zona=0&tipo=0&page={page}"
                
                try:
                    response = requests.get(search_url, headers=headers, timeout=15)
                    response.encoding = 'ISO-8859-1'
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    print(f"   ⚠️  Erro de rede na página {page}: {e}")
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.find_all('div', class_='job-item')
                
                if not job_cards:
                    print(f"   ℹ️  Sem mais vagas na página {page}")
                    break
                
                page_job_count = 0
                for card in job_cards:
                    if job_count >= max_results:
                        break
                    
                    try:
                        title_elem = card.find('h2').find('a', class_='oferta-link')
                        if not title_elem:
                            continue
                        
                        title = title_elem.get_text(strip=True)
                        job_path = title_elem.get('href', '')
                        job_url = f"https://www.net-empregos.com{job_path}" if job_path.startswith('/') else job_path
                        
                        details_div = card.find('div', class_='job-ad-item')
                        if not details_div:
                            continue
                        
                        details = details_div.find_all('li')
                        
                        date_posted = details[0].get_text(strip=True) if len(details) > 0 else None
                        location = details[1].get_text(strip=True) if len(details) > 1 else "Portugal"
                        company = details[3].get_text(strip=True) if len(details) > 3 else "Unknown"
                        
                        is_remote = False
                        work_model = ""
                        text_check = f"{title} {location}".lower()
                        if 'remoto' in text_check or 'remote' in text_check:
                            work_model = 'Remoto'
                            is_remote = True
                        elif 'híbrido' in text_check or 'hibrido' in text_check or 'hybrid' in text_check:
                            work_model = 'Híbrido'
                        
                        job_id = f"netempregos-{hashlib.md5(job_url.encode('utf-8')).hexdigest()[:12]}"
                        
                        all_jobs.append({
                            'id': job_id,
                            'site': 'net-empregos',
                            'job_url': job_url,
                            'title': title,
                            'company': company,
                            'location': location,
                            'date_posted': date_posted,
                            'is_remote': is_remote,
                            'work_model': work_model,
                            'description': '',
                        })
                        job_count += 1
                        page_job_count += 1
                    except Exception as e:
                        print(f"   ⚠️  Erro ao extrair vaga: {e}")
                        continue
                
                print(f"   ✅ Página {page}: {page_job_count} vagas extraídas")
                page += 1
                time.sleep(2)  # Rate limiting mais conservador
            
            print(f"✅ Net-Empregos ({term}): {job_count} vagas encontradas")
            
        except Exception as e:
            print(f"❌ Erro ao fazer scrape do Net-Empregos ({term}): {e}")
            
    return pd.DataFrame(all_jobs)

 # ========================================
# LANDING.JOB SCRAPER (SCRAPING DIRETO)
# ========================================

def scrape_landing_jobs(search_terms, max_results=30):
    """Scraper para Landing.jobs usando scraping direto do site"""
    all_jobs = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    for term in search_terms:
        job_count = 0
        page = 1
        max_pages = 3
        
        try:
            while job_count < max_results and page <= max_pages:
                print(f"   📄 Página {page} de {term}...")
                
                # URL de pesquisa do Landing.jobs
                search_url = f"https://landing.jobs/jobs?search={term.replace(' ', '%20')}&page={page}"
                
                try:
                    response = requests.get(search_url, headers=headers, timeout=15)
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    articles = soup.find_all('article', class_='lj-jobcard-static')
                    if not articles:
                        print(f"   ℹ️  Sem mais vagas na página {page}")
                        break
                    
                    page_job_count = 0
                    for article in articles:
                        if job_count >= max_results:
                            break
                        
                        try:
                            # Título e URL
                            title_elem = article.find('h2', class_='lj-jobcard-static__title')
                            if not title_elem:
                                continue
                            title_link = title_elem.find('a')
                            if not title_link:
                                continue
                            
                            title = title_link.get_text(strip=True)
                            job_path = title_link.get('href', '')
                            job_url = f"https://landing.jobs{job_path}" if job_path.startswith('/') else job_path
                            
                            # Empresa
                            company_elem = article.find('div', class_='lj-jobcard-static__company')
                            company = 'Unknown'
                            if company_elem:
                                company_link = company_elem.find('a')
                                if company_link:
                                    company = company_link.get_text(strip=True)
                            
                            # Localização
                            location_elem = article.find('span', class_='lj-jobcard-static__location')
                            location = 'Portugal'
                            if location_elem:
                                location_text = location_elem.get_text(strip=True)
                                # Mapear códigos de país e nomes
                                if 'PT' in location_text:
                                    location = location_text.replace('PT', 'Portugal')
                                elif location_text:
                                    location = location_text
                            
                            # Modelo de trabalho (remote/hybrid/onsite)
                            badge_elem = article.find('span', class_=lambda x: x and 'badge' in str(x))
                            is_remote = False
                            work_model = ""
                            if badge_elem:
                                badge_classes = badge_elem.get('class', [])
                                badge_text = badge_elem.get_text(strip=True).lower()
                                if 'remote' in str(badge_classes) or 'remote' in badge_text:
                                    work_model = 'Remoto'
                                    is_remote = True
                                elif 'hybrid' in str(badge_classes) or 'hybrid' in badge_text:
                                    work_model = 'Híbrido'
                                elif 'onsite' in str(badge_classes) or 'onsite' in badge_text:
                                    work_model = 'Presencial'
                            
                            # ID único baseado no URL
                            job_id = f"landingjobs-{hashlib.md5(job_url.encode('utf-8')).hexdigest()[:12]}"
                            
                            all_jobs.append({
                                'id': job_id,
                                'site': 'landingjobs',
                                'job_url': job_url,
                                'title': title,
                                'company': company,
                                'location': location,
                                'date_posted': '',
                                'is_remote': is_remote,
                                'work_model': work_model,
                                'description': '',
                            })
                            job_count += 1
                            page_job_count += 1
                            
                        except Exception as e:
                            print(f"   ⚠️  Erro ao extrair vaga: {e}")
                            continue
                    
                    print(f"   ✅ Página {page}: {page_job_count} vagas extraídas")
                    page += 1
                    time.sleep(1)
                    
                except requests.exceptions.RequestException as e:
                    print(f"   ⚠️  Erro de rede: {e}")
                    break
            
            print(f"✅ Landing.jobs ({term}): {job_count} vagas encontradas")
            
        except Exception as e:
            print(f"❌ Erro ao fazer scrape do Landing.jobs ({term}): {e}")
            
    return pd.DataFrame(all_jobs)           

# ========================================
# CORREÇÃO DAS DESCRIÇÕES
# ========================================

import json

def enrich_itjobs_descriptions(jobs_df, max_enrich=25, delay=1.5):
    """
    Vai à página individual de cada vaga ITJobs buscar a descrição completa.
    Usa JSON-LD structured data (mais fiável) com fallback para content-block.
    """
    if jobs_df.empty:
        return jobs_df
    
    print(f"📖 A enriquecer descrições ITJobs (máx {max_enrich})...")
    enriched = 0
    
    for idx, row in jobs_df.iterrows():
        if enriched >= max_enrich:
            break
        
        # Só enriquece vagas ITJobs sem descrição
        if row.get('site') != 'itjobs' or (pd.notna(row.get('description')) and row.get('description')):
            continue
        
        job_url = row.get('job_url', '')
        if not job_url:
            continue
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(job_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            description = None
            
            # Método 1: JSON-LD structured data (mais fiável)
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld:
                try:
                    data = json.loads(json_ld.string)
                    if 'description' in data:
                        # Extrai texto do HTML
                        desc_soup = BeautifulSoup(data['description'], 'html.parser')
                        description = desc_soup.get_text(separator=' ', strip=True)
                except (json.JSONDecodeError, AttributeError):
                    pass
            
            # Método 2: Fallback para content-block
            if not description:
                content_block = soup.find('div', class_='content-block')
                if content_block:
                    # Remove action-pills e watermark
                    for elem in content_block.find_all(['span', 'p'], class_=lambda x: x and ('action-pill' in str(x) or 'watermark' in str(x))):
                        elem.decompose()
                    paragraphs = content_block.find_all('p')
                    if paragraphs:
                        description = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            # Método 3: Último recurso - qualquer div com muito texto
            if not description:
                for div in soup.find_all('div'):
                    text = div.get_text(separator=' ', strip=True)
                    if len(text) > 500 and ('requisitos' in text.lower() or 'requirements' in text.lower()):
                        description = text
                        break
            
            if description and len(description) > 100:
                jobs_df.at[idx, 'description'] = description
                enriched += 1
            
            # Rate limiting
            time.sleep(delay)
        
        except Exception as e:
            print(f"⚠️  Erro ao enriquecer {job_url}: {e}")
            continue
    
    print(f"✅ Descrições enriquecidas: {enriched}")
    return jobs_df

# ========================================
# FUNÇÃO DE EMAIL (com HTML attachment)
# ========================================

def send_email_notification(jobs_csv_path, html_dashboard_path, jobs_df):
    resend.api_key = config.RESEND_API_KEY
    
    top_jobs = jobs_df.head(15)
    html_table = top_jobs[["priority", "score", "title", "company", "ips_contact", "action"]].to_html(index=False)
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
    <h2>🎯 Job Radar - {datetime.now().strftime('%d/%m/%Y')}</h2>
    <p>Encontrei <strong>{len(jobs_df)}</strong> vagas relevantes (filtradas e classificadas).</p>
    
    <h3>🔝 Top 15 vagas (por score):</h3>
    {html_table}
    
    <p><strong>Legenda:</strong></p>
    <ul>
    <li>🟢 Score 70-100: Candidatura prioritária</li>
    <li>🟡 Score 40-69: Candidatura se tiver tempo</li>
    <li>🔴 Score 0-39: Ignorar</li>
    <li>👤 IPS Contact: Tem contacto IPS (networking!)</li>
    </ul>
    
    <p><strong>📎 Anexos:</strong></p>
    <ul>
    <li>📊 CSV completo com todas as vagas</li>
    <li>🌐 Dashboard HTML interativo (abre no browser!)</li>
    </ul>
    
    <p><em>Abre o ficheiro HTML no browser para uma interface visual interativa!</em></p>
    </body>
    </html>
    """
    
    with open(jobs_csv_path, "rb") as f:
        csv_base64 = base64.b64encode(f.read()).decode("utf-8")
    
    with open(html_dashboard_path, "rb") as f:
        html_base64 = base64.b64encode(f.read()).decode("utf-8")
    
    csv_filename = jobs_csv_path.split("/")[-1]
    html_filename = html_dashboard_path.split("/")[-1]
    
    try:
        resend.Emails.send({
            "from": "Job Radar <onboarding@resend.dev>",
            "to": ["config.EMAIL_RECIPIENT"],
            "subject": f"🎯 Job Radar - {len(jobs_df)} vagas - {datetime.now().strftime('%d/%m/%Y')}",
            "html": html_content,
            "attachments": [
                {"content": csv_base64, "filename": csv_filename},
                {"content": html_base64, "filename": html_filename}
            ]
        })
        print("📧 Email enviado com sucesso (CSV + Dashboard HTML)!")
    except Exception as e:
        print(f"❌ Erro ao enviar email: {e}")


# ========================================
# SCORING SYSTEM
# ========================================
def calculate_job_score(job_row, applied_ids=None):
    if applied_ids is None:
        applied_ids = set()
    
    score = 0
    title = str(job_row.get('title', '')).lower()
    description = str(job_row.get('description', '')).lower()
    text_to_search = f"{title} {description}"
    
    # ⭐ PENALIZAÇÃO FORTE se já candidata
    job_id = str(job_row.get('id', ''))
    if job_id in applied_ids:
        score -= 100  # Praticamente remove da lista
    
    description_weight = 1 if len(description) > 100 else 2
    
    # ... (resto do código de scoring mantém-se igual)

    # IAM keywords - agora com peso condicional
    iam_keywords = {
        'identity and access management': 25, 'iam': 20, 'saml': 15,
        'oidc': 15, 'oauth': 12, 'single sign-on': 20, 'sso': 15,
        'active directory': 12, 'azure ad': 15, 'entra id': 15,
        'okta': 12, 'ping identity': 20, 'cyberark': 15,
        'privileged access': 18, 'pam': 12, 'identity governance': 18,
    }
    
    secops_keywords = {
        'incident response': 15, 'security operations': 12, 'soc': 10,
        'siem': 12, 'sentinel': 15, 'splunk': 12, 'threat detection': 12,
        'vulnerability management': 10, 'security engineer': 15,
        'cybersecurity': 12, 'information security': 12,
    }
    
    automation_keywords = {
        'python': 10, 'powershell': 10, 'bash': 10, 'automation': 8,
        'rest api': 8, 'scripting': 8,
    }
    
    all_keywords = {**iam_keywords, **secops_keywords, **automation_keywords}
    
    # Se keyword está SÓ no título, dá peso dobrado
    for keyword, points in all_keywords.items():
        if keyword in title:
            score += points * 1.5  # Bónus de título
        elif keyword in description:
            score += points
    
    # Bónus por título conter "IAM" explicitamente
    if 'iam' in title:
        score += 15
    
    # Bónus estruturais
    if job_row.get('is_remote') == True or 'remote' in text_to_search or 'remoto' in text_to_search:
        score += 15
    if 'hybrid' in text_to_search or 'híbrido' in text_to_search:
        score += 8
    
    location = str(job_row.get('location', '')).lower()
    if 'portugal' in location or 'lisbon' in location or 'porto' in location:
        score += 10
    
    # Penalizações
    if any(x in text_to_search for x in ['7 years', '8 years', '10 years', 'director', 'vp ', 'head of']):
        score -= 20
    if any(x in title for x in ['junior', 'intern', 'trainee']):
        score -= 15
    
    negative_keywords = ['aml', 'kyc', 'sap', 'mainframe', 'help desk', 'service desk']
    for keyword in negative_keywords:
        if keyword in text_to_search:
            score -= 30
    
    return max(0, min(100, score))

def should_exclude_job(job_row):
    title = str(job_row.get('title', '')).lower()
    description = str(job_row.get('description', '')).lower()
    text = f"{title} {description}"
    
    hard_excludes = [
        'aml', 'kyc', 'anti-money laundering', 'transaction monitoring',
        'sap security', 'mainframe', 'reverse engineer', 'malware analyst',
        'help desk', 'service desk', 'data center security', 'physical security',
    ]
    
    for exclude in hard_excludes:
        if exclude in text:
            return True
    
    location = str(job_row.get('location', '')).lower()
    if location:
        if not any(x in location for x in ['portugal', 'lisbon', 'lisboa', 'porto', 'remote', '']):
            return True
        if any(x in location for x in ['us', 'usa', 'united states', 'uk', 'united kingdom', 'germany', 'france', 'maine']):
            return True
    
    return False


def check_ips_connection(company_name):
    ips_companies = {
        'adentis': 'Sérgio Antunes (Head of People)',
        'idw': 'Ex-aluno IPS',
        'inetum': 'Diogo',
        'devoteam': 'Andreia',
    }
    
    company_lower = str(company_name).lower()
    for company, contact in ips_companies.items():
        if company in company_lower:
            return contact
    return None


def get_priority_category(score, ips_contact):
    if ips_contact:
        return '🟢 ALTA'
    if score >= 70:
        return '🟢 ALTA'
    elif score >= 40:
        return '🟡 MÉDIA'
    else:
        return '🔴 BAIXA'


def get_action_recommendation(score, ips_contact):
    if ips_contact:
        return f'👤 CONTACTAR: {ips_contact}'
    elif score >= 70:
        return '✅ Candidatar HOJE'
    elif score >= 40:
        return '⏰ Candidatar esta semana'
    else:
        return '❌ Ignorar'


# ========================================
# HTML DASHBOARD GENERATOR (COMPLETO)
# ========================================

def generate_html_dashboard(jobs_df, filename):
    html_content = f"""<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 Job Radar Dashboard - {datetime.now().strftime('%d/%m/%Y %H:%M')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; min-height: 100vh; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        header {{ background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); margin-bottom: 30px; }}
        h1 {{ color: #667eea; font-size: 2.5em; margin-bottom: 10px; }}
        .stats {{ display: flex; gap: 20px; margin-top: 20px; flex-wrap: wrap; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; flex: 1; min-width: 150px; text-align: center; }}
        .stat-card h3 {{ font-size: 2em; margin-bottom: 5px; }}
        .filters {{ background: white; padding: 20px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); margin-bottom: 30px; display: flex; gap: 15px; flex-wrap: wrap; }}
        .filter-group {{ display: flex; flex-direction: column; }}
        .filter-group label {{ font-weight: 600; margin-bottom: 5px; }}
        .filter-group select, .filter-group input {{ padding: 10px; border: 2px solid #e0e0e0; border-radius: 8px; }}
        .job-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 20px; }}
        .job-card {{ background: white; border-radius: 15px; padding: 25px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); position: relative; }}
        .job-card.high-priority {{ border-left: 5px solid #10b981; }}
        .job-card.medium-priority {{ border-left: 5px solid #f59e0b; }}
        .job-card.low-priority {{ border-left: 5px solid #ef4444; opacity: 0.7; }}
        .priority-badge {{ position: absolute; top: 15px; right: 15px; padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; }}
        .priority-high {{ background: #10b981; color: white; }}
        .priority-medium {{ background: #f59e0b; color: white; }}
        .priority-low {{ background: #ef4444; color: white; }}
        .job-title {{ font-size: 1.3em; font-weight: 700; margin-bottom: 10px; padding-right: 80px; }}
        .company {{ font-size: 1.1em; color: #667eea; font-weight: 600; margin-bottom: 15px; }}
        .meta {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 15px; }}
        .meta-item {{ background: #f3f4f6; padding: 5px 12px; border-radius: 20px; font-size: 13px; }}
        .ips-contact {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 10px; border-radius: 8px; margin: 15px 0; font-weight: 600; }}
        .score-bar {{ background: #e5e7eb; height: 8px; border-radius: 10px; overflow: hidden; margin: 15px 0; }}
        .score-fill {{ height: 100%; border-radius: 10px; }}
        .score-fill.high {{ background: #10b981; }}
        .score-fill.medium {{ background: #f59e0b; }}
        .score-fill.low {{ background: #ef4444; }}
        .action-btn {{ display: inline-block; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 8px; font-weight: 600; margin-top: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎯 Job Radar Dashboard</h1>
            <p style="color: #666;">Atualizado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
<div class="stats">
    <!-- Prioridades -->
    <div class="stat-card" style="background: linear-gradient(135deg, #10b981, #059669);">
        <h3>{len(jobs_df[jobs_df['priority'] == '🟢 ALTA'])}</h3><p>🟢 Alta</p>
    </div>
    <div class="stat-card" style="background: linear-gradient(135deg, #f59e0b, #d97706);">
        <h3>{len(jobs_df[jobs_df['priority'] == '🟡 MÉDIA'])}</h3><p>🟡 Média</p>
    </div>
    <div class="stat-card" style="background: linear-gradient(135deg, #ef4444, #dc2626);">
        <h3>{len(jobs_df[jobs_df['priority'] == '🔴 BAIXA'])}</h3><p>🔴 Baixa</p>
    </div>
    <div class="stat-card" style="background: linear-gradient(135deg, #8b5cf6, #7c3aed);">
        <h3>{len(jobs_df[jobs_df['ips_contact'].notna()])}</h3><p>👤 IPS</p>
    </div>
</div>

<!-- Sources em segunda linha -->
<div class="stats" style="margin-top: 15px;">
    <div class="stat-card"><h3>{len(jobs_df[jobs_df['site'] == 'linkedin'])}</h3><p>LinkedIn</p></div>
    <div class="stat-card"><h3>{len(jobs_df[jobs_df['site'] == 'indeed'])}</h3><p>Indeed</p></div>
    <div class="stat-card"><h3>{len(jobs_df[jobs_df['site'] == 'itjobs'])}</h3><p>ITJobs</p></div>
    <div class="stat-card"><h3>{len(jobs_df[jobs_df['site'] == 'net-empregos'])}</h3><p>Net-Empregos</p></div>
    <div class="stat-card"><h3>{len(jobs_df[jobs_df['site'] == 'landingjobs'])}</h3><p>Landing.jobs</p></div>
</div>
        </header>
    <div class="filters">
    <div class="filter-group">
        <label>🔍 Pesquisar</label>
        <input type="text" id="searchInput" placeholder="Título ou empresa..." onkeyup="filterJobs()">
    </div>
    <div class="filter-group">
        <label>📊 Prioridade</label>
        <select id="priorityFilter" onchange="filterJobs()">
            <option value="">Todas</option>
            <option value="high">🟢 Alta</option>
            <option value="medium">🟡 Média</option>
            <option value="low">🔴 Baixa</option>
        </select>
    </div>
    <div class="filter-group">
        <label>🌐 Fonte</label>
        <select id="sourceFilter" onchange="filterJobs()">
            <option value="">Todas</option>
            <option value="linkedin">LinkedIn</option>
            <option value="indeed">Indeed</option>
            <option value="itjobs">ITJobs</option>
            <option value="net-empregos">Net-Empregos</option>
            <option value="landingjobs">Landing.jobs</option>
        </select>
    </div>
</div>
"""
    
    for _, job in jobs_df.iterrows():
        score = job['score']
        priority_class = 'high-priority' if 'ALTA' in job['priority'] else ('medium-priority' if 'MÉDIA' in job['priority'] else 'low-priority')
        priority_badge = 'priority-high' if 'ALTA' in job['priority'] else ('priority-medium' if 'MÉDIA' in job['priority'] else 'priority-low')
        score_fill_class = 'high' if score >= 70 else ('medium' if score >= 40 else 'low')
        
        ips_html = ''
        if pd.notna(job.get('ips_contact')):
            ips_html = f'<div class="ips-contact">👤 Contacto IPS: {job["ips_contact"]}</div>'
        
        location = job.get('location', '')
        location_tags = []
        if 'remote' in str(location).lower() or 'remoto' in str(location).lower():
            location_tags.append('🏠 Remoto')
        if any(x in str(location).lower() for x in ['lisbon', 'lisboa']):
            location_tags.append('📍 Lisboa')
        if 'porto' in str(location).lower():
            location_tags.append('📍 Porto')
        
        meta_html = ''.join([f'<span class="meta-item">{tag}</span>' for tag in location_tags])
        
        html_content += f"""
            <div class="job-card {priority_class}" data-priority="{priority_class}" data-source="{job.get('site', '')}" data-score="{score}">
                <span class="priority-badge {priority_badge}">{job['priority']}</span>
                <div class="job-title">{job['title']}</div>
                <div class="company">{job['company']}</div>
                <div class="meta">{meta_html}</div>
                {ips_html}
                <div class="score-bar"><div class="score-fill {score_fill_class}" style="width: {score}%"></div></div>
                <div style="display: flex; justify-content: space-between; margin-top: 10px;">
                    <strong style="color: #667eea;">Score: {score}/100</strong>
                    <span style="color: #666; font-size: 13px;">{job['action']}</span>
                </div>
                <a href="{job.get('job_url', '#')}" target="_blank" class="action-btn">Ver Vaga →</a>
            </div>
"""
    
    html_content += """
        </div>
    </div>
    <script>
    function filterJobs() {
    const searchInput = document.getElementById('searchInput').value.toLowerCase();
    const priorityFilter = document.getElementById('priorityFilter').value;
    const sourceFilter = document.getElementById('sourceFilter').value;
    
    document.querySelectorAll('.job-card').forEach(card => {
        const title = card.querySelector('.job-title').textContent.toLowerCase();
        const company = card.querySelector('.company').textContent.toLowerCase();
        const priority = card.dataset.priority;
        const source = card.dataset.source;
        
        let show = true;
        if (searchInput && !title.includes(searchInput) && !company.includes(searchInput)) show = false;
        if (priorityFilter && !priority.includes(priorityFilter)) show = false;
        if (sourceFilter && source !== sourceFilter) show = false;
        
        card.style.display = show ? 'block' : 'none';
        });
    }
    </script>
</body>
</html>
"""
    
    html_filename = filename.replace('.csv', '.html')
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    return html_filename


# ========================================
# MAIN SCRIPT
# ========================================

print("🔍 A procurar vagas...\n")

# 1. JobSpy (LinkedIn + Indeed)
jobspy_searches = [
    {"term": "identity access management", "location": "Portugal"},
    {"term": "IAM engineer", "location": "Portugal"},
    {"term": "cybersecurity analyst", "location": "Lisbon"},
    {"term": "security operations", "location": "Portugal"},
    {"term": "SAML OIDC", "location": "Portugal"},
]

jobspy_jobs = []
for search in jobspy_searches:
    try:
        jobs = scrape_jobs(
            site_name=["indeed", "linkedin"],
            search_term=search["term"],
            location=search["location"],
            results_wanted=20,
            hours_old=168,
            country='portugal'
        )
        if not jobs.empty:
            jobspy_jobs.append(jobs)
            print(f"✅ JobSpy ({search['term']}): {len(jobs)} vagas")
    except Exception as e:
        print(f"❌ Erro JobSpy ({search['term']}): {e}")

# 2. ITJobs.pt (Custom scraper)
print("\n🔍 A procurar no ITJobs.pt...")
itjobs_search_terms = ["IAM", "cybersecurity", "security", "identity"]
itjobs_df = scrape_itjobs_pt(itjobs_search_terms, max_results=30)

# ⭐ NOVO: Enriquecer descrições antes de combinar
itjobs_df = enrich_itjobs_descriptions(itjobs_df, max_enrich=25)

# ⭐ NOVO 3. Net-Empregos.com
print("\n🔍 A procurar no Net-Empregos...")
netempregos_search_terms = ["IAM", "Cybersecurity", "Cibersegurança", "SOC", "Information Security"]
netempregos_df = scrape_net_empregos(netempregos_search_terms, max_results=30)

# ⭐ NOVO 4. Landing.jobs
print("\n🔍 A procurar no Landing.jobs...")
landingjobs_search_terms = ["IAM", "cybersecurity", "security", "identity"]
landingjobs_df = scrape_landing_jobs(landingjobs_search_terms, max_results=30)

# Combinar resultados
all_dfs = []
if jobspy_jobs:
    combined_jobspy = pd.concat(jobspy_jobs, ignore_index=True)
    all_dfs.append(combined_jobspy)

if not itjobs_df.empty:
    all_dfs.append(itjobs_df)

if not netempregos_df.empty:
    all_dfs.append(netempregos_df)

if not landingjobs_df.empty:
    all_dfs.append(landingjobs_df)

if all_dfs:
    combined = pd.concat(all_dfs, ignore_index=True)
    unique_jobs = combined.drop_duplicates(subset=['id'])
    
    print(f"\n🧹 A filtrar e classificar {len(unique_jobs)} vagas...")
    
    # ⭐ Carregar candidaturas previas
    applied_ids = set(app['job_id'] for app in load_applications())
    print(f"📋 {len(applied_ids)} candidaturas previas registadas")
    
    filtered_jobs = []
    for _, job in unique_jobs.iterrows():
        if not should_exclude_job(job):
            job_dict = job.to_dict()
            job_dict['score'] = calculate_job_score(job, applied_ids)
            job_dict['applied'] = '✅ JÁ CANDIDATA' if job.get('id') in applied_ids else ''
            job_dict['ips_contact'] = check_ips_connection(job.get('company', ''))
            job_dict['priority'] = get_priority_category(job_dict['score'], job_dict['ips_contact'])
            job_dict['action'] = get_action_recommendation(job_dict['score'], job_dict['ips_contact'])
            filtered_jobs.append(job_dict)
    
    scored_jobs = pd.DataFrame(filtered_jobs)
    scored_jobs = scored_jobs.sort_values('score', ascending=False)
    
    columns_order = ['priority', 'score', 'applied', 'action','site', 'id', 'title', 'company',
                 'location', 'date_posted', 'ips_contact', 'job_url']
    existing_columns = [col for col in columns_order if col in scored_jobs.columns]
    scored_jobs_export = scored_jobs[existing_columns]
    
    filename = f"jobs_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    scored_jobs_export.to_csv(filename, index=False, sep=';', encoding='utf-8-sig')
    
    print(f"\n📊 Total: {len(scored_jobs)} vagas relevantes")
    print(f"💾 CSV: {filename}")
    
    print("\n🎨 A gerar dashboard HTML...")
    html_filename = generate_html_dashboard(scored_jobs, filename)
    print(f"🌐 Dashboard: {html_filename}")
    
    print("\n🔝 Top 10 vagas:\n")
    top_10 = scored_jobs.head(10)[['priority', 'score', 'title', 'company', 'ips_contact']]
    print(top_10.to_string(index=False))
    
    # Estatísticas
    high = len(scored_jobs[scored_jobs['priority'] == '🟢 ALTA'])
    medium = len(scored_jobs[scored_jobs['priority'] == '🟡 MÉDIA'])
    low = len(scored_jobs[scored_jobs['priority'] == '🔴 BAIXA'])
    
    print(f"\n📈 Distribuição:")
    print(f"   🟢 Alta: {high} | 🟡 Média: {medium} | 🔴 Baixa: {low}")
    
    # Enviar email com CSV + HTML
    send_email_notification(filename, html_filename, scored_jobs)
else:
    print("❌ Nenhuma vaga encontrada")

# Adicionar ao fim do job_radar.py
import os
import glob

# Manter só últimos 30 dias
old_files = glob.glob('jobs_*.csv') + glob.glob('jobs_*.html')
for f in old_files:
    if os.path.getmtime(f) < datetime.now().timestamp() - 30*24*3600:
        os.remove(f)
