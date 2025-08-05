# 🌾 Kisan Mitra: AI-Powered Agricultural Assistant

Kisan Mitra is an advanced, AI-driven agricultural assistant designed to empower Indian farmers by delivering **real-time, data-driven insights** through voice, text, and image inputs. This multi-modal solution provides personalized, multilingual support to address key farming concerns like crop diseases, crop prices, weather forecasts, and government schemes.

---

## ✨ Key Features

### 🔊 1. Multi-Modal Interaction
Interact naturally with the system using any of the following modes:
- **Voice Commands**: Full support for multilingual speech-to-text interaction.
- **Text Queries**: Traditional chat interface to type and receive responses.
- **Image Uploads**: Upload a photo of crops to instantly detect diseases and pests using AI image classification.

### 🌐 2. End-to-End Multilingual Pipeline
- Supports multiple Indian languages including **English, Hindi, Malayalam**, and more.
- Multilingual coverage spans across:
  - Speech recognition (input)
  - Query understanding and processing
  - Final audio/text responses

### 🧠 3. AI Agent with Real-Time Tool Integration
Powered by **Google Gemini Pro** using the **Agno Agent framework**, the assistant can:
- 🔄 **Fetch Live Crops Prices** for any crop and location.
- ☁️ **Provide Local Weather Forecasts** and agri-advisories.
- 📢 **Explore Government Schemes**: Get personalized updates on subsidies, support programs, and agricultural initiatives.

### 🔐 4. User Authentication & Session Management
- Secure login and registration system
- Persistent user sessions
- Chat history stored in a **PostgreSQL** database for continuity

### ⚡ 5. Optimized for Performance
- Built using **asynchronous programming** (`async/await`)
- Intelligent **response caching** for speed and efficiency
- Non-blocking API calls with **HTTPX**

---

## 🛠️ Tech Stack

| Component        | Technology Used                           |
|------------------|--------------------------------------------|
| **Backend**      | Python, FastAPI                            |
| **Frontend**     | Streamlit                                  |
| **AI Core**      | Google Gemini Pro + Agno Agent Framework   |
| **Speech-to-Text** | Google Cloud Speech-to-Text             |
| **Text-to-Speech** | Google Cloud Text-to-Speech             |
| **Translation**  | Google Cloud Translation                   |
| **Database**     | PostgreSQL                                 |
| **Async API Communication** | HTTPX                          |

---

## 🎯 Use Cases

- Diagnose crop issues instantly by uploading photos
- Get daily mandi prices for your region
- Ask questions in your native language (voice or text)
- Understand complex government schemes in simple terms
- Get hyper-local weather updates before sowing or spraying

---

Kisan Mitra is built to reduce the digital divide and bring AI-driven agricultural intelligence directly to the hands of Indian farmers.
