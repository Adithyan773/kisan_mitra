import streamlit as st
import requests
import base64
from PIL import Image
from st_audiorec import st_audiorec
import time

# --- CONFIGURATION ---
API_BASE_URL = "http://127.0.0.1:8000"
st.set_page_config(page_title="Project Kisan 🧑‍🌾", layout="centered", initial_sidebar_state="auto")

# --- STYLING ---
st.markdown("""
<style>
    .main .block-container { padding-top: 2rem; padding-bottom: 6rem; }
    .hidden-audio { display: none; }
    .st-emotion-cache-1y4p8pa { max-width: 70rem; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state: 
    st.session_state.messages = []
if "user_info" not in st.session_state: 
    st.session_state.user_info = None
if "page" not in st.session_state:
    st.session_state.page = "login"
if "autoplay_audio" not in st.session_state: 
    st.session_state.autoplay_audio = None
if "processing_audio" not in st.session_state: 
    st.session_state.processing_audio = False
if "last_audio_hash" not in st.session_state: 
    st.session_state.last_audio_hash = None

def make_api_call(audio_bytes=None, visual_file=None, text_query=""):
    user = st.session_state.user_info
    
    spinner_message = "Kisan Mitra is analyzing your request..."
    if audio_bytes:
        spinner_message = "Transcribing audio and preparing your response..."

    with st.chat_message("assistant"):
        with st.spinner(spinner_message):
            try:
                files = {}
                if audio_bytes: 
                    files['audio_file'] = ('audio.wav', audio_bytes, 'audio/wav')
                if visual_file: 
                    files['visual_file'] = (visual_file.name, visual_file.getvalue(), visual_file.type)
                
                user_location = f"{user['city']}, {user['district']}, {user['state']}"
                data = {
                    "user_location": user_location, 
                    "language_name": user.get("language", "English"), 
                    "speak_aloud": user.get("speak_aloud", True), 
                    "text_query": text_query or ""
                }
                
                response = requests.post(f"{API_BASE_URL}/process-interaction/", files=files, data=data, timeout=180)
                response.raise_for_status()
                result = response.json()
                
                if audio_bytes:
                    transcript = result.get("query_transcript", "").strip()
                    if transcript:
                        st.session_state.messages[-1]["text"] = f"🎙️: *\"{transcript}\"*"
                    else:
                        st.session_state.messages[-1]["text"] = "🎙️: *(No clear speech detected)*"
                
                ai_response_text = result.get("ai_response", "Sorry, I couldn't get a response.")
                st.session_state.messages.append({"role": "assistant", "text": ai_response_text})
                
                audio_b64 = result.get("audio_output_b64")
                if audio_b64 and user.get("speak_aloud"):
                    st.session_state.autoplay_audio = f'<audio class="hidden-audio" autoplay><source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3"></audio>'
                
                st.session_state.processing_audio = False
                st.rerun()
                
            except requests.exceptions.RequestException as e:
                st.error(f"Network error: {e}. Is the backend server running?")
                st.session_state.messages.append({"role": "assistant", "text": f"Error: Could not connect to the server. Please ensure the backend is running."})
            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.session_state.messages.append({"role": "assistant", "text": f"An unexpected error occurred: {e}"})
            finally:
                st.session_state.processing_audio = False

def show_login_page():
    st.header("Login to Project Kisan 🧑‍🌾")
    with st.form("login_form"):
        name = st.text_input("Username (Your Name)")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if not name or not password:
                st.error("Please enter both username and password.")
            else:
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/login",
                        data={"username": name, "password": password}
                    )
                    if response.status_code == 200:
                        st.success("Login successful!")
                        st.session_state.user_info = response.json()
                        st.session_state.page = "chat"
                        st.rerun()
                    else:
                        st.error(f"Login failed: {response.json().get('detail', 'Invalid credentials')}")
                except requests.exceptions.ConnectionError:
                    st.error("Connection failed. Is the backend server running?")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
    
    st.markdown("---")
    if st.button("Don't have an account? Register here"):
        st.session_state.page = "register"
        st.rerun()

def show_register_page():
    st.header("Register for Project Kisan 🧑‍🌾")
    with st.form("register_form"):
        st.write("Please provide your details to create an account.")
        name = st.text_input("Full Name (This will be your username)")
        state = st.text_input("State (e.g., Karnataka)")
        district = st.text_input("District (e.g., Kolar)")
        city = st.text_input("City / Town / Village")
        password = st.text_input("Password", type="password")
        
        submitted = st.form_submit_button("Register")
        if submitted:
            if not all([name, state, district, city, password]):
                st.error("Please fill out all fields.")
            else:
                user_data = {
                    "name": name, "state": state, "district": district,
                    "city": city, "password": password
                }
                try:
                    response = requests.post(f"{API_BASE_URL}/register", json=user_data)
                    if response.status_code == 201:
                        st.success("Registration successful! Please log in.")
                        st.session_state.page = "login"
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Registration failed: {response.json().get('detail', 'Unknown error')}")
                except requests.exceptions.ConnectionError:
                    st.error("Connection failed. Is the backend server running?")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")

    st.markdown("---")
    if st.button("Already have an account? Login here"):
        st.session_state.page = "login"
        st.rerun()

def show_chat_page():
    with st.sidebar:
        st.header(f"Welcome, {st.session_state.user_info['name']}!")
        st.markdown(f"📍 {st.session_state.user_info['city']}, {st.session_state.user_info['state']}")
        st.markdown("---")
        
        st.header("Controls")
        st.session_state.user_info["language"] = st.selectbox("Response Language", options=[
            "English", "Hindi (हिन्दी)", "Kannada (ಕನ್ನಡ)", "Tamil (தமிழ்)", 
            "Telugu (తెలుగు)", "Malayalam (മലയാളം)", "Bengali (বাংলা)"
        ])
        st.session_state.user_info["speak_aloud"] = st.checkbox("Speak response aloud", value=True)
        st.markdown("---")
        
        st.subheader("Upload a Photo")
        uploaded_image = st.file_uploader("Upload a photo of your crop", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        st.markdown("---")
        
        st.subheader("Record Audio")
        if not st.session_state.processing_audio:
            wav_audio_data = st_audiorec()
            if wav_audio_data is not None:
                audio_hash = hash(wav_audio_data)
                if audio_hash != st.session_state.last_audio_hash:
                    st.session_state.last_audio_hash = audio_hash
                    st.session_state.processing_audio = True
                    st.session_state.messages.append({"role": "user", "text": "🎙️ Processing voice message..."})
                    make_api_call(audio_bytes=wav_audio_data, visual_file=uploaded_image)
        else:
            st.info("🎙️ Processing your voice message...")
        
        st.markdown("---")
        if st.button("Logout"): 
            for key in st.session_state.keys():
                del st.session_state[key]
            st.session_state.page = "login"
            st.rerun()

    st.header("Kisan Mitra Assistant")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("image"): st.image(msg["image"], width=200)
            if msg.get("text"): st.markdown(msg["text"])

    if st.session_state.autoplay_audio:
        st.markdown(st.session_state.autoplay_audio, unsafe_allow_html=True)
        st.session_state.autoplay_audio = None

    if not st.session_state.processing_audio:
        if prompt := st.chat_input("Ask about crops, prices, or schemes..."):
            st.session_state.messages.append({"role": "user", "text": prompt})
            make_api_call(visual_file=uploaded_image, text_query=prompt)
    else:
        st.chat_input("Processing voice message...", disabled=True)

# --- MAIN ROUTER ---
if st.session_state.page == "login":
    show_login_page()
elif st.session_state.page == "register":
    show_register_page()
elif st.session_state.page == "chat" and st.session_state.user_info:
    show_chat_page()
else:
    st.session_state.page = "login"
    st.rerun()