from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Skill, Candidate, JobOffer, Application, ResumeDocument
import tempfile
import os

User = get_user_model()


class SkillAPITestCase(APITestCase):
    def setUp(self):
        self.skill = Skill.objects.create(name="Python")
    
    def test_list_skills(self):
        url = reverse('skill-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Python')
    
    def test_create_skill(self):
        url = reverse('skill-list')
        data = {'name': 'JavaScript'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Skill.objects.count(), 2)
    
    def test_retrieve_skill(self):
        url = reverse('skill-detail', kwargs={'pk': self.skill.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Python')


class CandidateAPITestCase(APITestCase):
    def setUp(self):
        self.candidate = Candidate.objects.create(
            first_name="Marie",
            last_name="Dubois",
            email="marie.dubois@email.com",
            location="Paris, France",
            headline="Développeuse Full Stack"
        )
    
    def test_list_candidates(self):
        url = reverse('candidate-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['first_name'], 'Marie')
    
    def test_create_candidate(self):
        url = reverse('candidate-list')
        data = {
            'first_name': 'Pierre',
            'last_name': 'Martin',
            'email': 'pierre.martin@email.com',
            'location': 'Lyon, France',
            'headline': 'Data Scientist'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Candidate.objects.count(), 2)
    
    def test_retrieve_candidate(self):
        url = reverse('candidate-detail', kwargs={'pk': self.candidate.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Marie')
    
    def test_upload_resume(self):
        url = reverse('candidate-upload-resume', kwargs={'pk': self.candidate.pk})
        
        # Créer un fichier temporaire pour le test
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("CV de test\nExpérience: 5 ans\nCompétences: Python, Django")
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, 'rb') as file:
                data = {'file': file}
                response = self.client.post(url, data, format='multipart')
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(ResumeDocument.objects.count(), 1)
                
                # Vérifier que le texte a été extrait
                resume = ResumeDocument.objects.first()
                self.assertIn("CV de test", resume.parsed_text)
        finally:
            os.unlink(temp_file_path)


class JobOfferAPITestCase(APITestCase):
    def setUp(self):
        self.job_offer = JobOffer.objects.create(
            title="Développeur Full Stack",
            company="TechCorp",
            location="Paris, France",
            description="Poste de développeur full stack avec React et Django",
            seniority="senior",
            is_remote=True
        )
    
    def test_list_job_offers(self):
        url = reverse('joboffer-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Développeur Full Stack')
    
    def test_create_job_offer(self):
        url = reverse('joboffer-list')
        data = {
            'title': 'Data Scientist',
            'company': 'AI Solutions',
            'location': 'Lyon, France',
            'description': 'Poste de data scientist avec Python et ML',
            'seniority': 'mid',
            'is_remote': False
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(JobOffer.objects.count(), 2)
    
    def test_retrieve_job_offer(self):
        url = reverse('joboffer-detail', kwargs={'pk': self.job_offer.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Développeur Full Stack')


class ApplicationAPITestCase(APITestCase):
    def setUp(self):
        self.candidate = Candidate.objects.create(
            first_name="Marie",
            last_name="Dubois",
            email="marie.dubois@email.com"
        )
        self.job_offer = JobOffer.objects.create(
            title="Développeur Full Stack",
            company="TechCorp",
            description="Poste de développeur"
        )
        self.application = Application.objects.create(
            candidate=self.candidate,
            job_offer=self.job_offer,
            status="new"
        )
    
    def test_list_applications(self):
        url = reverse('application-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'new')
    
    def test_create_application(self):
        # Créer un nouveau candidat et une nouvelle offre pour éviter les conflits
        new_candidate = Candidate.objects.create(
            first_name="Pierre",
            last_name="Martin",
            email="pierre.martin@email.com"
        )
        new_job_offer = JobOffer.objects.create(
            title="Data Scientist",
            company="AI Corp",
            description="Poste de data scientist"
        )
        
        url = reverse('application-list')
        data = {
            'candidate': new_candidate.pk,
            'job_offer': new_job_offer.pk,
            'status': 'screening'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Application.objects.count(), 2)
    
    def test_retrieve_application(self):
        url = reverse('application-detail', kwargs={'pk': self.application.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'new')


class ResumeDocumentAPITestCase(APITestCase):
    def setUp(self):
        self.candidate = Candidate.objects.create(
            first_name="Marie",
            last_name="Dubois",
            email="marie.dubois@email.com"
        )
        self.resume = ResumeDocument.objects.create(
            candidate=self.candidate,
            original_filename="cv_marie.pdf",
            content_type="application/pdf",
            parsed_text="CV de Marie Dubois\nExpérience: 5 ans"
        )
    
    def test_list_resumes(self):
        url = reverse('resumedocument-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['original_filename'], 'cv_marie.pdf')
    
    def test_retrieve_resume(self):
        url = reverse('resumedocument-detail', kwargs={'pk': self.resume.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['original_filename'], 'cv_marie.pdf')
        self.assertIn("CV de Marie Dubois", response.data['parsed_text'])