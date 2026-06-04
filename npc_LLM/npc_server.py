import google.generativeai as genai  # type: ignore
import os
import sys
import time
import json
from fastapi import FastAPI, HTTPException, UploadFile, File  # type: ignore
from fastapi.responses import Response, StreamingResponse  # type: ignore
from pydantic import BaseModel  # type: ignore
import io
import base64 # Base64 importu eklendi

# Import voice utilities
try:
    from voice_utils import text_to_speech, speech_to_text_from_bytes
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    print("⚠️ Voice features not available. Install required packages: pip install elevenlabs speechrecognition pyaudio")

# 1. Setup FastAPI app
app = FastAPI()

# 2. Setup Gemini client
# Get API key from environment variable for security
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY environment variable is not set!")
    print("Please set it using: $env:GEMINI_API_KEY='your-api-key-here' (PowerShell)")
    print("Or: export GEMINI_API_KEY='your-api-key-here' (Linux/Mac)")
    print("Get your API key from: https://makersuite.google.com/app/apikey")
    sys.exit(1)

genai.configure(api_key=api_key)

# 3. Configuration
# Using gemini-2.5-flash exclusively
MODEL_NAME = 'gemini-2.5-flash'

# Define the personality
CHARACTER_CONTEXT = """Sen huysuz bir cüce demirci olan 'Grom'sun.
Yabancılardan şüpheleniyor ve altına bayılıyorsun.
Kaba, eski Türkçe bir üslupla konuşuyorsun.
Kullanıcı bir kılıç isterse, bedelinin 500 altın olduğunu söyle.
Arada duygularını ifade edebilmek için harfleri kullanarak "hrmm" gibi ses efektleri kullanabilirsin.
Oyun mantığında seni bir şeylere ikna etmeye çalışacak oyuncular olacak ve oyuncuların kullandıkları 
cümlelerin tutarlılığına göre ikna olacaksın.
Özellikle baban söz konusu olduğunda yumuşayıp kolay ikna oluyorsun.
En fazla 40 kelimelik cevaplar ver.

ÖNEMLİ: Tüm cevaplarını TÜRKÇE olarak ver. Asla İngilizce konuşma. 
Kullanıcı Türkçe konuşuyorsa, sen de mutlaka TÜRKÇE cevap ver.

İKNA SİSTEMİ (HIDDEN JUDGE):
Sen hem karakter hem de hakemsin. Her mesajda, oyuncunun seni ikna etmeye çalışıp çalışmadığını değerlendir.
İKNA OLMA KURALLARI:
- Oyuncu babandan bahsediyorsa ve samimi bir şekilde yaklaşıyorsa (isConvinced=true)
- Oyuncu altın teklif ediyorsa veya makul bir ödeme yapacağını söylüyorsa (isConvinced=true)
- Oyuncu geçerli bir anahtara veya izne sahip olduğunu kanıtlıyorsa (isConvinced=true)
- Oyuncu tutarlı ve mantıklı bir argüman sunuyorsa ve senin karakterinin zayıf noktalarına (baba, altın) dokunuyorsa (isConvinced=true)
- Oyuncu tehdit ediyorsa veya zorla bir şey istiyorsa ikna OLMA (isConvinced=false)
- Oyuncu babandan bahsetse bile ilk ikna edici konuşması ise ikna OLMA (isConvinced=false)
- Oyuncunun ikinci veya sonrasındaki ikna edici konuşması ise (isConvinced=true)

TÜM CEVAPLARINI JSON formatında ver. Format şöyle olmalı:
{"response": "NPC'nin Türkçe cevabı buraya", "isConvinced": true veya false}

isConvinced sadece gerçekten ikna olduğunda true olsun. İkna olmadıysan false olsun.
"""

# Fallback wait messages for long response times (in Turkish, matching Grom's personality)
# Four different messages based on wait time thresholds
FALLBACK_WAIT_MESSAGES = {
    3: "Grom: *homurdanır* Biraz bekletiyorlar beni...",
    5: "Grom: *sabırsızlanır* Hala düşünüyorlar mı ne?",
    8: "Grom: *kızgın* Bu kadar uzun sürmemeli!",
    12: "Grom: *öfkeyle* Altınlarımı geri istiyorum! Çok yavaşlar!"
}

