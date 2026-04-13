import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Oldal beállítása
st.set_page_config(page_title="Csirakert Magraktár", page_icon="🌱")

st.title("🌱 Csirakert Magraktár")
st.write(f"Üdvözöllek, Mester! Kezeld itt a precíziós magkészletet.")

# Kapcsolódás a Google Sheets-hez (a korábbi secrets.toml beállításaidat használva)
conn = st.connection("gsheets", type=GSheetsConnection)

# Adatok beolvasása (Feltételezzük, hogy a táblázat neve 'Magok')
df = conn.read(worksheet="Magok")

# --- RAKTÁRKÉSZLET MEGJELENÍTÉSE ---
st.subheader("Aktuális készlet")
# Kiszínezzük, ha kevés a mag (pl. 500g alatt)
def highlight_low_stock(s):
    return ['background-color: #ff4b4b' if val < 500 else '' for val in s]

st.dataframe(df.style.apply(highlight_low_stock, subset=['Mennyiség (g)']), use_container_width=True)

# --- MAG KIVÉTELE / HOZZÁADÁSA ---
st.divider()
st.subheader("Tranzakció (Mérés után)")

with st.form("inventory_form"):
    mag_tipus = st.selectbox("Melyik magból vettél ki?", df["Mag fajtája"].unique())
    mennyiseg_valtozas = st.number_input("Mennyiség változása (grammban). Kivételnél használj mínusz jelet! (pl. -70)", step=1)
    
    submit_button = st.form_submit_button("Mentés")

if submit_button:
    # Aktuális index megkeresése
    idx = df.index[df['Mag fajtája'] == mag_tipus].tolist()[0]
    
    # Új érték kiszámolása
    regi_ertek = df.at[idx, "Mennyiség (g)"]
    uj_ertek = regi_ertek + mennyiseg_valtozas
    
    if uj_ertek < 0:
        st.error(f"Hiba! Nincs elég mag a raktárban. (Jelenleg: {regi_ertek}g)")
    else:
        # Táblázat frissítése
        df.at[idx, "Mennyiség (g)"] = uj_ertek
        df.at[idx, "Utolsó módosítás"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Mentés a Google Sheets-be
        conn.update(worksheet="Magok", data=df)
        st.success(f"Frissítve! {mag_tipus}: {regi_ertek}g -> {uj_ertek}g")
        st.balloons()
        # Oldal újratöltése a friss adatokkal
        st.rerun()

# --- ÚJ MAG HOZZÁADÁSA ---
with st.expander("Új magfajta felvétele a rendszerbe"):
    uj_mag = st.text_input("Mag neve")
    kezdo_keszlet = st.number_input("Kezdő készlet (g)", min_value=0, step=100)
    if st.button("Hozzáadás"):
        uj_sor = pd.DataFrame([{"Mag fajtája": uj_mag, "Mennyiség (g)": kezdo_keszlet, "Utolsó módosítás": datetime.now().strftime("%Y-%m-%d %H:%M")}])
        df = pd.concat([df, uj_sor], ignore_index=True)
        conn.update(worksheet="Magok", data=df)
        st.success(f"{uj_mag} hozzáadva!")
        st.rerun()
