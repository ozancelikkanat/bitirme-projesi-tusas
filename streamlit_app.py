# GitHub'a Yükleme

Mevcut repo:

```text
https://github.com/ozancelikkanat/bitirme-projesi-tusas
```

## Web arayüzüyle

1. Hazırlanan ZIP dosyasını bilgisayarınızda açın.
2. GitHub reposunda **Add file → Upload files** seçin.
3. ZIP dosyasının kendisini değil, açılan klasörün **içindeki dosya ve klasörleri**
   yükleme alanına sürükleyin.
4. Commit mesajına `Karar destek sistemi kaynak kodu eklendi` yazın.
5. **Commit changes** düğmesine basın.

## Git komutlarıyla

```powershell
git clone https://github.com/ozancelikkanat/bitirme-projesi-tusas.git
cd bitirme-projesi-tusas
```

Hazırlanan klasörün içeriğini bu klasöre kopyaladıktan sonra:

```powershell
git add .
git commit -m "Karar destek sistemi kaynak kodu eklendi"
git push origin main
```

## Yüklemeden önce

- Gerçek TUSAŞ verilerini eklemeyin.
- `.env`, `secrets.toml`, kişisel dosya yolları ve erişim anahtarlarını eklemeyin.
- Örnek olarak yalnızca `data/sample_wrinkle_data.csv` dosyasını kullanın.
