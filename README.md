# 🎮⚔️ Dwarf Grom — LLM Destekli Akıllı NPC Oyun Prototipi

> Unity oyun motoru içerisinde **Büyük Dil Modeli (LLM)**, **Ses Tanıma (STT)** ve **Ses Sentezi (TTS)** teknolojilerini bir araya getiren, yapay zeka destekli akıllı NPC etkileşim sistemi.

Oyuncu, oyundaki cüce demirci karakter **Grom** ile hem **yazılı** hem de **sesli** olarak doğal dilde iletişim kurabilir. Grom'un davranışları, özel olarak tasarlanmış bir **Hidden Judge (Gizli Hakem)** mekanizması aracılığıyla oyuncunun sunduğu argümanların tutarlılığına ve ikna ediciliğine göre dinamik olarak değişir.

---

## 📌 Öne Çıkan Özellikler

| Özellik | Açıklama |
|---|---|
| 🧠 **LLM Tabanlı Diyalog** | Google Gemini 2.5 Flash API ile doğal dilde sohbet |
| 🎙️ **Sesli İletişim** | Mikrofon ile konuşma → STT → LLM → TTS → NPC seslendirme |
| ⌨️ **Yazılı İletişim** | Sohbet paneli üzerinden metin tabanlı diyalog |
| 🤖 **Hidden Judge Sistemi** | NPC'nin ikna edilip edilemeyeceğini değerlendiren gizli hakem mekanizması |
| 🏃 **Dinamik NPC Davranışı** | İkna durumuna göre NPC'nin oyuncuyu takip etmesi veya reddetmesi |
| 🎭 **Karakter Kişiliği** | Prompt Engineering ile tasarlanmış tutarlı karakter profili |
| 🔊 **ElevenLabs TTS** | Çok dilli ses sentezi ile doğal NPC seslendirme |
| 🔁 **Gerçek Zamanlı İletişim** | Unity ↔ Python arasında REST API üzerinden JSON haberleşme |

---

## 🏗️ Sistem Mimarisi

Proje, birbirine REST API ile bağlanan iki ana katmandan oluşur:

```
┌─────────────────────────────────────────────────────────────┐
│                    UNITY İSTEMCİSİ (C#)                     │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌───────────┐  │
│  │ ChatUI   │  │ NPC      │  │ Player    │  │ Camera    │  │
│  │ (Arayüz) │  │Interaction│  │ Movement  │  │ Follow    │  │
│  └────┬─────┘  └─────┬────┘  └───────────┘  └───────────┘  │
│       │              │                                       │
│       └──────┬───────┘                                       │
│              ▼                                               │
│  ┌───────────────────┐       ┌──────────────┐               │
│  │   CallTheAPI      │       │ SimpleFollow  │               │
│  │  (HTTP İstemci)   │──────▶│ (NPC Takip)   │               │
│  └─────────┬─────────┘       └──────────────┘               │
│            │                                                 │
└────────────┼─────────────────────────────────────────────────┘
             │  HTTP POST (JSON / Base64 Audio)
             ▼
┌─────────────────────────────────────────────────────────────┐
│                  PYTHON BACKEND (FastAPI)                     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ npc_server.py│  │ npc_brain.py │  │  voice_utils.py  │   │
│  │  (API Sunucu)│  │ (LLM Mantık) │  │  (STT / TTS)     │   │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │
│         │                 │                    │              │
│         │         ┌───────▼───────┐   ┌───────▼──────────┐  │
│         │         │  Gemini API   │   │  ElevenLabs API  │  │
│         │         │  (2.5 Flash)  │   │  (Multilingual)  │  │
│         │         └───────────────┘   └──────────────────┘  │
│         │                                      │             │
│         │         ┌────────────────────────────┘             │
│         │         │  Google Speech Recognition               │
│         │         └──────────────────────────────            │
└─────────┼────────────────────────────────────────────────────┘
          │
          ▼  JSON Response: { reply, isConvinced, audio(base64) }
```

