#!/usr/bin/env python3
"""
Uso:
  python apply.py                    # Lista vagas recentes
  python apply.py add <job_id>       # Marca como candidata
  python apply.py remove <job_id>    # Remove candidatura
  python apply.py list               # Lista todas candidaturas
"""
import sys
import json
import glob
import os
import pandas as pd
from datetime import datetime

APPLICATIONS_FILE = 'applications.json'

def load_applications():
    try:
        with open(APPLICATIONS_FILE, 'r') as f:
            return json.load(f).get('applied_jobs', [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_applications(applications):
    with open(APPLICATIONS_FILE, 'w') as f:
        json.dump({'applied_jobs': applications}, f, indent=2, ensure_ascii=False)

def get_latest_csv():
    files = glob.glob('jobs_*.csv')
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def list_recent_jobs():
    csv_file = get_latest_csv()
    if not csv_file:
        print("❌ Nenhum CSV encontrado")
        return
    
    df = pd.read_csv(csv_file, sep=';')
    applications = load_applications()
    applied_ids = set(a['job_id'] for a in applications)
    
    print(f"\n📋 Últimas vagas ({csv_file}):\n")
    print(f"{'ID':<45} {'Score':<6} {'Pri':<5} {'Title':<40} {'Company':<20}")
    print("-" * 120)
    
    for _, row in df.head(30).iterrows():
        job_id = str(row.get('id', ''))
        applied_mark = ' ✅' if job_id in applied_ids else '  '
        title = str(row.get('title', ''))[:40]
        company = str(row.get('company', ''))[:20]
        print(f"{job_id:<45} {row.get('score', 0):<6} {row.get('priority', ''):<5} {title:<40} {company:<20}{applied_mark}")

def add_application(job_id, status='applied'):
    csv_file = get_latest_csv()
    if csv_file:
        df = pd.read_csv(csv_file, sep=';')
        job = df[df['id'] == job_id]
        if not job.empty:
            title = job.iloc[0].get('title', 'Unknown')
            company = job.iloc[0].get('company', 'Unknown')
        else:
            title = input("Título da vaga: ")
            company = input("Empresa: ")
    else:
        title = input("Título da vaga: ")
        company = input("Empresa: ")
    
    applications = load_applications()
    
    if any(a['job_id'] == job_id for a in applications):
        print(f"⚠️  Vaga já marcada como candidata")
        return
    
    applications.append({
        'job_id': job_id,
        'title': title,
        'company': company,
        'applied_date': datetime.now().strftime('%Y-%m-%d'),
        'status': status,
        'notes': ''
    })
    
    save_applications(applications)
    print(f"✅ Marcada como candidata: {title} @ {company}")

def remove_application(job_id):
    applications = load_applications()
    original_len = len(applications)
    applications = [a for a in applications if a['job_id'] != job_id]
    
    if len(applications) < original_len:
        save_applications(applications)
        print(f"✅ Candidatura removida")
    else:
        print(f"⚠️  Vaga não encontrada")

def list_all_applications():
    applications = load_applications()
    if not applications:
        print("📭 Nenhuma candidatura registada")
        return
    
    print(f"\n📋 {len(applications)} candidaturas registadas:\n")
    for app in applications:
        print(f"📅 {app['applied_date']} | {app['status']:<10} | {app['title']} @ {app['company']}")

if __name__ == '__main__':
    if len(sys.argv) == 1:
        list_recent_jobs()
    elif sys.argv[1] == 'add' and len(sys.argv) >= 3:
        add_application(sys.argv[2])
    elif sys.argv[1] == 'remove' and len(sys.argv) >= 3:
        remove_application(sys.argv[2])
    elif sys.argv[1] == 'list':
        list_all_applications()
    else:
        print(__doc__)
