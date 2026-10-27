**English** | [Türkçe](README.tr.md)

# 🎮⚔️ Dwarf Grom — LLM-Powered Smart NPC Game Prototype

> An AI-powered smart NPC interaction system that combines a **Large Language Model (LLM)**, **Speech-to-Text (STT)** and **Text-to-Speech (TTS)** inside the Unity game engine.

The player can talk to **Grom**, the in-game dwarf blacksmith, in natural language, both by **typing** and by **voice**. Grom's behavior changes dynamically based on how consistent and persuasive the player's arguments are, judged by a purpose-built **Hidden Judge** mechanism.

> **Note:** The NPC is designed to speak Turkish. Speech recognition, the character's dialogue and voice synthesis all run in Turkish.

---

## 📌 Key Features

| Feature | Description |
|---|---|
| 🧠 **LLM-Based Dialogue** | Natural-language conversation via the Google Gemini 2.5 Flash API |
| 🎙️ **Voice Interaction** | Speak into the mic → STT → LLM → TTS → NPC voice |
| ⌨️ **Text Interaction** | Text-based dialogue through a chat panel |
| 🤖 **Hidden Judge System** | A hidden judge that decides whether the NPC can be convinced |
| 🏃 **Dynamic NPC Behavior** | The NPC follows or refuses the player depending on whether it was convinced |
| 🎭 **Character Personality** | A consistent character profile designed with prompt engineering |
| 🔊 **ElevenLabs TTS** | Natural NPC voice with multilingual speech synthesis |
| 🔁 **Real-Time Communication** | JSON messaging between Unity and Python over a REST API |

---

## 🏗️ System Architecture

The project consists of two main layers connected by a REST API:

```
┌─────────────────────────────────────────────────────────────┐
│                     UNITY CLIENT (C#)                       │
│                                                             │
│  ┌──────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  │
│  │ ChatUI   │  │ NPC       │  │ Player    │  │ Camera    │  │
│  │ (UI)     │  │Interaction│  │ Movement  │  │ Follow    │  │
│  └────┬─────┘  └─────┬─────┘  └───────────┘  └───────────┘  │
│       │              │                                      │
│       └──────┬───────┘                                      │
│              ▼                                              │
│  ┌───────────────────┐       ┌──────────────┐               │
│  │   CallTheAPI      │       │ SimpleFollow │               │
│  │  (HTTP Client)    │──────▶│ (NPC Follow) │               │
│  └─────────┬─────────┘       └──────────────┘               │
│            │                                                │
└────────────┼────────────────────────────────────────────────┘
             │  HTTP POST (JSON / Base64 Audio)
             ▼
┌─────────────────────────────────────────────────────────────┐
│                  PYTHON BACKEND (FastAPI)                   │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ npc_server.py│  │ npc_brain.py │  │  voice_utils.py  │   │
│  │ (API Server) │  │ (LLM Logic)  │  │  (STT / TTS)     │   │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │
│         │                 │                    │            │
│         │         ┌───────▼───────┐   ┌────────▼─────────┐  │
│         │         │  Gemini API   │   │  ElevenLabs API  │  │
│         │         │  (2.5 Flash)  │   │  (Multilingual)  │  │
│         │         └───────────────┘   └──────────────────┘  │
│         │                                      │            │
│         │         ┌────────────────────────────┘            │
│         │         │  Google Speech Recognition              │
│         │         └─────────────────────────────            │
└─────────┼───────────────────────────────────────────────────┘
          │
          ▼  JSON Response: { reply, isConvinced, audio(base64) }
```

---

## 📂 Project Structure

