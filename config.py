# CFRP Wrinkle Karar Destek Sistemi

CFRP kompozit yapılardaki **wrinkle (lif kırışıklığı)** kusurlarını geometrik olarak
karakterize eden, risk sınıfına ayıran ve seçilen kusurlar için kırılma mekaniği
tabanlı göreceli öncelik göstergeleri üreten akademik bir Streamlit uygulamasıdır.

> **Önemli:** Bu yazılım kesin bakım, uçuşa elverişlilik, sertifikasyon veya parça
> kabul/red kararı vermez. Yalnızca mühendislik incelemesi için önceliklendirme
> sağlar.

## Özellikler

- CSV, XLSX, XLS ve ODS veri yükleme
- Kolon eşleştirme ve veri kalite kontrolü
- Etkin ölçü ve açısal sapma hesabı
- Dört seviyeli risk sınıflandırması
- Orta, Yüksek ve Kritik kusurlar için ΔK ve Paris Yasası katmanı
- Göreceli ömür/inceleme önceliği göstergeleri
- Grafikler, Excel/CSV dışa aktarma ve kusur bazlı yorumlama

## Hesap Akışı

```text
Ham veri
  → Etkin ölçü
  → Açısal sapma
  → Risk skoru
  → Risk sınıfı
  → ΔK
  → Paris Yasası
  → Göreceli ömür göstergesi
  → Mühendislik inceleme önceliği
```

### Etkin ölçü

```text
Derinlik varsa:       Etkin Ölçü = Derinlik
Derinlik yoksa:       Etkin Ölçü = Yükseklik / 2
İkisi de yoksa:       Hesap dışı
```

`Yükseklik / 2` yaklaşımı bir mühendislik varsayımıdır.

### Açısal sapma ve risk

```text
θ = arctan(πD / W)
Risk_Skor = Etkin Ölçü × Etkin Açı
```

Burada `D` etkin ölçüyü, `W` genişliği temsil eder. Açı derece cinsinden
hesaplanır.

| Risk sınıfı | Risk skoru |
|---|---:|
| Düşük | `< 0,50` |
| Orta | `0,50 – < 3,00` |
| Yüksek | `3,00 – < 15,00` |
| Kritik | `≥ 15,00` |

Genişlik ağırlıklı risk ana sınıflandırmada kullanılmaz; yalnızca duyarlılık
göstergesi olarak tutulabilir.

### Kırılma mekaniği

Yalnızca **Orta + Yüksek + Kritik** kusurlar ileri analize aktarılır.

```text
a = Etkin Ölçü / 2
a_m = a_mm / 1000
ΔK = Y × σ × √(πa)
da/dN = C(ΔK)^m
```

Varsayılan değerler:

- `Y = 1,12`
- `σ = 250 MPa`
- `C = 1×10⁻¹⁰`
- `m = 3`

Bu değerler doğrulanmış malzeme sabitleri değil, **mühendislik/parametrik
kabullerdir**. Ömür çıktısı mutlak kalan çevrim değildir; aynı varsayımlar
altındaki kusurları karşılaştıran göreceli bir göstergedir.

## Kurulum

Python 3.10 veya üzeri önerilir.

```bash
git clone https://github.com/ozancelikkanat/bitirme-projesi-tusas.git
cd bitirme-projesi-tusas
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Windows kullanıcıları `run_app.bat` dosyasını da çalıştırabilir.

## Örnek Veri

Anonim örnek dosya:

```text
data/sample_wrinkle_data.csv
```

Beklenen temel kolonlar:

```text
defect_id, length, width, depth, height
```

Gerçek şirket/proje verileri, kişisel bilgiler, erişim anahtarları veya gizli
dosyalar bu repoya eklenmemelidir.

## Test

```bash
pytest -q
```

## Streamlit Community Cloud

1. Repoyu GitHub'a yükleyin.
2. [Streamlit Community Cloud](https://share.streamlit.io/) üzerinden **New app**
   seçin.
3. Repository ve `main` branch'i seçin.
4. Main file path alanına `streamlit_app.py` yazın.
5. Deploy düğmesine basın.

## Proje Durumu ve Sorumluluk Reddi

Bu depo akademik bitirme projesi prototipidir. TUSAŞ'ın resmî yazılımı,
onaylanmış mühendislik aracı veya kurumsal ürünü değildir. Depoda TUSAŞ'a ait
gizli/özel veri bulunmaz ve eklenmemelidir. Gerçek mühendislik kullanımından
önce malzeme testleri, sonlu elemanlar analizi, uzman değerlendirmesi ve ilgili
sertifikasyon süreçleriyle doğrulanmalıdır.

## Lisans

Bu pakete bilerek bir açık kaynak lisansı eklenmemiştir. Kodu açık kaynak
olarak lisanslamak isterseniz MIT, Apache-2.0 veya kurumunuzun uygun gördüğü
başka bir lisansı ayrıca seçebilirsiniz.
