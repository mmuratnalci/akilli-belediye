import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# Sayfa ayarları
st.set_page_config(
    page_title="Belediye Hizmet Kalitesi Analiz",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------
# 1) SABİTLER VE YARDIMCI FONKSİYONLAR
# ----------------------------

HIZMET_ALANLARI = {
    "ulasim": "🚌 Ulaşım Hizmetleri",
    "temizlik": "🧹 Temizlik ve Çevre",
    "altyapi": "🔧 Altyapı Hizmetleri",
    "parklar": "🌳 Parklar ve Yeşil Alanlar",
    "iletisim": "📞 Belediye İletişimi"
}

HIZMET_KODLARI = ["ulasim", "temizlik", "altyapi", "parklar", "iletisim"]

OLUMLU_KELIMELER = [
    "iyi", "güzel", "memnun", "rahat", "kolay", "hızlı", "düzenli",
    "güvenli", "yakın", "hizmet", "başarılı", "uygun", "gelişmiş",
    "harika", "mükemmel", "tamam", "yeterli", "temiz", "düzgün",
    "verimli", "etkili", "iyileşti", "tamamlandı"
]

OLUMSUZ_KELIMELER = [
    "kötü", "yetersiz", "sorun", "eksik", "bozuk", "düzensiz", "geç",
    "kalitesiz", "uzak", "zor", "hantal", "gürültü", "çalışmıyor",
    "aksıyor", "yoğun", "sıkıntı", "stresli", "berbat", "feci",
    "iğrenç", "kara", "kirli", "eski", "harap", "perişan"
]

# ----------------------------
# 2) SENTETİK VERİ ÜRETME
# ----------------------------

def sentetik_veri_olustur():
    np.random.seed(42)
    n = 150

    mahalleler = [
        "Merkez", "Bahçelievler", "İnönü", "Sakarya", "Yeşilova",
        "Güzeltepe", "Akarsu", "Yıldız", "Köyceğiz", "Yenimahalle"
    ]

    veri = {
        "vatandas_id": np.arange(1, n + 1),
        "yas": np.random.randint(18, 75, n),
        "mahalle": np.random.choice(mahalleler, n),
        "cinsiyet": np.random.choice(["Erkek", "Kadın", "Diğer"], n),
        "ulasim": np.random.randint(1, 6, n),
        "temizlik": np.random.randint(1, 6, n),
        "altyapi": np.random.randint(1, 6, n),
        "parklar": np.random.randint(1, 6, n),
        "iletisim": np.random.randint(1, 6, n),
    }

    df = pd.DataFrame(veri)

    yorumlar = []
    for i in range(n):
        puanlar = df.loc[i, HIZMET_KODLARI].to_dict()
        ortalama_puan = np.mean(list(puanlar.values()))
        en_dusuk_hizmet = min(puanlar, key=puanlar.get)

        if ortalama_puan >= 4.2:
            temel = "Belediye hizmetlerinden genel olarak memnunum. "
        elif ortalama_puan >= 3.0:
            temel = "Hizmetler bazı alanlarda iyiyken, birkaç konuda iyileştirmeye ihtiyaç var. "
        else:
            temel = "Belediye hizmetleri bazı alanlarda oldukça yetersiz. "

        sorun_haritasi = {
            "ulasim": "Ulaşım hizmetlerinde zaman zaman sorun yaşıyorum ve otobüslerin düzeni daha iyi olmalı. Sefer saatleri düzenlenmeli.",
            "temizlik": "Temizlik ve çevre düzeni konusunda daha özen gösterilmesini istiyorum. Sokaklarda daha sık temizlik yapılması gerekiyor.",
            "altyapi": "Altyapı çalışmaları daha hızlı ve düzenli yapılmalı. Su kesilmeleri ve elektrik sorunları sık yaşanıyor.",
            "parklar": "Parklar ve yeşil alanların bakımı daha iyi olmalı. Çocuk oyun alanları daha güvenli hale getirilmeli.",
            "iletisim": "Belediye iletişimi daha açık, hızlı ve erişilebilir olmalı. Şikayetlerin çözümü daha hızlı gerçekleşmeli."
        }

        yorum = temel + sorun_haritasi[en_dusuk_hizmet]
        yorumlar.append(yorum)

    df["yorum"] = yorumlar
    df["memnuniyet_puani"] = df[HIZMET_KODLARI].mean(axis=1)
    return df

# ----------------------------
# 3) YORUM ANALİZİ
# ----------------------------

def yorumları_analiz_et(df):
    sonuc_df = df.copy()

    def duygu_puani_hesapla(yorum):
        kucuk_yorum = yorum.lower()
        olumlu_sayı = sum(1 for kelime in OLUMLU_KELIMELER if kelime in kucuk_yorum)
        olumsuz_sayı = sum(1 for kelime in OLUMSUZ_KELIMELER if kelime in kucuk_yorum)
        return olumlu_sayı - olumsuz_sayı

    def duygu_etiketi(puan):
        if puan > 0:
            return "Olumlu"
        elif puan < 0:
            return "Olumsuz"
        return "Nötr"

    sonuc_df["yorum_puani"] = sonuc_df["yorum"].apply(duygu_puani_hesapla)
    sonuc_df["yorum_duygusu"] = sonuc_df["yorum_puani"].apply(duygu_etiketi)

    return sonuc_df

# ----------------------------
# 4) İSTATİSTİKSEL ANALİZLER
# ----------------------------

def hizmet_ortalamalarını_hesapla(df):
    ortalamalari = []
    for kod in HIZMET_KODLARI:
        ort = df[kod].mean()
        ortalamalari.append({
            "kod": kod,
            "hizmet_adı": HIZMET_ALANLARI[kod],
            "ortalama_puan": round(ort, 2)
        })
    return pd.DataFrame(ortalamalari).sort_values("ortalama_puan")

def oncelikli_alanları_belirle(ortalama_df):
    sonuc = ortalama_df.copy()

    def oncelik_belirle(puan):
        if puan < 2.5:
            return "Acil"
        elif puan < 3.5:
            return "Öncelikli"
        elif puan < 4.5:
            return "İyi"
        else:
            return "Mükemmel"

    sonuc["oncelik_durumu"] = sonuc["ortalama_puan"].apply(oncelik_belirle)
    return sonuc.sort_values("ortalama_puan")

# ----------------------------
# 5) CSV YÜKLEME VE DOĞRULAMA
# ----------------------------

def csv_dosyasını_doğrula(df):
    gerekli = ["ulasim", "temizlik", "altyapi", "parklar", "iletisim", "yorum"]
    eksik = [sütun for sütun in gerekli if sütun not in df.columns]

    if eksik:
        raise ValueError(
            f"CSV dosyasında eksik sütunlar var: {', '.join(eksik)}. "
            f"Gerekli sütunlar: {', '.join(gerekli)}"
        )

# ----------------------------
# 6) ANA UYGULAMA
# ----------------------------

st.title("🏙️ Akıllı Belediye Hizmet Kalitesi Analiz Sistemi")
st.caption("Kamu yönetimi öğrencileri için eğitim amaçlı, yorum analizi ve grafik destekli web uygulaması.")

# Sidebar
st.sidebar.header("Ayarlar")
secenek = st.sidebar.radio("Veri kaynağı", ("Sentetik Veriler Kullan", "CSV Dosyası Yükle"))

if secenek == "CSV Dosyası Yükle":
    uploaded_file = st.sidebar.file_uploader("CSV dosyası yükleyin", type=["csv"])
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            csv_dosyasını_doğrula(df)
            st.sidebar.success("CSV dosyası başarıyla yüklendi.")
        except Exception as e:
            st.error(f"CSV yüklenirken hata oluştu: {e}")
            st.stop()
    else:
        st.info("Lütfen bir CSV dosyası yükleyin.")
        st.stop()
else:
    df = sentetik_veri_olustur()

df = yorumları_analiz_et(df)
ortalama_df = hizmet_ortalamalarını_hesapla(df)
oncelik_df = oncelikli_alanları_belirle(ortalama_df)

# Ana metrikler
st.subheader("Temel Metrikler")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Toplam Vatandaş", len(df))
with col2:
    st.metric("Genel Memnuniyet", f"{df['memnuniyet_puani'].mean():.2f}/5")
with col3:
    st.metric("En Düşük Alan", oncelik_df.iloc[0]["hizmet_adı"])

# 1) Grafik: Hizmet alanlarına göre puanlar
st.subheader("Hizmet Alanlarına Göre Ortalama Puanlar")
fig1 = px.bar(
    ortalama_df,
    x="hizmet_adı",
    y="ortalama_puan",
    color="ortalama_puan",
    color_continuous_scale="RdYlGn_r",
    range_y=[1, 5],
    title="Hizmet alanlarının 1-5 Likert ortalaması",
    labels={"hizmet_adı": "Hizmet Alanı", "ortalama_puan": "Ortalama Puan"}
)
st.plotly_chart(fig1, use_container_width=True)

# 2) Grafik: Memnuniyet dağılımı
st.subheader("Vatandaş Memnuniyet Dağılımı")

df["memnuniyet_seviye"] = pd.cut(
    df["memnuniyet_puani"],
    bins=[0, 2, 3, 5],
    labels=["Düşük", "Orta", "Yüksek"]
)

fig2 = px.pie(
    df["memnuniyet_seviye"].value_counts().reset_index(),
    names="index",
    values="memnuniyet_seviye",
    title="Memnuniyet seviyeleri"
)
st.plotly_chart(fig2, use_container_width=True)

# 3) Yorum analizi
st.subheader("Açık Uçlu Yorum Analizi")
duygu_sayisi = df["yorum_duygusu"].value_counts().reset_index()
duygu_sayisi.columns = ["duygu", "adet"]

fig3 = px.bar(
    duygu_sayisi,
    x="duygu",
    y="adet",
    color="duygu",
    title="Yorum duygu dağılımı",
    labels={"duygu": "Duygu", "adet": "Yorum Sayısı"}
)
st.plotly_chart(fig3, use_container_width=True)

# 4) Örnek yorumlar
st.subheader("Örnek Yorumlar")
st.dataframe(df[["vatandas_id", "yorum", "yorum_duygusu"]].head(10), use_container_width=True)

# 5) Öncelik alanları
st.subheader("Öncelikli İyileştirme Alanları")
st.dataframe(oncelik_df.rename(columns={"hizmet_adı": "Hizmet Alanı", "ortalama_puan": "Ortalama Puan", "oncelik_durumu": "Öncelik Durumu"}), use_container_width=True)

# 6) Sonuç indir
st.subheader("Sonuç İndirme")
download_df = oncelik_df.rename(columns={
    "hizmet_adı": "Hizmet_Alani",
    "ortalama_puan": "Ortalama_Puan",
    "oncelik_durumu": "Oncelik_Durumu"
})
csv_data = download_df.to_csv(index=False, encoding="utf-8-sig")
st.download_button(
    label="Sonuçları CSV olarak indir",
    data=csv_data,
    file_name="belediye_hizmet_kalitesi_raporu.csv",
    mime="text/csv"
)

# Son açıklama
st.markdown("---")
st.markdown("Bu uygulama, başlangıç seviyesindeki öğrenciler için anlaşılır ve öğretici olarak tasarlanmıştır.")
