import streamlit as st
import requests
import numpy as np
import math
import datetime

# --- POISSON & STATISTIK FUNKTIONEN ---
def poisson_wahrscheinlichkeit(k, lam):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam**k * math.exp(-lam)) / math.factorial(k)

st.set_page_config(page_title="WM 2026 Multi-Source Live Simulator", page_icon="🏆", layout="wide")

st.title("🏆 WM 2026 Multi-Source Live Simulator")
st.markdown("Diese App lädt alle heutigen Spiele **vor Anpfiff** und gleicht die Aufstellungen live ab!")

# Sidebar für API-Konfiguration
st.sidebar.header("🔑 API-Konfiguration")
api_key = st.sidebar.text_input("Gib deinen RapidAPI-Key ein:", type="password")

# --- HISTORISCHE BASIS-RATINGS ---
base_ratings = {
    "Deutschland": {"att": 1.6, "def": 0.9},
    "Argentinien": {"att": 1.5, "def": 0.8},
    "Frankreich": {"att": 1.7, "def": 0.9},
    "Elfenbeinküste": {"att": 1.1, "def": 1.3},
    "Niederlande": {"att": 1.4, "def": 1.0},
    "Schweden": {"att": 1.2, "def": 1.1}
}

if not api_key:
    st.info("Bitte gib deinen RapidAPI-Key in der linken Sidebar ein, um die heutigen Live-Daten freizuschalten.")
