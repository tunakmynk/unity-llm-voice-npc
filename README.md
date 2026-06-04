# 🎙️ Unity LLM Voice NPC Prototype

Bu proje, Unity oyun motoru içerisinde Büyük Dil Modelleri (LLM) ve ses tanıma teknolojilerini bir araya getiren akıllı bir NPC prototipidir. Oyuncu, mikrofon aracılığıyla NPC ile doğal bir konuşma gerçekleştirir. LLM tarafından analiz edilen konuşma içeriğine göre NPC, oyuncuyu takip etme veya reddetme gibi dinamik davranışlar sergiler.

---

# 📌 Proje Özeti

Oyuncu, oyundaki cüce karakter **Grom** ile hem yazılı hem de sesli olarak iletişim kurabilir. Grom'un davranışları, oyuncunun sunduğu argümanların ikna ediciliğine göre değişir.

Sistem iki ana bileşenden oluşur:

1. **Unity İstemcisi (Client)**

   * Oyuncu girişlerini yönetir.
   * NPC hareketlerini kontrol eder.
   * Kullanıcı arayüzünü sağlar.
   * Python backend ile haberleşir.

2. **Python Backend (Server)**

   * Ses ve metin girdilerini işler.
   * Gemini API üzerinden LLM yanıtları üretir.
   * NPC'nin karar verme mekanizmasını çalıştırır.
   * Sonuçları Unity istemcisine JSON olarak döndürür.

---

# 📂 Proje Yapısı

```text
Project Root
│
├── Dwarf Grom Game NEW/
│   └── Unity istemcisi
│
└── npc_LLM/
    ├── npc_server.py
    ├── npc_brain.py
    └── voice_utils.py
```

## 🎮 Dwarf Grom Game NEW/

Unity tarafındaki istemci uygulamasıdır.

### Görevleri

* Oyuncudan ses ve metin girdilerini almak
* NPC animasyonlarını ve hareketlerini yönetmek
* Kullanıcı arayüzünü kontrol etmek
* Python API sunucusuyla haberleşmek

---

## 🐍 npc_LLM/

LLM tabanlı karar verme ve ses işleme sistemlerinin bulunduğu backend klasörüdür.

### `npc_server.py`

FastAPI kullanılarak geliştirilmiş asenkron API sunucusudur.

#### Sorumlulukları

* Unity'den gelen HTTP isteklerini almak
* Oyuncu mesajlarını işlemek
* NPC mantığını çalıştırmak
* Sonuçları JSON olarak geri döndürmek

---

### `npc_brain.py`

NPC'nin yapay zeka mantığını yöneten çekirdek modüldür.

#### Özellikler

* Gemini API entegrasyonu
* Prompt Engineering sistemi
* Karakter kişiliği yönetimi
* Hidden Judge (Gizli Hakem) mekanizması

#### Hidden Judge Sistemi

Oyuncunun NPC'yi ikna etmek için sunduğu argümanlar ayrı bir değerlendirme sürecinden geçirilir.

Bu sistem:

* Oyuncunun söylediklerini analiz eder
* İkna seviyesini hesaplar
* NPC'nin oyuncuyu takip edip etmeyeceğine karar verir

---

### `voice_utils.py`

Ses işleme işlemlerini yöneten yardımcı modüldür.

#### İçerdiği Sistemler

**Speech-to-Text (STT)**

* Mikrofon girişini alır
* Konuşmayı metne dönüştürür

**Text-to-Speech (TTS)**

* NPC cevaplarını seslendirir
* ElevenLabs entegrasyonu ile doğal konuşma üretir

---

# 🛠️ Kurulum ve Çalıştırma

Unity istemcisini çalıştırmadan önce Python backend sunucusunun başlatılması gerekir.

## 1. Gereksinimler

Sistemde Python 3.8 veya üzeri bir sürüm bulunmalıdır.

Backend klasörüne geçin:

```bash
cd npc_LLM
```

Gerekli paketleri kurun:

```bash
pip install google-generativeai fastapi uvicorn pydantic elevenlabs SpeechRecognition pyaudio keyboard
```

---

## 2. API Anahtarlarının Tanımlanması

### Gemini API

#### Windows (PowerShell)

```powershell
$env:GEMINI_API_KEY="sizin_api_anahtariniz"
```

#### macOS / Linux

```bash
export GEMINI_API_KEY="sizin_api_anahtariniz"
```

---

### ElevenLabs API (Opsiyonel)

Eğer TTS özelliklerini kullanacaksanız:

#### Windows (PowerShell)

```powershell
$env:ELEVENLABS_API_KEY="sizin_api_anahtariniz"
```

#### macOS / Linux

```bash
export ELEVENLABS_API_KEY="sizin_api_anahtariniz"
```

---

## 3. Sunucuyu Başlatma

Backend klasöründe aşağıdaki komutu çalıştırın:

```bash
uvicorn npc_server:app --reload
```

Başarılı bir başlangıç sonrasında sunucu aşağıdaki adreste çalışacaktır:

```text
http://127.0.0.1:8000
```

Artık Unity istemcisi backend ile iletişim kurabilir.

---

# 🎮 Oynanış ve Kontroller

Python sunucusu çalışırken Unity projesini başlatın:

```text
Dwarf Grom Game NEW
```

---

## ⌨️ Yazılı İletişim

NPC ile metin üzerinden konuşmak için:

```text
X Tuşu
```

* Sohbet kutusunu açar.
* Yazılı mesaj göndermenizi sağlar.

---

## 🎙️ Sesli İletişim

NPC ile sesli konuşmak için:

```text
V Tuşunu Basılı Tut
```

* Mikrofon kaydı başlar.
* Konuşma metne dönüştürülür.
* NPC tarafından analiz edilir.

---

# 🧠 NPC Davranış Mekaniği

Oyuncu ve Grom arasında doğal bir diyalog gerçekleşir.

### Eğer Oyuncu Başarılı Şekilde İkna Ederse

✅ Grom oyuncuyu takip etmeye başlar.

### Eğer Oyuncu Başarısız Olursa

❌ Grom oyuncuyu takip etmeyi reddeder veya takibi bırakır.

Bu kararlar, LLM destekli Hidden Judge sistemi tarafından belirlenir.

---

# 🔧 Kullanılan Teknolojiler

## Oyun Motoru

* Unity

## Backend

* Python
* FastAPI
* Uvicorn

## Yapay Zeka

* Google Gemini API

## Ses İşleme

* SpeechRecognition
* PyAudio
* ElevenLabs

## Veri İletişimi

* REST API
* JSON

---

# Gelecek Geliştirmeler

* Çoklu NPC desteği
* Karakter hafızası (Memory System)
* Duygu analizi
* Görev tabanlı diyaloglar
* Yerel LLM desteği
* Daha gelişmiş NPC davranış ağaçları

---

# 📄 Lisans

Bu proje eğitim, araştırma ve prototipleme amaçlı geliştirilmiştir.
