# Colab Çalıştırma Kılavuzu (A100)

Bu kılavuz, model çıktılarının Google Colab'da nasıl üretileceğini adım adım anlatır. Üretim yalnızca
Colab Pro'daki **A100** GPU ile yapılır. Fazlar sırasıyla şunlardır; her birini ancak analiz sorumlusu size
"şimdi çalıştırın" dediğinde çalıştırın:

| Faz | Ne üretir | Tahmini süre |
|---|---|---|
| **smoke** | 5 istem × 3 model, aynı oturumda **iki kez** (iki ayrı çalıştırma klasörü) | 15–25 dakika |
| **pilot** | 190 istem × 3 model | 20–40 dakika |
| **pilot_bs1** | pilotun 100 istemi, toplu iş boyutu 1 ile (pilottan sonra) | 20–40 dakika |
| **smoke_gemma** | 5 istem × Gemma 4 E4B, aynı oturumda **iki kez** (karar D06) | 10–20 dakika |
| **pilot_gemma** | Gemma'nın pilotu: 190 istem, toplu iş boyutu 1 (G2 kararı) | 20–40 dakika |
| **main** | 1.900 istem × 4 model, toplu iş boyutu 1 (G2 kararı); modeller **ayrı oturumlarda** ("Ana çalıştırma" bölümü) | toplam 11–12 A100 saati |

Süreler model indirmeleri dahil kaba tahminlerdir.

## 0. Bir kez yapılacak hazırlık

1. https://drive.google.com adresinde **Drive'ım (My Drive)** içindeki **`Colab Notebooks`** klasörünü açın.
   (Colab bu klasörü kendisi oluşturur; yoksa tam bu adla, arada boşlukla, siz oluşturun.)
   İçinde `emel_hoca_konf_colab` adlı bir klasör, onun içinde de iki klasör açın: `bundles` ve `runs`.
   Sonuç:
   - `Drive'ım/Colab Notebooks/emel_hoca_konf_colab/bundles/`
   - `Drive'ım/Colab Notebooks/emel_hoca_konf_colab/runs/`

   Not defteri bu yolu en üstteki `DRIVE_ROOT` parametresinden okur
   (`/content/drive/MyDrive/Colab Notebooks/emel_hoca_konf_colab`); bu satırı değiştirmeyin.
   Daha önce `Drive'ım/emel_hoca_konf_colab/` klasörünü oluşturduysanız artık kullanılmıyor.
2. Hugging Face erişim anahtarı (token) **gerekmez**: dört model de herkese açık. İndirmeler anonim yapılır.
   Yine de kullanmak isterseniz token'ı **hiçbir dosyaya, hücreye veya mesaja yazmayın**; yalnızca Colab'ın
   "Secrets" bölümüne girilir (adım 3.4).

## 1. Paketi Drive'a yükleyin

1. Analiz sorumlusu size paket dosyasının adını söyler, örneğin
   `instruction-order-study/dist/colab_bundle_smoke_1a2b3c4.zip`.
2. Drive'da `Colab Notebooks/emel_hoca_konf_colab/bundles/` klasörünü açın → **Yeni (New)** →
   **Dosya yükle (File upload)** → Mac'te `Masaüstü/emel_hoca_konf/instruction-order-study/dist/` içindeki
   zip dosyasını seçin.
3. Yükleme bitene kadar bekleyin (sağ altta yeşil onay işareti). Zip'i açmayın; olduğu gibi kalsın.
4. `bundles/` klasöründe her faz için **yalnızca güncel paket** bulunsun. Analiz sorumlusu bir paketin
   geçersiz (superseded) olduğunu söylediyse onu bu klasörden silin; aynı faz için birden fazla paket varsa
   not defteri hangisini kullanacağını bilemez ve `STOP: several bundles ...` mesajıyla durur.

## 2. Not defterini açın ve A100'ü seçin

1. https://colab.research.google.com adresine gidin → **Dosya (File)** → **Not defteri yükle
   (Upload notebook)** → Mac'te `instruction-order-study/colab/run_generation.ipynb` dosyasını seçin.
   (Yeni bir oturum açtığınızda Mac'teki güncel not defterini yükleyin. Açık bir oturumda bir sonraki faza
   geçerken not defterini yeniden yüklemeyin; yalnızca `PHASE` satırını değiştirin.)
