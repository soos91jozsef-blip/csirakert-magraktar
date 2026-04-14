import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Oldal beállítása
st.set_page_config(page_title="Csírakert Magraktár", page_icon="🌱")

st.title("🌱 Csírakert Magraktár")
st.write(f"Üdvözöllek, Mester! Kezeld itt a precíziós magkészletet.")

# Kapcsolódás a Google Sheets-hez
conn = st.connection("gsheets", type=GSheetsConnection)

# Adatok beolvasása (Minden alkalommal frissítjük)
df = conn.read(worksheet="Magok", ttl=0)

# --- HELYSZÍN VÁLASZTÁSA ---
st.divider()
helyszin_lista = ["Ada", "Mohol", "Szeged"]
valasztott_helyszin = st.selectbox("📍 Melyik raktárban dolgozol most?", helyszin_lista)

st.sidebar.header("Összesített nézet")
mutasd_mindet = st.sidebar.checkbox("Minden város készlete egyben")

# --- ADATOK ELŐKÉSZÍTÉSE ---
def format_with_status(gramm):
    suly_szoveg = f"{gramm / 1000:.2f} kg" if gramm >= 1000 else f"{int(gramm)} g"
    if gramm < 200: return f"🔴 {suly_szoveg}"
    elif gramm < 500: return f"🟡 {suly_szoveg}"
    elif gramm < 1000: return f"🟢 {suly_szoveg}"
    else: return f"✅ {suly_szoveg}"

if mutasd_mindet:
    st.subheader("🌐 Összesített raktárkészlet")
    # Csoportosítás mag szerint és összeadás
    display_df = df.groupby("Mag fajtája", as_index=False).agg({"Mennyiség (g)": "sum", "Utolsó módosítás": "max"})
else:
    st.subheader(f"🏠 Aktuális készlet: {valasztott_helyszin}")
    display_df = df[df["Helyszín"] == valasztott_helyszin].copy()

# Megjelenítés
if not display_df.empty:
    display_df["Állapot"] = display_df["Mennyiség (g)"].apply(format_with_status)
    st.data_editor(
        display_df[["Mag fajtája", "Mennyiség (g)", "Állapot", "Utolsó módosítás"]],
        column_config={
            "Mennyiség (g)": st.column_config.ProgressColumn("Szint", format="", min_value=0, max_value=5000, color="blue"),
        },
        hide_index=True, use_container_width=True, disabled=True
    )
else:
    st.info(f"Ebben a raktárban ({valasztott_helyszin}) még nincs regisztrált mag.")

# --- TRANZAKCIÓ (MÉRÉS UTÁN) ---
st.divider()
st.subheader(f"Tranzakció ({valasztott_helyszin})")

# Csak a választott helyszín magjai közül választhatunk a levonáshoz
helyi_magok = df[df["Helyszín"] == valasztott_helyszin]["Mag fajtája"].tolist()

if helyi_magok:
    kijelolt_mag = st.selectbox("Melyik magból vettél ki / tettél be?", helyi_magok)
    valtozas = st.number_input("Mennyiség változása (grammban). Levonásnál mínusz jel! (pl. -70)", step=10)

    if st.button("Mentés"):
        # Sor indexének megkeresése (Helyszín ÉS Mag név alapján!)
        idx = df[(df["Helyszín"] == valasztott_helyszin) & (df["Mag fajtája"] == kijelolt_mag)].index[0]
        
        # Frissítés
        df.at[idx, "Mennyiség (g)"] += valtozas
        df.at[idx, "Utolsó módosítás"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Google Sheets frissítése
        conn.update(worksheet="Magok", data=df)
        st.success(f"Frissítve! {kijelolt_mag} új egyenlege {valasztott_helyszin} raktárában: {df.at[idx, 'Mennyiség (g)']} g")
        st.rerun()

# --- ÚJ MAG HOZZÁADÁSA ---
with st.expander("➕ Új magfajta felvétele ebbe a raktárba"):
    uj_mag_nev = st.text_input("Új mag neve")
    uj_mennyiseg = st.number_input("Kezdő mennyiség (g)", min_value=0, step=100)
    
    if st.button("Új mag rögzítése"):
        uj_sor = pd.DataFrame([{
            "Helyszín": valasztott_helyszin,
            "Mag fajtája": uj_mag_nev,
            "Mennyiség (g)": uj_mennyiseg,
            "Utolsó módosítás": datetime.now().strftime("%Y-%m-%d %H:%M")
        }])
        df = pd.concat([df, uj_sor], ignore_index=True)
        conn.update(worksheet="Magok", data=df)
        st.success(f"{uj_mag_nev} rögzítve {valasztott_helyszin} helyszínre!")
        st.rerun()
# --- ADMINISZTRÁCIÓ (TÖRLÉS) ---
st.divider()
with st.expander("🗑️ Adminisztráció (Mag törlése)"):
    st.warning(f"Figyelem! Innen csak a(z) {valasztott_helyszin} raktárból törölhetsz magot.")
    
    # Csak az adott helyszín magjait listázzuk
    torlendo_magok = df[df["Helyszín"] == valasztott_helyszin]["Mag fajtája"].tolist()
    
    if torlendo_magok:
        valasztott_torlesre = st.selectbox("Melyik magot töröljük véglegesen?", ["-- Válassz --"] + torlendo_magok)
        
        if st.button("Kijelölt mag törlése"):
            if valasztott_torlesre != "-- Válassz --":
                # Sor eltávolítása (Helyszín ÉS Név alapján)
                df = df.drop(df[(df["Helyszín"] == valasztott_helyszin) & (df["Mag fajtája"] == valasztott_torlesre)].index)
                
                # Google Sheets frissítése
                conn.update(worksheet="Magok", data=df)
                st.success(f"A(z) {valasztott_torlesre} magot sikeresen eltávolítottuk a(z) {valasztott_helyszin} raktárból.")
                st.rerun()
            else:
                st.error("Kérlek, válassz ki egy magot a törléshez!")
    else:
        st.info("Ebben a raktárban nincs törölhető mag.")
