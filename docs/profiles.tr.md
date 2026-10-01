# Profiller

Profiller yalnızca sınırlı OpenCode `steps` bütçelerini değiştirir.

- **Dengeli:** günlük kullanım için varsayılan seçim.
- **Yüksek Kalite:** zor işler için daha geniş bütçeler.
- **Ekonomik:** rutin işler için daha küçük bütçeler.
- **Kota Tasarrufu:** en küçük hazır bütçeler; zor işlerde çözümden önce durabilir.
- **Özel:** Dengeli bütçelere ek olarak kesin model seçimi.

Özel seçim `sağlayıcı/model[#varyant]` biçimindedir. Açık onay verilmedikçe yerel roller tek sağlayıcıda kalır. Varsayılan `--model` verilmeden yalnızca bir rol değiştirilirse oturumdan devralınan sağlayıcı bilinemez; bu nedenle kurulum açık sağlayıcı karıştırma onayı ister. Modelin hesabınızda bulunup bulunmadığını OpenCode `/models` ile kontrol edin.


Çalışma zamanındaki `steps` değerleri ve model seçimleri yalnızca JSON ayarında tutulur. Markdown rol dosyalarında istemler ve izinler bulunur; aynı sayısal ayarlar iki yerde tutulmaz. Ana `--model` seçimi `#varyant` kabul etmez; sağlayıcı destekliyorsa rol için `--role-model` kullanılabilir. Model kimliklerinde ek eğik çizgiler olabilir. `steps`, model dönüşü bütçesidir; token tavanı değildir. Tarayıcı profilleri [yerel konsolda](local-console.md) bulunur; Özel seçim mevcut adımları korur. Doğrulanmış OpenCode sözleşmesi olmadan sayısal eşzamanlılık ayarı iddia edilmez.


Tarayıcıdaki Kurulum sekmesi, her biri ayrı uzman görevi ve modeli olan 1–50 yardımcı yuvası oluşturabilir. Aynı görev birden çok yuvada bulunabilir. Bu sayı eşzamanlı çalışma garantisi değil, hazır yuva sayısıdır. Mevcut özel `#variant` seçimleri korunur; doğrulanmış varyant listesi yoksa yeni seçim kapalıdır. Varyant adı kendiliğinden düşünme eforu anlamına gelmez. Şef her zaman koordinatördür, çalışan uzman değildir.

Kurulumda on iş türü önerisi de vardır: görsel oluşturma, oyun, web sitesi, araştırma, backend/API, mobil uygulama, veri analizi, hata düzeltme, güvenlik/kontrol ve belge/içerik. Her öneri farklı 2–5 yardımcı ve dört adım tarzından birini hazırlar; yalnız kaydedilmemiş taslağı değiştirir ve kaydetmeden geri alınabilir. Ucuz model, token tasarrufu veya otomatik eşzamanlı başlatma vaat etmez. Görsel üretmek için ayrı bir görsel aracı gerekir; metin modeli tek başına piksel oluşturmaz. İsteğe bağlı 50 yuvalık ekip konsolda onarlı sayfalarla gösterilir ve eşzamanlı çalışma garantisi değildir.
