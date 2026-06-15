# Gemini Voicer (Orange Pi Sesli Asistan) 

Orange Pi PC (Armbian/Debian CLI) üzerinde kullanmak için yazdığım, sıfır gecikmeli çalışmayı hedefleyen, biraz esnaf ruhlu ve hibrit yapılı bir sesli asistan projesi. 

Piyasadaki hazır asistanlar gibi hantal değil; tamamen saf Python, arecord ve donanımsal amixer/alsa kontrolleriyle çalışıyor.

## Bu Projede Ne Çılgınlıklar Yaptım?

* **Hibrit TTS (Sıfır Gecikme Taktiği):** Asistan uykudayken "Efendim", "Ses ayarlandı" gibi kısa kelimeleri internete gönderip vakit kaybetmiyor. `espeak-ng` ile anında yerelde patlatıyor. Gemini'dan gelen uzun cevapları ise `edge-tts` ile RAM disk (`/tmp`) üzerinden temiz bir sesle okuyor.
* **MADO BASS & TIZ (Donanımsal Ekolayzer):** Sesi yazılımsal olarak boğmak yerine, amixer üzerinden doğrudan ses kartının DAC ve Line Out çıkışlarına hükmediyor. Komutla bası ve tizi (-12 ile +12 arası) donanımsal olarak ayarlayabiliyorsunuz.
* **Akıllı Akış Algoritması (RAM Koruma Kalkanı):** Gürültülü ortamlarda veya arkada müzik çalarken mikrofonun sonsuza kadar kayıt yapıp Orange Pi'yi kilitlemesini engellemek için 8 saniyelik bir acımasız kesme sınırı var.
* **%100 İsabetli Lokal Müzik Arama:** Flash belleğin içindeki MP3'leri ararken sesli harfleri ve boşlukları yutan bir ünsüz harf iskeleti algoritması kullanıyor. Yani `Ahmet Kaya - Tapa Tapa` şarkısını bulmak için mikrofona sadece `taptap` demeniz yetiyor (`tptp` eşleşmesiyle nokta atışı buluyor).
* **YouTube Music Radyo Modu:** İnternetten bir şarkı açtığınızda sadece o şarkıyı çalmıyor; YouTube algoritmasından o tarzın devamındaki 20 şarkıyı çekip `mpv` üzerinden arkada akış (radyo) başlatıyor.

## Nasıl Çalıştırılır?

1. Gerekli paketleri Linux'a kurun:
```bash
   sudo apt install mpv espeak-ng alsa-utils arecord
   ```
2. Python kütüphanelerini yükleyin:
```bash
   pip install edge-tts speech-recognition google-generativeai ytmusicapi pyttsx3 gTTS
   ```
3. Gemini API keyinizi ortam değişkeni (environment variable) olarak tanımlayın (kodun içine kabak gibi yazmayın botlar patlatıyor):
```bash
   export GEMINI_API_KEY="kendi_keyiniz"
   ```
4. Ve scripti ateşleyin:
```bash
   python gemini_voicer.py
   ```

## Bazı Komutlar

- *"Hey Gemini"* veya *"Merhabalar"* -> Asistanı uyandırır.
- *"Durdur" / "Kes" / "Devam et"* -> `pkill -STOP` ve `-CONT` sinyalleriyle müziği arkada pürüzsüzce yönetir.
- *"Lokal duman çal"* -> Flash belleğe gider.
- *"Sesi 50 yap"* / *"Bası 5 yap"* -> Doğrudan donanıma fısıldar.

Kafanıza göre geliştirin, yorum satırlarında zaten gerekli taktikleri bıraktım. Rastgele!

(dürüst olayım kodun hepsi ai :d)
```