---

## 📂 Proje Yapısı

```
Dwarf Grom Game NEW/
│
├── Assets/
│   ├── C# SCRİPTS/              # Unity tarafı script'leri
│   │   ├── CallTheAPI.cs         # Python backend ile HTTP haberleşme (Singleton)
│   │   ├── ChatUI.cs             # Sohbet arayüzü ve mikrofon kaydı yönetimi
│   │   ├── NPCInteraction.cs     # Oyuncu-NPC mesafe algılama ve etkileşim tetikleme
│   │   ├── SimpleFollow.cs       # LLM kararına göre NPC takip davranışı
│   │   ├── PlayerMovement.cs     # 3. şahıs karakter hareketi (CharacterController)
│   │   ├── CameraFollow.cs       # Mouse ile 3. şahıs kamera kontrolü
│   │   └── AudioUtils.cs         # AudioClip → WAV byte dönüşümü
│   │
│   ├── Animations/               # Karakter animasyon dosyaları
│   ├── Scenes/                   # Unity sahne dosyaları
│   └── RPGPP_LT/                 # Low Poly RPG asset'leri
│
├── npc_LLM/                      # Python backend
│   ├── npc_server.py             # FastAPI asenkron API sunucusu
│   ├── npc_brain.py              # LLM entegrasyonu ve karakter mantığı
│   ├── voice_utils.py            # STT/TTS ses işleme modülü
│   └── requirements.txt          # Python bağımlılıkları
│
└── README.md
```

---

## 🧠 Teknik Detaylar

### Unity Tarafı (C#)

#### `CallTheAPI.cs` — API İstemcisi
- **Singleton Pattern** ile global erişim sağlar
- `UnityWebRequest` kullanarak Python backend'e HTTP POST istekleri gönderir
- Metin mesajlarını JSON formatında, ses verilerini **Base64** encode ederek iletir
- NPC yanıtındaki ses verisini (Base64 MP3) çözerek `AudioSource` üzerinden oynatır
- `UnityEvent` sistemi ile NPC yanıtını ve ikna durumunu diğer bileşenlere yayınlar
- **Coroutine** tabanlı asenkron iş akışı yönetimi

#### `ChatUI.cs` — Kullanıcı Arayüzü
- TextMeshPro tabanlı sohbet paneli (ScrollRect ile kaydırılabilir log)
- **X tuşu** ile açılıp kapanan sohbet penceresi
- **V tuşu basılı tutma** ile mikrofon kaydı (Push-to-Talk)
- `Microphone.Start/End` API'si ile ses kaydı alır, `AudioUtils` ile WAV formatına çevirir
- Chat açıkken oyuncu hareketi ve kamera kontrolü devre dışı kalır

#### `NPCInteraction.cs` — Etkileşim Tetikleyici
- `Vector3.Distance` ile oyuncu-NPC mesafe hesaplaması
- Belirli mesafe içinde etkileşim prompt'u gösterimi
- Gizmos ile Editor'de etkileşim mesafesinin görselleştirilmesi

#### `SimpleFollow.cs` — NPC Takip Sistemi
- `CallTheAPI.IsConvinced` durumuna göre NPC davranışını belirler
- `Vector3.MoveTowards` ile hedef takibi, `stoppingDistance` ile durma mesafesi
- Animator parametreleri ile yürüme/durma animasyon geçişleri
- `OnNPCConvinced` event'ine abone olarak anlık tepki

#### `PlayerMovement.cs` — Oyuncu Hareketi
- `CharacterController.SimpleMove` ile kamera yönelimli 3. şahıs hareket
- `Quaternion.RotateTowards` ile yumuşak karakter dönüşü
- Sohbet paneli açıkken hareketin tamamen devre dışı bırakılması

