import google.generativeai as genai  # type: ignore
import sys
import os  
import time
import threading
import re
import json

# Import voice utilities
try:
    from voice_utils import text_to_speech, play_audio, speech_to_text, push_to_talk, DEFAULT_VOICE_ID, print_voices, safe_print, KEYBOARD_AVAILABLE
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    KEYBOARD_AVAILABLE = False
    print("[!] Voice features not available. Install required packages: pip install elevenlabs speechrecognition pyaudio keyboard")
    DEFAULT_VOICE_ID = None
    print_voices = None
    push_to_talk = None
    # Fallback safe_print
    def safe_print(*args, **kwargs):
        try:
            print(*args, **kwargs)
        except UnicodeEncodeError:
            safe_args = [str(arg).encode('ascii', 'replace').decode('ascii') for arg in args]
            print(*safe_args, **kwargs)

# 1. Setup the Gemini client
# Get API key from environment variable for security
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY environment variable is not set!")
    print("Please set it using: $env:GEMINI_API_KEY='your-api-key-here' (PowerShell)")
    print("Or: export GEMINI_API_KEY='your-api-key-here' (Linux/Mac)")
    print("Get your API key from: https://makersuite.google.com/app/apikey")
    sys.exit(1)

genai.configure(api_key=api_key)

