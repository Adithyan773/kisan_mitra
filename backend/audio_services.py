from google.cloud import speech, texttospeech
from pydub import AudioSegment
import io
import wave
import traceback

print("✅ Running audio_services.py with EXPLICIT sample rate.")

def transcribe_audio(content: bytes, language_code: str) -> str:
    
    try:
        print(f"Transcribing audio: {len(content)} bytes, language: {language_code}")

        if not content or len(content) < 100:
            print("Audio content is too small or empty")
            return ""

        try:
            sound = AudioSegment.from_file(io.BytesIO(content))
        except Exception as e:
            print(f"Failed to load audio with pydub: {e}")
            return ""

        print(f"Audio properties: channels={sound.channels}, frame_rate={sound.frame_rate}, duration={len(sound)}ms")

        if len(sound) < 500:
            print("Audio is too short (less than 0.5 seconds)")
            return ""

        if sound.channels > 1:
            print(f"Converting from {sound.channels} channels to mono")
            sound = sound.set_channels(1)

        target_sample_rate = sound.frame_rate
        if target_sample_rate < 8000:
            target_sample_rate = 16000
            sound = sound.set_frame_rate(target_sample_rate)
            print(f"Upsampled to {target_sample_rate} Hz")
        elif target_sample_rate > 48000:
            target_sample_rate = 48000
            sound = sound.set_frame_rate(target_sample_rate)
            print(f"Downsampled to {target_sample_rate} Hz")

        sound = sound.set_sample_width(2)

        mono_wav_buffer = io.BytesIO()
        sound.export(mono_wav_buffer, format="wav")
        mono_content = mono_wav_buffer.getvalue()

        print(f"Processed audio: {len(mono_content)} bytes")

        final_sample_rate = 0
        try:
            with wave.open(io.BytesIO(mono_content), 'rb') as wav_file:
                frames = wav_file.getnframes()
                final_sample_rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                print(f"WAV validation: frames={frames}, sample_rate={final_sample_rate}, channels={channels}")
                if frames == 0:
                    print("WAV file has no audio frames")
                    return ""
        except Exception as e:
            print(f"WAV validation failed: {e}")
            return ""

        client = speech.SpeechClient()
        audio = speech.RecognitionAudio(content=mono_content)

       
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=final_sample_rate, 
            language_code=language_code,
            audio_channel_count=1,
            enable_automatic_punctuation=True,
            use_enhanced=True,
            profanity_filter=True,
            max_alternatives=1,
        )

        print(f"Sending request to Google Speech-to-Text API with sample rate {final_sample_rate}...")
        response = client.recognize(config=config, audio=audio)

        if response and response.results:
            transcript = response.results[0].alternatives[0].transcript.strip()
            confidence = response.results[0].alternatives[0].confidence
            print(f"Transcription successful: '{transcript}' (confidence: {confidence:.2f})")
            return transcript
        else:
            print("No transcription results returned by API")
            return ""

    except Exception as e:
        print(f"Error during transcription: {e}")
        traceback.print_exc()
        return ""

def synthesize_speech(text: str, language_code: str) -> bytes:
    """Converts text to speech using Google Cloud Text-to-Speech."""
    try:
        print(f"Synthesizing speech: '{text[:50]}...' in {language_code}")

        if not text.strip():
            print("No text to synthesize")
            return b""

        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0
        )

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        print(f"Speech synthesis successful: {len(response.audio_content)} bytes")
        return response.audio_content

    except Exception as e:
        print(f"Error in speech synthesis: {e}")
        traceback.print_exc()
        return b""