2. Üst menüden **Çalışma zamanı (Runtime)** → **Çalışma zamanı türünü değiştir (Change runtime type)** →
   **Donanım hızlandırıcı (Hardware accelerator): A100 GPU** → **Kaydet (Save)**.
   A100 seçeneği görünmüyorsa Colab Pro aboneliğini kontrol edin. A100 o an verilemiyorsa bir süre sonra tekrar
   deneyin. **T4, L4 veya başka bir GPU ile çalıştırmayın**; not defteri zaten `STOP` mesajıyla durur.
3. Sağ üstte **Bağlan (Connect)** düğmesine basın ve bağlantının kurulmasını bekleyin.

## 3. Parametreleri girin ve çalıştırın

1. İlk kod hücresinde (`Parameters`) en üstte işaretli `DRIVE_ROOT` satırına dokunmayın; yalnızca `PHASE`
   satırını faza göre düzenleyin:
   `PHASE = "smoke"`, `PHASE = "pilot"`, `PHASE = "pilot_bs1"` veya `PHASE = "main"`; Gemma için
   `PHASE = "smoke_gemma"` veya `PHASE = "pilot_gemma"`.
   Diğer değerleri değiştirmeyin: `BUNDLE = "auto"`, `RUN_ID = "auto"`, `MODELS = "all"`, `RESTART_MODELS = ""`.
   (İstisnalar: ana çalıştırmada `MODELS`, aşağıdaki "Ana çalıştırma" bölümü; ortam değişince
   `RESTART_MODELS`, bölüm 4.)
   **Başka hiçbir hücreyi değiştirmeyin.**
2. **Çalışma zamanı (Runtime)** → **Tümünü çalıştır (Run all)** (kısayol: Ctrl+F9 / ⌘+F9).
3. "Google Drive'a bağlan" penceresi açılır: hesabınızı seçin ve **İzin ver (Allow)** deyin.
4. (Gerekmez) Token kullanacaksanız, çalıştırmadan önce sol kenardaki **anahtar simgesine (Secrets)**
   tıklayın → **Add new secret** → Name: `HF_TOKEN`, Value: token'ınız → **Notebook access** anahtarını açın.
   Token yoksa not defteri normal çalışır (`No HF_TOKEN secret; downloads are anonymous.`).
