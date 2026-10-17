# WSettings RAM (v0.1 - Beta)

> **⚠️ Uyarı:** Bu proje henüz **geliştirme aşamasındadır (v0.1)**. Bazı özellikler tamamlanma sürecindedir ve deneysel işlevler içerebilir.

**WSettings RAM**, Windows işletim sistemleri için tasarlanmış; RAM optimizasyonu, sistem süreç kontrolü, yazılım mağazası, virüs tarama analizleri ve ağ bağlantı izleme (IP Viewer) modüllerini tek bir çatı altında toplayan modern bir masaüstü yönetim aracıdır.

---

## 🛡️ Güvenlik ve VirusTotal Analizi

Projenin şeffaflığı ve kullanıcı güvenliği bizim için önceliklidir. Uygulamanın **v0.1** sürümüne ait derlenmiş executable (`.exe`) dosyasının VirusTotal tarama sonuçlarına aşağıdaki bağlantıdan ulaşabilirsiniz:

🔍 [**VirusTotal Raporunu Görüntüle**](https://www.virustotal.com/gui/file/21b12f8c0dcfcf9204d8043f980296839bf387a55f56f19e7d77f9c9c56bb93b?nocache=1) *(Lütfen kendi VirusTotal rapor linkinizi buraya ekleyin)*

### ⚠️ Antivirüs Uarıları Hakkında (False Positive Notu)
Uygulama `PyInstaller` kullanılarak pakete dönüştürüldüğü ve sistem derinliklerinde (RAM temizleme, süreç sonlandırma, ağ izleme `psutil`) işlemler yaptığı için bazı antivirüs motorları (örneğin *Bkav Pro*, *CrowdStrike*, *SecureAge* vb.) dosyayı **False Positive (Yanlış Alarm)** olarak algılayabilir. 

* **Kod Açıklığı:** Yazılım tamamen açık kaynaklıdır ve kaynak kodları repoda mevcuttur.
* **Güvenlik:** Arka planda hiçbir zararlı kod, veri sızdırma veya yetkisiz işlem barındırmaz. Dilerseniz projeyi doğrudan Python kaynak kodundan çalıştırabilir veya kendiniz `.exe` olarak derleyebilirsiniz.

---

## 🚀 Öne Çıkan Özellikler

* **💻 RAM Monitörü ve Optimizasyonu:**
  * Çalışan tüm işlemleri ve bellek tüketimlerini gerçek zamanlı izleme.
  * Arka plandaki askıda kalan belleği temizleyerek %50-%60 oranında RAM rahatlatma.
  * Tek tıkla istenmeyen süreçleri tamamen sonlandırma (`Kill Process`).

* **📦 Program Yükleme Merkezi (Software Hub):**
  * ISO imajları, edit/kurgu yazılımları, sosyal medya ve sistem araçları dahil geniş yazılım arşivi.
  * Doğrudan ve güvenli kaynaklardan indirme imkanı.

* **🛡️ Virüs Taraması ve Analiz:**
  * Sistemdeki şüpheli süreçleri ve dizinleri tarama.
  * Tespit edilen zararlıların dosya bazlı kaldırılması ve davranış analiz detayları.

* **🌐 IP Viewer (Ağ İzleyici):**
  * Bilgisayarınızın hangi uygulama, servis veya IP adresleriyle bağlantı kurduğunu anlık takip etme.
  * Şüpheli ağ trafiğini ve port kullanımını görüntüleme.

---

## 🛠️ Kurulum ve Çalıştırma

### Kaynak Koddan Çalıştırma

1. Repoyu klonlayın:
   ```bash
   git clone https://github.com/kullanici-adi/wsettings-ram.git
   cd wsettings-ram
   ```

2. Gerekli Python kütüphanelerini yükleyin:
   ```bash
   pip install customtkinter psutil requests
   ```

3. Uygulamayı başlatın:
   ```bash
   python main.py
   ```

### Executable (.exe) Olarak Derleme

Uygulamayı konsol penceresi olmadan tek bir `.exe` haline getirmek için:

```bash
pyinstaller --noconsole --onefile --uac-admin --name="WSettingsRam" main.py
```

---

## 📋 Yol Haritası (Roadmap) - v0.1 ve Sonrası

* [x] **v0.1:** Temel kullanıcı arayüzü ve RAM izleme modülü.
* [x] **v0.1:** IP Viewer ve ağ bağlantı analizi entegrasyonu.
* [ ] **v0.2:** Otomatik güncelleme altyapısının eklenmesi.
* [ ] **v0.3:** Virüs tarama motorunun genişletilmesi ve sezgisel (heuristic) tarama desteği.

---

## 💬 İletişim ve Geri Bildirim

Geliştirme aşamasında karşılaştığınız hataları veya önerilerinizi [**Issues**](../../issues) sekmesinden bildirebilirsiniz.
