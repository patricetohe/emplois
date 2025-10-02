from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Skill(models.Model):
    name = models.CharField(max_length=128, unique=True)

    def __str__(self) -> str:
        return self.name


class Candidate(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="candidate_profile", null=True, blank=True)
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=200, blank=True)
    headline = models.CharField(max_length=200, blank=True)
    summary = models.TextField(blank=True)
    skills = models.ManyToManyField(Skill, through="CandidateSkill", related_name="candidates", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class CandidateSkill(models.Model):
    class Proficiency(models.IntegerChoices):
        BEGINNER = 1, "Beginner"
        INTERMEDIATE = 2, "Intermediate"
        ADVANCED = 3, "Advanced"
        EXPERT = 4, "Expert"

    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    proficiency = models.IntegerField(choices=Proficiency.choices, default=Proficiency.INTERMEDIATE)
    years_of_experience = models.DecimalField(max_digits=4, decimal_places=1, default=0)

    class Meta:
        unique_together = ("candidate", "skill")


class Experience(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="experiences")
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["-start_date"]


class Education(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="educations")
    school = models.CharField(max_length=200)
    degree = models.CharField(max_length=200, blank=True)
    field_of_study = models.CharField(max_length=200, blank=True)
    start_year = models.IntegerField(null=True, blank=True)
    end_year = models.IntegerField(null=True, blank=True)


class ResumeDocument(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="resumes")
    file = models.FileField(upload_to="resumes/")
    original_filename = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    parsed_text = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class JobOffer(models.Model):
    class Seniority(models.TextChoices):
        INTERN = "intern", "Intern"
        JUNIOR = "junior", "Junior"
        MID = "mid", "Mid"
        SENIOR = "senior", "Senior"
        LEAD = "lead", "Lead"

    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    required_skills = models.ManyToManyField(Skill, related_name="job_offers", blank=True)
    seniority = models.CharField(max_length=20, choices=Seniority.choices, blank=True)
    is_remote = models.BooleanField(default=False)
    posted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.title} @ {self.company}"


class Application(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        SCREENING = "screening", "Screening"
        TEST = "test", "Test"
        INTERVIEW = "interview", "Interview"
        OFFER = "offer", "Offer"
        HIRED = "hired", "Hired"
        REJECTED = "rejected", "Rejected"

    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="applications")
    job_offer = models.ForeignKey(JobOffer, on_delete=models.CASCADE, related_name="applications")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    score = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("candidate", "job_offer")

