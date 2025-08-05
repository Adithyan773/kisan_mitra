from google.cloud import translate_v2 as translate
from .config import settings 

def translate_text(text: str, target_language: str) -> str:
    """Translates text to the target language using Google Cloud Translation."""
    translate_client = translate.Client()

    if isinstance(text, bytes):
        text = text.decode("utf-8")

    try:
        result = translate_client.translate(text, target_language=target_language)
        return result["translatedText"]
    except Exception as e:
        print(f"Error in translation: {e}")
        raise