```
Dwarf Grom Game NEW/
│
├── Assets/
│   ├── C# SCRİPTS/              # Unity-side scripts
│   │   ├── CallTheAPI.cs         # HTTP communication with the Python backend (Singleton)
│   │   ├── ChatUI.cs             # Chat interface and microphone recording
│   │   ├── NPCInteraction.cs     # Player–NPC distance detection and interaction trigger
│   │   ├── SimpleFollow.cs       # NPC follow behavior driven by the LLM's decision
│   │   ├── PlayerMovement.cs     # Third-person character movement (CharacterController)
│   │   ├── CameraFollow.cs       # Mouse-driven third-person camera
│   │   └── AudioUtils.cs         # AudioClip → WAV byte conversion
│   │
│   ├── Animations/               # Character animation files
│   ├── Scenes/                   # Unity scene files
│   └── RPGPP_LT/                 # Low-poly RPG assets
│
├── npc_LLM/                      # Python backend
│   ├── npc_server.py             # Asynchronous FastAPI server
│   ├── npc_brain.py              # LLM integration and character logic
│   ├── voice_utils.py            # STT/TTS audio processing module
│   └── requirements.txt          # Python dependencies
│
└── README.md
```

---

## 🧠 Technical Details

### Unity Side (C#)

#### `CallTheAPI.cs` — API Client
- Provides global access via the **Singleton pattern**
- Sends HTTP POST requests to the Python backend with `UnityWebRequest`
- Sends text messages as JSON and audio as **Base64**
- Decodes the audio in the NPC's reply (Base64 MP3) and plays it through an `AudioSource`
- Broadcasts the NPC's reply and convinced state to other components through `UnityEvent`
- **Coroutine**-based asynchronous workflow

#### `ChatUI.cs` — User Interface
- TextMeshPro-based chat panel (scrollable log with ScrollRect)
- Chat window toggled with the **X key**
- Microphone recording by **holding V** (push-to-talk)
- Records audio with `Microphone.Start/End` and converts it to WAV with `AudioUtils`
- Player movement and camera control are disabled while the chat is open

#### `NPCInteraction.cs` — Interaction Trigger
- Player–NPC distance calculated with `Vector3.Distance`
- Shows an interaction prompt within a set distance
- Visualizes the interaction range in the Editor with Gizmos

#### `SimpleFollow.cs` — NPC Follow System
- Sets NPC behavior from `CallTheAPI.IsConvinced`
- Follows the target with `Vector3.MoveTowards` and stops at `stoppingDistance`
- Walk/idle animation transitions through Animator parameters
- Reacts instantly by subscribing to the `OnNPCConvinced` event

#### `PlayerMovement.cs` — Player Movement
- Camera-relative third-person movement with `CharacterController.SimpleMove`
- Smooth character rotation with `Quaternion.RotateTowards`
- Movement fully disabled while the chat panel is open

#### `CameraFollow.cs` — Camera Control
- Orbital camera movement with mouse input
- Pitch clamping for a natural viewing angle

---

### Python Backend

#### `npc_server.py` — FastAPI Server
- **Asynchronous** HTTP API server (FastAPI + Uvicorn)
- **Endpoints:**
  - `POST /chat` — Takes text or audio input, returns the LLM reply and optional TTS audio
  - `POST /chat/voice` — Voice reply endpoint (MP3 stream)
  - `POST /tts` — Standalone text-to-speech
  - `POST /stt` — Standalone speech-to-text (file upload)
  - `GET /voice/status` — Voice service health check
- **Session management:** chat sessions per `player_id` (groundwork for multiplayer)
- Routes Base64 audio to STT and passes the transcribed text to the LLM
- Error handling: rate limit (429), authentication (401/403), safety filter and general errors

#### `npc_brain.py` — NPC AI Brain
- Structured chat session with the **Google Gemini 2.5 Flash** model
- **Prompt engineering:**
  - Character personality (a grumpy dwarf blacksmith who loves gold and speaks in an old-fashioned Turkish style)
  - Hidden Judge rules (conditions for being convinced, refusal scenarios)
  - Structured JSON response schema (`response` + `isConvinced`)
- **Rule-based responses:** fast reactions via keyword detection (regex that handles Turkish suffixes)
- **Fallback wait messages:** progressive waiting messages when the API is slow
- Multithreaded API calls (run in the background without blocking the main thread)

#### `voice_utils.py` — Audio Processing Module
- **Text-to-Speech (TTS):**
  - ElevenLabs SDK v2.x integration (with backward-compatible fallbacks)
  - Turkish speech synthesis with the `eleven_multilingual_v2` model
  - Adaptive API calls compatible with multiple SDK versions
  - REST API fallback mechanism
