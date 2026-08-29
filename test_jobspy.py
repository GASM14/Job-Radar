from jobspy import scrape_jobs

# Teste simples: vagas IAM em Portugal
jobs = scrape_jobs(
    site_name=["indeed", "linkedin"],
    search_term="identity access management",
    location="Portugal",
    results_wanted=10,
    hours_old=72,  # vagas das últimas 72h
    country='portugal'
)

print(f"Encontrei {len(jobs)} vagas:\n")
print(jobs[["title", "company", "location", "job_type", "date_posted"]].to_string())
