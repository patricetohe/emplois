#!/usr/bin/env python
"""
Script de seed pour générer des données de test.
Usage: python manage.py shell < seed_data.py
"""

from api.models import Skill, Candidate, CandidateSkill, Experience, Education, JobOffer
from django.contrib.auth import get_user_model
import random
from datetime import date, timedelta

User = get_user_model()

# Nettoyer les données existantes
print("Nettoyage des données existantes...")
CandidateSkill.objects.all().delete()
Experience.objects.all().delete()
Education.objects.all().delete()
ResumeDocument.objects.all().delete()
Application.objects.all().delete()
Candidate.objects.all().delete()
JobOffer.objects.all().delete()
Skill.objects.all().delete()

# Créer les compétences
print("Création des compétences...")
skills_data = [
    "Python", "JavaScript", "React", "Django", "Node.js", "PostgreSQL", "MongoDB",
    "Docker", "Kubernetes", "AWS", "Git", "Linux", "Machine Learning", "Data Science",
    "DevOps", "Frontend", "Backend", "Full Stack", "Mobile Development", "iOS",
    "Android", "React Native", "Flutter", "Java", "C++", "C#", ".NET", "PHP",
    "Laravel", "Symfony", "Ruby", "Rails", "Go", "Rust", "TypeScript", "Vue.js",
    "Angular", "Svelte", "HTML", "CSS", "SASS", "Bootstrap", "Tailwind CSS",
    "GraphQL", "REST API", "Microservices", "Agile", "Scrum", "Project Management",
    "UI/UX Design", "Figma", "Adobe Creative Suite", "Photoshop", "Illustrator",
    "Marketing Digital", "SEO", "Analytics", "Google Analytics", "Facebook Ads",
    "Content Marketing", "Social Media", "Email Marketing", "Sales", "Business Development",
    "Customer Success", "Product Management", "Finance", "Accounting", "HR",
    "Recruitment", "Training", "Legal", "Compliance", "Security", "Cybersecurity"
]

skills = []
for skill_name in skills_data:
    skill, created = Skill.objects.get_or_create(name=skill_name)
    skills.append(skill)
    if created:
        print(f"  Créé: {skill_name}")

# Créer des candidats
print("Création des candidats...")
candidates_data = [
    {
        "first_name": "Marie", "last_name": "Dubois", "email": "marie.dubois@email.com",
        "phone": "01 23 45 67 89", "location": "Paris, France",
        "headline": "Développeuse Full Stack Senior",
        "summary": "Développeuse passionnée avec 5 ans d'expérience en développement web full stack. Expertise en React, Django et PostgreSQL."
    },
    {
        "first_name": "Pierre", "last_name": "Martin", "email": "pierre.martin@email.com",
        "phone": "01 98 76 54 32", "location": "Lyon, France",
        "headline": "Data Scientist",
        "summary": "Data Scientist avec une formation en mathématiques et 3 ans d'expérience en machine learning et analyse de données."
    },
    {
        "first_name": "Sophie", "last_name": "Bernard", "email": "sophie.bernard@email.com",
        "phone": "02 11 22 33 44", "location": "Nantes, France",
        "headline": "Product Manager",
        "summary": "Product Manager expérimentée avec une expertise en stratégie produit et gestion d'équipes agiles."
    },
    {
        "first_name": "Thomas", "last_name": "Petit", "email": "thomas.petit@email.com",
        "phone": "03 44 55 66 77", "location": "Toulouse, France",
        "headline": "DevOps Engineer",
        "summary": "Ingénieur DevOps avec une expertise en infrastructure cloud, Docker, Kubernetes et CI/CD."
    },
    {
        "first_name": "Julie", "last_name": "Robert", "email": "julie.robert@email.com",
        "phone": "04 55 66 77 88", "location": "Marseille, France",
        "headline": "UX/UI Designer",
        "summary": "Designer UX/UI créative avec une approche centrée utilisateur et une expertise en design d'interfaces modernes."
    }
]

candidates = []
for candidate_data in candidates_data:
    candidate = Candidate.objects.create(**candidate_data)
    candidates.append(candidate)
    print(f"  Créé: {candidate.first_name} {candidate.last_name}")

# Ajouter des compétences aux candidats
print("Ajout des compétences aux candidats...")
candidate_skills = [
    # Marie - Full Stack
    [("Python", 4, 5), ("Django", 4, 4), ("React", 4, 3), ("JavaScript", 4, 4), ("PostgreSQL", 3, 3)],
    # Pierre - Data Scientist
    [("Python", 4, 4), ("Machine Learning", 4, 3), ("Data Science", 4, 3), ("PostgreSQL", 3, 2)],
    # Sophie - Product Manager
    [("Product Management", 4, 5), ("Agile", 4, 4), ("Project Management", 4, 4), ("Analytics", 3, 3)],
    # Thomas - DevOps
    [("Docker", 4, 4), ("Kubernetes", 4, 3), ("AWS", 4, 4), ("Linux", 4, 5), ("DevOps", 4, 4)],
    # Julie - UX/UI
    [("UI/UX Design", 4, 4), ("Figma", 4, 3), ("Adobe Creative Suite", 3, 4), ("HTML", 3, 3), ("CSS", 3, 3)]
]

