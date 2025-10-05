
# Instagram Uploader — Metro GUI (CSV Toplu) 🚀

Instagram Business/Creator hesapları için **Instagram Graph API** tabanlı, masaüstü kullanımına uygun, modern bir **ttkbootstrap (Metro)** arayüze sahip yükleyici.  
Tek bir pencereden **tekli** (resim/video) yükleme yapabilir, ya da **CSV** ile **toplu** gönderi akışını başlatabilirsiniz. 🎯

> **Önemli:** Bu araç, **Meta Instagram Graph API** kullanır. Kişisel (standart) hesaplarla çalışmaz; **Business** veya **Creator** hesap gerektirir.  
> Ayrıca ilgili **Facebook Sayfası** bağlantısı ve **uygulama** yapılandırması (permissions, access token) şarttır.

---

## ✨ Özellikler
- **Tekli Yükleme:** Resim veya video URL’si + Caption alanı
- **Toplu Yükleme (CSV):** `type,url,caption` başlıklı CSV’den çoklu işlem
- **Video İçin Polling:** İşleme (processing) sürecini duruma göre bekler
- **Donmayan Arayüz:** Tüm API işlemleri arka planda ayrı thread ile
- **İlerleme Göstergeleri:** Toplam (determinate) + Anlık (indeterminate) progress bar
- **Kolay Yapılandırma:** `.env` veya `ayarlar.txt` ile ayarlar
- **Ayrıntılı Loglama:** Anlık işlem adımları ve sonuçlar

---

## 📦 Gereksinimler
- Python 3.9+
- Bağımlılıklar:
  - `requests`
  - `ttkbootstrap`
  - `python-dotenv` (opsiyonel)

> Kurulum:
```bash
pip install requests ttkbootstrap python-dotenv
```

---

## 🔧 Kurulum
1. Depoyu klonlayın:
   ```bash
   git clone https://github.com/<kullanici-adiniz>/instagram-uploader-metro-gui.git
   cd instagram-uploader-metro-gui
   ```
2. **Ayar dosyasını** oluşturun: `ayarlar.txt`  
   Örnek için `ayarlar.txt.example` dosyasını kopyalayın ve düzenleyin:
   ```bash
   cp ayarlar.txt.example ayarlar.txt
   ```
   Ardından `access_token` ve `ig_user_id` alanlarını gerçek değerlerinizle doldurun.
3. (İsteğe bağlı) `.env` kullanacaksanız, aşağıdaki gibi bir `.env` oluşturabilirsiniz:
   ```env
   IG_ACCESS_TOKEN=EAAB...GERCEK_TOKEN
   IG_USER_ID=1784...GERCEK_ID
   IG_API_VERSION=v21.0
   ```
   > **Öncelik:** `.env` > `ayarlar.txt` (uygulama önce `.env` değişkenlerini okur, yoksa `ayarlar.txt`’ye başvurur)

---

## ▶️ Çalıştırma
```bash
python instagram_uploader_gui.py
```
Uygulama açıldığında:
- **Tekli Yükleme** sekmesinde:
  - Medya Tipi: `Resim` veya `Video`
  - Medya URL: Doğrudan dosya URL’i (http/https)
  - Caption: Açıklama metni (isteğe bağlı)
  - **Tekli Yükle** butonuna basın.
- **Toplu Yükleme (CSV)** sekmesinde:
  - `type,url,caption` başlıklı bir CSV seçin
  - **CSV’den Yüklemeyi Başlat** butonuna basın.

> **CSV Örneği** için `samples/example.csv` dosyasına bakın.

---

## 🧩 CSV Biçimi
Zorunlu başlıklar: `type,url,caption` (case-insensitive)

| Sütun | Değerler | Açıklama |
|------:|----------|----------|
| type  | `image` veya `video` | Medya türü |
| url   | http/https | Doğrudan erişilebilir medya dosyası URL’i |
| caption | serbest metin | (İsteğe bağlı) gönderi açıklaması |

> Geçersiz veya boş satırlar otomatik atlanır.

---

## 🔒 Güvenlik & İpuçları
- **Access Token’ınızı** asla depo içine düz metin olarak koymayın. `.env` ve/veya gizli değişkenler kullanın.
- Token’ınızın **süre** ve **izin** kapsamlarını kontrol edin (Instagram Graph API gereksinimleri).
- Medya URL’leri **doğrudan erişilebilir** olmalı. Yönlendirme/kimlik doğrulama gerektiren URL’ler başarısız olabilir.
- Video işleme süreleri içeriğe ve uzunluğa göre değişebilir. `poll_interval` ve `timeout` değerlerini ayarlarınızda değiştirebilirsiniz.
---
## 🔐 Token Nasıl Alınır? (Instagram Graph API)

