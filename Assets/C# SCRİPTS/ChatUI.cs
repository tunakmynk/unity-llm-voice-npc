using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.Collections;

public class ChatUI : MonoBehaviour
{
    [Header("UI References")]
    public TMP_InputField chatInputField;  
    public Button sendButton;              
    public KeyCode openChatKey = KeyCode.T; 
    public KeyCode holdToSpeakKey = KeyCode.V;
    public TextMeshProUGUI recordingIndicator; 
    
    [Header("Chat Panel")]
    public GameObject chatPanel;           
    public TextMeshProUGUI chatLogText;    
    public ScrollRect chatScrollRect; 

    private CallTheAPI npcController;
    public static bool IsChatOpen = false;
    public static ChatUI Instance;

    private AudioClip recordedClip;
    private bool isRecording = false;
    
    void Awake()
    {
        if (Instance == null)
            Instance = this;
        else
            Destroy(gameObject);
    }

    void Start()
    {
        npcController = CallTheAPI.Instance;
        
        if (sendButton != null)
            sendButton.onClick.AddListener(SendMessage);
        
        if (chatInputField != null)
            chatInputField.onSubmit.AddListener(delegate { SendMessage(); });
        
        CloseChat();
        SetPanelSize();
        
        if (recordingIndicator != null)
            recordingIndicator.gameObject.SetActive(false);

        if (npcController != null)
            npcController.OnNPCResponse.AddListener(OnNPCResponse);
    }
    
    void Update()
    {
        if (IsChatOpen && Input.GetKeyDown(KeyCode.Escape))
            CloseChat();

        if (IsChatOpen)
        {
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;

            if (Input.GetKeyDown(holdToSpeakKey))
            {
                StartRecording();
            }
            else if (Input.GetKeyUp(holdToSpeakKey))
            {
                StopRecordingAndSend();
            }
        }
    }
    
    public void StartRecording()
    {
        Debug.Log("[ChatUI] StartRecording called.");
        if (Microphone.devices.Length > 0)
        {
            Debug.Log($"[ChatUI] Microphone found: {Microphone.devices[0]}");
            isRecording = true;
            if (recordingIndicator != null) 
            {
                recordingIndicator.gameObject.SetActive(true);
                Debug.Log("[ChatUI] Recording Indicator set to Active.");
            }
            else
            {
                Debug.LogWarning("[ChatUI] Recording Indicator reference is missing!");
            }
            
            recordedClip = Microphone.Start(null, false, 10, 44100);
            Debug.Log("[ChatUI] Microphone.Start called.");
        }
        else
        {
            Debug.LogWarning("[ChatUI] No microphone devices found!");
        }
    }

    public void StopRecordingAndSend()
    {
        if (!isRecording) return;

        isRecording = false;
        if (recordingIndicator != null) recordingIndicator.gameObject.SetActive(false);

        if (Microphone.IsRecording(null))
        {
            Microphone.End(null);
            
            byte[] wavData = AudioUtils.FromAudioClip(recordedClip);
            if (npcController != null)
            {
                // AddToChatLog("Sen (Ses): ..."); // Artık sunucudan geleni bekleyeceğiz
                npcController.SendAudioToNPC(wavData);
            }
        }
    }
    
    public void ToggleChat()
    {
        IsChatOpen = !IsChatOpen;

        if (chatPanel != null)
            chatPanel.SetActive(IsChatOpen);
        
        if (IsChatOpen)
        {
            if (chatInputField != null)
            {
                chatInputField.Select();
                chatInputField.ActivateInputField();
            }
        }
        else
        {
            Cursor.lockState = CursorLockMode.Locked;
            Cursor.visible = false;
        }
    }
    
    void CloseChat()
    {
        IsChatOpen = false;
        
        if (chatPanel != null)
            chatPanel.SetActive(false);
        
        if (chatInputField != null)
            chatInputField.text = "";

        Cursor.lockState = CursorLockMode.Locked;
        Cursor.visible = false;
    }
    
    void SendMessage()
    {
        if (chatInputField == null || npcController == null) return;
        
        string message = chatInputField.text.Trim();
        if (string.IsNullOrEmpty(message)) return;
        
        AddToChatLog($"Sen: {message}");
        npcController.SendMessageToNPC(message);
        
        chatInputField.text = "";
        chatInputField.Select();
        chatInputField.ActivateInputField();
    }
    
    void OnNPCResponse(string userText, string npcReply)
    {
        // Eğer sunucudan kullanıcı metni geldiyse (Sesli konuşma yapıldıysa)
        if (!string.IsNullOrEmpty(userText))
        {
            AddToChatLog($"Sen (Ses): {userText}");
        }

        AddToChatLog($"Grom: {npcReply}");
    }
    
    void AddToChatLog(string message)
    {
        if (chatLogText != null)
        {
            chatLogText.text += message + "\n\n";
            StartCoroutine(ForceScrollDown());
        }
    }

    IEnumerator ForceScrollDown()
    {
        yield return new WaitForEndOfFrame(); 
        if(chatScrollRect != null)
        {
             chatScrollRect.verticalNormalizedPosition = 0f; 
        }
    }
    
    void OnDestroy()
    {
        if (npcController != null)
            npcController.OnNPCResponse.RemoveListener(OnNPCResponse);
    }

    void SetPanelSize()
    {
        if (chatPanel != null)
        {
            RectTransform rect = chatPanel.GetComponent<RectTransform>();
            if (rect != null)
            {
                rect.anchorMin = new Vector2(0, 0);
                rect.anchorMax = new Vector2(1, 0.4f);
                rect.pivot = new Vector2(0.5f, 0);
                rect.offsetMin = Vector2.zero; 
                rect.offsetMax = Vector2.zero; 
            }
        }
    }
}