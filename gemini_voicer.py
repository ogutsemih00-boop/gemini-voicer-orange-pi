import os
import sys
import time
import subprocess
import re
import struct
import math
import asyncio
import edge_tts
import speech_recognition as sr
import google.generativeai as genai
import random
from ytmusicapi import YTMusic
import pyttsx3 # <--- YENİ: Yerel ses motorumuz
from gtts import gTTS  # <--- Kodun EN ÜSTÜNE bu importu eklemeyi unutma reis!
from ctypes import *
from contextlib import contextmanager
from difflib import SequenceMatcher

os.system("pkill -9 arecord > /dev/null 2>&1")

# 1. GEMINI API AYARI
GEMINI_API_KEY = "GEMINI API KEY"
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-2.5-flash')
chat = model.start_chat(history=[])

# 2. MİKROFON VE SES KARTI AYARI
MIKROFON_CIHAZI = "plughw:0,0"
MADO_BASS = 0  # -12 ile +12 arası çalışır (0 normaldir)
MADO_TIZ = 0   # -12 ile +12 arası çalışır (0 normaldir)

# 3. YEREL SES (TTS) MOTORU AYARLARI
print("Yerel Ses Motoru (TTS) başlatılıyor...")
try:
    engine = pyttsx3.init()
    engine.setProperty('rate', 140) # Konuşma hızı (Çok hızlı olursa Orange Pi yutar, 140 idealdir)
    engine.setProperty('volume', 1.0) # Sesi köklüyoruz
    
    # Türkçe sesi bulup ayarlıyoruz
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'tr' in voice.id or 'turkish' in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break
except Exception as e:
    print(f"[HATA] TTS Motoru başlatılamadı: {e}")


def rastgele_muzik_bul():
    """ Reis sustuğunda kendi kafasına göre çalabileceği rastgele sorgu havuzu """
    
    # Burayı kendi zevkine göre istediğin gibi doldur reis!
    # Sanatçı adı, şarkı adı veya "90lar türkçe pop", "bass boosted" gibi tarzlar yazabilirsin.
    tarzlar_ve_sarkilar = [
        # Senin eklediklerin (İlk 14)
        "Tarkan", "Sezen Aksu", "Barış Manço", "Cem Karaca", "Duman", "Mor ve Ötesi",
        "Runaway", "Live for Speed soundtrack", "90lar türkçe pop", "retro wave emg",
        "Anadolu Rock mix", "Sagopa Kajmer eski", "Ceza", "Toygar Işıklı",
    
        # 90'lar & 2000'ler Türkçe Pop
        "Mustafa Sandal", "Kenan Doğulu", "Sertab Erener", "Nilüfer", "Ajda Pekkan",
        "Hande Yener", "Demet Akalın", "Serdar Ortaç", "Yıldız Tilbe", "Gülşen",
        "Murat Boz", "Yalın", "Göksel", "Nil Karaibrahimgil", "Levent Yüksel",
        "Mirkelam", "Yonca Evcimik", "Burak Kut", "Çelik", "İzel", "Yaşar",
        
        # Anadolu Rock & Efsaneler
        "Erkin Koray", "Moğollar", "Fikret Kızılok", "Haluk Levent", "Kıraç",
        "Kurtalan Ekspres", "3 Hürel", "Selda Bağcan", "Ahmet Kaya", 
    
        # Türkçe Rock & Metal & Alternatif Gruplar
        "Manga", "Athena", "Şebnem Ferah", "Teoman", "Pinhani", "Kargo", 
        "Kurban", "Yüksek Sadakat", "Gripin", "Seksendört", "Zakkum", "Model", 
        "Flört", "Adamlar", "Yüzyüzeyken Konuşuruz", "Dolu Kadehi Ters Tut", 
        "Madrigal", "Son Feci Bisiklet", "Pentagram", "Hayko Cepkin", 
        "Ogün Sanlısoy", "Vega", "Feridun Düzağaç", "Redd", "Pilli Bebek", "Aylin Aslım",
    
        # Türkçe Rap & Hip-Hop
        "Ezhel", "Gazapizm", "Patron", "Şanışer", "Allâme", "Joker", 
        "Norm Ender", "Killa Hakan", "Sansar Salvo", "Mode XL", "Cartel", "Eypio",
    
        # Arabesk & Türk Sanat / Halk Müziği
        "Müslüm Gürses", "İbrahim Tatlıses", "Ferdi Tayfur", "Orhan Gencebay", 
        "Neşet Ertaş", "Aşık Veysel", "Zeki Müren", "Müzeyyen Senar", 
        "Bülent Ersoy", "Zara", "Kubat", "Volkan Konak", "Kıvırcık Ali",
    
        # Modern Alternatif & İndie & Pop
        "Gaye Su Akyol", "Mabel Matiz", "Sena Şener", "Evdeki Saat", "Can Bonomo", 
        "Emir Can İğrek", "Funda Arar", "Candan Erçetin", "Sıla", "Bengü", 
        "Mustafa Ceceli", "Gökhan Türkmen", "Emre Aydın", "Murat Dalkılıç", 
        "Edis", "Zeynep Bastık", "Cem Adrian", "Bülent Ortaçgil", "Hüsnü Arkan", "Nilipek.",
    
        # Oyun Müzikleri, Soundtrack'ler ve Spesifik Tarzlar
        "Need for Speed Underground 2 soundtrack", "GTA Vice City Flash FM", 
        "Synthwave mix", "Turkish Psych Rock", "Lounge Müzik", "Slow Türk mix",
        "Arabesk Rap mix", "Cyberpunk 2077 radio", "Lo-Fi Turkish"
    ]
    
    secilen = random.choice(tarzlar_ve_sarkilar)
    print(f"\n[RADYO MODU] Sistem boşta kaldı. Rastgele seçilen tarz/sanatçı: {secilen}")
    
    # Bizim normal youtube fonksiyonunu tetikliyoruz, arkada mpv açılıyor
    youtube_muzik_cal(secilen)
    


