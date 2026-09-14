# Kullanım raporu ve yerel son kontrol

`usage_report.py`, doğrulanmış `opencode stats --json` komutunu çalıştırır ve dönen JSON verisini gösterir. Konuşma kayıtlarını okumaz, eksik token miktarını tahmin etmez, maliyet veya kota yüzdesi uydurmaz. Komut yoksa ya da geçerli veri dönmezse açıkça `unavailable` sonucu verir.

`local_eval.py`, adı, komut dizisi ve sınırlı süre içeren açık bir JSON tanımı kullanır. Kabuk çalıştırmaz. Aday dosyaları kontrolden önce ve sonra parmak iziyle doğrular. Dosyalar değişirse sonuç `candidate_changed` olur. Zorunlu değerlendirme eksik, başarısız veya eskiyse görev kaydı son incelemeye izin vermez.