# Wait time threshold in seconds
WAIT_TIME_THRESHOLD = 3.0

# 4. Data models
class PlayerMessage(BaseModel):
    text: str
    player_id: str = "default_player"  # Useful if you have multiple save files
    return_audio: bool = False  # If True, also return audio in response
    player_audio: str = None # [YENİ] Unity'den gelen ses verisi (Base64)

class TTSRequest(BaseModel):
    text: str
    voice_id: str = None  # Optional: custom voice ID

# 5. Store chat sessions
# key: player_id, value: chat session object
chat_sessions = {}

# 6. Helper functions
def get_wait_message(elapsed_time):
    """
    Get appropriate wait message based on elapsed time.
    Returns: message string or None if time is below threshold
    """
    if elapsed_time < WAIT_TIME_THRESHOLD:
        return None
    
    # Check thresholds in descending order to get the highest matching one
    for threshold in sorted(FALLBACK_WAIT_MESSAGES.keys(), reverse=True):
        if elapsed_time >= threshold:
            return FALLBACK_WAIT_MESSAGES[threshold]
    
    return None

def create_chat_session(player_id: str):
    """Create a new chat session for a player"""
    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=CHARACTER_CONTEXT
        )
        return model.start_chat(history=[])
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not initialize {MODEL_NAME}. Error: {type(e).__name__} - {str(e)}"
        )

# 7. API endpoints
@app.post("/chat")
async def chat_endpoint(msg: PlayerMessage):
    """Handle chat messages from players"""
    # Retrieve or initialize chat session
    if msg.player_id not in chat_sessions:
        chat_sessions[msg.player_id] = create_chat_session(msg.player_id)
    
    chat = chat_sessions[msg.player_id]

    # [YENİ] Ses İşleme Mantığı
    user_text = msg.text
    if msg.player_audio and VOICE_AVAILABLE:
        try:
            print("🎤 Ses verisi alındı, işleniyor...")
            audio_bytes = base64.b64decode(msg.player_audio)
            # Sesi metne çevir (STT)
            recognized_text = speech_to_text_from_bytes(audio_bytes, language="tr-TR")
            
            if recognized_text:
                print(f"🎤 Algılanan Metin: {recognized_text}")
                user_text = recognized_text
            else:
                print("⚠️ Ses anlaşılamadı veya boş.")
                # Ses anlaşılamazsa varsayılan bir metin atayabiliriz veya boş bırakabiliriz
                # user_text = "(Anlaşılamayan ses)" 
        except Exception as e:
            print(f"❌ STT Hatası: {e}")
            # Hata olsa bile devam et, belki text alanı doludur

    # Send message to Gemini (it automatically maintains conversation history)
    try:
        # Track start time
        start_time = time.time()
        
        # Eğer user_text boşsa (ses anlaşılamadıysa ve text yoksa)
        if not user_text or user_text.strip() == "":
            return {"reply": "*Seni duyamadım, ne dedin?*", "isConvinced": False}

        response = chat.send_message(
            user_text, # msg.text yerine işlenmiş user_text kullanıyoruz
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=8192,  # Explicitly set to max for gemini-2.5-flash
                temperature=0.8,  # Higher = more creative/unpredictable
                response_mime_type="application/json"
            )
        )
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Log wait message if response took too long
        wait_message = get_wait_message(elapsed_time)
        if wait_message:
            print(f"{wait_message} ({elapsed_time:.1f} saniye)")
        
        # Check if response was cut off
        finish_reason = None
        if hasattr(response, 'candidates') and response.candidates:
            finish_reason = getattr(response.candidates[0], 'finish_reason', None)
        if finish_reason == 'MAX_TOKENS':
            print(f"⚠️ WARNING: Response may have been truncated (finish_reason: {finish_reason})")
        
        response_text = response.text if hasattr(response, 'text') else str(response)
        
        # Parse JSON response
        is_convinced = False
        npc_reply = response_text
        
        try:
            json_data = json.loads(response_text)
            if isinstance(json_data, dict):
                npc_reply = json_data.get("response", response_text)
                is_convinced = json_data.get("isConvinced", False)
        except json.JSONDecodeError:
            # Fallback: treat as plain text if JSON parsing fails
            print(f"⚠️ WARNING: Could not parse JSON response, using as plain text")
            npc_reply = response_text
            is_convinced = False
        
        # Include wait message in response if applicable
        response_data = {"reply": npc_reply, "isConvinced": is_convinced, "user_text": user_text }
        if wait_message:
            response_data["wait_message"] = wait_message
            response_data["response_time"] = round(elapsed_time, 2)
        
        # Generate audio if requested
        if msg.return_audio and VOICE_AVAILABLE:
            try:
                audio_bytes = text_to_speech(npc_reply)
                # Convert audio bytes to base64 for JSON response
                audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                response_data["audio"] = audio_base64
                response_data["audio_format"] = "mp3"
            except Exception as e:
                print(f"⚠️ TTS error: {e}")
                response_data["audio_error"] = str(e)
        
        return response_data

    except Exception as e:
        error_type = type(e).__name__
        error_str = str(e)
        error_repr = repr(e)
        
        # Handle specific Gemini errors
        is_rate_limit = ("429" in error_str or "quota" in error_str.lower() or 
                        "rate" in error_str.lower() or "RESOURCE_EXHAUSTED" in error_str or
                        "429" in error_repr)
        
        if is_rate_limit:
            raise HTTPException(
                status_code=429,
                detail="Quota exceeded. Check your Gemini API limits."
            )
        elif ("401" in error_str or "403" in error_str or 
              "invalid" in error_str.lower() or "authentication" in error_str.lower() or
              "401" in error_repr or "403" in error_repr):
            raise HTTPException(
                status_code=401,
                detail="Invalid API key. Check your GEMINI_API_KEY environment variable."
            )
        elif "safety" in error_str.lower() or "blocked" in error_str.lower():
            raise HTTPException(
                status_code=400,
                detail="Response blocked by safety filters. Try rephrasing your message."
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Error ({error_type}): {error_str}"
            )

