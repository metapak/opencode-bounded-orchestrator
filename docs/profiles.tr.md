# Profiller

Profiller yalnızca sınırlı OpenCode `steps` bütçelerini değiştirir.

- **Dengeli:** günlük kullanım için varsayılan seçim.
- **Yüksek Kalite:** zor işler için daha geniş bütçeler.
- **Ekonomik:** rutin işler için daha küçük bütçeler.
- **Kota Tasarrufu:** en küçük hazır bütçeler; zor işlerde çözümden önce durabilir.
- **Özel:** Dengeli bütçelere ek olarak kesin model seçimi.

Özel seçim `sağlayıcı/model[#varyant]` biçimindedir. Açık onay verilmedikçe yerel roller tek sağlayıcıda kalır. Varsayılan `--model` verilmeden yalnızca bir rol değiştirilirse oturumdan devralınan sağlayıcı bilinemez; bu nedenle kurulum açık sağlayıcı karıştırma onayı ister. Modelin hesabınızda bulunup bulunmadığını OpenCode `/models` ile kontrol edin.


Runtime `steps` and model selectors are stored only in JSON config. Markdown role files retain prompts and permissions, avoiding duplicate scalar overrides. Root `--model` does not accept `#variant`; use `--role-model` for provider-supported variants. Model IDs can contain slash segments. `steps` are model-turn budgets, not token ceilings. Browser profiles are available through [the local console](local-console.md); custom keeps existing steps. No numeric parallelism setting is claimed without a verified OpenCode contract.
