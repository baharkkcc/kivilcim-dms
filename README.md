# 🚀 Kıvılcım DMS - Teknik Doküman Yönetim Sistemi

Kıvılcım DMS, üretim ve kalite departmanlarının teknik dokümanlarını, revizyonlarını, onay süreçlerini ve bildirimlerini profesyonel bir standartta yönetmesini sağlayan tam donanımlı (Full-Stack) bir web uygulamasıdır.

Bu proje **Streamlit (Frontend)**, **FastAPI (Backend)** ve **PostgreSQL (Database)** mimarisiyle sıfırdan geliştirilmiş ve **Docker** ile konteynerize edilmiştir.

---

## 🌟 Son Güncelleme Notları (Geliştirmeler ve Hata Çözümleri)

Projede bugün gerçekleştirilen başlıca altyapısal ve tasarımsal geliştirmeler aşağıda özetlenmiştir:

### 1. 🛡️ Güvenlik ve Üretim Ortamına (Production) Hazırlık
- **Geliştirici Araçlarının Kapatılması:** Veritabanına arayüzden müdahale edilmesini sağlayan `pgAdmin` servisi Docker konfigürasyonundan tamamen kaldırıldı. 
- **API Gizliliği:** Backend (FastAPI) dökümantasyon (Swagger UI / ReDoc) uç noktaları dışarıdan erişime kapatılarak (`docs_url=None`) sistemin dışarıya sızması engellendi. Önizlemelerin çalışması için backend portu güvenli şekilde yapılandırıldı.

### 2. 👥 "Çalışan Personeller" Paneli (Yeni Özellik)
- Arayüze tamamen yeni bir sekme eklendi. Yöneticilerin SQL kodları yazmadan sistemdeki çalışanları görebilmesi için **"Sicil Numarası"** (username), **"Ad Soyad"** ve **"Unvan"** bazlı dinamik bir personel tablosu oluşturuldu.

### 3. 🔔 Gelişmiş Bildirim ve Onay Sistemi
- **Bildirim Tetikleyicileri Onarıldı:** Yeni bir belge veya revizyon yüklendiğinde, seçilen onaycılara gerçek zamanlı olarak *"Belge incelemeniz için gönderildi"* şeklinde sistem bildirimleri düşmesi sağlandı.
- **Zorunlu Onaycılar (Koruma):** Bir belge revize edildiğinde, belgeyi ilk yükleyen kişinin ve önceki onaycıların sistemden yanlışlıkla silinmesi engellendi. Bu kişiler "Zorunlu Onaycılar" olarak ekrana sabitlendi.
- **E-Posta Tarzı Bildirim Arayüzü:** Bildirimler sekmesi modernize edilerek "okunmamış/okunmuş" durumlarına göre renklendirildi ve "Okundu" yerine daha işlevsel "Aç" (detaylara git) butonlarıyla donatıldı.

### 4. 🗂️ Doküman Yaşam Döngüsü ve Arşivleme
- **Arşiv ve Güncel Filtresi:** Doküman Listesine "Durum" (Güncel/Arşiv) filtresi eklendi. Eski versiyonlar ve "Reddedilen" belgeler artık silinmiyor, kırmızı renkli *(Revize Edildi)* veya *(Reddedildi)* ibareleriyle "Arşiv" sekmesinde ömür boyu saklanıyor.
- **Güvenli Doküman Silme:** Sistem/Kalite/Üretim yöneticilerine özel, çift onay mekanizmalı (inline expander) çok şık bir "Dokümanı Kalıcı Olarak Sil" butonu eklendi. Backend'e `cascade delete` kurgulanarak veritabanında "yetim veri" bırakmadan silme işlemi yapılması sağlandı.

### 5. 🎨 Profesyonel Arayüz (UI/UX) ve Hata Çözümleri
- **Renk ve Tema Optimizasyonları:** Göz yoran parlak mavi buton renkleri Streamlit'in ciddi kurumsal "Royal Blue" stiline geri döndürüldü.
- **Navigasyon (Routing) Hatası Çözüldü:** Doküman detaylarındayken sol menüden başka bir butona tıklandığında uygulamanın donma/takılma problemi, `session_state` mimarisi güncellenerek tamamen giderildi.
- **Departman Filtresi:** Aynı belgede birden fazla departman (örn: "Ar-Ge, Tasarım") tanımlandığında filtrelemenin çalışmama sorunu string parsing yöntemleriyle çözüldü.
- **Sol Panel (Sidebar) Daraltıldı:** "Kıvılcım DMS" başlığıyla modernize edilen sol paneldeki gereksiz üst boşluklar CSS ile sıfırlandı, ekran kaydırma ihtiyacı ortadan kaldırıldı.

---

## 🚀 Kurulum ve Çalıştırma

Projenin bilgisayarınızda çalışması için yalnızca **Docker Desktop**'ın kurulu olması yeterlidir.

1. Proje klasörünü bilgisayarınıza indirin veya klonlayın:
   ```bash
   git clone https://github.com/baharkkcc/kivilcim-dms.git
   cd kivilcim-dms
   ```

2. Docker ile projeyi tek tuşla başlatın:
   ```bash
   docker compose up -d --build
   ```

3. Kurulum tamamlandıktan sonra tarayıcınızdan uygulamaya erişin:
   👉 **http://localhost:8502**

*(Arka plan API ve dosya sunucusu `8001`, PostgreSQL veritabanı ise `5433` portu üzerinden arka planda haberleşmektedir.)*