for i, candidate in enumerate(candidates):
    if i < len(candidate_skills):
        for skill_name, proficiency, years in candidate_skills[i]:
            try:
                skill = Skill.objects.get(name=skill_name)
                CandidateSkill.objects.create(
                    candidate=candidate,
                    skill=skill,
                    proficiency=proficiency,
                    years_of_experience=years
                )
            except Skill.DoesNotExist:
                print(f"  Compétence non trouvée: {skill_name}")

# Ajouter des expériences
print("Ajout des expériences...")
experiences_data = [
    # Marie
    [
        {"title": "Développeuse Full Stack", "company": "TechCorp", "start_date": date(2021, 1, 1), "end_date": None, "is_current": True, "description": "Développement d'applications web avec React et Django"},
        {"title": "Développeuse Frontend", "company": "WebAgency", "start_date": date(2019, 6, 1), "end_date": date(2020, 12, 31), "is_current": False, "description": "Développement d'interfaces utilisateur avec React et TypeScript"}
    ],
    # Pierre
    [
        {"title": "Data Scientist", "company": "DataCorp", "start_date": date(2022, 3, 1), "end_date": None, "is_current": True, "description": "Analyse de données et développement de modèles de machine learning"},
        {"title": "Analyste de données", "company": "Analytics Inc", "start_date": date(2020, 9, 1), "end_date": date(2022, 2, 28), "is_current": False, "description": "Analyse de données business et création de rapports"}
    ]
]

for i, candidate in enumerate(candidates[:2]):  # Ajouter expériences aux 2 premiers candidats
    if i < len(experiences_data):
        for exp_data in experiences_data[i]:
            Experience.objects.create(candidate=candidate, **exp_data)

# Créer des offres d'emploi
print("Création des offres d'emploi...")
job_offers_data = [
    {
        "title": "Développeur Full Stack Senior",
        "company": "StartupTech",
        "location": "Paris, France",
        "description": "Nous recherchons un développeur full stack senior pour rejoindre notre équipe en pleine croissance. Vous travaillerez sur des projets innovants utilisant React, Django et PostgreSQL.",
        "seniority": "senior",
        "is_remote": True
    },
    {
        "title": "Data Scientist",
        "company": "AI Solutions",
        "location": "Lyon, France",
        "description": "Rejoignez notre équipe de data scientists pour développer des solutions d'IA innovantes. Expertise en Python, machine learning et analyse de données requise.",
        "seniority": "mid",
        "is_remote": False
    },
    {
        "title": "Product Manager",
        "company": "Innovation Corp",
        "location": "Nantes, France",
        "description": "Nous cherchons un Product Manager expérimenté pour piloter le développement de nos produits digitaux. Expérience en gestion de produits et méthodologies agiles requise.",
        "seniority": "senior",
        "is_remote": True
    },
    {
        "title": "DevOps Engineer",
        "company": "CloudTech",
        "location": "Toulouse, France",
        "description": "Ingénieur DevOps recherché pour gérer notre infrastructure cloud. Expertise en Docker, Kubernetes, AWS et CI/CD requise.",
        "seniority": "mid",
        "is_remote": False
    },
    {
        "title": "UX/UI Designer",
        "company": "Design Studio",
        "location": "Marseille, France",
        "description": "Designer UX/UI créatif recherché pour concevoir des interfaces utilisateur exceptionnelles. Maîtrise de Figma et Adobe Creative Suite requise.",
        "seniority": "mid",
        "is_remote": True
    }
]

job_offers = []
for job_data in job_offers_data:
    job = JobOffer.objects.create(**job_data)
    job_offers.append(job)
    print(f"  Créé: {job.title} @ {job.company}")

# Ajouter des compétences requises aux offres
print("Ajout des compétences requises aux offres...")
job_skills = [
    # Développeur Full Stack
    ["Python", "Django", "React", "JavaScript", "PostgreSQL"],
    # Data Scientist
    ["Python", "Machine Learning", "Data Science", "PostgreSQL"],
    # Product Manager
    ["Product Management", "Agile", "Project Management", "Analytics"],
    # DevOps Engineer
    ["Docker", "Kubernetes", "AWS", "Linux", "DevOps"],
    # UX/UI Designer
    ["UI/UX Design", "Figma", "Adobe Creative Suite", "HTML", "CSS"]
]

for i, job in enumerate(job_offers):
    if i < len(job_skills):
        for skill_name in job_skills[i]:
            try:
                skill = Skill.objects.get(name=skill_name)
                job.required_skills.add(skill)
            except Skill.DoesNotExist:
                print(f"  Compétence non trouvée: {skill_name}")

print("Seed terminé avec succès!")
print(f"Créé: {len(skills)} compétences, {len(candidates)} candidats, {len(job_offers)} offres")