#### `CameraFollow.cs` — Kamera Kontrolü
- Mouse girişi ile orbital kamera hareketi
- Pitch sınırlama (clamp) ile doğal görüş açısı kontrolü

---

### Python Backend

#### `npc_server.py` — FastAPI Sunucusu
- **Asenkron** HTTP API sunucusu (FastAPI + Uvicorn)
- **Endpoint'ler:**
  - `POST /chat` — Metin veya ses girişi alır, LLM yanıtı ve opsiyonel TTS sesi döndürür
  - `POST /chat/voice` — Sesli yanıt endpoint'i (MP3 stream)
  - `POST /tts` — Bağımsız metin-ses dönüşümü
  - `POST /stt` — Bağımsız ses-metin dönüşümü (dosya yükleme)
  - `GET /voice/status` — Ses servisi durum kontrolü
- **Oturum yönetimi:** `player_id` bazlı chat session'ları (çoklu oyuncu desteği altyapısı)
- Base64 ile gelen ses verisinin STT'ye yönlendirilmesi ve metin olarak LLM'e aktarılması
- Hata yönetimi: Rate limit (429), Authentication (401/403), Safety filter ve genel hatalar

#### `npc_brain.py` — NPC Yapay Zeka Beyni
- **Google Gemini 2.5 Flash** modeli ile yapılandırılmış sohbet oturumu
- **Prompt Engineering:**
  - Karakter kişiliği tanımı (huysuz cüce demirci, altın tutkusu, eski Türkçe üslup)
  - Hidden Judge kuralları (ikna koşulları, reddedilme senaryoları)
  - JSON formatında yapılandırılmış yanıt şeması (`response` + `isConvinced`)
