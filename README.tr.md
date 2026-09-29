[English](README.md) · [Türkçe](README.tr.md)

![Bordo perdeli sıcak orkestra sahnesinde şef ve farklı görevlerde yardımcı müzisyenler](docs/assets/cover-tr.svg)

# OpenCode Bounded Orchestrator

[![CI](https://github.com/metapak/opencode-bounded-orchestrator/actions/workflows/ci.yml/badge.svg)](https://github.com/metapak/opencode-bounded-orchestrator/actions/workflows/ci.yml)
[![Lisans](https://img.shields.io/badge/lisans-Apache--2.0-blue.svg)](LICENSE)

Sınırları belirlenmiş bir **OpenCode V2** ekibi için yerel, Türkçe/İngilizce kurulum ve kullanım ekranı. Siz sonucu tarif edersiniz; ana şef işi planlayıp sınırları belirli görevlere ayırır ve yardımcılara devreder. Şef kaynak araştırması, düzenleme, derleme, test veya inceleme işini kendi yapmaz.

> Resmî olmayan topluluk projesidir; OpenCode veya geliştiricileriyle bağlantılı ya da onlar tarafından onaylanmış değildir.

## Komut yazmadan kurun

1. **[Güncel main ZIP dosyasını indirin](https://github.com/metapak/opencode-bounded-orchestrator/archive/refs/heads/main.zip)** ve klasörün tamamını çıkarın. Bu bağlantı deponun en yeni `main` dalını ve grafik başlatıcıları içerir; eski v0.1.0 sürüm ZIP'i değildir.
2. **Başlatıcıyı açın:** macOS'ta `launchers/Bounded Orchestrator.app`, Windows'ta `launchers/Launch Bounded Orchestrator.vbs` dosyasına çift tıklayın.
3. **Mevcut proje klasörünüzü** sistemin klasör seçicisinden seçin. Bir depoda çalışıyorsanız Git proje klasörünüzü seçin. Tarayıcıda yerel Kurulum ekranı açılır; 1–10 yardımcı yuvasını, görevlerini ve modellerini seçin, önerilen değişiklikleri inceleyip **Kur ve kaydet** düğmesine basın.
4. Kurulan ekibi kullanmak için OpenCode'u o projede yeniden başlatın. Seçilen klasör yolu tarayıcıda salt okunurdur; başka proje için başlatıcıyı yeniden açın.

Grafik başlatıcılar için ayrıca **[Python 3.11 veya üzeri](https://www.python.org/downloads/)** kurulmalıdır; Python paketlenmez. Kurulan ajanları kullanmak için OpenCode V2 2.0.0+ gerekir. Yerel ekran yalnızca `127.0.0.1` adresinde çalışır, Türkçe açılır ve İngilizceye geçilebilir. Yardımcı sayısı hazır ekip kapasitesidir; otomatik başlatma sayısı veya sayısal eşzamanlılık sınırı değildir. Modeller OpenCode sağlayıcınızdaki erişime bağlıdır. Doğrulanmış varyant/efor listesi yoksa yeni seçim kapalı kalır, mevcut özel seçim korunur.

Linux veya yalnızca terminal kullanımı için [isteğe bağlı komut satırı yoluna](INSTALL-MACOS-LINUX.md#optional-linux-and-command-line-path) bakın. Eski `setup.command`, `setup.cmd` ve `scripts/install.py` de isteğe bağlı alternatiflerdir. Ayrıntılar: [macOS/Linux kurulum](INSTALL-MACOS-LINUX.md), [Windows kurulum](INSTALL-WINDOWS.md), [yerel konsol](docs/local-console.md).

![Şef ve üç yardımcılı OpenCode Kullanım orkestrasının Türkçe örnek ekranı](docs/assets/console-tr.png)

*Örnek verili Kullanım ekranı. Gösterilen oturumlar, yardımcılar, modeller ve token sayıları hesabınıza veya canlı kullanımınıza ait değildir.*

## Ekip nasıl çalışır?

Kurulan ana `owner` için varsayılan araç izni kapalıdır; yalnızca bounded-orchestrator becerisi, kullanıcıya soru sorma ve seçilen yardımcı ajanlara devir açıktır. Talimatları onu konuşma, planlama, devir ve kısa uzman raporlarıyla sınırlar. Yardımcılar yeni yardımcı açamaz; yalnızca `implementer` temelli bir yardımcı, kendisine verilen alanda uygulama yazar. Varsayılan bir uygun yardımcıdır; eşzamanlı iş için bağımsız alanlar ve gerekçe gerekir. Bunlar OpenCode ayarı ve talimatlarıdır; paket dış çalışma zamanının her davranışını denetlediğini iddia etmez.

Tarayıcıdaki Kurulum *planlanan* ekibi, Kullanım ise *gözlenen* oturumları gösterir. Örnek orkestradaki dört karakter, dört ajan sınırı veya şu an çalışan dört ajan demek değildir. OpenCode'un temizlenmiş dışa aktarımı kararlı oturum bağları içeriyorsa şef ve bağlı çocuk oturumlardaki yardımcılar gösterilir. Gözlenen her karakterin görevine özel çizimi ve görünür model/varyant bilgisi vardır; eksik değerler açıkça belirtilir. Tek başına model veya rol, ajan kimliği sayılmaz. Şefe tıklayınca baton ve notalar başlar; başka yere tıklayana kadar döner. Enter ve Space de düğmeyi etkinleştirir. Otomatik hareket veya ayrı Canlandır düğmesi yoktur.

Kullanım grafikleri en son 12 temizlenmiş oturumun kesin gözlenen sayaçlarını temel alır; bilinmeyen ve eksik kapsam gösterilir. `opencode stats` ekran sayıları yuvarlanmış olabilir ve kesin grafiklere sessizce eklenmez. Çalışma tarzı dağılımı yalnızca oturum yerel ayar geçmişiyle güvenle eşleştiğinde tahmin edilir. Maliyet, kota, tasarruf, abonelik bakiyesi veya canlı ajan çalışması çıkarılmaz. DEMO verileri hesap kullanımı gibi sunulmaz. Bkz. [kullanım ve yerel kontrol](docs/usage-and-local-eval.tr.md).

## Tercihler ve güvenli değişiklik

Çalışma tarzları sınırlı OpenCode `steps` bütçelerini değiştirir; bunlar token tavanı değildir. Ekonomi ve Kota tasarrufu daha az adım ayırıp erken durabilir; Kalite daha çok adım ayırır. Kesin token tasarrufu vaat etmez veya düşünme eforunu kendiliğinden değiştirmez. Model listesi, varsa seçilen projenin `opencode models` sonucundan gelir; çevrimdışı örnekler doğrulanmamış olarak işaretlenir. **Model listesini yenile** yalnızca tıklandığında OpenCode'dan yenileme ister. Konsol kimlik bilgilerini veya sohbet gövdelerini göstermez.

Kurulum değişiklikleri önce gösterilir, ardından seçilen projeye sahiplik kaydı ve özel yedeklerle yazılır. Ekip küçültülürken yalnızca daha önce yönetilen ve değişmemiş yardımcı dosyaları kaldırılır; kaldırılanlar yedeklenir. **Tercihler → Son değişikliği geri al**, yalnızca konsolun son tercih kaydını geri çevirir ve ilgisiz ayarları korur. Ekip kurulumunu veya küçültmeyi geri almaz. Dışarıda değiştirilmiş ya da çakışan yönetilen dosyalar sessizce ezilmez. Özel çalışma verileri Git tarafından yok sayılır; kaldırma ilgisiz ve değiştirilmiş dosyaları korur. Bkz. [profiller](docs/profiles.tr.md), [mimari](docs/architecture.md), [görev kaydı](docs/task-ledger.tr.md) ve [SSS](docs/faq.tr.md).

## Geliştirme ve sınırlar

Kurucu ve depo testleri GitHub Actions üzerinde Ubuntu, macOS ve Windows'ta çalışır. Bu geliştirme ortamında OpenCode CLI ve gerçek sağlayıcı oturumu yoktu; Finder/Windows üzerinden gerçek çift tıklama da denenmedi. Tarayıcı akışları temizlenmiş örnek verilerle kontrol edildi. Model erişimi, varyantlar ve canlı dışa aktarım biçimi kurulumunuza bağlıdır. Üretilen dosyalar belgelenen OpenCode V2 ayar ve izin sözleşmelerini kullanır; paket model erişimini veya sayısal eşzamanlı yardımcı sınırını garanti edemez.

[Yol haritası](docs/roadmap.tr.md), [katkı rehberi](CONTRIBUTING.md), [güvenlik politikası](SECURITY.md), [değişiklik geçmişi](CHANGELOG.md) ve [sürüm notları](docs/release-v0.1.0.tr.md) bulunur. Apache-2.0 lisanslıdır; atıf [NOTICE](NOTICE) ve [kaynak bilgileri](docs/provenance.md) dosyalarındadır.
