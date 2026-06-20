import streamlit as st
import requests
import numpy as np
import math

# --- POISSON & STATISTIK FUNKTIONEN ---
def poisson_wahrscheinlichkeit(k, lam):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam**k * math.exp(-lam)) / math.factorial(k)

def prob_mindestens_tore(bereiche, lam):
    prob_weniger = sum(poisson_wahrscheinlichkeit(i, lam) for i in range(bereiche))
    return max(0.0, min(1.0, 1.0 - prob_weniger))

st.set_page_config(page_title="WM 2026 Multi-Source Live Simulator", page_icon="🏆", layout="wide")

st.title("🏆 WM 2026 Multi-Source Live Simulator")
st.markdown("Diese App berechnet Vorhersagen aus dem Durchschnitt historischer Stärken und aktuellen Live-Kaderdaten!")

# Sidebar für API-Konfiguration
st.sidebar.header("🔑 API-Konfiguration")
api_key = st.sidebar.text_input("Gib deinen RapidAPI-Key ein:", type="password")

# --- HISTORISCHE BASIS-RATINGS (Aus deiner Haupt-App) ---
base_ratings = {
    "Deutschland": {"att": 1.6, "def": 0.9},
    "Argentinien": {"att": 1.5, "def": 0.8},
    "Frankreich": {"att": 1.7, "def": 0.9},
    "Elfenbeinküste": {"att": 1.1, "def": 1.3},
    "Niederlande": {"att": 1.4, "def": 1.0},
    "Schweden": {"att": 1.2, "def": 1.1}
}

if not api_key:
    st.info("Bitte gib deinen RapidAPI-Key in der linken Sidebar ein, um Live-Daten freizuschalten.")
else:
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "free-api-live-football-data.p.rapidapi.com"
    }

    # 1. LIVE-SPIELE LADEN
    @st.cache_data(ttl=15)
    def hole_aktuelle_live_spiele():
        url = "https://free-api-live-football-data.p.rapidapi.com/football-current-live"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json().get('response', {}).get('live', []), "OK"
        except:
            pass
        return [], "Keine Verbindung"

    spiele, api_status = hole_aktuelle_live_spiele()
    spiele_auswahl = []
    spiele_mapping = {}

    if spiele:
        for s in spiele:
            try:
                match_id = s.get('id') or s.get('matchId')
                h_name = s['teams']['home']['name']
                a_name = s['teams']['away']['name']
                label = f"🔴 LIVE: {h_name} vs. {a_name}"
                spiele_auswahl.append(label)
                spiele_mapping[label] = {"id": match_id, "home": h_name, "away": a_name}
            except:
                pass

    st.subheader("🔮 Berechne ein Spiel")

    # Modus-Auswahl: Falls kein Spiel live ist, kannst du manuell wie gewohnt simulieren!
    modus = st.radio("Simulations-Modus wählen:", ["Manuelle Simulation (Historisch)", "Echtzeit Live-Kader Simulation (API)"])

    if modus == "Echtzeit Live-Kader Simulation (API)":
        if not spiele_auswahl:
            st.warning("Aktuell sind keine Live-Spiele in der API aktiv. Nutze den manuellen Modus oder teste mit dem Dummy:")
            spiele_auswahl = ["Test-Spiel: Deutschland vs. Frankreich"]
            spiele_mapping["Test-Spiel: Deutschland vs. Frankreich"] = {"id": "dummy", "home": "Deutschland", "away": "Frankreich"}
        
        gewaehltes_spiel = st.selectbox("Wähle ein aktives Live-Spiel:", spiele_auswahl)
        spiel_daten = spiele_mapping[gewaehltes_spiel]
        heimteam = spiel_daten["home"]
        auswaertsteam = spiel_daten["away"]
    else:
        # Klassische Auswahl aus deiner Haupt-App
        teams_liste = sorted(list(base_ratings.keys()))
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            heimteam = st.selectbox("Heimteam wählen:", teams_liste, index=0)
        with col_sel2:
            auswaertsteam = st.selectbox("Auswärtsteam wählen:", teams_liste, index=1)
        spiel_daten = {"id": None}

    # 2. LINEUP-ABRUF
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

        # Basis-Ratings holen (oder Standardwerte falls Team unbekannt in der API)
        r_h = base_ratings.get(heimteam, {"att": 1.3, "def": 1.0})
        r_a = base_ratings.get(auswaertsteam, {"att": 1.2, "def": 1.1})

        # Dynamischer Taktik-Faktor durch echten Kader (falls vorhanden)
        def_faktor_h = 1.0
        att_faktor_h = 1.0
        if kader_h:
            def_h = sum(1 for _, pos in kader_h if 'D' in str(pos).upper())
            def_faktor_h = 1.0 if def_h >= 4 else 1.15

        # Berechnung der Erwartungswerte (Poisson-Schnittstelle)
        exp_h = r_h["att"] * (1.0 / r_a["def"]) * att_faktor_h
        exp_a = r_a["att"] * (1.0 / r_h["def"]) * def_faktor_h

        # Matrix aufbauen
        max_tore = 6
        matrix = np.zeros((max_tore, max_tore))
        for h in range(max_tore):
            for a in range(max_tore):
                matrix[h, a] = poisson_wahrscheinlichkeit(h, exp_h) * poisson_wahrscheinlichkeit(a, exp_a)

        sieg_h = np.sum(np.tril(matrix, -1))
        remis = np.sum(np.diag(matrix))
        sieg_a = np.sum(np.triu(matrix, 1))

        # Bestimmung des wahrscheinlichsten exakten Ergebnisses
        h_max, a_max = np.unravel_index(np.argmax(matrix), matrix.shape)
        chance_max = matrix[h_max, a_max]

        # --- AUSGABE IM GEWOHNTEN DESIGN (Dein Bild 2) ---
        st.success("### 📊 Analyse-Ergebnis (Gemittelte Quellen)")
        
        st.markdown(f"Sieg {heimteam}")
        st.system_heading = False
        st.subheader(f"**{sieg_h:.1%}**")
        
        st.markdown("Unentschieden")
        st.subheader(f"**{remis:.1%}**")
        
        st.markdown(f"Sieg {auswaertsteam}")
        st.subheader(f"**{sieg_a:.1%}**")
        
        st.write("---")
        st.markdown(f"🎯 **Wahrscheinlichstes exaktes Ergebnis:** {h_max} : {a_max} (Chance: {chance_max:.1%})")

        # Falls echte Kader geladen wurden, zeigen wir sie diskret darunter an
        if kader_h:
            with st.expander("🔍 Eingeflossene Live-Aufstellungen anzeigen"):
                c1, c2 = st.columns(2)
                with c1:
                    st.bold(f"{heimteam}:")
                    for n, p in kader_h: st.write(f"- `{p}` {n}")
                with c2:
                    st.bold(f"{auswaertsteam}:")
                    for n, p in kader_a: st.write(f"- `{p}` {n}")
