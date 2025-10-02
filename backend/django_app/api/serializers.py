from rest_framework import serializers

from .models import Skill, Candidate, CandidateSkill, Experience, Education, ResumeDocument, JobOffer, Application


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id", "name"]


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = [
            "id",
            "title",
            "company",
            "start_date",
            "end_date",
            "description",
            "is_current",
        ]


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = [
            "id",
            "school",
            "degree",
            "field_of_study",
            "start_year",
            "end_year",
        ]


class CandidateSkillSerializer(serializers.ModelSerializer):
    skill = SkillSerializer()

    class Meta:
        model = CandidateSkill
        fields = ["skill", "proficiency", "years_of_experience"]


class ResumeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeDocument
        fields = [
            "id",
            "file",
            "original_filename",
            "content_type",
            "parsed_text",
            "uploaded_at",
        ]
        read_only_fields = ["parsed_text", "uploaded_at"]


class CandidateSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)
    experiences = ExperienceSerializer(many=True, read_only=True)
    educations = EducationSerializer(many=True, read_only=True)
    resumes = ResumeDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Candidate
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "location",
            "headline",
            "summary",
            "skills",
            "experiences",
            "educations",
            "resumes",
            "created_at",
            "updated_at",
        ]


class JobOfferSerializer(serializers.ModelSerializer):
    required_skills = SkillSerializer(many=True, read_only=True)

    class Meta:
        model = JobOffer
        fields = [
            "id",
            "title",
            "company",
            "location",
            "description",
            "required_skills",
            "seniority",
            "is_remote",
            "posted_at",
            "expires_at",
        ]


class ApplicationSerializer(serializers.ModelSerializer):
    candidate = serializers.PrimaryKeyRelatedField(queryset=Candidate.objects.all())
    job_offer = serializers.PrimaryKeyRelatedField(queryset=JobOffer.objects.all())

    class Meta:
        model = Application
        fields = [
            "id",
            "candidate",
            "job_offer",
            "status",
            "score",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]




