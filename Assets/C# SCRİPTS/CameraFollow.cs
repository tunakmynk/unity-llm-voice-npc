using UnityEngine;

public class CameraFollow : MonoBehaviour
{
    public Transform target;            
    public float mouseSensitivity = 3f; 
    public float distanceFromPlayer = 5f; 
    public float heightOffset = 2f;     
    
    public Vector2 pitchLimits = new Vector2(-40, 85); 

    private float rotationX = 0f;
    private float rotationY = 0f;

    void Start()
    {
        Cursor.lockState = CursorLockMode.Locked;
        Cursor.visible = false;
    }

    void LateUpdate()
    {
        // --- EKLENEN KISIM: KESİN ÇÖZÜM ---
        
        // ChatUI scriptindeki statik değişkene bakıyoruz.
        // Eğer Chat açıksa, bu script hiçbir şey yapmasın ve dursun.
        if (ChatUI.IsChatOpen)
        {
            return; 
        }
        
        // ----------------------------------

        if (target == null) return;

        // 1. Get Mouse Input
        rotationX += Input.GetAxis("Mouse X") * mouseSensitivity;
        rotationY -= Input.GetAxis("Mouse Y") * mouseSensitivity;

        // 2. Clamp
        rotationY = Mathf.Clamp(rotationY, pitchLimits.x, pitchLimits.y);

        // 3. Calculate Rotation
        Quaternion targetRotation = Quaternion.Euler(rotationY, rotationX, 0);
        Vector3 targetPosition = target.position + Vector3.up * heightOffset;
        Vector3 finalPosition = targetPosition - (targetRotation * Vector3.forward * distanceFromPlayer);

        // 4. Apply
        transform.position = finalPosition;
        transform.LookAt(targetPosition);
    }
}