import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Oldal beállítása
st.set_page_config(page_title="Csirakert Magraktár", page_icon="🌱")

st.title("🌱 Csirakert Magraktár")
st.write(f"Üdvözöllek, Mester! Kezeld itt a precíziós magkészletet.")

# Kapcsolódás a Google Sheets-hez
conn = st.connection("gsheets", type=GSheetsConnection)

# Adatok beolvasása - frissítés kényszerítése ttl=0-val
df = conn.read(worksheet="Magok", ttl=0)

# --- ADMIN: MAG TÖRLÉSE (Sidebar) ---
with st.sidebar:
    st.header("⚙️ Adminisztráció")
    st.write("Itt tudod eltávolítani a hibásan felvitt sorokat.")
    
    # Kiválasztjuk melyik magot akarjuk törölni
    magok_listaja = df["Mag fajtája"].tolist()
    torlendo_mag = st.selectbox("Válaszd ki a törlendő magot:", options=["-- Válassz --"] + magok_listaja)
    
    if st.button("🗑️ Kijelölt mag törlése"):
        if torlendo_mag != "-- Válassz --":
            # Szűrjük ki a törlendő magot a táblázatból
            df_frissitve = df[df["Mag fajtája"] != torlendo_mag]
            
            # Mentés a Google Sheets-be
            conn.update(worksheet="Magok", data=df_frissitve)
            
            st.warning(f"'{torlendo_mag}' eltávolítva!")
            st.cache_data.clear()
            st.rerun()
        else:
            st.error("Nincs kiválasztva mag!")

# --- RAKTÁRKÉSZLET MEGJELENÍTÉSE ---
st.subheader("Aktuális készlet")

display_df = df.copy()

# Segédfüggvény a kg/g váltóhoz és az Emojikhoz
def format_with_status(gramm):
    # Mértékegység meghatározása
    suly_szoveg = f"{gramm / 1000:.2f} kg" if gramm >= 1000 else f"{int(gramm)} g"
    
    # Állapotjelző emoji meghatározása
    if gramm < 200:
        return f"🔴 {suly_szoveg}"
    elif gramm < 500:
        return f"🟡 {suly_szoveg}"
    elif gramm < 1000:
        return f"🟢 {suly_szoveg}"
    else:
        return f"✅ {suly_szoveg}"

display_df["Készlet"] = display_df["Mennyiség (g)"].apply(format_with_status)

# Megjelenítés
st.data_editor(
    display_df[["Mag fajtája", "Mennyiség (g)", "Készlet", "Utolsó módosítás"]],
    column_config={
        "Mag fajtája": "Mag neve",
        "Mennyiség (g)": st.column_config.ProgressColumn(
            "Szint",
            help="Vizuális telítettség",
            format="",
            min_value=0,
            max_value=5000,
            color="blue", # Fix kék sáv, ez stabil
        ),
        "Készlet": "Állapot",
        "Utolsó módosítás": "Frissítve"
    },
    hide_index=True,
    use_container_width=True,
    disabled=True
)

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
        
        st.cache_data.clear()
        st.rerun()

# --- ÚJ MAG HOZZÁADÁSA (VÉDELEMMEL) ---
with st.expander("Új magfajta felvétele a rendszerbe"):
    with st.form("new_seed_form"):
        uj_mag = st.text_input("Mag neve").strip()
        kezdo_keszlet = st.number_input("Kezdő készlet (g)", min_value=0, step=100)
        hozzaadas_button = st.form_submit_button("Hozzáadás")
        
        if hozzaadas_button and uj_mag:
            # Ellenőrizzük, hogy létezik-e már ilyen név (kis/nagybetű nem számít)
            letezo_magok = [m.lower() for m in df["Mag fajtája"].tolist()]
            
            if uj_mag.lower() in letezo_magok:
                st.error(f"Hiba! '{uj_mag}' nevű mag már szerepel a listában.")
            else:
                # Új sor elkészítése
                uj_adat = pd.DataFrame([{
                    "Mag fajtája": uj_mag, 
                    "Mennyiség (g)": kezdo_keszlet, 
                    "Utolsó módosítás": datetime.now().strftime("%Y-%m-%d %H:%M")
                }])
                
                # Adat hozzáadása a meglévőhöz
                frissitett_df = pd.concat([df, uj_adat], ignore_index=True)
                
                # Mentés a Google Sheets-be
                conn.update(worksheet="Magok", data=frissitett_df)
                
                st.success(f"'{uj_mag}' sikeresen rögzítve!")
                st.cache_data.clear()
                st.rerun()