> Aşağıdaki adımlar **Business/Creator** Instagram hesapları içindir. Ayrıca Instagram hesabınızın bir **Facebook Sayfasına** bağlı olması gerekir.

1) **Meta for Developers** sayfasına gidin ve yeni bir uygulama oluşturun  
   https://developers.facebook.com/apps/  
   - **Create App** butonuna tıklayın  
   - **Other** seçin  
   - **App name** girin, devam edin  
   - **Select an app type** olarak **Business** seçin  
   - Detay ekranında ekstra ayar yapmadan **Create app** ile tamamlayın

2) **Uygulamanızı açın**  
   https://developers.facebook.com/apps/ adresine dönün, az önce oluşturduğunuz **app**’i seçin.

3) **Instagram ürününü ekleyin**  
   Sol menüden **Instagram** (Instagram Graph API) öğesini bulun ve ekleyin.  
   Bu bölümde “**Generate access tokens**” adımlarını takip edin.

4) **Graph API Explorer ile Access Token alın**  
   https://developers.facebook.com/tools/explorer/  
   - Sol üstte **Meta App** olarak kendi uygulamanızı seçin  
   - **Permissions** bölümüne aşağıdaki izinleri ekleyin (gerektiği kadar):  
     - `instagram_basic`  
     - `instagram_manage_comments`  
     - `instagram_manage_insights`  
     - `instagram_content_publish`  
     - `instagram_manage_messages`  
     - `instagram_branded_content_brand`  
     - `instagram_branded_content_creator`  
     - `instagram_branded_content_ads_brand`  
     - `instagram_manage_upcoming_events`  
   - **Generate Access Token** ile bir **User Access Token** üretin

5) **Token’ı projeye tanımlayın**  
   - `ayarlar.txt` içine `access_token` alanına yapıştırın  
   - veya `.env` dosyasında `IG_ACCESS_TOKEN` olarak kullanın

> **İpucu:** Üretilen token’ların ömrü kısadır. Üretim ortamında **Long-Lived** (uzun ömürlü) token’a dönüştürmeniz önerilir. Gerekirse **Pages** izinlerini ve **Instagram Business Account** bağlantısını kontrol edin. Uygulamanızı **Live Mode**’a almak ve kullanıcı/rol atamaları yapmak da gerekebilir.

### Örnek ayarlar

**ayarlar.txt**
```ini
access_token=EAAB...SAMPLE_ACCESS_TOKEN
ig_user_id=1784...SAMPLE_USER_ID
api_version=v21.0
poll_interval=5
timeout=600
```

**.env**
```env
IG_ACCESS_TOKEN=EAAB...GERCEK_TOKEN
IG_USER_ID=1784...GERCEK_ID
IG_API_VERSION=v21.0
```

---

## 🛠️ Sorun Giderme (Troubleshooting)
- **"ayarlar.txt içinde Access Token ve IG User ID bulunamadı"**  
  → `ayarlar.txt` dosyasında `access_token` ve `ig_user_id` değerleri dolu mu? `.env` varsa değişken adları doğru mu?
- **API hatası / JSON dönmedi**  
  → Meta Graph API isteği başarısız olabilir. Hata kodu ve mesajı log’da yazacaktır. Token izinleri, hesap türü (Business/Creator) ve medya URL’lerini kontrol edin.
- **Video işlem hatası veya zaman aşımı**  
  → `timeout` süresini artırmayı deneyin. Dosya formatının Instagram tarafından desteklendiğinden emin olun.
- **URL Hatası**  
  → Mutlaka `http://` veya `https://` ile başlayan ve doğrudan indirilebilir bir URL girin.

---

## ❓ SSS
**S: Kişisel hesapta çalışır mı?**  
C: Hayır. Sadece **Business/Creator** hesaplarla çalışır.

**S: Yerel dosyayı yükleyebilir miyim?**  
C: Bu sürüm doğrudan URL ile çalışır. Yerel dosyalar için önce bir depolama servisine yükleyip **doğrudan** URL sağlamalısınız.

**S: Caption zorunlu mu?**  
C: Hayır. Boş bırakılabilir.

---

## 📄 Lisans
MIT

---

