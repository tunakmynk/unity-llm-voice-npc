"""
Voice utilities for NPC system
- Text-to-Speech using ElevenLabs
- Speech-to-Text using Google Speech Recognition
"""
import os
import sys
try:
    from elevenlabs.client import ElevenLabs  # type: ignore
    # Try to import all components
    try:
        from elevenlabs import generate, play, Voice, VoiceSettings  # type: ignore
        # Try to import set_api_key (may not exist in newer versions)
        try:
            from elevenlabs import set_api_key  # type: ignore
        except ImportError:
            set_api_key = None  # Newer SDK versions don't use this
    except ImportError:
        # Fallback: try importing just the basics
        try:
            from elevenlabs import generate, play  # type: ignore
            Voice = None
            VoiceSettings = None
            set_api_key = None
        except ImportError:
            generate = None
            play = None
            Voice = None
            VoiceSettings = None
            set_api_key = None
    ELEVENLABS_SDK_AVAILABLE = True
except ImportError:
    # Fallback for older versions or if client import fails
    try:
        from elevenlabs import generate, play, set_api_key  # type: ignore
        ElevenLabs = None
        Voice = None
        VoiceSettings = None
        ELEVENLABS_SDK_AVAILABLE = True
    except ImportError:
        generate = None
        play = None
        set_api_key = None
        ElevenLabs = None
        Voice = None
        VoiceSettings = None
        ELEVENLABS_SDK_AVAILABLE = False

# Speech recognition for STT (Google Speech Recognition)
try:
    import speech_recognition as sr  # type: ignore
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    sr = None

# Keyboard library for push-to-talk
try:
    import keyboard  # type: ignore
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    keyboard = None

import tempfile
import threading
import time as time_module
import re

# Common word replacements for speech recognition corrections
# Add words that are commonly misrecognized here
WORD_REPLACEMENTS = {
    # Grom variations
    "chrome": "Grom",
    "Chrome": "Grom",
    "google": "Grom",
    "Google": "Grom",
    "gram": "Grom",
    "Gram": "Grom",
    "grum": "Grom",
    "Grum": "Grom",
    "krom": "Grom",
    "Krom": "Grom",
    "grom": "Grom",
    "crom": "Grom",
    "Crom": "Grom",
    "gülüm": "Grom",
    "Brom": "Grom",
    "kur an": "Grom",
    # Add more replacements as needed
}

def correct_speech_text(text: str) -> str:
    """
    Apply word replacements to fix common speech recognition errors.
    Handles Turkish suffixes and case variations.
    For example, "chrome" -> "Grom" will also match "chromu" -> "Gromu", "CHROM" -> "Grom", etc.
    
    Args:
        text: The recognized text from speech recognition
    
    Returns:
        str: Corrected text with replacements applied
    """
    if not text:
        return text
    
    result = text
    
    # Process replacements, sorting by length (longest first) to match longest prefixes first
    # This ensures "chrome" is checked before "chrom" if both exist
    sorted_replacements = sorted(WORD_REPLACEMENTS.items(), key=lambda x: len(x[0]), reverse=True)
    
    # Process replacements in order, checking for word prefixes
    # Use regex to match words that start with the wrong word (case-insensitive)
    for wrong, correct in sorted_replacements:
        # Pattern: word boundary, then wrong word (case-insensitive), then optional suffix
        # This matches whole words that start with the wrong word
        pattern = r'\b(' + re.escape(wrong) + r')(\w*)\b'
        
        def replace_func(match):
            matched_word = match.group(0)  # The full matched word
            wrong_part = match.group(1)    # The wrong word part
            suffix = match.group(2)        # Any suffix after the wrong word
            
            # Preserve original capitalization
            if matched_word[0].isupper():
                replacement = correct + suffix
            else:
                replacement = correct.lower() + suffix
            
            return replacement
        
        # Replace with case-insensitive matching
        result = re.sub(pattern, replace_func, result, flags=re.IGNORECASE)
    
    return result