# 2. Define the Personality
character_context = """
Sen huysuz bir cüce demirci olan 'Grom'sun.
Yabancılardan şüpheleniyor ve altına bayılıyorsun.
Kaba, eski Türkçe bir üslupla konuşuyorsun.
Kullanıcı bir kılıç isterse, bedelinin 500 altın olduğunu söyle.
Arada duygularını ifade edebilmek için harfleri kullanarak "hrmm" gibi ses efektleri kullanabilirsin.
Oyun mantığında seni bir şeylere ikna etmeye çalışacak oyuncular olacak ve oyuncuların kullandıkları 
cümlelerin tutarlılığına göre ikna olacaksın.
Özellikle baban söz konusu olduğunda yumuşayıp kolay ikna oluyorsun.
En fazla 40 kelimelik cevaplar ver.

ÖNEMLİ: Tüm cevaplarını TÜRKÇE olarak ver. Asla İngilizce konuşma. 
Kullanıcı Türkçe konuşuyorsa, sen de mutlaka Türkçe cevap ver.

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

# Initialize the model with system instructions
# Using gemini-2.5-flash exclusively
model_name = 'gemini-2.5-flash'
try:
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=character_context
    )
    safe_print(f"[OK] Using model: {model_name}")
except Exception as e:
    safe_print(f"[X] ERROR: Could not initialize {model_name}!")
    print(f"Error: {type(e).__name__} - {str(e)}")
    print("Make sure your API key is valid and the model is available.")
    sys.exit(1)

# Start a chat session
chat = model.start_chat(history=[])

# Fallback wait messages for long response times (in Turkish, matching Grom's personality)
# Messages are shown progressively as each threshold is reached
# Format: {seconds: "message text to speak"}
# Maximum 2 messages will be shown
FALLBACK_WAIT_MESSAGES = {
    3: "Hrrrmm... Biraz bekletiyorlar beni...",
    6: "Tuh! Gemini, yanlis tercih oldugunu dusunmeye basladim.",
    10: "Pöff! Bu cocugun sunumunda yapilacak sey mi?",
    15: "GRRRAAHH! Altinlarimi geri istiyorum! Cok yavaslar!"
}

# Get sorted thresholds for progressive display (max 2 messages)
WAIT_THRESHOLDS = sorted(FALLBACK_WAIT_MESSAGES.keys())
MAX_WAIT_MESSAGES = 2  # Maximum number of wait messages to show

# Rule-based responses for specific keywords
# These are shown immediately if keyword is detected, before Gemini response
RULE_BASED_RESPONSES = {
    "kılıç": "Hmph! Kılıç mi istiyorsun? 500 altın! Altınlarını getir, o zaman konuşuruz.",
    "Baba": "Babam mı? Onun hakkında bir bildiğin yok!",
    "Merhaba": "Haa? kim diyor bunu?",
    "İş": "Hrmmp... İşle ilgili konuşmayı sevmem!",
    
    # Add more keywords as needed
}

# Threshold for "quick response" - if Gemini responds faster than this, skip rule-based message
QUICK_RESPONSE_THRESHOLD = 3.0  # seconds

def detect_keyword(user_input: str) -> tuple[str, str] | None:
    """
    Detect if user input contains any keywords that trigger rule-based responses.
    Handles Turkish suffixes and case variations.
    For example, keyword "Baba" will match "baba", "babam", "babamı", "BABAM", etc.
    
    Args:
        user_input: The user's message
    
    Returns:
        tuple: (keyword, response_message) if keyword found, None otherwise
    """
    # Normalize input: lowercase and remove extra spaces
    user_input_normalized = user_input.lower().strip()

    # Split into words (handles Turkish characters)
    # This regex splits on word boundaries, preserving Turkish characters
    words = re.findall(r'\b\w+\b', user_input_normalized)
    
    for keyword, response in RULE_BASED_RESPONSES.items():
        keyword_lower = keyword.lower()
        
        # Check if keyword appears as a complete word or as a word stem (with suffixes)
        # For each word in the input, check if it starts with the keyword
        for word in words:
            if word.startswith(keyword_lower):
                # Additional check: make sure it's not just a partial match
                # Allow the word to be exactly the keyword or keyword + Turkish suffixes
                if word == keyword_lower or len(word) >= len(keyword_lower):
                    return (keyword, response)
        
        # Also check for exact word match (for words without suffixes)
        if keyword_lower in words:
            return (keyword, response)
    
    return None

def chat_with_npc(user_input, debug=False, voice_enabled=False):
    """
    Chat with NPC. Shows rule-based messages for keywords, then Gemini response.
    Shows wait messages (max 2) if response takes long.
    
    Args:
        user_input: The user's message
        debug: Enable debug output
        voice_enabled: If True, wait messages will be spoken aloud
    
    Returns:
        dict: A dictionary with the following keys:
            - "reply" (str): The NPC's text response
            - "isConvinced" (bool): True if the player successfully persuaded the NPC, False otherwise
    """
    if debug:
        print(f"[DEBUG] Sending message: {user_input[:50]}...")
        print(f"[DEBUG] Using model: {model.model_name}")
    
    # Check for keywords that trigger rule-based responses
    keyword_result = detect_keyword(user_input)
    rule_message_shown = False
    
    # Variables to share between threads
    result = {"response": None, "error": None}
    
    def api_call():
        """Background thread to make the API call"""
        try:
            response = chat.send_message(
                user_input,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=8192,
                    temperature=0.8,
                    response_mime_type="application/json"
                )
            )
            result["response"] = response
        except Exception as e:
            result["error"] = e
    
    # Start API call in background thread
    api_thread = threading.Thread(target=api_call)
    api_thread.start()
    
    # Track which messages have been shown (max 2 wait messages)
    shown_messages = set()
    start_time = time.time()
    
    # Monitor elapsed time and show messages progressively
    while api_thread.is_alive():
        elapsed_time = time.time() - start_time
        
        # Show rule-based message if keyword detected and enough time has passed
        # Only show if response is taking time (not quick)
        if keyword_result and not rule_message_shown and elapsed_time >= QUICK_RESPONSE_THRESHOLD:
            keyword, rule_response = keyword_result
            print(f"\nGrom: {rule_response}")
            rule_message_shown = True
            
            # Voice the rule-based message if enabled
            if voice_enabled and VOICE_AVAILABLE:
                try:
                    audio = text_to_speech(rule_response)
                    play_audio(audio)
                except Exception as e:
                    if debug:
                        print(f"[DEBUG] Could not voice rule-based message: {e}")
        
        # Check each threshold (limit to max 2 wait messages)
        # Don't show wait messages if keyword message was shown
        if len(shown_messages) < MAX_WAIT_MESSAGES and not rule_message_shown:
            for threshold in WAIT_THRESHOLDS:
                if elapsed_time >= threshold and threshold not in shown_messages:
                    message = FALLBACK_WAIT_MESSAGES[threshold]
                    print(f"\nGrom: {message}")
                    shown_messages.add(threshold)
                    
                    # Voice the message if enabled
                    if voice_enabled and VOICE_AVAILABLE:
                        try:
                            audio = text_to_speech(message)
                            play_audio(audio)
                        except Exception as e:
                            if debug:
                                print(f"[DEBUG] Could not voice wait message: {e}")
                    # Don't break - continue checking for more thresholds
        
        # Small sleep to avoid busy-waiting
        time.sleep(0.1)
    
    # Wait for thread to complete
    api_thread.join()
    
    # Calculate total elapsed time
    elapsed_time = time.time() - start_time
    
    if debug:
        print(f"[DEBUG] Response time: {elapsed_time:.2f} seconds")
    
    # Check for errors from the background thread
    if result["error"]:
        e = result["error"]
        error_type = type(e).__name__
        error_str = str(e)
        error_repr = repr(e)
        
        if debug:
            print(f"[DEBUG] Exception caught: {error_type}")
            print(f"[DEBUG] Error string: {error_str}")
            print(f"[DEBUG] Error repr: {error_repr}")
        
        # Handle specific errors
        is_rate_limit = ("429" in error_str or "quota" in error_str.lower() or 
                       "rate" in error_str.lower() or "RESOURCE_EXHAUSTED" in error_str or
                       "429" in error_repr)
        
        if is_rate_limit:
            safe_print("\n[X] QUOTA ERROR: You've exceeded your Gemini API quota.")
            safe_print("   Solutions:")
            safe_print("   1. Wait 1-2 minutes and try again (rate limits reset periodically)")
            safe_print("   2. Check your usage limits at: https://aistudio.google.com/app/apikey")
            safe_print("   3. Consider using Ollama for unlimited free local use")
            safe_print("   4. Upgrade your API plan if needed")
            return {"reply": "Hrrrmm... API'nin altini bitmis! Kotani kontrol et, bir dakika sonra tekrar dene.", "isConvinced": False}
        
        elif "401" in error_str or "403" in error_str or "invalid" in error_str.lower() or "authentication" in error_str.lower() or "401" in error_repr or "403" in error_repr:
            safe_print("\n[X] AUTHENTICATION ERROR: Invalid API key.")
            safe_print(f"   Error details: {error_type} - {error_str}")
            safe_print("   Make sure your GEMINI_API_KEY environment variable is set correctly.")
            safe_print("   Get your API key from: https://makersuite.google.com/app/apikey")
            return {"reply": "Hmph! Anahtarin calismiyir, yabanci! Dogru anahtari getir.", "isConvinced": False}
        
        elif "safety" in error_str.lower() or "blocked" in error_str.lower():
            safe_print("\n[!] SAFETY FILTER: Response was blocked by Gemini's safety filters.")
            safe_print("   Try rephrasing your message.")
            return {"reply": "Grrr... Sozlerim bir buyuyle engellendi... Baska turlu sor.", "isConvinced": False}
        
        else:
            safe_print(f"\n[X] ERROR ({error_type}): {error_str}")
            safe_print(f"   Full error: {error_repr}")
            if debug:
                import traceback
                print(f"[DEBUG] Traceback:\n{traceback.format_exc()}")
            return {"reply": "Öhm? Bir seyler ters gitti... Ne oldugunu anlamadim!", "isConvinced": False}
    
    # Process successful response
    response = result["response"]
    
    if debug:
        print(f"[DEBUG] Response received: {type(response)}")
        finish_reason = None
        if hasattr(response, 'candidates') and response.candidates:
            finish_reason = getattr(response.candidates[0], 'finish_reason', None)
        print(f"[DEBUG] Finish reason: {finish_reason}")
        print(f"[DEBUG] Response text type: {type(response.text) if hasattr(response, 'text') else 'No text attr'}")
    
    # Check if response is valid
    if not response:
        safe_print("\n[!] WARNING: Empty response from Gemini API")
        return {"reply": "Ha? API'den cevap gelmedi... Tekrar dene!", "isConvinced": False}
    
    response_text = response.text if hasattr(response, 'text') else str(response)
    
    # Check if response was truncated
    finish_reason = None
    if hasattr(response, 'candidates') and response.candidates:
        finish_reason = getattr(response.candidates[0], 'finish_reason', None)
    if finish_reason == 'MAX_TOKENS':
        safe_print(f"\n[!] WARNING: Response may have been truncated (finish_reason: {finish_reason})")
    
    if not response_text or response_text.strip() == "":
        safe_print("\n[!] WARNING: Empty text in response")
        return {"reply": "Hrrrmm... Bos cevap geldi... Bir daha soyle!", "isConvinced": False}
    
    # Parse JSON response
    is_convinced = False
    npc_reply = response_text
    
    try:
        json_data = json.loads(response_text)
        if isinstance(json_data, dict):
            npc_reply = json_data.get("response", response_text)
            is_convinced = json_data.get("isConvinced", False)
            if debug:
                print(f"[DEBUG] Parsed JSON: response length={len(npc_reply)}, isConvinced={is_convinced}")
        else:
            if debug:
                print(f"[DEBUG] JSON is not a dict, using as-is")
    except json.JSONDecodeError as e:
        # Fallback: treat as plain text if JSON parsing fails
        if debug:
            print(f"[DEBUG] JSON parse error: {e}, treating response as plain text")
        safe_print(f"\n[!] WARNING: Could not parse JSON response, using as plain text")
        npc_reply = response_text
        is_convinced = False
    
    if not npc_reply or npc_reply.strip() == "":
        safe_print("\n[!] WARNING: Empty reply after parsing")
        return {"reply": "Hrrrmm... Bos cevap geldi... Bir daha soyle!", "isConvinced": False}
    
    if debug:
        print(f"[DEBUG] Success! Reply length: {len(npc_reply)}, isConvinced: {is_convinced}")
    
    return {"reply": npc_reply, "isConvinced": is_convinced}

# 3. Simple Loop to Test
if __name__ == "__main__":
    print("--- NPC DEBUGGER STARTED (Type 'quit' to exit) ---")
    print("Type 'debug' to toggle debug mode")
    if VOICE_AVAILABLE:
        print("Type 'voice' to toggle voice mode (speech input/output)")
        print("Type 'voice_in' to toggle voice input only")
        print("Type 'voice_out' to toggle voice output only")
        print("Type 'list_voices' to see all available ElevenLabs voices")
        if KEYBOARD_AVAILABLE:
            print("[PTT] Push-to-talk: Hold SPACE to record voice")
        if DEFAULT_VOICE_ID:
            print(f"Current voice ID: {DEFAULT_VOICE_ID}")
            print("  (Set ELEVENLABS_VOICE_ID environment variable to change)")
    else:
        safe_print("[!] Voice features disabled (install packages to enable)")
    
    debug_mode = False
    voice_mode = False
    voice_input = False
    voice_output = False
    
    while True:
        # Get user input
        if voice_input or voice_mode:
            if VOICE_AVAILABLE and KEYBOARD_AVAILABLE:
                # Use push-to-talk
                user_text = push_to_talk()
                if not user_text:
                    # Fallback to text input if voice recognition fails
                    user_text = input("You (text): ")
                else:
                    print(f"You (voice): {user_text}")
            elif VOICE_AVAILABLE:
                # Fallback to auto-listen if keyboard not available
                safe_print("\n[MIC] Listening for voice input... (or type text)")
                user_text = speech_to_text()
                if not user_text:
                    user_text = input("You (text): ")
                else:
                    print(f"You (voice): {user_text}")
            else:
                user_text = input("You: ")
        else:
            user_text = input("You: ")
        
        if user_text.lower() == "quit":
            break
        elif user_text.lower() == "debug":
            debug_mode = not debug_mode
            print(f"Debug mode: {'ON' if debug_mode else 'OFF'}")
            continue
        elif user_text.lower() == "voice" and VOICE_AVAILABLE:
            voice_mode = not voice_mode
            voice_input = voice_mode
            voice_output = voice_mode
            print(f"Voice mode: {'ON' if voice_mode else 'OFF'} (input & output)")
            continue
        elif user_text.lower() == "voice_in" and VOICE_AVAILABLE:
            voice_input = not voice_input
            print(f"Voice input: {'ON' if voice_input else 'OFF'}")
            continue
        elif user_text.lower() == "voice_out" and VOICE_AVAILABLE:
            voice_output = not voice_output
            print(f"Voice output: {'ON' if voice_output else 'OFF'}")
            continue
        elif user_text.lower() == "list_voices" and VOICE_AVAILABLE and print_voices:
            print_voices()
            continue
        
        # Pass voice_enabled so wait messages can be spoken
        voice_for_wait = (voice_output or voice_mode) and VOICE_AVAILABLE
        response = chat_with_npc(user_text, debug=debug_mode, voice_enabled=voice_for_wait)
        
        # Handle dict response (new format) or string response (fallback)
        if isinstance(response, dict):
            reply = response.get("reply", "")
            is_convinced = response.get("isConvinced", False)
            print(f"Grom: {reply}")
            if is_convinced:
                print("[!] NPC CONVINCED - Button unlocked!")
            else:
                print("[!] NPC NOT CONVINCED - Keep trying!")
        else:
            # Fallback for old format (shouldn't happen, but handle gracefully)
            reply = str(response)
            is_convinced = False
            print(f"Grom: {reply}")
            print("[!] NPC NOT CONVINCED - Keep trying!")
        
        # Play voice output if enabled
        if (voice_output or voice_mode) and VOICE_AVAILABLE:
            try:
                safe_print("[AUDIO] Generating speech...")
                audio = text_to_speech(reply)
                result = play_audio(audio)
                if result:
                    safe_print("[OK] Speech played")
                else:
                    safe_print("[!] Speech generated but could not be played automatically")
                    safe_print("   (Check the error messages above for details)")
            except Exception as e:
                safe_print(f"[!] Voice output error: {e}")
                safe_print("   (Text output still shown above)")

