# Sık sorulan sorular ve sorun giderme

**Paket sağlayıcı seçer mi?** Hayır. Varsayılan roller mevcut OpenCode oturum modelini devralır. `/connect` ve `/models` kullanılır.

**Kota Tasarrufu kesin olarak az token harcar mı?** Hayır. Yalnızca adım bütçelerini küçültür. Gerçek kullanım göreve, modele, sağlayıcıya ve OpenCode davranışına bağlıdır.

**Özel model neden kabul edilmedi?** `sağlayıcı/model` veya `sağlayıcı/model#varyant` biçimini kullanın. Sağlayıcı karıştırmak açık onay ister.

**Mevcut dosya neden korundu?** Kurucu kendisine ait olmayan bir çakışma buldu. İnceledikten sonra değiştirmeyi seçerseniz önce yedek alır.

**Kullanım raporu neden yok?** `opencode stats --json` bulunamadı, başarısız oldu, süreyi aştı veya geçersiz JSON verdi.
