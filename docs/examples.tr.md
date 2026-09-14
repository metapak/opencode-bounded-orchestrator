# Örnekler

Kurulumdan sonra OpenCode’a normal şekilde “Sepet toplamındaki hatayı düzelt ve tekrar testi ekle” yazabilirsiniz. Ana yönetici isteği inceler, yazma alanını `implementer` rolüne verir, sonucu sabitler ve doğrulamayı başka role yaptırır.

Büyük işler için görev kaydı kullanılabilir:

```bash
python3 .opencode/tools/ledger.py start sepet-duzeltme --title "Sepet toplamını düzelt"
python3 .opencode/tools/ledger.py add incele --title "Hesaplama akışını incele" --owner-role explorer
python3 .opencode/tools/ledger.py add uygula --title "Düzeltmeyi yap" --owner-role implementer --depends-on incele
python3 .opencode/tools/ledger.py status
```