- **Rule-Based Response:** Anahtar kelime tespiti ile hızlı tepki sistemi (Türkçe ek uyumlu regex)
- **Fallback Wait Messages:** API yanıt gecikmeleri için progresif bekleme mesajları
- Multithreaded API çağrısı (ana thread'i bloklamadan arka planda çalışma)

#### `voice_utils.py` — Ses İşleme Modülü
- **Text-to-Speech (TTS):**
  - ElevenLabs SDK v2.x entegrasyonu (geriye uyumlu fallback'ler)
  - `eleven_multilingual_v2` modeli ile Türkçe ses sentezi
  - Birden fazla SDK sürümüne uyumlu adaptif API çağrıları
  - REST API fallback mekanizması
- **Speech-to-Text (STT):**
  - Google Speech Recognition API (Türkçe dil desteği)
  - `correct_speech_text()` fonksiyonu ile yaygın tanıma hatalarının otomatik düzeltilmesi
  - WAV formatından ve mikrofon girişinden ses tanıma
- **Push-to-Talk:** Klavye (Space tuşu) basılı tutma ile ses kaydı

---

### Hidden Judge (Gizli Hakem) Sistemi

Oyuncunun NPC'yi ikna etme sürecini değerlendiren yapay zeka mekanizmasıdır:

```
Oyuncu Mesajı → Gemini LLM → JSON { response, isConvinced }
                    │
                    ▼
            ┌──────────────┐
            │ Değerlendirme│
            │   Kriterleri │
            └──────┬───────┘
                   │
         ┌─────────┼──────────┐
         ▼         ▼          ▼
    ✅ İkna Ol  ❌ Reddet   ⏳ Bekle
    - Baba       - Tehdit     - İlk deneme
      konusu     - Zorlama    - Yetersiz
    - Altın      - Tutarsız     argüman
      teklifi      argüman
    - Geçerli
      kanıt
```

- Oyuncu babadan bahsedip samimi yaklaşırsa → ikna olur
- Altın teklif edilirse veya makul ödeme taahhüdü varsa → ikna olur
- Tehdit veya zorlama varsa → kesinlikle ikna olmaz
- İlk ikna girişiminde → ikna olmaz (en az 2 tur gereklidir)

---

## 🎮 Oynanış ve Kontroller

| Tuş | İşlev |
|---|---|
| `W / A / S / D` | Karakter hareketi |
| `Mouse` | Kamera kontrolü |
| `X` | Sohbet panelini aç/kapat |
| `V` (Basılı Tut) | Sesli konuşma (Push-to-Talk) |
| `ESC` | Sohbet panelini kapat |

### Oyun Akışı
1. Oyuncu, 3D dünyada serbestçe hareket eder
2. Grom'a yaklaştığında etkileşim prompt'u belirir
3. `X` tuşu ile sohbet panelini açar veya `V` ile sesli konuşur
4. Grom, oyuncunun söylediklerini değerlendirir ve karakter olarak yanıt verir
5. Oyuncu yeterince ikna edici olursa Grom takip etmeye başlar

---

## 🛠️ Kurulum ve Çalıştırma

### Gereksinimler
- **Unity 6** (URP — Universal Render Pipeline)
- **Python 3.8+**
- **Gemini API Key** ([Google AI Studio](https://aistudio.google.com/app/apikey))
- **ElevenLabs API Key** (Opsiyonel — TTS için) ([ElevenLabs](https://elevenlabs.io/))

### 1. Python Backend Kurulumu

```bash
cd npc_LLM
pip install google-generativeai fastapi uvicorn pydantic elevenlabs SpeechRecognition pyaudio keyboard
```

### 2. API Anahtarlarının Tanımlanması

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="sizin_gemini_api_anahtariniz"
$env:ELEVENLABS_API_KEY="sizin_elevenlabs_api_anahtariniz"   # Opsiyonel
```

**macOS / Linux:**
```bash
export GEMINI_API_KEY="sizin_gemini_api_anahtariniz"
export ELEVENLABS_API_KEY="sizin_elevenlabs_api_anahtariniz"   # Opsiyonel
```

### 3. Sunucuyu Başlatma

```bash
cd npc_LLM
uvicorn npc_server:app --reload
```

Sunucu başarıyla başladığında `http://127.0.0.1:8000` adresinde çalışır.

### 4. Unity Projesini Açma

Unity Hub üzerinden projeyi açın ve sahneyi çalıştırın.

---

## 🔧 Kullanılan Teknolojiler

| Kategori | Teknoloji |
|---|---|
| **Oyun Motoru** | Unity 6 (URP) |
| **Programlama Dilleri** | C# (Unity), Python (Backend) |
| **LLM** | Google Gemini 2.5 Flash |
| **API Framework** | FastAPI + Uvicorn |
| **Ses Sentezi (TTS)** | ElevenLabs (eleven_multilingual_v2) |
| **Ses Tanıma (STT)** | Google Speech Recognition |
| **Veri İletişimi** | REST API, JSON, Base64 |
| **UI Framework** | TextMeshPro, Unity UI |
| **3D Modeller** | Low Poly Modular Character Pack |
| **Render Pipeline** | Universal Render Pipeline (URP) |

---

## 📈 Gelecek Geliştirmeler

- [ ] Çoklu NPC desteği (farklı kişiliklerde AI karakterler)
- [ ] Karakter hafızası sistemi (uzun süreli konuşma bağlamı)
- [ ] Duygu analizi ve yüz ifadesi entegrasyonu
- [ ] Görev tabanlı diyalog sistemi (quest chain)
- [ ] Yerel LLM desteği (Ollama entegrasyonu)
- [ ] Daha gelişmiş NPC davranış ağaçları (Behavior Tree)
- [ ] WebSocket ile gerçek zamanlı streaming yanıtlar

---

## 📄 Lisans

Bu proje eğitim, araştırma ve prototipleme amaçlı geliştirilmiştir.

## Oynanış Videosu

[![Videoyu İzlemek İçin Tıklayın](https://img.youtube.com/vi/wW9WMaQVq_k/0.jpg)](https://www.youtube.com/watch?v=wW9WMaQVq_k)

