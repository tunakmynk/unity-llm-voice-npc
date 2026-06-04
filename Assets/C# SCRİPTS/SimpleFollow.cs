using UnityEngine;

public class SimpleFollow : MonoBehaviour
{
    [Header("Ayarlar")]
    public Transform target;          // Takip edilecek hedef (Ana Karakter)
    public float speed = 5f;          // Hız
    public float stoppingDistance = 2.0f; // Durma mesafesi

    [Header("Animasyon")]
    public Animator npcAnimator;      // Animator bileşeni buraya gelecek

    [Header("API Bağlantısı")]
    private CallTheAPI apiController; // API kontrolcüsü
    private bool isFollowing = false; // NPC takip ediyor mu?

    void Start()
    {
        // API kontrolcüsünü bul (Unity 6.2 uyumlu)
        apiController = Object.FindFirstObjectByType<CallTheAPI>();
        if (apiController != null)
        {
            // NPC ikna olduğunda takip başlat
            apiController.OnNPCConvinced.AddListener(StartFollowing);
            Debug.Log("[SimpleFollow] API bağlantısı kuruldu. Grom ikna olunca takip başlayacak.");
        }
        else
        {
            Debug.LogWarning("[SimpleFollow] CallTheAPI bulunamadı! Takip otomatik başlamayacak.");
        }
    }

    void Update()
    {
        // API'den güncel durumu al ve senkronize et
        if (apiController != null)
        {
            isFollowing = apiController.IsConvinced;
        }

        // Sadece isFollowing true ise takip et
        if (!isFollowing || target == null) 
        {
            // Takip etmiyorsa durma animasyonuna geç
            if (npcAnimator != null)
            {
                npcAnimator.SetBool("IsWalking", false);
            }
            return;
        }

        // Mesafeyi ölç
        float distance = Vector3.Distance(transform.position, target.position);

        // HAREKET DURUMU
        if (distance > stoppingDistance)
        {
            // 1. Hedefe dön
            Vector3 targetPosition = new Vector3(target.position.x, transform.position.y, target.position.z);
            transform.LookAt(targetPosition);

            // 2. İlerle
            transform.position = Vector3.MoveTowards(transform.position, targetPosition, speed * Time.deltaTime);

            // 3. Yürüme Animasyonunu AÇ (IsWalking = true)
            if (npcAnimator != null)
            {
                npcAnimator.SetBool("IsWalking", true);
            }
        }
        // DURMA DURUMU
        else
        {
            // 3. Yürüme Animasyonunu KAPAT (IsWalking = false)
            if (npcAnimator != null)
            {
                npcAnimator.SetBool("IsWalking", false);
            }
        }
    }

    /// <summary>
    /// API'den NPC ikna olduğunda çağrılır. Takibi başlatır.
    /// </summary>
    public void StartFollowing()
    {
        if (target == null)
        {
            Debug.LogError("[SimpleFollow] Hedef (target) atanmamış! Takip başlatılamıyor.");
            return;
        }

        isFollowing = true;
        Debug.Log("[SimpleFollow] Grom ikna oldu! Oyuncuyu takip etmeye başladı.");
    }

    /// <summary>
    /// Takibi durdurur (opsiyonel - oyun mantığı için gerekirse kullanılabilir)
    /// </summary>
    public void StopFollowing()
    {
        isFollowing = false;
        if (npcAnimator != null)
        {
            npcAnimator.SetBool("IsWalking", false);
        }
        Debug.Log("[SimpleFollow] Takip durduruldu.");
    }

    void OnDestroy()
    {
        // Event bağlantısını temizle
        if (apiController != null)
        {
            apiController.OnNPCConvinced.RemoveListener(StartFollowing);
        }
    }
}