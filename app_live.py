import streamlit as st
import requests
import numpy as np
import math
import datetime

# --- MATHEMATISCHE GRUND-FUNKTIONEN (POISSON) ---
def poisson_wahrscheinlichkeit(k, lam):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam**k * math.exp(-lam)) / math.factorial(k)

def prob_mindestens_tore(bereiche, lam):
    prob_weniger = sum(poisson_wahrscheinlichkeit(i, lam) for i in range(bereiche))
    return max(0.0, min(1.0, 1.0 - prob_weniger))

st.set_page_config(page_title="WM 2026 Ultimate Live Expert Simulator", page_icon="🏆", layout="wide")

st.title("🏆 WM 2026 Ultimate Live Expert Simulator")
st.markdown("Das vollendete Analyse-Paket powered by Live-API-Kaderdaten (Zeitraum: Heute + 3 Tage)!")

# Sidebar für API-Konfiguration
st.sidebar.header("🔑 API-Konfiguration")
api_key = st.sidebar.text_input("Gib deinen RapidAPI-Key ein:", type="password")

# --- HISTORISCHE BASIS-RATINGS ---
base_ratings = {
    'Argentinien': {'att': 1.8, 'def': 0.7, 'corners': 1.2, 'cards': 1.1},
    'Frankreich': {'att': 1.8, 'def': 0.8, 'corners': 1.3, 'cards': 0.8},
    'Brasilien': {'att': 1.7, 'def': 0.8, 'corners': 1.2, 'cards': 1.2},
    'Spanien': {'att': 1.7, 'def': 0.9, 'corners': 1.4, 'cards': 0.7},
    'England': {'att': 1.7, 'def': 0.8, 'corners': 1.3, 'cards': 0.6},
    'Deutschland': {'att': 1.6, 'def': 1.0, 'corners': 1.2, 'cards': 0.8},
    'Niederlande': {'att': 1.5, 'def': 0.9, 'corners': 1.1, 'cards': 1.0},
    'Elfenbeinküste': {'att': 1.2, 'def': 1.1, 'corners': 0.9, 'cards': 1.4},
    'Kanada': {'att': 1.4, 'def': 1.0, 'corners': 1.0, 'cards': 1.1},
    'USA': {'att': 1.3, 'def': 1.0, 'corners': 1.1, 'cards': 0.9},
}

kader_daten = {
    'Deutschland': [
        ('Joshua Kimmich', 0.03, 0.22), ('Jonathan Tah', 0.04, 0.25), ('Antonio Rüdiger', 0.05, 0.28),
        ('Robert Andrich', 0.06, 0.35), ('Florian Wirtz', 0.25, 0.10), ('Kai Havertz', 0.22, 0.08),
        ('Jamal Musiala', 0.20, 0.07), ('Niclas Füllkrug', 0.18, 0.05)
    ],
    'Elfenbeinküste': [
        ('Wilfried Singo', 0.03, 0.24), ('Evan Ndicka', 0.04, 0.26), ('Eric Bailly', 0.02, 0.32),
        ('Franck Kessié', 0.15, 0.30), ('Seko Fofana', 0.10, 0.20), ('Sébastien Haller', 0.30, 0.05),
        ('Simon Adingra', 0.22, 0.08), ('Oumar Diakité', 0.18, 0.12)
    ]
}

if not api_key:
    st.info("Bitte gib deinen RapidAPI-Key in der linken Sidebar ein.")
else:
    headers = {"X-RapidAPI-Key": api_key, "X-RapidAPI-Host": "free-api-live-football-data.p.rapidapi.com"}

    @st.cache_data(ttl=300)
    def hole_sortierte_wm_spiele():
        url = "https://free-api-live-football-data.p.rapidapi.com/football-get-matches-by-date"
        # Schleife für Heute + 3 Tage
        wm_spiele = []
        for i in range(4):
            datum = (datetime.date.today() + datetime.timedelta(days=i)).strftime('%Y%m%d')
            try:
                response = requests.get(url, headers=headers, params={"date": datum})
                if response.status_code == 200:
                    raw_data = response.json()
                    liste = raw_data.get('response', raw_data.get('data', raw_data.get('matches', [])))
                    if isinstance(liste, list):
                        for s in liste:
                            liga = str(s.get('league', {}).get('name', '')).lower()
                            if 'world cup' in liga or 'wm' in liga or any(t in str(s) for t in ["Germany", "USA", "Ivory Coast"]):
                                match_id = s.get('id') or s.get('matchId')
                                h_name = s.get('teams', {}).get('home', {}).get('name', 'Home')
                                a_name = s.get('teams', {}).get('away', {}).get('name', 'Away')
                                time_str = s.get('time', 'Anstehend')
                                wm_spiele.append({
                                    "label": f"[{datum}] {time_str} - {h_name} vs. {a_name}",
                                    "id": match_id, "home": h_name, "away": a_name
                                })
            except: pass
        return sorted(wm_spiele, key=lambda x: x['label'])

    with st.spinner("Lade Spielplan für die nächsten 3 Tage..."):
        spiele_liste = hole_sortierte_wm_spiele()

    spiele_mapping = {s["label"]: s for s in spiele_liste}
    gewaehltes_spiel = st.selectbox("Wähle ein WM-Spiel:", list(spiele_mapping.keys()) or ["Keine Spiele verfügbar"])
    
    if gewaehltes_spiel != "Keine Spiele verfügbar" and st.button("Experten-Simulation starten 🎲"):
        spiel_daten = spiele_mapping[gewaehltes_spiel]
        # Restliche Logik bleibt unverändert...
        st.write(f"Analyse für: {spiel_daten['home']} vs {spiel_daten['away']}")
        # Hier fügst du deinen restlichen Berechnungs-Code ein (wurde aus Platzgründen hier gekürzt)
        st.warning("Berechnungslogik aktiv - füge hier deinen restlichen Code-Block ein.")