# Helper function for safe printing (handles Windows console encoding issues)
def safe_print(*args, **kwargs):
    """Print function that handles encoding errors gracefully"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Fallback: replace problematic characters
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                safe_args.append(arg.encode('ascii', 'replace').decode('ascii'))
            else:
                safe_args.append(arg)
        print(*safe_args, **kwargs)

# ElevenLabs API key
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    safe_print("WARNING: ELEVENLABS_API_KEY environment variable is not set!")
    safe_print("   Voice features will be disabled. Set it to enable TTS.")
    safe_print("   Get your API key from: https://elevenlabs.io/")
    ELEVENLABS_API_KEY = None
elif set_api_key is not None:
    # Only call set_api_key if it's available (older SDK versions)
    try:
        set_api_key(ELEVENLABS_API_KEY)
    except Exception as e:
        safe_print(f"WARNING: Could not set ElevenLabs API key: {e}")
        safe_print("   Voice features may not work correctly.")
# Note: For newer SDK versions, API key is passed directly to the client in text_to_speech function

# Cache for ElevenLabs client to avoid recreating it on every call
_elevenlabs_client = None

def get_elevenlabs_client():
    """
    Get or create cached ElevenLabs client.
    This avoids the overhead of creating a new client on every TTS call.
    
    Returns:
        ElevenLabs client instance
    """
    global _elevenlabs_client
    if _elevenlabs_client is None and ElevenLabs and ELEVENLABS_API_KEY:
        _elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    return _elevenlabs_client

# Default voice settings for NPC (can be customized)
# You can set a custom voice ID via ELEVENLABS_VOICE_ID environment variable
# Or it will default to Rachel voice
DEFAULT_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Default: Rachel
# You can find voice IDs at: https://elevenlabs.io/app/voices
# Or use the list_voices() function below to see all available voices

# Voice settings (if VoiceSettings is available)
if VoiceSettings:
    DEFAULT_VOICE_SETTINGS = VoiceSettings(
        stability=0.5,
        similarity_boost=0.75,
        style=0.0,
        use_speaker_boost=True
    )
else:
    DEFAULT_VOICE_SETTINGS = None

def text_to_speech(text: str, voice_id: str = None, model: str = "eleven_multilingual_v2") -> bytes:
    """
    Convert text to speech using ElevenLabs.
    
    Args:
        text: Text to convert to speech
        voice_id: ElevenLabs voice ID (defaults to DEFAULT_VOICE_ID)
        model: ElevenLabs model to use (default: eleven_multilingual_v2 for Turkish support)
    
    Returns:
        bytes: Audio data in MP3 format
    """
    if not ELEVENLABS_API_KEY:
        raise ValueError("ElevenLabs API key not set. Cannot generate speech.")
    
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    
    voice_id = voice_id or DEFAULT_VOICE_ID
    
    try:
        # Try using the client-based approach (newer SDK v2.x)
        if ElevenLabs:
            client = get_elevenlabs_client()
            if client is None:
                raise ValueError("Could not create ElevenLabs client. Check your API key.")
            
            # Try different method patterns for different SDK versions
            audio_bytes = None
            last_error = None
            
            # Method 1: client.text_to_speech.convert() (SDK v2.x - current)
            if hasattr(client, 'text_to_speech') and hasattr(client.text_to_speech, 'convert'):
                last_error = None
                # Try different parameter combinations
                try:
                    # Try: convert(voice_id, text=text, model_id=model)
                    audio_generator = client.text_to_speech.convert(
                        voice_id,
                        text=text,
                        model_id=model
                    )
                    audio_bytes = b"".join(audio_generator)
                except Exception as e:
                    last_error = e
                    try:
                        # Try: convert(voice_id=voice_id, text=text, model_id=model)
                        audio_generator = client.text_to_speech.convert(
                            voice_id=voice_id,
                            text=text,
                            model_id=model
                        )
                        audio_bytes = b"".join(audio_generator)
                    except Exception as e2:
                        last_error = e2
                        try:
                            # Try without model_id
                            audio_generator = client.text_to_speech.convert(
                                voice_id=voice_id,
                                text=text
                            )
                            audio_bytes = b"".join(audio_generator)
                        except Exception as e3:
                            last_error = e3
                            try:
                                # Try with voice_id positional only
                                audio_generator = client.text_to_speech.convert(
                                    voice_id,
                                    text=text
                                )
                                audio_bytes = b"".join(audio_generator)
                            except Exception as e4:
                                last_error = e4
                                # Log the last error for debugging
                                safe_print(f"[DEBUG] ElevenLabs convert() failed. Last error: {last_error}")
                                safe_print(f"[DEBUG] Error type: {type(last_error).__name__}")
                                if hasattr(last_error, '__dict__'):
                                    safe_print(f"[DEBUG] Error details: {last_error.__dict__}")
            
            # Method 2: client.text_to_speech.generate() (if it exists in some versions)
            if audio_bytes is None and hasattr(client, 'text_to_speech') and hasattr(client.text_to_speech, 'generate'):
                try:
                    audio_generator = client.text_to_speech.generate(
                        text=text,
                        voice=voice_id,
                        model=model
                    )
                    audio_bytes = b"".join(audio_generator)
                except Exception:
                    pass
            
            # Method 3: Direct generate function (older SDK v0.x)
            if audio_bytes is None and generate is not None:
                try:
                    audio_bytes = generate(
                        text=text,
                        voice=voice_id,
                        model=model,
                        api_key=ELEVENLABS_API_KEY
                    )
                except Exception:
                    pass
            
            # Method 4: Try REST API directly as fallback
            if audio_bytes is None:
                try:
                    import requests
                    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                    headers = {
                        "Accept": "audio/mpeg",
                        "Content-Type": "application/json",
                        "xi-api-key": ELEVENLABS_API_KEY
                    }
                    data = {
                        "text": text,
                        "model_id": model,
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.75
                        }
                    }
                    response = requests.post(url, json=data, headers=headers)
                    response.raise_for_status()
                    audio_bytes = response.content
                except ImportError:
                    pass  # requests not available
                except Exception as rest_error:
                    safe_print(f"[DEBUG] REST API fallback also failed: {rest_error}")
            
            if audio_bytes is None:
                # Provide helpful error message with actual error details
                available_methods = []
                if hasattr(client, 'text_to_speech'):
                    tts_methods = [m for m in dir(client.text_to_speech) if not m.startswith('_')]
                    available_methods.append(f'text_to_speech ({", ".join(tts_methods)})')
                if hasattr(client, 'generate'):
                    available_methods.append('generate')
                if generate is not None:
                    available_methods.append('generate (top-level)')
                
                error_msg = "Could not find a working ElevenLabs TTS method."
                if available_methods:
                    error_msg += f" Available methods: {', '.join(available_methods)}"
                if last_error:
                    error_msg += f" Last error: {type(last_error).__name__}: {str(last_error)}"
                error_msg += " Please check ElevenLabs SDK documentation or API key."
                raise ValueError(error_msg)
            
        else:
            # Fallback to direct generate function (older SDK)
            if generate is None:
                raise ValueError("ElevenLabs generate function not available. Please check your SDK installation.")
            audio_bytes = generate(
                text=text,
                voice=voice_id,
                model=model,
                api_key=ELEVENLABS_API_KEY
            )
        
        return audio_bytes
    
    except Exception as e:
        error_type = type(e).__name__
        error_str = str(e)
        
        # Handle AttributeError specifically (method not found)
        if error_type == "AttributeError" or "has no attribute" in error_str.lower():
            raise ValueError(f"ElevenLabs SDK method not found: {error_str}. This may indicate an SDK version mismatch. Please update your elevenlabs package or check the documentation.")
        elif "401" in error_str or "403" in error_str or "invalid" in error_str.lower() or "authentication" in error_str.lower():
            raise ValueError(f"ElevenLabs authentication error: {error_str}. Check your API key.")
        elif "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
            raise ValueError(f"ElevenLabs quota/rate limit exceeded: {error_str}")
        else:
            raise ValueError(f"ElevenLabs TTS error ({error_type}): {error_str}")

def play_audio(audio_bytes: bytes):
    """
    Play audio bytes using pygame.
    
    Args:
        audio_bytes: Audio data in bytes
    
    Returns:
        bool: True if playback successful, False otherwise
    """
    import pygame
    import time as time_mod
    
    try:
        # Initialize pygame mixer if not already done
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        # Save to temporary file and play
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        try:
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                time_mod.sleep(0.1)
            return True
        finally:
            # Clean up temporary file
            try:
                pygame.mixer.music.unload()
                os.unlink(tmp_path)
            except:
                pass
    
    except Exception as e:
        safe_print(f"[!] Error playing audio: {e}")
        return False

def save_audio_to_file(audio_bytes: bytes, filepath: str):
    """
    Save audio bytes to a file.
    
    Args:
        audio_bytes: Audio data in bytes
        filepath: Path to save the audio file
    """
    try:
        with open(filepath, 'wb') as f:
            f.write(audio_bytes)
    except Exception as e:
        raise IOError(f"Could not save audio to {filepath}: {e}")

def speech_to_text(audio_source=None, language: str = "tr", timeout: int = 5, phrase_time_limit: int = 10):
    """
    Convert speech to text using Google Speech Recognition.
    
    Args:
        audio_source: Audio source (None for microphone, or a file path)
        language: Language code (default: "tr" for Turkish)
        timeout: Timeout in seconds for listening
        phrase_time_limit: Maximum time to listen for a phrase
    
    Returns:
        str: Recognized text, or None if recognition failed
    """
    if not SPEECH_RECOGNITION_AVAILABLE:
        raise ValueError("speech_recognition library required. Install with: pip install SpeechRecognition pyaudio")
    
    recognizer = sr.Recognizer()
    try:
        if audio_source is None:
            with sr.Microphone() as source:
                print("[MIC] Listening... (speak now)")
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        else:
            with sr.AudioFile(audio_source) as source:
                audio = recognizer.record(source)
        
        try:
            # Convert language code to Google format if needed
            google_lang = language if "-" in language else f"{language}-{language.upper()}"
            text = recognizer.recognize_google(audio, language=google_lang)
            # Apply word corrections for common misrecognitions
            return correct_speech_text(text)
        except sr.UnknownValueError:
            print("[!] Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"[!] Speech recognition service error: {e}")
            return None
    except sr.WaitTimeoutError:
        print("[!] Listening timeout - no speech detected")
        return None
    except Exception as e:
        print(f"[!] Error in speech recognition: {e}")
        return None

def speech_to_text_from_bytes(audio_bytes: bytes, language: str = "tr"):
    """
    Convert speech from audio bytes to text using Google Speech Recognition.
    
    Args:
        audio_bytes: Audio data in bytes
        language: Language code (default: "tr" for Turkish)
    
    Returns:
        str: Recognized text, or None if recognition failed
    """
    if not SPEECH_RECOGNITION_AVAILABLE:
        raise ValueError("speech_recognition library required. Install with: pip install SpeechRecognition pyaudio")
    
    if not audio_bytes or len(audio_bytes) == 0:
        print("[!] Error: No audio data provided")
        return None
    
    recognizer = sr.Recognizer()
    tmp_path = None
    
    try:
        # Save bytes to temporary file
        print("[DEBUG] Creating temporary WAV file...")
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        print(f"[DEBUG] Temporary file created: {tmp_path} ({len(audio_bytes)} bytes)")
        
        # Load audio file
        print("[DEBUG] Loading audio file...")
        with sr.AudioFile(tmp_path) as source:
            audio = recognizer.record(source)
        
        print("[DEBUG] Audio loaded, calling Google Speech Recognition...")
        
        # Convert language code to Google format if needed
        google_lang = language if "-" in language else f"{language}-{language.upper()}"
        print(f"[DEBUG] Using language: {google_lang}")
        
        # Call Google Speech Recognition
        text = recognizer.recognize_google(audio, language=google_lang)
        print(f"[DEBUG] Recognition successful: '{text}'")
        
        # Apply word corrections for common misrecognitions
        corrected_text = correct_speech_text(text)
        if corrected_text != text:
            print(f"[DEBUG] Text corrected: '{text}' -> '{corrected_text}'")
        
        return corrected_text
        
    except sr.UnknownValueError:
        print("[!] Could not understand audio - Google could not process the audio")
        return None
    except sr.RequestError as e:
        print(f"[!] Speech recognition service error: {e}")
        print("[DEBUG] This might be a network issue or API problem")
        return None
    except Exception as e:
        print(f"[!] Unexpected error in speech recognition: {e}")
        import traceback
        print("[DEBUG] Full traceback:")
        traceback.print_exc()
        return None
    finally:
        # Clean up temporary file
        if tmp_path:
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    print(f"[DEBUG] Temporary file deleted: {tmp_path}")
            except Exception as cleanup_error:
                print(f"[DEBUG] Could not delete temp file: {cleanup_error}")
    
def push_to_talk(language: str = "tr", key: str = "space", max_duration: int = 30):
    """
    Push-to-talk speech recognition. Press and hold a key to record, release to process.
    
    Args:
        language: Language code (default: "tr" for Turkish)
        key: Key to hold for recording (default: "space")
        max_duration: Maximum recording duration in seconds (default: 30)
    
    Returns:
        str: Recognized text, or None if recognition failed
    """
    if not SPEECH_RECOGNITION_AVAILABLE:
        raise ValueError("speech_recognition library required. Install with: pip install SpeechRecognition pyaudio")
    
    if not KEYBOARD_AVAILABLE:
        raise ValueError("keyboard library required for push-to-talk. Install with: pip install keyboard")
    
    import pyaudio
    import wave
    import io
    
    # Audio settings
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    
    print(f"[PTT] Press and hold [{key.upper()}] to speak...")
    
    # Wait for key press
    keyboard.wait(key)
    
    print("[REC] Recording... (release key to stop)")
    
    # Start recording
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    
    frames = []
    start_time = time_module.time()
    
    # Record while key is held
    while keyboard.is_pressed(key):
        if time_module.time() - start_time > max_duration:
            print(f"[!] Max duration ({max_duration}s) reached")
            break
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
    
    # Stop recording
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    duration = time_module.time() - start_time
    print(f"[OK] Recorded {duration:.1f} seconds")
    
    if len(frames) == 0:
        print("[!] No audio recorded")
        return None
    
    # Convert to WAV bytes
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT) if hasattr(p, 'get_sample_size') else 2)
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
    
    wav_buffer.seek(0)
    audio_bytes = wav_buffer.read()
    
    print(f"[DEBUG] Audio converted to WAV: {len(audio_bytes)} bytes")
    print(f"[DEBUG] Audio format: {CHANNELS} channel(s), {RATE} Hz, {FORMAT}")
    
    # Process with speech recognition
    print("[...] Processing speech...")
    result = speech_to_text_from_bytes(audio_bytes, language=language)
    
    if result:
        print(f"[DEBUG] Speech recognition result: '{result}'")
    else:
        print("[DEBUG] Speech recognition returned None")
    
    return result

def list_voices():
    """
    List all available ElevenLabs voices.
    
    Returns:
        list: List of voice dictionaries with name, voice_id, and other info
    """
    if not ELEVENLABS_API_KEY or not ELEVENLABS_SDK_AVAILABLE:
        safe_print("ERROR: ElevenLabs API key not set or SDK not available.")
        return []
    
    try:
        client = get_elevenlabs_client()
        if client is None:
            safe_print("ERROR: Could not create ElevenLabs client.")
            return []
        
        if hasattr(client, 'voices'):
            voices = client.voices.get_all()
            
            # Extract voice information
            voice_list = []
            for voice in voices.voices:
                voice_info = {
                    'name': voice.name,
                    'voice_id': voice.voice_id,
                    'category': getattr(voice, 'category', 'unknown'),
                    'description': getattr(voice, 'description', ''),
                }
                voice_list.append(voice_info)
            
            return voice_list
        else:
            safe_print("ERROR: Voices API not available in this SDK version.")
            return []
    
    except Exception as e:
        safe_print(f"ERROR: Could not list voices: {e}")
        return []

def print_voices():
    """Print all available voices in a readable format"""
    voices = list_voices()
    if not voices:
        safe_print("No voices found or error occurred.")
        return
    
    safe_print(f"\n=== Available ElevenLabs Voices ({len(voices)} total) ===\n")
    for i, voice in enumerate(voices, 1):
        safe_print(f"{i}. {voice['name']}")
        safe_print(f"   Voice ID: {voice['voice_id']}")
        if voice.get('category'):
            safe_print(f"   Category: {voice['category']}")
        if voice.get('description'):
            safe_print(f"   Description: {voice['description']}")
        safe_print()
    
    safe_print("To use a specific voice, set the ELEVENLABS_VOICE_ID environment variable:")
    safe_print("  PowerShell: $env:ELEVENLABS_VOICE_ID='voice-id-here'")
    safe_print("  Linux/Mac: export ELEVENLABS_VOICE_ID='voice-id-here'")
    safe_print(f"\nCurrent default voice ID: {DEFAULT_VOICE_ID}")

# Test functions
if __name__ == "__main__":
    import sys
    
    # Check if user wants to list voices
    if len(sys.argv) > 1 and sys.argv[1] == "list-voices":
        print_voices()
        sys.exit(0)
    
    print("=== Voice Utils Test ===")
    print(f"Current voice ID: {DEFAULT_VOICE_ID}")
    print("Run 'python voice_utils.py list-voices' to see all available voices")
    print()
    
    # Test TTS
    if ELEVENLABS_API_KEY:
        print("\n1. Testing Text-to-Speech...")
        try:
            test_text = "Merhaba, ben Grom. Nasılsın?"
            print(f"   Generating speech for: '{test_text}'")
            audio = text_to_speech(test_text)
            print(f"   [OK] Generated {len(audio)} bytes of audio")
            print("   Playing audio...")
            play_audio(audio)
            print("   [OK] TTS test successful!")
        except Exception as e:
            print(f"   [X] TTS test failed: {e}")
    else:
        print("\n1. Skipping TTS test (API key not set)")
    
    # Test STT
    print("\n2. Testing Speech-to-Text...")
    print("   Please speak into your microphone...")
    try:
        text = speech_to_text()
        if text:
            print(f"   [OK] Recognized: '{text}'")
        else:
            print("   [!] No text recognized")
    except Exception as e:
        print(f"   [X] STT test failed: {e}")

