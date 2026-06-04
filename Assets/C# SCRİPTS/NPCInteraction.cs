using UnityEngine;
using TMPro; // Eğer "E'ye bas" yazısı eklemek isterseniz

public class NPCInteraction : MonoBehaviour
{
    [Header("Settings")]
    public float interactionDistance = 3.0f;
    public KeyCode interactionKey = KeyCode.X;
    
    [Header("References")]
    public Transform playerTransform;
    
    // Ekranda "X'e bas" yazısı göstermek için
    public GameObject interactionPromptUI; 

    private void Start()
    {
        // Başlangıçta prompt kapalı olsun
        if (interactionPromptUI != null)
            interactionPromptUI.SetActive(false);

        // Eğer playerTransform atanmadıysa otomatik bulmaya çalış
        if (playerTransform == null)
        {
            // PlayerMovement scripti olan objeyi bul
            PlayerMovement player = FindFirstObjectByType<PlayerMovement>();
            if (player != null)
            {
                playerTransform = player.transform;
            }
            else
            {
                // Alternatif olarak "Player" tag'i ile bul
                GameObject playerObj = GameObject.FindGameObjectWithTag("Player");
                if (playerObj != null)
                    playerTransform = playerObj.transform;
            }
        }
    }

    private void Update()
    {
        if (playerTransform == null) return;

        float distance = Vector3.Distance(transform.position, playerTransform.position);

        // Mesafe kontrolü ve UI gösterme
        if (distance <= interactionDistance)
        {
            // Chat açık değilse prompt'u göster
            if (interactionPromptUI != null && !ChatUI.IsChatOpen)
            {
                interactionPromptUI.SetActive(true);
            }
            else if (interactionPromptUI != null)
            {
                interactionPromptUI.SetActive(false);
            }

            // Yakındayken tuşa basılırsa (Chat açma/kapama)
            if (Input.GetKeyDown(interactionKey))
            {
                if (ChatUI.Instance != null)
                {
                    ChatUI.Instance.ToggleChat();
                    
                    // Chat açılınca prompt'u gizle
                    if (interactionPromptUI != null)
                        interactionPromptUI.SetActive(false);
                }
                else
                {
                    Debug.LogWarning("ChatUI Instance bulunamadı! Sahneye ChatUI scripti ekli mi?");
                }
            }

            // Sesli Konuşma (V tuşu) - Chat açık olmasa bile çalışır
            if (ChatUI.Instance != null)
            {
                if (Input.GetKeyDown(KeyCode.V))
                {
                    ChatUI.Instance.StartRecording();
                }
                else if (Input.GetKeyUp(KeyCode.V))
                {
                    ChatUI.Instance.StopRecordingAndSend();
                }
            }
        }
        else
        {
            // Uzaklaşınca prompt'u gizle
            if (interactionPromptUI != null)
                interactionPromptUI.SetActive(false);
        }
    }
    
    // Editor'de mesafeyi görmek için gizmo
    private void OnDrawGizmosSelected()
    {
        Gizmos.color = Color.yellow;
        Gizmos.DrawWireSphere(transform.position, interactionDistance);
    }
}
