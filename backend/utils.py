
LANGUAGE_MAP = {
    
    "English": {"stt": "en-IN", "translate": "en", "tts": "en-IN"},
    "Hindi (हिन्दी)": {"stt": "hi-IN", "translate": "hi", "tts": "hi-IN"},
    "Kannada (ಕನ್ನಡ)": {"stt": "kn-IN", "translate": "kn", "tts": "kn-IN"},
    "Tamil (தமிழ்)": {"stt": "ta-IN", "translate": "ta", "tts": "ta-IN"},
    "Telugu (తెలుగు)": {"stt": "te-IN", "translate": "te", "tts": "te-IN"},
    "Malayalam (മലയാളം)": {"stt": "ml-IN", "translate": "ml", "tts": "ml-IN"},
    "Bengali (বাংলা)": {"stt": "bn-IN", "translate": "bn", "tts": "bn-IN"},
    "Gujarati (ગુજરાતી)": {"stt": "gu-IN", "translate": "gu", "tts": "gu-IN"},
    "Marathi (मराठी)": {"stt": "mr-IN", "translate": "mr", "tts": "mr-IN"},
    "Urdu (اردو)": {"stt": "ur-IN", "translate": "ur", "tts": "ur-IN"},
    "Punjabi (ਪੰਜਾਬੀ)": {"stt": "pa-IN", "translate": "pa", "tts": "pa-IN"},
}

def get_language_codes(language_name: str) -> dict:
    """Returns the API language codes for a given language name."""
    primary_name = language_name.split(" ")[0]
    
    for key, value in LANGUAGE_MAP.items():
        if key.startswith(primary_name):
            return value
            
    return LANGUAGE_MAP["English"] 