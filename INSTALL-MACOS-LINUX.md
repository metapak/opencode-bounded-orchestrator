# Install on macOS and Linux

Published Mac beta.1/beta.2 downloads have unresolved first-launch blocks. They are not the recommended installation route. A local source build opened successfully on the development Mac; this does not prove public downloaded apps work. Apple Developer ID signing and notarization are unavailable. Do not remove quarantine or disable Gatekeeper.

The source build requires Python 3.11+ and PyInstaller. Follow the [local source build instructions](docs/ustam-hub.md). A guided Script Editor source installer is being tested; its downloaded-source opening route is not yet accepted. Once locally built, open **Ustam.app**, select apps, then add projects in the browser. The app includes its runtime and can be moved on its own.

On Linux, extract the complete native ZIP from the [beta.2 release](https://github.com/metapak/ustam-opencode-orchestrator/releases/tag/ustam-v1.0.0-beta.2), keep its files together and open **Ustam**. Python is bundled.

Install and sign in to each selected provider CLI before starting real work. Configuration and previews do not start paid jobs. Review changes before applying project configuration. See the [unified guide](docs/ustam-hub.md).

Removing a project from Ustam removes its registration, not its folder. Restore is a separate operation for supported managed configuration; OpenCode restore is unavailable. Deleting the app does not uninstall project configuration or erase saved Ustam state. The hub has no project uninstall action.

[Older provider console installation](docs/legacy-macos-linux.md) is advanced compatibility only.

# macOS and Linux kurulumu

Yayımlanmış Mac beta.1/beta.2 indirmelerinde ilk açılış engeli sürüyor; önerilen kurulum yolu değiller. Geliştirme Mac’inde yerel kaynak derlemesi açıldı; bu, herkese açık indirmelerin çalıştığını kanıtlamaz. Apple Developer ID imzası ve noter onayı mevcut değil. Karantinayı kaldırmayın, Gatekeeper’ı kapatmayın.

Kaynak derlemesi Python 3.11+ ve PyInstaller gerektirir. [Yerel kaynak derleme yönergelerini](docs/ustam-hub.tr.md) izleyin. Script Editor üzerinden yönlendirmeli kaynak kurucusu test ediliyor; indirilmiş kaynağın açılış yolu henüz kabul edilmedi. Yerel derlemeden sonra **Ustam.app** açın, uygulamaları seçin ve tarayıcıda projeleri ekleyin. Uygulama çalışma zamanını içerir ve tek başına taşınabilir.

Linux’ta [beta.2 sürümündeki](https://github.com/metapak/ustam-opencode-orchestrator/releases/tag/ustam-v1.0.0-beta.2) yerel ZIP’i tamamen çıkarın, dosyalarını birlikte tutun ve **Ustam** açın. Python pakete dahildir.

Gerçek iş başlatmadan önce seçilen sağlayıcı CLI’sini kurup oturum açın. Yapılandırma ve önizleme ücretli görev başlatmaz. Proje ayarlarını uygulamadan önce değişiklikleri inceleyin. [Birleşik rehbere](docs/ustam-hub.tr.md) bakın.

Projeyi Ustam’dan kaldırmak kaydını kaldırır; klasörünü silmez. Geri yükleme, desteklenen yönetilen ayarlar için ayrı işlemdir; OpenCode geri yüklemesi yoktur. Uygulamayı silmek proje ayarlarını kaldırmaz veya kayıtlı Ustam verisini silmez. Hub’da proje kurulumunu kaldırma işlemi yoktur.

[Eski sağlayıcı konsolu kurulumu](docs/legacy-macos-linux.md) yalnız ileri düzey uyumluluk içindir.
