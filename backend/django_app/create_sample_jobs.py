"""
Script pour créer des offres d'emploi d'exemple.
"""

import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import JobOffer, Skill
from django.utils import timezone
from datetime import timedelta

def create_sample_jobs():
    """Crée des offres d'emploi d'exemple."""
    
    # Créer quelques compétences si elles n'existent pas
    skills_data = [
        'Python', 'Django', 'JavaScript', 'React', 'Machine Learning',
        'Data Science', 'SQL', 'PostgreSQL', 'Docker', 'AWS',
        'Git', 'Linux', 'API', 'REST', 'GraphQL'
    ]
    
    skills = {}
    for skill_name in skills_data:
        skill, created = Skill.objects.get_or_create(name=skill_name)
        skills[skill_name] = skill
        if created:
            print(f"✅ Compétence créée: {skill_name}")
    
    # Offres d'exemple
    jobs_data = [
        {
            'title': 'Développeur Python Senior',
            'company': 'TechCorp',
            'location': 'Paris',
            'description': 'Nous recherchons un développeur Python senior pour rejoindre notre équipe. Vous travaillerez sur des projets innovants utilisant Django, PostgreSQL et des APIs REST. Expérience requise en machine learning et data science.',
            'seniority': 'senior',
            'is_remote': True,
            'required_skills': ['Python', 'Django', 'PostgreSQL', 'Machine Learning']
        },
        {
            'title': 'Data Scientist',
            'company': 'DataLab',
            'location': 'Lyon',
            'description': 'Poste de Data Scientist pour analyser de grandes quantités de données et développer des modèles prédictifs. Maîtrise de Python, SQL et des outils de machine learning requise.',
            'seniority': 'mid',
            'is_remote': False,
            'required_skills': ['Python', 'Machine Learning', 'Data Science', 'SQL']
        },
        {
            'title': 'Développeur Full Stack',
            'company': 'WebAgency',
            'location': 'Marseille',
            'description': 'Développeur full stack pour créer des applications web modernes. Stack technique: React, Django, PostgreSQL. Expérience en Docker et AWS appréciée.',
            'seniority': 'mid',
            'is_remote': True,
            'required_skills': ['JavaScript', 'React', 'Python', 'Django', 'Docker']
        },
        {
            'title': 'Ingénieur DevOps',
            'company': 'CloudTech',
            'location': 'Toulouse',
            'description': 'Ingénieur DevOps pour gérer notre infrastructure cloud et automatiser nos déploiements. Expertise en Docker, AWS et Linux requise.',
            'seniority': 'senior',
            'is_remote': True,
            'required_skills': ['Docker', 'AWS', 'Linux', 'Git']
        },
        {
            'title': 'Développeur Frontend',
            'company': 'UIAgency',
            'location': 'Nantes',
            'description': 'Développeur frontend spécialisé en React pour créer des interfaces utilisateur modernes et responsives. Connaissance de GraphQL et des APIs REST.',
            'seniority': 'junior',
            'is_remote': False,
            'required_skills': ['JavaScript', 'React', 'API', 'REST', 'GraphQL']
        }
    ]
    
    created_count = 0
    for job_data in jobs_data:
        # Extraire les compétences
        required_skills = job_data.pop('required_skills')
        
        # Créer l'offre
        job, created = JobOffer.objects.get_or_create(
            title=job_data['title'],
            company=job_data['company'],
            defaults={
                **job_data,
                'posted_at': timezone.now(),
                'expires_at': timezone.now() + timedelta(days=30)
            }
        )
        
        if created:
            # Ajouter les compétences
            for skill_name in required_skills:
                if skill_name in skills:
                    job.required_skills.add(skills[skill_name])
            
            created_count += 1
            print(f"✅ Offre créée: {job.title} @ {job.company}")
        else:
            print(f"⚠️ Offre existante: {job.title} @ {job.company}")
    
    print(f"\n🎉 {created_count} nouvelles offres créées!")
    print(f"📊 Total des offres en base: {JobOffer.objects.count()}")

if __name__ == '__main__':
    create_sample_jobs()