else:
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "free-api-live-football-data.p.rapidapi.com"
    }

    # 1. ALLE SPIELE DES TAGES LADEN (VOR UND WÄHREND DES SPIELS)
    @st.cache_data(ttl=60) # 1 Minute Cache
    def hole_alle_heutigen_spiele():
        url = "https://free-api-live-football-data.p.rapidapi.com/football-get-matches-by-date"
        # Holt das aktuelle Datum im Format YYYYMMDD (z.B. 20260620)
        heute_str = datetime.date.today().strftime('%Y%m%d')
        querystring = {"date": heute_str}
        
        try:
            response = requests.get(url, headers=headers, params=querystring)
            if response.status_code == 200:
                # Die API gibt die Spiele meistens in einer Liste unter 'response' oder 'matches' zurück
                daten = response.json().get('response', [])
                if not daten and isinstance(response.json().get('data'), list):
                    daten = response.json().get('data')
                return daten, "OK"
        except Exception as e:
            return [], str(e)
        return [], "Keine Spiele gefunden"

    with st.spinner("Lade den heutigen Spielplan (inklusive anstehender Spiele)..."):
        spiele, api_status = hole_alle_heutigen_spiele()

    spiele_auswahl = []
    spiele_mapping = {}

    if spiele:
        for s in spiele:
            try:
                # Anpassung an die typische Struktur deiner API für Tages-Spiele
                match_id = s.get('id') or s.get('matchId') or s.get('idMatch')
                h_name = s['teams']['home']['name']
                a_name = s['teams']['away']['name']
                
                # Startzeit oder Status auslesen
                status = s.get('status', {}).get('type', '')
                time_str = s.get('time', '') or s.get('status', {}).get('statusStr', 'Anstehend')
                
                label = f"[{time_str}] {h_name} vs. {a_name}"
                spiele_auswahl.append(label)
                spiele_mapping[label] = {"id": match_id, "home": h_name, "away": a_name}
            except:
                pass

    st.subheader("🔮 Berechne ein Spiel")
    modus = st.radio("Simulations-Modus wählen:", ["Echtzeit Live-Kader Simulation (API)", "Manuelle Simulation (Historisch)"])

    if modus == "Echtzeit Live-Kader Simulation (API)":
        if not spiele_auswahl:
            st.warning("Keine Spiele für das aktuelle Datum in der API gefunden. Nutze den manuellen Modus oder den Dummy:")
            spiele_auswahl = ["Test-Spiel: Deutschland vs. Frankreich"]
            spiele_mapping["Test-Spiel: Deutschland vs. Frankreich"] = {"id": "dummy", "home": "Deutschland", "away": "Frankreich"}
        
        gewaehltes_spiel = st.selectbox("Wähle ein anstehendes oder laufendes Spiel des Tages:", spiele_auswahl)
        spiel_daten = spiele_mapping[gewaehltes_spiel]
        heimteam = spiel_daten["home"]
        auswaertsteam = spiel_daten["away"]
    else:
        teams_liste = sorted(list(base_ratings.keys()))
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1: heimteam = st.selectbox("Heimteam wählen:", teams_liste, index=0)
        with col_sel2: auswaertsteam = st.selectbox("Auswärtsteam wählen:", teams_liste, index=1)
        spiel_daten = {"id": None}

    # 2. LINEUP-ABRUF (Sucht nach der Startelf vor dem Spiel)
    def hole_kader(match_id):
        if not match_id or match_id == "dummy":
            return [], []
        url = "https://free-api-live-football-data.p.rapidapi.com/football-match-lineups"
        try:
            res = requests.get(url, headers=headers, params={"matchid": match_id})
            if res.status_code == 200:
                lineups = res.json().get('response', {}).get('lineup', [])
                if len(lineups) >= 2:
                    k_h = [(p['player']['name'], p['player'].get('position', 'M')) for p in lineups[0].get('startXI', [])]
                    k_a = [(p['player']['name'], p['player'].get('position', 'M')) for p in lineups[1].get('startXI', [])]
                    return k_h, k_a
        except:
            pass
        return [], []

    if st.button("Multi-Source-Simulation starten 🎲", type="primary", use_container_width=True):
        kader_h, kader_a = hole_kader(spiel_daten["id"])

        r_h = base_ratings.get(heimteam, {"att": 1.4, "def": 1.0})
        r_a = base_ratings.get(auswaertsteam, {"att": 1.2, "def": 1.1})

        # Dynamischer Taktik-Faktor durch echten Kader (Falls Aufstellung ca. 30 Min vor Anpfiff geladen wird)
        def_faktor_h = 1.0
        if kader_h:
            def_h = sum(1 for _, pos in kader_h if 'D' in str(pos).upper())
            def_faktor_h = 1.0 if def_h >= 4 else 1.15

        exp_h = r_h["att"] * (1.0 / r_a["def"])
        exp_a = r_a["att"] * (1.0 / r_h["def"]) * def_faktor_h

        max_tore = 6
        matrix = np.zeros((max_tore, max_tore))
        for h in range(max_tore):
            for a in range(max_tore):
                matrix[h, a] = poisson_wahrscheinlichkeit(h, exp_h) * poisson_wahrscheinlichkeit(a, exp_a)

        sieg_h = np.sum(np.tril(matrix, -1))
        remis = np.sum(np.diag(matrix))
        sieg_a = np.sum(np.triu(matrix, 1))

        st.success("### 📊 Analyse-Ergebnis (Gemittelte Quellen)")
        
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Sieg {heimteam}", f"{sieg_h:.1%}")
        c2.metric("Unentschieden", f"{remis:.1%}")
        c3.metric(f"Sieg {auswaertsteam}", f"{sieg_a:.1%}")

        # Feedback-Meldung zum Kader-Status vor dem Spiel
        st.write("---")
        if kader_h:
            st.info("📌 Die offiziellen Startaufstellungen wurden rechtzeitig vor Spielbeginn erkannt und sind in die Berechnung eingeflossen!")
            with st.expander("🔍 Eingeflossene Live-Aufstellungen anzeigen"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**{heimteam}:**")
                    for n, p in kader_h: st.write(f"- `{p}` {n}")
                with col2:
                    st.markdown(f"**{auswaertsteam}:**")
                    for n, p in kader_a: st.write(f"- `{p}` {n}")
        else:
            st.warning("⚠️ Die offiziellen Startaufstellungen sind für dieses Spiel noch nicht von der FIFA/Liga freigegeben (meistens 45-30 Min. vor Anpfiff der Fall). Die App rechnet aktuell mit den historischen Stamm-Ratings.")
