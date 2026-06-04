using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;
using System.Text;
using System;
using UnityEngine.Events;

[Serializable]
public class PlayerMessage
{
    public string text;
    public string player_id = "default_player";
    public bool return_audio = false;
    public string player_audio; // Base64 encoded WAV
}

[Serializable]
public class ChatResponse
{
    public string reply;
    public bool isConvinced;
    public string audio;
    public string audio_format;
    public string user_text; // [YENİ] Sunucudan gelen algılanan kullanıcı metni
}

public class CallTheAPI : MonoBehaviour
{
    [Header("Server Configuration")]
    [SerializeField] private string serverUrl = "http://localhost:8000";
    
    [Header("Audio Settings")]
    [SerializeField] private bool includeAudio = true;
    [SerializeField] private AudioSource audioSource;
    
    [Header("Events")]
    public UnityEvent OnNPCConvinced;
    public UnityEvent<string, string> OnNPCResponse; // (UserText, NPCText)
    
    [Header("Debug")]
    [SerializeField] private bool debugMode = false;
    
    public bool IsConvinced { get; private set; } = false;
    
    public static CallTheAPI Instance { get; private set; }
    
    void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }
        else
        {
            Destroy(gameObject);
            return;
        }
        
        if (audioSource == null)
        {
            audioSource = gameObject.AddComponent<AudioSource>();
        }
    }
    
    void Start()
    {
        if (debugMode)
        {
            Debug.Log($"[CallTheAPI] Server URL: {serverUrl}");
        }
    }
    
    public void SendMessageToNPC(string playerText)
    {
        if (string.IsNullOrEmpty(playerText))
        {
            Debug.LogWarning("Cannot send empty message to NPC");
            return;
        }
        
        StartCoroutine(ChatWithNPC(playerText, null));
    }

    public void SendAudioToNPC(byte[] audioData)
    {
        if (audioData == null || audioData.Length == 0)
        {
            Debug.LogWarning("Cannot send empty audio to NPC");
            return;
        }

        string base64Audio = Convert.ToBase64String(audioData);
        StartCoroutine(ChatWithNPC("", base64Audio));
    }
    
    IEnumerator ChatWithNPC(string text, string audioBase64)
    {
        var message = new PlayerMessage
        {
            text = text,
            player_id = "player_1",
            return_audio = includeAudio,
            player_audio = audioBase64
        };
        
        string jsonData = JsonUtility.ToJson(message);
        byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonData);
        
        if (debugMode)
        {
            Debug.Log($"[CallTheAPI] Sending: {text}");
        }
        
        UnityWebRequest request = new UnityWebRequest($"{serverUrl}/chat", "POST");
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");
        request.timeout = 30;
        
        yield return request.SendWebRequest();
        
        // Handle response (NO yield statements inside this block)
        if (request.result == UnityWebRequest.Result.Success)
        {
            string responseText = request.downloadHandler.text;
            ChatResponse response = null;
            
            // Parse JSON outside of try-catch that contains yield
            bool parseSuccess = false;
            try
            {
                response = JsonUtility.FromJson<ChatResponse>(responseText);
                parseSuccess = true;
            }
            catch (Exception e)
            {
                Debug.LogError($"[CallTheAPI] Failed to parse response: {e.Message}");
                request.Dispose();
                yield break;
            }
            
            if (parseSuccess && response != null)
            {
                bool wasConvinced = IsConvinced;
                IsConvinced = response.isConvinced;
                
                Debug.Log($"Grom: {response.reply}");
                // Pass both user_text and reply to the event
                OnNPCResponse?.Invoke(response.user_text, response.reply);
                
                if (!wasConvinced && IsConvinced)
                {
                    Debug.Log("[GAME] Grom is now CONVINCED! Following player...");
                    OnNPCConvinced?.Invoke();
                }
                
                // Play audio if available (this will yield, but it's OUTSIDE try-catch)
                if (includeAudio && !string.IsNullOrEmpty(response.audio))
                {
                    yield return StartCoroutine(PlayAudioFromBase64(response.audio));
                }
            }
        }
        else
        {
            Debug.LogError($"[CallTheAPI] Request failed: {request.error}");
            if (request.responseCode == 0)
            {
                Debug.LogError("Server might not be running. Start it with: uvicorn npc_server:app --host 0.0.0.0 --port 8000");
            }
        }
        
        request.Dispose();
    }
    
    IEnumerator PlayAudioFromBase64(string base64Audio)
    {
        // Step 1: Convert base64 to bytes (NO yield here, so try-catch is OK)
        byte[] audioBytes = null;
        string tempPath = "";
        
        try
        {
            audioBytes = Convert.FromBase64String(base64Audio);
            tempPath = System.IO.Path.Combine(Application.temporaryCachePath, "npc_audio.mp3");
            System.IO.File.WriteAllBytes(tempPath, audioBytes);
        }
        catch (Exception e)
        {
            Debug.LogError($"[CallTheAPI] Error converting audio: {e.Message}");
            yield break; // Exit coroutine - this is allowed because it's at the end
        }
        
        // Step 2: Load audio file (yield happens OUTSIDE try-catch)
        UnityWebRequest www = UnityWebRequestMultimedia.GetAudioClip("file://" + tempPath, AudioType.MPEG);
        yield return www.SendWebRequest();
        
        // Step 3: Handle loaded audio (NO yield here)
        if (www.result == UnityWebRequest.Result.Success)
        {
            AudioClip clip = DownloadHandlerAudioClip.GetContent(www);
            if (clip != null && audioSource != null)
            {
                audioSource.clip = clip;
                audioSource.Play();
                yield return new WaitWhile(() => audioSource.isPlaying);
            }
        }
        else
        {
            Debug.LogError($"[CallTheAPI] Audio load error: {www.error}");
        }
        
        www.Dispose();
        
        // Step 4: Cleanup temp file (NO yield here, so try-catch is OK)
        try
        {
            if (System.IO.File.Exists(tempPath))
            {
                System.IO.File.Delete(tempPath);
            }
        }
        catch (Exception e)
        {
            Debug.LogWarning($"[CallTheAPI] Could not delete temp file: {e.Message}");
        }
    }
    
    public void ResetConvincedState()
    {
        IsConvinced = false;
    }
}