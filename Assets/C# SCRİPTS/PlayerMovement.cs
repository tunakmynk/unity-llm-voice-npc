using UnityEngine;

public class PlayerMovement : MonoBehaviour
{
    public float moveSpeed = 5f;
    public float rotationSpeed = 720f;
    public Transform cameraTransform;

    private Animator animator;
    private CharacterController controller; 

    void Start()
    {
        animator = GetComponent<Animator>();
        controller = GetComponent<CharacterController>();
    }

    void Update()
    {
        // --- EKLENEN KISIM: CHAT KONTROLÜ ---
        // Eğer Chat penceresi açıksa, hareket kodlarını çalıştırma.
        if (ChatUI.IsChatOpen)
        {
            // 1. Yürüme animasyonunu durdur (yoksa olduğu yerde yürür gibi görünür)
            if (animator != null)
            {
                animator.SetBool("IsWalking", false);
            }

            // 2. Karakteri olduğu yerde tut ama yerçekimi uygulamaya devam et
            // (Bunu yapmazsak karakter havada asılı kalabilir)
            if (controller != null)
            {
                controller.SimpleMove(Vector3.zero);
            }

            // 3. Kodun geri kalanını okuma, buradan çık.
            return;
        }
        // -------------------------------------


        // 1. Safety Check for Camera
        if (cameraTransform == null && Camera.main != null) 
            cameraTransform = Camera.main.transform;
        if (cameraTransform == null) return;

        // 2. Get Input
        float horizontal = Input.GetAxis("Horizontal");
        float vertical = Input.GetAxis("Vertical");

        // 3. Calculate Direction based on Camera
        Vector3 camForward = cameraTransform.forward;
        Vector3 camRight = cameraTransform.right;
        camForward.y = 0;
        camRight.y = 0;
        camForward.Normalize();
        camRight.Normalize();

        Vector3 moveDirection = (camForward * vertical) + (camRight * horizontal);

        // 4. Animation Logic
        bool isMoving = moveDirection.magnitude >= 0.1f;
        if (animator != null)
        {
            animator.SetBool("IsWalking", isMoving);
        }

        // 5. Movement Logic
        if (isMoving)
        {
            // Rotate the character to face movement
            Quaternion targetRotation = Quaternion.LookRotation(moveDirection);
            transform.rotation = Quaternion.RotateTowards(transform.rotation, targetRotation, rotationSpeed * Time.deltaTime);
            
            // Move using the Controller (Handles walls + Gravity automatically)
            controller.SimpleMove(moveDirection * moveSpeed);
        }
        else
        {
            // Even when not moving keys, apply gravity so he doesn't float
            controller.SimpleMove(Vector3.zero);
        }
    }
}