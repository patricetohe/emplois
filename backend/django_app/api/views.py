from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
import os
import tempfile

from .models import Skill, Candidate, JobOffer, Application, ResumeDocument
from .serializers import (
    SkillSerializer,
    CandidateSerializer,
    JobOfferSerializer,
    ApplicationSerializer,
    ResumeDocumentSerializer,
)
from .cv_parser import extract_text_from_file


class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all().order_by("name")
    serializer_class = SkillSerializer
    permission_classes = [AllowAny]


class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidate.objects.all().order_by("-created_at")
    serializer_class = CandidateSerializer
    permission_classes = [AllowAny]

    @action(detail=True, methods=["post"], url_path="upload-resume")
    def upload_resume(self, request, pk=None):
        candidate = self.get_object()
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response({"detail": "Missing file"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Créer le document
        doc = ResumeDocument.objects.create(
            candidate=candidate,
            file=uploaded_file,
            original_filename=uploaded_file.name,
            content_type=getattr(uploaded_file, "content_type", ""),
        )
        
        # Extraire le texte du CV
        try:
            # Créer un fichier temporaire avec un nom unique
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1])
            try:
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_file.flush()
                temp_file.close()  # Fermer le fichier avant de l'utiliser
                
                # Extraire le texte
                extracted_text = extract_text_from_file(temp_file.name, doc.content_type)
                if extracted_text:
                    doc.parsed_text = extracted_text
                    doc.save()
            finally:
                # Nettoyer le fichier temporaire
                try:
                    os.unlink(temp_file.name)
                except OSError:
                    pass  # Ignorer les erreurs de suppression sur Windows
        except Exception as e:
            # Log l'erreur mais ne pas faire échouer l'upload
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors du parsing du CV: {e}")
        
        return Response(ResumeDocumentSerializer(doc).data, status=status.HTTP_201_CREATED)


class JobOfferViewSet(viewsets.ModelViewSet):
    queryset = JobOffer.objects.all().order_by("-posted_at")
    serializer_class = JobOfferSerializer
    permission_classes = [AllowAny]


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all().order_by("-created_at")
    serializer_class = ApplicationSerializer
    permission_classes = [AllowAny]


class ResumeDocumentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ResumeDocument.objects.all().order_by("-uploaded_at")
    serializer_class = ResumeDocumentSerializer
    permission_classes = [AllowAny]