def mpv_caliyor_mu():
    """ İşletim sisteminde aktif olarak mpv (müzik) açık mı kontrol eder """
    try:
        # Linux'ta mpv sürecini arar
        çıktı = subprocess.check_output("pgrep -x mpv", shell=True)
        return True # Eğer süreç varsa True döner
    except subprocess.CalledProcessError:
        return False # mpv kapandıysa veya hiç açılmadıysa False döner
        
def asistan_konus(metin):
    """ Kelime uzunluğuna göre yerel veya bulut motorunu seçen, gecikmesiz hibrit TTS """
    try:
        # Karakter temizliği
        temiz_metin = metin.replace("*", "").replace("#", "").replace("_", "").replace('"', '').replace("'", "")
        
        if not temiz_metin.strip():
            return
            
        print(f"[ASİSTAN KONUŞUYOR]: {temiz_metin}")
        
        # --- TAKTİK 1: TEK KELİMELİK SİSTEM MESAJLARI İÇİN YEREL VE ANINDA (OFFLINE) ---
        # "Efendim", "Ses ayarlandı" gibi kısa veya sabit komutları internete göndermeden yerelde patlatıyoruz.
        # Bu sayede ses kartı sıfır gecikmeyle uyanır, kelime asla yutulmaz.
        if len(temiz_metin.split()) <= 2 or temiz_metin in ["Efendim", "Ses ayarlandı.", "Oturum kapatıldı.", "Bağlantı hatası oluştu."]:
            komut = f'espeak-ng -vtr -s 140 "{temiz_metin}" --stdout | aplay -D default'
            subprocess.run(komut, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return

        # --- TAKTİK 2: UZUN GEMINI CEVAPLARI İÇİN MICROSOFT EDGE STREAM ---
        VOICE = "tr-TR-AhmetNeural"
        
        async def stream_oku():
            try:
                # ARM işlemcilerde pipe yerine RAM disk (/tmp) kullanmak en garantisidir.
                dosya_yolu = "/tmp/gemini_tts.mp3"
                communicate = edge_tts.Communicate(temiz_metin, VOICE)
                
                # Sesi saniyeler içinde RAM'e kaydet
                await communicate.save(dosya_yolu)
                
                # Temiz bir şekilde dosyadan çal (Hata verirse ekranda görelim diye DEVNULL kaldırdık)
                mpv_komut = f'mpv --no-video --volume=100 {dosya_yolu}'
                subprocess.run(mpv_komut, shell=True)
                
            except Exception as e:
                print(f"[EDGE-TTS HATASI]: {e}")

        asyncio.run(stream_oku())
        
    except Exception as e:
        print(f"[TTS HİBRİT HATASI]: {e}")
# 4. YOUTUBE MUSIC ALTYAPISI
print("YouTube Music altyapısı uyandırılıyor...")
try:
    yt = YTMusic()
    print("Sistem tamamen hazır reis!\n")
except Exception as e:
    print(f"[HATA] YTMusic başlatılamadı: {e}")

def arecord_ile_dinle(dosya_adi="/dev/shm/gecici_ses.wav", uyanik_mod=False):
    """ SIFIR DIŞ KÜTÜPHANE! Saf Python ve arecord ile kendi sessizlik algılayıcımız """
    
    if os.path.exists(dosya_adi):
        try: os.remove(dosya_adi)
        except: pass

    # ---> YENİ EKLENEN SATIR (ALSA'yı rahatlatan zombi temizleyici) <---
    os.system("pkill -9 arecord > /dev/null 2>&1")

    # arecord'u arka planda başlatıp canlı veriyi (stdout) Python'a boruluyoruz
    komut = f"arecord -D {MIKROFON_CIHAZI} -f S16_LE -r 16000 -c 1 -t wav"
    process = subprocess.Popen(komut, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    header = process.stdout.read(44)
    ses_parcalari = [header]
    
    SES_ESIGI = 1600  
    BEKLEME_SURESI = 2.0 if uyanik_mod else 0.8  
    MAX_KAYIT_SURESI = 8.0 # <-- YENİ: RAM patlamasını engelleyecek maksimum dinleme süresi
    
    ses_basladi = False
    sessizlik_baslangici = None
    ses_baslama_ani = None # <-- YENİ: Sesi ilk duyduğu anın kronometresi
    
    try:
        while True:
            chunk = process.stdout.read(3200)
            if not chunk:
                break
                
            ses_parcalari.append(chunk)
            
            count = len(chunk) // 2
            try:
                shorts = struct.unpack(f"<{count}h", chunk)
                rms = math.sqrt(sum(s*s for s in shorts) / count)
            except:
                rms = 0

            if rms > SES_ESIGI:
                if not ses_basladi:
                    ses_basladi = True
                    ses_baslama_ani = time.time() # Sesi ilk duyduğu saniyeyi kaydet
                sessizlik_baslangici = None 
            else:
                if ses_basladi:
                    if sessizlik_baslangici is None:
                        sessizlik_baslangici = time.time() 
                    elif time.time() - sessizlik_baslangici > BEKLEME_SURESI:
                        break # Normal sessizlikte çıkış
            
            # --- YENİ: RAM KORUMA KALKANI ---
            # Eğer müzik çalıyorsa veya gürültü hiç susmuyorsa, 8 saniye sonra kaydı acımadan kes.
            if ses_basladi and (time.time() - ses_baslama_ani > MAX_KAYIT_SURESI):
                break
                        
    except Exception as e:
        print(f"[KAYIT İŞLEME HATASI]: {e}")
        
    process.terminate()
    process.wait()
    
    with open(dosya_adi, "wb") as f:
        f.write(b"".join(ses_parcalari))

def sesten_metne(dosya_adi="/dev/shm/gecici_ses.wav"):
    r = sr.Recognizer()
    if not os.path.exists(dosya_adi) or os.path.getsize(dosya_adi) == 0:
        return ""
    try:
        with sr.AudioFile(dosya_adi) as source:
            audio = r.record(source)
        return r.recognize_google(audio, language="tr-TR").lower()
    except:
        return "" 

def yaziyi_rakama_cevir(metin):
    sozluk = {
        "sıfır": "0", "bir": "1", "iki": "2", "üç": "3", "dört": "4",
        "beş": "5", "altı": "6", "yedi": "7", "sekiz": "8", "dokuz": "9",
        "on": "10", "yirmi": "20", "otuz": "30", "kırk": "40", "elli": "50",
        "altmış": "60", "atmış": "60", "yetmiş": "70", "seksen": "80",
        "doksan": "90", "yüz": "100"
    }
    yeni_metin = metin
    for kelime, rakam in sozluk.items():
        yeni_metin = re.sub(rf'\b{kelime}\b', rakam, yeni_metin)
    yeni_metin = yeni_metin.replace("bastı", "bas").replace("bastık", "bas").replace("bası", "bas")
    yeni_metin = yeni_metin.replace("tizi", "tiz").replace("tizi ", "tiz")
    return yeni_metin

def ses_seviyesini_ayarla(komut):
    sayilar = re.findall(r'\d+', komut)
    if sayilar:
        seviye = int(sayilar[0])
        seviye = max(0, min(100, seviye)) 
        
        print(f"\n[DONANIM] Ses seviyesi %{seviye} olarak ayarlanıyor...")
        subprocess.run(f"amixer -c 0 sset 'Line Out' {seviye}%", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(f"amixer -c 0 sset 'DAC' {seviye}%", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    return False

def ekolayzer_ayarla(komut):
    global MADO_BASS, MADO_TIZ
    
    # Eksi değerleri de yakalayabilmek için regex filtresi
    sayilar = re.findall(r'-?\d+', komut)
    if not sayilar:
        return False
        
    seviye = int(sayilar[0])
    seviye = max(-12, min(12, seviye)) # Donanımsal patlama olmasın diye -12 ile +12 arasına sınırlıyoruz
    
    if "bas" in komut:
        MADO_BASS = seviye
        print(f"\n[SES SİSTEMİ] Bas ayarı {MADO_BASS} olarak güncellendi!")
        asistan_konus(f"Bas {MADO_BASS} yapıldı.")
        return True
    elif "tiz" in komut:
        MADO_TIZ = seviye
        print(f"\n[SES SİSTEMİ] Tiz ayarı {MADO_TIZ} olarak güncellendi!")
        asistan_konus(f"Tiz {MADO_TIZ} yapıldı.")
        return True
        
    return False
    
    
def unsuz_iskelet_cikar(metin):
    """ Metindeki tüm sesli harfleri, boşlukları ve özel karakterleri siler.
        Örn: 'Ahmet Kaya - Tapa Tapa' -> 'hmtkytptp'
        'taptap' -> 'tptp'
    """
    temiz = metin.lower()
    temiz = re.sub(r'[aeıioöuü]', '', temiz) # Sesli harfleri yut
    temiz = re.sub(r'[^a-z0-9çğş]', '', temiz)  # Harf ve sayı dışındaki her şeyi sil
    return temiz

def lokal_muzik_bul_ve_cal(arama_sorgusu):
    """ Sesli harf iskeletiyle %100 isabetli lokal arama yapar """
    global MADO_BASS, MADO_TIZ
    USB_YOLU = "/media/usbflash"
    
    sorgu = arama_sorgusu.lower().strip()
    print(f"[SİSTEM ANALİZİ] Gelen Ham Komut: '{sorgu}'")

    # MÜZİĞİ ANINDA KES
    subprocess.run("pkill -9 mpv", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5) 

    # Tetikleyicileri ve dolgu kelimeleri temizle
    tetikleyiciler = [
        r'\blokal[a-z]*\b', r'\bokal[a-z]*\b', r'\bkalden\b',
        r'\bflash[a-z]*\b', r'\bflaş[a-z]*\b', r'\blaş[a-z]*\b', 
        r'\bhafıza[a-z]*\b', r'\bfıza[a-z]*\b', r'\bzadan\b',
        r'\bdisk[a-z]*\b', r'\bbellek[a-z]*\b'
    ]
    for desen in tetikleyiciler:
        sorgu = re.sub(desen, '', sorgu)

    dolgu_kelimeleri = [
        "çal", "oynat", "müzik", "müziği", "şarkı", "şarkısını", "falan", "filan", 
        "diyince", "bize", "bi", "bir", "lütfen", "aç", "söyle", "getir"
    ]
    for kelime in dolgu_kelimeleri:
        sorgu = re.sub(rf'\b{kelime}\b', '', sorgu)

    temiz_sorgu = re.sub(r'\s+', ' ', sorgu).strip()
    
    # İskelet Çıkarma İşlemi (taptap -> tptp)
    iskelet_sorgu = unsuz_iskelet_cikar(temiz_sorgu)
    
    if not os.path.exists(USB_YOLU):
        print("[HATA] Flash bellek bağlı değil!")
        asistan_konus("Flash bellek bağlı değil reis.")
        return

    tum_dosyalar = []
    for root, dirs, files in os.walk(USB_YOLU):
        for file in files:
            if file.lower().endswith('.mp3'):
                tum_dosyalar.append(os.path.join(root, file))

    if not tum_dosyalar:
        print("[UYARI] Flash belleğin içinde hiç MP3 bulunamadı.")
        asistan_konus("Flash belleğin içi boş kral.")
        return

    hedef_dosya = None

    if not temiz_sorgu or len(temiz_sorgu) < 2:
        hedef_dosya = random.choice(tum_dosyalar)
        print(f"[LOKAL RADYO] Rastgele seçilen: {os.path.basename(hedef_dosya)}")
    else:
        print(f"[LOKAL AKILLI ARAMA] Şarkı: '{temiz_sorgu}' | İskelet Format: '{iskelet_sorgu}'")
        
        en_yuksek_oran = 0.0
        en_yakin_dosya = None
        
        for dosya in tum_dosyalar:
            dosya_adi = os.path.basename(dosya).lower().replace(".mp3", "")
            iskelet_dosya = unsuz_iskelet_cikar(dosya_adi)
            
            # TAKTİK 1: Şarkı iskeleti dosyanın iskeleti içinde geçiyor mu?
            # tptp -> ahmetkayatptpofficial içinde var mı? VAR!
            if iskelet_sorgu in iskelet_dosya and len(iskelet_sorgu) > 1:
                hedef_dosya = dosya
                print("[İSKELET EŞLEŞMESİ BAŞARILI]")
                break
                
            # TAKTİK 2: Standart Benzerlik Skoru (Yedek)
            oran = SequenceMatcher(None, iskelet_sorgu, iskelet_dosya).ratio()
            if oran > en_yuksek_oran:
                en_yuksek_oran = oran
                en_yakin_dosya = dosya

        # İskelet tamamen içinde geçmiyorsa ama %40'tan fazla benziyorsa onu seç
        if not hedef_dosya and en_yuksek_oran >= 0.40:  
            print(f"[YAKINLIK EŞLEŞMESİ BAŞARILI] Skor: %{int(en_yuksek_oran*100)}")
            hedef_dosya = en_yakin_dosya

    if hedef_dosya:
        print(f"[LOKAL MÜZİK OYNATILIYOR]: {os.path.basename(hedef_dosya)}")
        mpv_komut = f'mpv --no-video --ao=alsa --volume=150 --af="equalizer=f=60:w=1:g={MADO_BASS},equalizer=f=16000:w=1:g={MADO_TIZ}" "{hedef_dosya}"'
        subprocess.Popen(mpv_komut, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        print(f"[LOKAL] '{temiz_sorgu}' için hiçbir mantıklı eşleşme bulunamadı.")
        asistan_konus("İstediğin şarkıyı flash bellekte bulamadım.")
        
        
def youtube_muzik_cal(arama_sorgusu):
    global MADO_BASS, MADO_TIZ
    
    temiz_sorgu = arama_sorgusu.replace("müzik", "").replace("müziği", "").replace("çal", "").replace("oynat", "").strip()
    temiz_sorgu = temiz_sorgu.replace("hey", "").replace("gemini", "").replace("ceminay", "").strip()
    
    # Şarkı ismi belirtilmediyse (Sadece "çal" veya "müzik çal" dediyse)
    if not temiz_sorgu:
        print("\n[SİSTEM] Belirli bir şarkı söylenmedi. Başlangıç için rastgele mod tetikleniyor...")
        rastgele_muzik_bul()
        return

    print(f"\n[YT MUSIC] '{temiz_sorgu}' internette aranıyor...")
    subprocess.run("pkill -9 mpv", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)

    try:
        arama_sonuclari = yt.search(query=temiz_sorgu, filter="songs")
        if arama_sonuclari:
            ilk_sonuc = arama_sonuclari[0]
            video_id = ilk_sonuc['videoId']
            
            print(f"[MÜZİK BULUNDU]: {ilk_sonuc['title']} - {ilk_sonuc['artists'][0]['name']}")
            print("[ALGORİTMA] YouTube algoritmasından bu şarkıya benzer liste (Radio) çekiliyor...")
            
            # --- YOUTUBE ALGORİTMASINI BURADA KOPARIYORUZ ---
            # get_watch_playlist fonksiyonu, o video_id'ye benzeyen sonraki 20-25 şarkıyı getirir
            izleme_listesi = yt.get_watch_playlist(videoId=video_id, limit=20)
            
            # Listeden tüm şarkıların URL'lerini sırayla topluyoruz
            oynatma_listesi_urleri = []
            if "tracks" in izleme_listesi:
                for track in izleme_listesi["tracks"]:
                    if "videoId" in track and track["videoId"]:
                        oynatma_listesi_urleri.append(f"https://www.youtube.com/watch?v={track['videoId']}")
            
            if oynatma_listesi_urleri:
                print(f"[ALGORİTMA BAŞARILI] Tarza uyan {len(oynatma_listesi_urleri)} şarkılık akış mpv'ye yükleniyor...")
                
                # --- YENİ: EKRANA SIRADAKİ ŞARKILARI YAZDIR ---
                print("\n--- YOUTUBE RADYO: SIRADAKİ PARÇALAR ---")
                # İlk şarkı zaten anında çalacağı için 1'den başlayıp listedeki sonraki 4 şarkıyı gösteriyoruz
                for i, track in enumerate(izleme_listesi["tracks"][1:5]): 
                    if "title" in track and "artists" in track:
                        print(f" {i+1}. {track['title']} - {track['artists'][0]['name']}")
                print(" ----------------------------------------\n")
                
                tum_linkler = " ".join(oynatma_listesi_urleri)
                
                # --- YENİ MPV KOMUTU (Şarkı adını basması için) ---
                # --quiet: mpv'nin gereksiz teknik loglarını gizler
                # --term-playing-msg: Sadece yeni şarkıya geçtiğinde ismini okunaklı şekilde basar
                # Bash'in yutmasını engellemek için parametreler tek tırnak ('...') içinde!
                mpv_komut = f"mpv --no-video --ao=alsa --vd-lavc-threads=4 --cache=yes --demuxer-max-bytes=150M --ytdl-raw-options=force-ipv4= --volume=150 --af='equalizer=f=60:w=1:g={MADO_BASS},equalizer=f=16000:w=1:g={MADO_TIZ}' --quiet --term-playing-msg='[-> RADYO ÇALIYOR]: ${{media-title}}' {tum_linkler}"
                subprocess.Popen(mpv_komut, shell=True, stderr=subprocess.DEVNULL)
            else:
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                mpv_komut = f"mpv --no-video --ao=alsa --vd-lavc-threads=4 --cache=yes --demuxer-max-bytes=150M --ytdl-raw-options=force-ipv4= --volume=150 --af='equalizer=f=60:w=1:g={MADO_BASS},equalizer=f=16000:w=1:g={MADO_TIZ}' --quiet --term-playing-msg='[-> ŞU AN ÇALIYOR]: ${{media-title}}' {video_url}"
                subprocess.Popen(mpv_komut, shell=True, stderr=subprocess.DEVNULL)
        else:
            print("[YT MUSIC] Maalesef şarkı bulunamadı kral.")
    except Exception as e:
        print(f"[YT MUSIC HATASI]: {e}")

# --- ANA DÖNGÜ (ASİSTANIN BEYNİ) ---
uyanik_mi = False
print("\n(Doğrudan 'Müzik çal' veya 'Sesi 50 yap' da diyebilirsiniz)\n")

while True:
    if not uyanik_mi:
        arecord_ile_dinle(dosya_adi="/dev/shm/gecici_ses.wav", uyanik_mod=False)
        gelen_ses = sesten_metne()
        
        if gelen_ses:
            gelen_ses = yaziyi_rakama_cevir(gelen_ses)
            print(f"[DUYULAN]: '{gelen_ses}'")
            
            # --- UYKUDAYKEN SES / MÜZİK KONTROLLERİ ---
            if "ses" in gelen_ses and any(harf.isdigit() for harf in gelen_ses):
                ses_seviyesini_ayarla(gelen_ses)
                asistan_konus("Ses ayarlandı.")
                time.sleep(1)
                continue 
            
            if "bas" in gelen_ses or "tiz" in gelen_ses:
                # Eğer cümlenin içinde herhangi bir sayı varsa (yazıyla veya rakamla fark etmez)
                if any(harf.isdigit() for harf in gelen_ses) or any(k in gelen_ses for k in ["bir","iki","üç","dört","beş","altı","yedi","sekiz","dokuz","on","eksi"]):
                    ekolayzer_ayarla(gelen_ses)
                    continue
            
            if "durdur" in gelen_ses or "kes" in gelen_ses or "kapat" in gelen_ses:
                print("[SİSTEM] Müzik tamamen kapatılıyor (Donanım kilitlenmemesi için)...")
                subprocess.run("pkill -9 mpv", shell=True) 
                asistan_konus("Müzik kapatıldı.")
                continue
            
 
                
            # --- MÜZİK ÇALMA KONTROL MERKEZİ (UYKU MODU) ---
            if "çal" in gelen_ses or "oynat" in gelen_ses:
                # Eğer cümlenin içinde lokal, flash, flaş, hafıza gibi yerel kelimelerden biri geçiyorsa
                # (Büyük/küçük harf duyarlılığını kaldırmak için re.IGNORECASE ekledik)
                if re.search(r'(lokal|okal|kalden|flash|laş|flaş|hafıza|fıza|zadan|disk|bellek)', gelen_ses, re.IGNORECASE):
                    print("[SİSTEM] Yerel tetikleyici yakalandı, doğrudan flash belleğe gidiliyor...")
                    lokal_muzik_bul_ve_cal(gelen_ses)
                else:
                    # İçinde hiçbir yerel kelime yoksa temizce internette ara
                    print("[SİSTEM] Yerel kelime bulunamadı, YouTube Music üzerinden aranıyor...")
                    youtube_muzik_cal(gelen_ses)
                
                time.sleep(1)
                continue
            
            if re.search(r'(lokal|flash|flaş|hafıza|disk|bellek)', gelen_ses):
                lokal_muzik_bul_ve_cal(gelen_ses)
                time.sleep(1)
                continue
            
            if any(kelime in gelen_ses for kelime in ["gemini", "ceminay", "hey", "merhabalar"]):
                print("\n[!] Buyur reis, dinliyorum...")
                asistan_konus("Efendim")
                uyanik_mi = True
                time.sleep(0.5)
    
    else:
        print("\nSöz sizde... Dinliyorum...")
        arecord_ile_dinle(dosya_adi="/dev/shm/gecici_ses.wav", uyanik_mod=True)
        komut = sesten_metne()
        
        if not komut:
            continue
            
        komut = yaziyi_rakama_cevir(komut)
        print(f"Senin Dediğin: >> {komut}")
        
        # --- 1. DURUM: KAPATMA KOMUTLARI ---
        if any(kelime in komut for kelime in ["görüşürüz", "kapat", "baybay", "uykuya geç"]):
            print("\nOturum kapatıldı. Uyku moduna geçiliyor.\n")
            asistan_konus("Görüşmek üzere, uyku moduna geçiyorum.")
            chat = model.start_chat(history=[])
            uyanik_mi = False
            time.sleep(2)
            continue
            
        # --- 2. DURUM: SES SEVİYESİ AYARI ---
        if "ses" in komut and any(harf.isdigit() for harf in komut):
            ayarlandi_mi = ses_seviyesini_ayarla(komut)
            if ayarlandi_mi:
                asistan_konus("Ses ayarlandı.")
                chat = model.start_chat(history=[])
                uyanik_mi = False
                time.sleep(1)
                continue
            
        if "bas" in komut or "tiz" in komut:
            if any(harf.isdigit() for harf in komut) or any(k in komut for k in ["bir","iki", ...]):
                ekolayzer_ayarla(komut)
                continue
            
        if "durdur" in komut or "kes" in komut or "kapat" in komut:
            print("[SİSTEM] Müzik tamamen kapatılıyor (Donanım kilitlenmemesi için)...")
            subprocess.run("pkill -9 mpv", shell=True) 
            asistan_konus("Müzik kapatıldı.")
            chat = model.start_chat(history=[])
            uyanik_mi = False
            time.sleep(1)
            continue
            
        # --- MÜZİK ÇALMA KONTROL MERKEZİ (UYANIK MOD) ---
        if "çal" in komut or "oynat" in komut:
            if re.search(r'(lokal|okal|kalden|flash|laş|flaş|hafıza|fıza|zadan|disk|bellek)', komut, re.IGNORECASE):
                print("[SİSTEM] Yerel tetikleyici yakalandı, doğrudan flash belleğe gidiliyor...")
                lokal_muzik_bul_ve_cal(komut)
            else:
                print("[SİSTEM] Yerel kelime bulunamadı, YouTube Music üzerinden aranıyor...")
                youtube_muzik_cal(komut)
                
            chat = model.start_chat(history=[])
            uyanik_mi = False
            time.sleep(2)
            continue
        
        if re.search(r'(lokal|flash|flaş|hafıza|disk|bellek)', komut):
                lokal_muzik_bul_ve_cal(komut)
                time.sleep(1)
                continue
            
        # --- 5. DURUM: NORMAL GEMINI SOHBETİ ---
        try:
            print("Gemini düşünüyor...")
            cevap = chat.send_message(komut)
            print("\n--- Gemini'ın cevabı ---")
            print(f"{cevap.text}")
            print("------------------------------")
            asistan_konus(cevap.text)
            
        except Exception as e:
            print(f"Gemini API ERROR: {e}")
            asistan_konus("Bağlantı hatası oluştu.")