5. Hücreler sırayla çalışır. Ne göreceksiniz:
   - Hücre 2: GPU adı (`NVIDIA A100-...`). A100 değilse `STOP` ile durur.
   - Hücre 3: `Drive root: /content/drive/MyDrive/Colab Notebooks/emel_hoca_konf_colab` ve paket listesi.
   - Hücre 4: `Bundle ... verified` (paketin bütün dosyalarının SHA-256 kontrolü geçti).
   - Hücre 5: kütüphane kurulumu ve sürümler (`transformers 5.17.0`, Colab'ın torch sürümü).
   - Hücre 7: `Phase smoke: ... 2 pass(es) ...` (smoke ve smoke_gemma iki geçiş yapar; diğer fazlar bir).
   - Hücre 8: her geçiş için `pass 1/2: <run_id>` başlığı, ardından her model için ilerleme satırları
     (`R4 check passed ...`, `batch 1/1 done ...`). Modeller sırayla çalışır: `smollm2`, `qwen25`, `phi4mini`
     (main'de ardından `gemma4e4b`; Gemma fazlarında yalnızca `gemma4e4b`).
   - Hücre 9: her çalıştırma klasörü için özet (`R4 check=passed`) ve `zip: .../<run_id>.zip`.
     Smoke ve smoke_gemma'da **iki** zip yazılır.
   - Hücre 10: `Drive flushed and unmounted.` (Drive'a her şeyin yazıldığını garanti eder.)
6. Sekmeyi açık tutun; bilgisayarın uyku moduna geçmemesine dikkat edin.

### Pilot ve pilot_bs1 aynı oturumda (karar D04)

Analiz sorumlusu iki paketi birlikte verir: `colab_bundle_pilot_<commit>.zip` ve `colab_bundle_pilot_bs1_<commit>.zip`.
İkisini de `bundles/` klasörüne yükleyin (faz adları tam eşleştiği için karışmazlar). Sonra aynı Colab oturumunda:

1. `PHASE = "pilot"` yapın → **Tümünü çalıştır**. Bitmesini bekleyin (hücre 10: `Drive flushed and unmounted.`).
2. Parametre hücresinde yalnızca `PHASE = "pilot_bs1"` yapın → yine **Tümünü çalıştır**. Drive yeniden bağlanır;
   kurulum hızlıdır. Bu faz toplu iş boyutu 1 ile çalıştığı için daha yavaştır.
3. Her iki fazın zip'lerini indirin (adım 5): `runs/pilot/` ve `runs/pilot_bs1/` altında birer tane.

İki fazın aynı oturumda (aynı GPU ve kütüphanelerle) çalışması, toplu iş değişmezliği karşılaştırması (A3) için
önemlidir. Arada oturum koparsa analiz sorumlusuna bildirin.

### Gemma 4 E4B (dördüncü model, karar D06)

Gemma'nın kendi fazları vardır; mevcut çalıştırmalara ve paketlere dokunulmaz. Hiçbir paketi silmeniz gerekmez:
faz adları tam eşleştiği için `smoke` ile `smoke_gemma`, `pilot` ile `pilot_gemma` karışmaz.

- **smoke_gemma** (tamamlandı): 5 istem, iki geçiş.
- **pilot_gemma** (G2 kararı): 190 istem, toplu iş boyutu 1, tek geçiş.
  1. Analiz sorumlusunun verdiği `colab_bundle_pilot_gemma_<commit>.zip` dosyasını `bundles/` klasörüne yükleyin.
  2. Yeni bir A100 oturumu açın ve Mac'teki **güncel** not defterini yükleyin (adım 2; not defteri G2 kararıyla
     değişti). `PHASE = "pilot_gemma"` yapıp **Tümünü çalıştır** deyin.
  3. Gemma ilk kez yaklaşık 16 GB indirir (birkaç dakika). Token gerekmez; model herkese açıktır.
  4. `runs/pilot_gemma/` altında bir zip oluşur. Açmadan `instruction-order-study/runs/pilot_gemma/` klasörüne
     koyun ve analiz sorumlusuna haber verin.

### Ana çalıştırma (main): uzun çalıştırma, modeller ayrı oturumlarda (karar G2)

Ana çalıştırma toplu iş boyutu 1 ile yapılır ve toplam 11–12 A100 saati sürer. Bağlantı koparsa en fazla bir
modelin kaybolması için modelleri **üç ayrı oturumda** çalıştırın. Hepsinde aynı paket ve `RUN_ID = "auto"`
kullanılır; not defteri her oturumda aynı çalıştırma klasörüne devam eder.

| Oturum | `MODELS` | Tahmini süre (üretim) |
|---|---|---|
| 1 | `MODELS = "smollm2,phi4mini"` | yaklaşık 3 saat |
| 2 | `MODELS = "qwen25"` | yaklaşık 3 saat |
| 3 | `MODELS = "gemma4e4b"` | yaklaşık 5,5 saat (en uzun oturum; mümkünse tek seferde bitirin) |

Her oturumdan önce:
1. **Compute unit bakiyesini kontrol edin.** Colab'da sağ üstteki RAM/Disk göstergesine tıklayın →
   **Kaynakları görüntüle (View resources)**. Panelde kalan compute unit miktarı ve saatlik tüketim yazar.
   (Bulamazsanız: https://colab.research.google.com/signup sayfası.) Bakiye oturumun tahmini süresine yetmiyorsa
   önce ek birim alın; yarıda kalan bir model sonraki oturumda kaldığı yerden devam eder, ama bunu önlemek daha iyidir.
2. **Sekmeyi açık tutun ve Mac'in uyumasını engelleyin.** Kapağı kapatmayın. En kolayı: Terminal'i açıp
   `caffeinate -di` yazın ve Enter'a basın. Çalıştırma bitene kadar o pencere açık kalsın; bitince Ctrl+C ile
   kapatın.
3. Parametre hücresinde `PHASE = "main"` ve o oturumun `MODELS` değerini yazın → **Tümünü çalıştır**.

Ne göreceksiniz: her model önce **A6 kontrolünü** yapar: 5 metni tek tek üretir ve pilot çıktılarıyla karşılaştırır
(`A6 check passed: 5/5 outputs byte-identical ...`). Sonra 1.900 metni tek tek üretir (`batch 1/1900 done ...`).
Hücre 9'da her model için `status=complete records=1900/1900 R4 check=passed A6=passed` görmelisiniz.

Bitirme: Drive'daki `runs/main/<run_id>.zip` her oturumun sonunda güncellenir. Zip'i **yalnızca son oturumdan
sonra** (dört model de `complete` olduğunda) indirip `instruction-order-study/runs/main/` klasörüne koyun. Her
oturumun sonunda hücre 9'daki satırları analiz sorumlusuna yazmanız yeterlidir.

## 4. Bağlantı koparsa veya Colab kapanırsa

Çıktılar her toplu işten (batch) sonra Drive'a yazılır; hiçbir şey kaybolmaz.

1. Not defterine dönün; **Yeniden bağlan (Reconnect)** deyin. Çalışma zamanı türünün hâlâ **A100** olduğunu
   kontrol edin (adım 2.2).
2. Parametre hücresine dokunmadan **Çalışma zamanı → Tümünü çalıştır** deyin. `RUN_ID = "auto"` aynı paketle
   başlatılmış çalıştırmayı bulur ve kaldığı yerden devam eder (`resuming run ...`,
   `N/M batches already done; skipping them`). Tamamlanmış modeller atlanır (`already complete`);
   tümünü yeniden çalıştırmak hiçbir işi tekrarlamaz.
3. Eğer hücre 8 şu mesajla durursa: `STOP: ... refused to resume because the environment or settings
   changed` — bu, yeni oturumda farklı bir A100 türü veya farklı kütüphane sürümü geldiği anlamına gelir.
   **Hiçbir şeyi silmeyin.** Bir modelin bütün çıktıları tek bir ortamdan gelmelidir (karar G2), bu yüzden o
   model yeni ortamda baştan üretilir:
   - Hücre 8'in çıktısında `REFUSING TO RESUME` satırının altında hangi modelin adı geçiyorsa (ör. `qwen25`),
     parametre hücresinde `RESTART_MODELS = "qwen25"` yapın ve **Tümünü çalıştır** deyin.
   - Not defteri o modelin yarım kalan çıktılarını `superseded/` klasörüne taşır (silinmez, analize girmez) ve
     modeli baştan üretir. Tamamlanmış bir model asla yeniden üretilmez.
   - Model bitince `RESTART_MODELS = ""` yapın. Durumu analiz sorumlusuna yazın.
   - Mesaj "settings" (ayarlar) farkından söz ediyorsa `RESTART_MODELS` kullanmayın; mesajı analiz sorumlusuna iletin.
4. Eğer hücre 8 `STOP (A6)` ile durursa: aynı ortamda üretilen kontrol metinleri pilottakilerle birebir aynı
   çıkmamıştır. **Yeniden çalıştırmayın**; mesajın tamamını analiz sorumlusuna iletin.
5. Smoke fazında bağlantı ikinci geçiş sırasında koparsa da aynı şekilde tümünü yeniden çalıştırın; ikinci
   geçiş kendi klasöründe kaldığı yerden devam eder. Durumu analiz sorumlusuna bildirin (iki geçişin aynı oturumda
   yapılması isteniyor).

## 5. Çıktıları Mac'e alın

1. Drive'da `Colab Notebooks/emel_hoca_konf_colab/runs/<faz>/` klasörünü açın (ör. `runs/smoke/`). Hücre 9'da
   listelenen her çalıştırma için orada bir `.zip` dosyası vardır (smoke'ta iki tane).
2. Her zip dosyasına sağ tıklayın → **İndir (Download)**. Klasörü değil, `.zip` dosyasını indirin.
   Zip'leri **tek tek** indirin: birkaç dosyayı birlikte seçip indirirseniz Drive onları tek bir
   `drive-download-….zip` dosyasında birleştirir; o dosyayı kullanmayın.
3. Zip dosyalarını **açmadan** Finder ile `Masaüstü/emel_hoca_konf/instruction-order-study/runs/<faz>/` klasörüne
   taşıyın (ör. `runs/smoke/`). Açmak isterseniz de olur; analiz sorumlusu iki durumu da tanır.
4. Analiz sorumlusuna yalnızca "<faz> zip'lerini yerleştirdim" deyin. Run id'yi bulmanız gerekmez: run id, zip
   dosyasının uzantısız adıdır (ör. `smoke_20261004-1558_51d293c` = faz, UTC tarih-saat, paketin commit'i).
   Analiz sorumlusu zip'leri güvenli biçimde açar ve `make import PHASE=<faz> RUN=all` ile sayıları, hash'leri,
   ortam tutarlılığını ve R4 kontrolünü doğrular.
5. Dosyaları **açıp düzenlemeyin, yeniden adlandırmayın, silmeyin.**

## 6. Yapılmaması gerekenler

- A100 dışında bir GPU ile veya CPU ile çalıştırmak.
- Parametre hücresi dışında herhangi bir hücreyi değiştirmek.
- Aynı faz için analiz sorumlusuna sormadan `RUN_ID = "new"` ile ikinci bir çalıştırma başlatmak.
- Drive'daki veya Mac'teki çıktı dosyalarını düzenlemek, silmek ya da yeniden adlandırmak.
- Token'ı bir hücreye, dosyaya veya sohbet mesajına yazmak.

## 7. Sık görülen mesajlar

| Mesaj | Anlamı ve yapılacak |
|---|---|
| `STOP: no GPU` | Çalışma zamanı türü GPU değil. Adım 2.2. |
| `STOP: this notebook must run on an A100 GPU` | Başka bir GPU verilmiş. Adım 2.2'de A100 seçin, yeniden bağlanın. |
| `STOP: folder '.../Colab Notebooks/emel_hoca_konf_colab/bundles' not found` | Drive klasörü eksik veya adı farklı (boşluk dahil). Adım 0.1. |
| `STOP: no colab_bundle_<faz>_<commit>.zip` | Paket yüklenmemiş, yanlış klasöre yüklenmiş ya da `PHASE` yanlış. Adım 1 ve 3.1. |
| `STOP: several bundles for phase ...` | Aynı faz için birden fazla paket var. Geçersiz olanı `bundles/` klasöründen silin (adım 1.4). |
| `STOP: SHA-256 mismatch` | Paket bozuk yüklenmiş. Zip'i Drive'dan silip yeniden yükleyin. |
| `STOP: bundle is for phase ...` | `PHASE` ile yüklenen paket farklı faz. `PHASE` değerini düzeltin. |
| `STOP: pip changed torch ...` veya `STOP: torch ... is older than 2.5` | Colab'ın torch sürümü uygun değil. Durun ve analiz sorumlusuna bildirin. |
| `STOP: transformers ... is installed but ... is pinned` | Kurulum beklenen sürümü vermedi. Durun ve analiz sorumlusuna bildirin. |
| `STOP (R4): ...` | Üretim ayarları onaylı greedy ayarlarla birebir değil; o toplu iş yazılmadı. Durun ve mesajı analiz sorumlusuna iletin. |
| `refused to resume ...` | Adım 4.3 (ortam değiştiyse `RESTART_MODELS`). |
| `STOP (A6): ...` | Kontrol metinleri pilottan farklı çıktı. Yeniden çalıştırmayın; analiz sorumlusuna bildirin (adım 4.4). |
| `STOP: MODELS must be among ...` veya `STOP: RESTART_MODELS must be among ...` | Model adı yanlış yazılmış. Paketteki model adlarını kullanın (`smollm2`, `qwen25`, `phi4mini`, `gemma4e4b`). |
| `already complete` | O model bitmiş; normal. |
