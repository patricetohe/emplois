import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def extract_text_from_file(file_path: str, content_type: str) -> Optional[str]:
    """
    Extrait le texte d'un fichier CV selon son type.
    
    Args:
        file_path: Chemin vers le fichier
        content_type: Type MIME du fichier
        
    Returns:
        Texte extrait ou None en cas d'erreur
    """
    try:
        if content_type == 'application/pdf':
            return _extract_from_pdf(file_path)
        elif content_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                             'application/msword']:
            return _extract_from_docx(file_path)
        elif content_type == 'text/plain':
            return _extract_from_txt(file_path)
        else:
            logger.warning(f"Type de fichier non supporté: {content_type}")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du texte: {e}")
        return None


def _extract_from_pdf(file_path: str) -> Optional[str]:
    """Extrait le texte d'un PDF."""
    try:
        import PyPDF2
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
    except ImportError:
        logger.error("PyPDF2 non installé. Installez avec: pip install PyPDF2")
        return None
    except Exception as e:
        logger.error(f"Erreur extraction PDF: {e}")
        return None


def _extract_from_docx(file_path: str) -> Optional[str]:
    """Extrait le texte d'un document Word."""
    try:
        from docx import Document
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except ImportError:
        logger.error("python-docx non installé. Installez avec: pip install python-docx")
        return None
    except Exception as e:
        logger.error(f"Erreur extraction DOCX: {e}")
        return None


def _extract_from_txt(file_path: str) -> Optional[str]:
    """Extrait le texte d'un fichier texte."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except UnicodeDecodeError:
        # Essayer avec d'autres encodages
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read().strip()
        except Exception as e:
            logger.error(f"Erreur extraction TXT: {e}")
            return None
    except Exception as e:
        logger.error(f"Erreur extraction TXT: {e}")
        return None
