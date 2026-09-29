# Sık sorulan sorular ve sorun giderme

**Paket sağlayıcı seçer mi?** Hayır. Varsayılan roller mevcut OpenCode oturum modelini devralır. `/connect` ve `/models` kullanılır.

**Kota Tasarrufu kesin olarak az token harcar mı?** Hayır. Yalnızca adım bütçelerini küçültür. Gerçek kullanım göreve, modele, sağlayıcıya ve OpenCode davranışına bağlıdır.

**Özel model neden kabul edilmedi?** `sağlayıcı/model` veya `sağlayıcı/model#varyant` biçimini kullanın. Sağlayıcı karıştırmak açık onay ister.

**Mevcut dosya neden korundu?** Kurucu kendisine ait olmayan bir çakışma buldu. İnceledikten sonra değiştirmeyi seçerseniz önce yedek alır.

**Kullanım raporu neden yok?** OpenCode CLI yoktur, desteklenen `opencode stats`/temizlenmiş dışa aktarım komutu başarısız olmuş veya süreyi aşmıştır ya da çıktısı tanınamamıştır. `stats --json` desteklenen bir seçenek değildir. Eksik sayaçlara hayalî sıfır konmaz.

**On yardımcı seçebildiğim hâlde neden daha az müzisyen görüyorum?** Kurulum hazır adlandırılmış yuvaları, Kullanım ise son dışa aktarım penceresinde bağı gözlenen oturumları gösterir. Hiçbiri sayısal çalışma zamanı eşzamanlılık sınırı değildir.

**Neden yeni varyant/efor seçemiyorum?** Tarayıcıda bu OpenCode sağlayıcısından doğrulanmış seçenek yoktur. Mevcut kayıtlı özel varyant korunur; paket efor ayarı uydurmaz.

**Yardımcı yeni ajan açabilir mi?** Kurulan OpenCode yardımcı izinleri `subagent` eylemini kapatır. Ana şefin varsayılan izni kapalıdır; yalnızca seçilen yardımcı listesine devir yapabilir.
