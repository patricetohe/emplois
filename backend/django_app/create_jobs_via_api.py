"""
Script pour créer des offres via l'API REST.
"""

import requests
import json

def create_jobs():
    """Crée des offres via l'API REST."""
    
    jobs_data = [
        {
            "title": "Développeur Python Senior",
            "company": "TechCorp",
            "location": "Paris",
            "description": "Nous recherchons un développeur Python senior pour rejoindre notre équipe. Vous travaillerez sur des projets innovants utilisant Django, PostgreSQL et des APIs REST. Expérience requise en machine learning et data science.",
            "seniority": "senior",
            "is_remote": True
        },
        {
            "title": "Data Scientist",
            "company": "DataLab",
            "location": "Lyon",
            "description": "Poste de Data Scientist pour analyser de grandes quantités de données et développer des modèles prédictifs. Maîtrise de Python, SQL et des outils de machine learning requise.",
            "seniority": "mid",
            "is_remote": False
        },
        {
            "title": "Développeur Full Stack",
            "company": "WebAgency",
            "location": "Marseille",
            "description": "Développeur full stack pour créer des applications web modernes. Stack technique: React, Django, PostgreSQL. Expérience en Docker et AWS appréciée.",
            "seniority": "mid",
            "is_remote": True
        },
        {
            "title": "Ingénieur DevOps",
            "company": "CloudTech",
            "location": "Toulouse",
            "description": "Ingénieur DevOps pour gérer notre infrastructure cloud et automatiser nos déploiements. Expertise en Docker, AWS et Linux requise.",
            "seniority": "senior",
            "is_remote": True
        },
        {
            "title": "Développeur Frontend",
            "company": "UIAgency",
            "location": "Nantes",
            "description": "Développeur frontend spécialisé en React pour créer des interfaces utilisateur modernes et responsives. Connaissance de GraphQL et des APIs REST.",
            "seniority": "junior",
            "is_remote": False
        }
    ]
    
    base_url = "http://localhost:8000/api/job-offers/"
    created_count = 0
    
    for job_data in jobs_data:
        try:
            response = requests.post(
                base_url,
                json=job_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 201:
                created_count += 1
                job = response.json()
                print(f"✅ Offre créée: {job['title']} @ {job['company']} (ID: {job['id']})")
            else:
                print(f"❌ Erreur création offre {job_data['title']}: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Erreur pour {job_data['title']}: {e}")
    
    print(f"\n🎉 {created_count} nouvelles offres créées!")
    
    # Vérifier le total
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            jobs = response.json()
            print(f"📊 Total des offres en base: {len(jobs)}")
    except Exception as e:
        print(f"❌ Erreur vérification: {e}")

if __name__ == '__main__':
    create_jobs()
