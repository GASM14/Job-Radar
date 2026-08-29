from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime, timedelta
import re

def scrape_itjobs_pt(search_terms, max_results=50):
    """
    Scraper customizado para ITJobs.pt
    """
    all_jobs = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for term in search_terms:
        try:
            # URL de pesquisa do ITJobs
            search_url = f"https://www.itjobs.pt/pesquisa?q={term.replace(' ', '+')}&search_type=job"
            
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Procurar vagas em blocos diários
            job_blocks = soup.find_all('div', class_='block borderless')
            
            current_date = None
            job_count = 0
            
            for block in job_blocks:
                # Extrair data do bloco (se existir)
                date_box = block.find('div', class_='date-box')
                if date_box:
                    day = date_box.find('div', class_='d-d')
                    month = date_box.find('div', class_='d-m')
                    if day and month:
                        current_date = f"{day.text.strip()} {month.text.strip()}"
                
                # Procurar lista de vagas dentro do bloco
                listing = block.find('ul', class_='listing')
                if not listing:
                    continue
                
                job_items = listing.find_all('li')
                
                for item in job_items:
                    if job_count >= max_results:
                        break
                    
                    try:
                        # Extrair título e URL
                        title_elem = item.find('div', class_='list-title')
                        if not title_elem:
                            continue
                        
                        title_link = title_elem.find('a', class_='title')
                        if not title_link:
                            continue
                        
                        title = title_link.get_text(strip=True)
                        job_path = title_link.get('href', '')
                        job_url = f"https://www.itjobs.pt{job_path}" if job_path.startswith('/') else job_path
                        
                        # Extrair empresa
                        company_elem = item.find('div', class_='list-name')
                        company_link = company_elem.find('a') if company_elem else None
                        company = company_link.get_text(strip=True) if company_link else "Unknown"
                        
                        # Extrair detalhes (localização e modelo de trabalho)
                        details_elem = item.find('div', class_='list-details')
                        location = "Portugal"
                        is_remote = False
                        work_model = ""
                        
                        if details_elem:
                            details_text = details_elem.get_text(separator='|', strip=True)
                            
                            # Extrair localização (depois do ícone de mapa)
                            location_match = re.search(r'fa-map-marker.*?\|([^|]+)\|', details_text)
                            if location_match:
                                location = location_match.group(1).strip()
                            
                            # Detectar modelo de trabalho
                            if 'Remoto' in details_text:
                                work_model = 'Remoto'
                                is_remote = True
                            elif 'Híbrido' in details_text:
                                work_model = 'Híbrido'
                            elif 'Presencial' in details_text:
                                work_model = 'Presencial'
                        
                        # Adicionar à lista
                        job_id = f"itjobs-{hash(job_url)}"
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
                            'description': '',  # ITJobs não mostra descrição completa na listagem
                        })
                        
                        job_count += 1
                        
                    except Exception as e:
                        print(f"⚠️  Erro ao extrair vaga: {e}")
                        continue
            
            print(f"✅ ITJobs.pt ({term}): {job_count} vagas encontradas")
            
        except Exception as e:
            print(f"❌ Erro ao fazer scrape do ITJobs.pt ({term}): {e}")
    
    return pd.DataFrame(all_jobs)


# Teste rápido
if __name__ == "__main__":
    print("🔍 A testar scraper ITJobs.pt...\n")
    
    test_terms = ["IAM", "cybersecurity", "security"]
    df = scrape_itjobs_pt(test_terms, max_results=10)
    
    if not df.empty:
        print(f"\n📊 Total: {len(df)} vagas\n")
        print("Top 10:\n")
        for idx, job in df.head(10).iterrows():
            remote_tag = "🏠" if job['is_remote'] else "🏢"
            print(f"{remote_tag} {job['title']}")
            print(f"   📍 {job['location']} | {job['work_model']}")
            print(f"   🏢 {job['company']}")
            print(f"   🔗 {job['job_url']}")
            print()
    else:
        print("❌ Nenhuma vaga encontrada")