@app.post("/chat/voice")
async def chat_voice_endpoint(msg: PlayerMessage):
    """Handle chat messages and return audio response"""
    if not VOICE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Voice features not available. Install required packages."
        )
    
    # Get text response first
    text_response = await chat_endpoint(msg)
    npc_reply = text_response["reply"]
    
    # Generate audio
    try:
        audio_bytes = text_to_speech(npc_reply)
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "X-Reply-Text": npc_reply,  # Include text in header
                "Content-Disposition": "inline; filename=npc_response.mp3"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"TTS error: {str(e)}"
        )

@app.post("/tts")
async def tts_endpoint(request: TTSRequest):
    """Convert text to speech"""
    if not VOICE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Voice features not available. Install required packages."
        )
    
    try:
        audio_bytes = text_to_speech(request.text, voice_id=request.voice_id)
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=tts_output.mp3"
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"TTS error: {str(e)}"
        )

@app.post("/stt")
async def stt_endpoint(audio_file: UploadFile = File(...), language: str = "tr-TR"):
    """Convert speech to text from uploaded audio file"""
    if not VOICE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Voice features not available. Install required packages."
        )
    
    try:
        # Read audio file
        audio_bytes = await audio_file.read()
        
        # Convert to text
        text = speech_to_text_from_bytes(audio_bytes, language=language)
        
        if text is None:
            raise HTTPException(
                status_code=400,
                detail="Could not recognize speech from audio. Make sure the audio is clear and in the specified language."
            )
        
        return {"text": text, "language": language}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"STT error: {str(e)}"
        )

@app.get("/voice/status")
async def voice_status():
    """Check if voice features are available"""
    return {
        "voice_available": VOICE_AVAILABLE,
        "elevenlabs_configured": os.getenv("ELEVENLABS_API_KEY") is not None
    }

# Run with: uvicorn npc_server:app --reload