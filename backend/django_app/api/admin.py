from django.contrib import admin

from .models import Skill, Candidate, CandidateSkill, Experience, Education, ResumeDocument, JobOffer, Application


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("id", "name")


class CandidateSkillInline(admin.TabularInline):
    model = CandidateSkill
    extra = 0


class ExperienceInline(admin.TabularInline):
    model = Experience
    extra = 0


class EducationInline(admin.TabularInline):
    model = Education
    extra = 0


class ResumeInline(admin.TabularInline):
    model = ResumeDocument
    extra = 0


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    search_fields = ("first_name", "last_name", "email")
    list_display = ("id", "first_name", "last_name", "email", "location")
    inlines = [CandidateSkillInline, ExperienceInline, EducationInline, ResumeInline]


@admin.register(JobOffer)
class JobOfferAdmin(admin.ModelAdmin):
    search_fields = ("title", "company")
    list_display = ("id", "title", "company", "seniority", "is_remote", "posted_at")
    list_filter = ("seniority", "is_remote")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "candidate", "job_offer", "status", "score", "created_at")
    list_filter = ("status",)

