# 🎙️ Unity LLM Voice NPC Prototype

Bu proje, Unity oyun motoru içerisinde büyük dil modelleri (LLM) ve ses tanıma teknolojilerini bir araya getiren bir akıllı NPC prototipidir. Oyuncu, mikrofon aracılığıyla NPC ile doğal bir konuşma gerçekleştirir. LLM tarafından analiz edilen konuşmanın içeriğine göre NPC, oyuncuyu takip etme veya reddetme gibi dinamik davranışlar sergiler.

## 📂 Proje Yapısı

Bu proje iki ana bileşenden oluşmaktadır:

* **`Dwarf Grom Game NEW/` (İstemci / Client):** Oyuncunun ses girişini alan, NPC hareketlerini ve arayüzü yöneten Unity projesi. 🎮
* **`npc_LLM/` (Sunucu / Python Backend):** 🐍
    * `npc_server.py`: Unity ile iletişimi sağlayan, **FastAPI** kullanılarak geliştirilmiş asenkron API sunucusu. İstemciden gelen verileri alır ve cevapları JSON formatında Unity'e döndürür.
    * `npc_brain.py`: Oyunun yapay zeka mantığını yöneten çekirdek modül. **Gemini API** entegrasyonunu içerir. Karakterin kişiliğini (Prompt Engineering) ve oyuncunun argümanlarına göre ikna olup olmadığını değerlendiren *Hidden Judge* (Gizli Hakem) sistemini barındırır.
    * `voice_utils.py`: Ses tanıma (STT) ve metin okuma (TTS) işlemlerini yöneten araçlar.

## 🛠️ Kurulum ve Çalıştırma (Python Backend)

Unity istemcisinin çalışabilmesi için öncelikle Python API sunucusunun ayağa kaldırılması gerekmektedir.

### 1. Gereksinimler
Sistemin çalışması için Python 3.8 veya üzeri bir sürümün yüklü olması gerekir. `npc_LLM` klasörüne giderek gerekli kütüphaneleri kurun:

```bash
cd npc_LLM
pip install google-generativeai fastapi uvicorn pydantic elevenlabs SpeechRecognition pyaudio keyboard```

2. Çevre Değişkenleri (API Key)
Yapay zeka modelinin yanıt üretebilmesi için Google Gemini API anahtarı gerekmektedir. Terminalinizde şu komutla anahtarınızı tanımlayın:

Windows (PowerShell):
$env:GEMINI_API_KEY="sizin_api_anahtariniz"

Mac/Linux:
export GEMINI_API_KEY="sizin_api_anahtariniz"

(Opsiyonel) Eğer seslendirme (TTS) özelliklerini kullanmak isterseniz, ELEVENLABS_API_KEY değişkenini de benzer şekilde sisteme ekleyebilirsiniz.

3. Sunucuyu Ayağa Kaldırma
Bağımlılıklar kurulduktan ve API anahtarı ayarlandıktan sonra, FastAPI sunucusunu başlatmak için şu komutu çalıştırın:
uvicorn npc_server:app --reload

Sunucu başarıyla başladığında http://127.0.0.1:8000 adresinde dinlemeye geçecektir. Ardından Unity projesini açıp prototipi deneyimlemeye başlayabilirsiniz.

## 🎮 Oynanış ve Kontroller (Unity İstemcisi)

Python sunucusu çalışır durumdayken Unity projesini (`Dwarf Grom Game NEW`) başlatın.

* **Yazılı İletişim:** Klavyeden **`X`** tuşuna basarak metin kutusunu açabilir ve Grom ile yazışabilirsiniz.
* **Sesli İletişim:** Klavyeden **`V`** tuşuna basılı tutarak mikrofonunuz aracılığıyla Grom ile konuşabilirsiniz.
* **Mekanik:** Grom'u argümanlarınızla ikna etmeyi başarırsanız, NPC sizi haritada takip etmeye başlar. İkna edemezseniz takibi bırakır.