- **Speech-to-Text (STT):**
  - Google Speech Recognition API (Turkish)
  - Automatic correction of common recognition errors with `correct_speech_text()`
  - Speech recognition from WAV files and microphone input
- **Push-to-talk:** record by holding a keyboard key (Space)

---

### Hidden Judge System

The AI mechanism that evaluates the player's attempt to convince the NPC:

```
Player Message → Gemini LLM → JSON { response, isConvinced }
                    │
                    ▼
            ┌──────────────┐
            │  Evaluation  │
            │   Criteria   │
            └──────┬───────┘
                   │
         ┌─────────┼───────────┐
         ▼         ▼           ▼
   ✅ Convinced  ❌ Refuse   ⏳ Wait
    - Father      - Threats    - First attempt
      topic       - Coercion   - Weak
    - Gold        - Incoherent   argument
      offer         argument
    - Valid
      evidence
```

- If the player brings up the father topic and approaches sincerely → convinced
- If gold is offered or a reasonable payment is promised → convinced
- If there are threats or coercion → never convinced
- On the first attempt → not convinced (at least 2 rounds are required)

---

## 🎮 Gameplay and Controls

| Key | Action |
|---|---|
| `W / A / S / D` | Move the character |
| `Mouse` | Control the camera |
| `X` | Open/close the chat panel |
| `V` (hold) | Voice chat (push-to-talk) |
| `ESC` | Close the chat panel |

### Game Flow
1. The player moves freely in the 3D world
2. An interaction prompt appears when approaching Grom
3. The player opens the chat panel with `X` or speaks with `V`
4. Grom evaluates what the player said and replies in character
5. If the player is convincing enough, Grom starts following them

---

## 🛠️ Installation and Usage

### Requirements
- **Unity 6** (URP — Universal Render Pipeline)
- **Python 3.8+**
- **Gemini API key** ([Google AI Studio](https://aistudio.google.com/app/apikey))
- **ElevenLabs API key** (optional, for TTS) ([ElevenLabs](https://elevenlabs.io/))

### 1. Set Up the Python Backend

```bash
cd npc_LLM
pip install google-generativeai fastapi uvicorn pydantic elevenlabs SpeechRecognition pyaudio keyboard
```

### 2. Set the API Keys

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your_gemini_api_key"
$env:ELEVENLABS_API_KEY="your_elevenlabs_api_key"   # Optional
```

**macOS / Linux:**
```bash
export GEMINI_API_KEY="your_gemini_api_key"
export ELEVENLABS_API_KEY="your_elevenlabs_api_key"   # Optional
```

### 3. Start the Server

```bash
cd npc_LLM
uvicorn npc_server:app --reload
```

Once started, the server runs at `http://127.0.0.1:8000`.

### 4. Open the Unity Project

Open the project in Unity Hub and run the scene.

---

## 🔧 Technologies Used

| Category | Technology |
|---|---|
| **Game Engine** | Unity 6 (URP) |
| **Languages** | C# (Unity), Python (backend) |
| **LLM** | Google Gemini 2.5 Flash |
| **API Framework** | FastAPI + Uvicorn |
| **Text-to-Speech** | ElevenLabs (eleven_multilingual_v2) |
| **Speech Recognition** | Google Speech Recognition |
| **Data Exchange** | REST API, JSON, Base64 |
| **UI Framework** | TextMeshPro, Unity UI |
| **3D Models** | Low Poly Modular Character Pack |
| **Render Pipeline** | Universal Render Pipeline (URP) |

---

## 📈 Future Improvements

- [ ] Multiple NPCs (AI characters with different personalities)
- [ ] Character memory (long-term conversation context)
- [ ] Sentiment analysis and facial expression integration
- [ ] Quest-based dialogue system (quest chains)
- [ ] Local LLM support (Ollama integration)
- [ ] More advanced NPC behavior trees
- [ ] Real-time streaming replies over WebSocket

---

## 📄 License

This project was developed for educational, research and prototyping purposes.

## Gameplay Video

[![Click to watch the video](https://img.youtube.com/vi/wW9WMaQVq_k/0.jpg)](https://www.youtube.com/watch?v=wW9WMaQVq_k)
