from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
import base64
import traceback
import asyncio 
from backend import ai_services, audio_services, database as db
from backend import translation_services
from backend.utils import get_language_codes

db.initialize_db()

app = FastAPI(title="Project Kisan API", version="1.0.0")

class UserRegistration(BaseModel):
    name: str
    state: str
    district: str
    city: str
    password: str

class UserInfo(BaseModel):
    id: int
    name: str
    state: str
    district: str
    city: str

@app.post("/register", status_code=status.HTTP_201_CREATED)
def register_user_endpoint(user_data: UserRegistration):
    success = db.register_user(
        name=user_data.name,
        state=user_data.state,
        district=user_data.district,
        city=user_data.city,
        password=user_data.password
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists. Please choose a different name."
        )
    return {"message": "User registered successfully"}

@app.post("/login", response_model=UserInfo)
def login_user_endpoint(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.login_user(name=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# --- OPTIMIZED & ASYNC-AWARE INTERACTION ENDPOINT ---
@app.post("/process-interaction/")
async def process_user_interaction(
    user_location: str = Form(...),
    language_name: str = Form(...),
    speak_aloud: bool = Form(...),
    audio_file: Optional[UploadFile] = File(None),
    text_query: Optional[str] = Form(""),
    visual_file: Optional[UploadFile] = File(None),
):
    try:
        lang_codes = get_language_codes(language_name)
        transcribed_text = ""
        
        print(f"\n--- Incoming Request for {user_location} ---")

        # 1. Handle audio input (non-blocking)
        if audio_file and audio_file.filename:
            audio_content = await audio_file.read()
            if len(audio_content) > 100:
                print("Processing audio transcription in background thread...")
                # Run synchronous, blocking STT call in a thread to not block the server
                transcribed_text = await asyncio.to_thread(
                    audio_services.transcribe_audio, audio_content, lang_codes["stt"]
                )
                transcribed_text = transcribed_text.strip() if transcribed_text else ""
                print(f"Transcription result: '{transcribed_text}'")
            else:
                print("Audio file too small, skipping transcription")

        # 2. Determine the effective prompt for AI
        effective_prompt = transcribed_text or text_query.strip()
        print(f"Effective prompt: '{effective_prompt}'")

        # 3. Validate if any meaningful query was provided
        if not effective_prompt and not visual_file:
            return JSONResponse(
                status_code=400,
                content={"ai_response": "Please provide a voice message, text query, or an image."}
            )

        # 4. Process the query with AI services 
        ai_response_english = ""
        user_info_for_ai = {"location": user_location} 
        
        try:
            if visual_file:
                print("Processing visual query with AI...")
                visual_content = await visual_file.read()
                ai_response_english = await ai_services.analyze_visuals(
                    prompt=effective_prompt, 
                    media_content=visual_content, 
                    mime_type=visual_file.content_type, 
                    user_info=user_info_for_ai
                )
            elif effective_prompt:
                print("Processing text query with AI...")
                ai_response_english = await ai_services.get_gemini_response(effective_prompt, user_info_for_ai)
            else:
                 ai_response_english = "I see you've uploaded an image. Could you please ask a question about it so I can help you better?"
            
            print(f"AI Response (English): '{ai_response_english[:100]}...'")

        except Exception as e:
            print(f"ERROR: AI service failed: {e}")
            ai_response_english = "I apologize, but I encountered an error while processing your request."

        # 5. Translate response if needed
        if language_name != "English" and ai_response_english:
            print(f"Translating response to {language_name} in background thread...")
            translated_response = await asyncio.to_thread(
                translation_services.translate_text, ai_response_english, lang_codes["translate"]
            )
        else:
            translated_response = ai_response_english
        
        print(f"Final response: '{translated_response[:100]}...'")

        # 6. Synthesize speech if requested 
        audio_output_b64 = None
        if speak_aloud and translated_response:
            print("Synthesizing speech in background thread...")
            audio_output_bytes = await asyncio.to_thread(
                audio_services.synthesize_speech, translated_response, lang_codes["tts"]
            )
            if audio_output_bytes:
                audio_output_b64 = base64.b64encode(audio_output_bytes).decode('utf-8')
                print("Speech synthesis successful")

        # 7. Return final response
        return JSONResponse(content={
            "query_transcript": transcribed_text,
            "ai_response": translated_response,
            "audio_output_b64": audio_output_b64,
        })

    except Exception as e:
        print(f"Unexpected error in process_user_interaction: {e}")
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": "An internal server error occurred."})

@app.get("/")
def read_root(): 
    return {"message": "Welcome to the Project Kisan API."}