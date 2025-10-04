"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static

from api.views import SkillViewSet, CandidateViewSet, JobOfferViewSet, ApplicationViewSet, ResumeDocumentViewSet
from api.matching_views import MatchingViewSet
from api.agent_views import AgentViewSet
from api.web_views import agent_test_view, stats_api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', agent_test_view, name='agent_test'),
    path('api/stats/', stats_api, name='stats_api'),
]

router = DefaultRouter()
router.register(r'skills', SkillViewSet)
router.register(r'candidates', CandidateViewSet)
router.register(r'job-offers', JobOfferViewSet)
router.register(r'applications', ApplicationViewSet)
router.register(r'resumes', ResumeDocumentViewSet)
router.register(r'matching', MatchingViewSet, basename='matching')
router.register(r'agent', AgentViewSet, basename='agent')

urlpatterns += [
    path('api/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
