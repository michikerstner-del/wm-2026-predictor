import streamlit as st
import requests
import numpy as np
import math
import datetime

# --- MATHEMATISCHE GRUND-FUNKTIONEN ---
def poisson_wahrscheinlichkeit(k, lam):
    if lam <= 0: return 1.0 if k == 0 else 0.0
    return (lam**k * math.exp(-lam)) / math.factorial(k)

def prob_mindestens_tore(bereiche, lam):
    prob_weniger = sum(poisson_wahrscheinlichkeit(i, lam) for i in range(bereiche))
    return max(0.0, min(1.0, 1.0 - prob_weniger))

st.set_page_config(page_title="WM 2026 Ultimate Live Expert Simulator", page_icon="🏆", layout="wide")
st.title("🏆 WM 2026 Ultimate Live Expert Simulator")

# --- KONFIGURATION & DATENBANKEN ---
api_key = st.sidebar.text_input("Gib deinen RapidAPI-Key ein:", type="password")

base_ratings = {
    'Argentinien': {'att': 1.8, 'def': 0.7, 'corners': 1.2, 'cards': 1.1},
    'Frankreich': {'att': 1.8, 'def': 0.8, 'corners': 1.3, 'cards': 0.8},
    'Deutschland': {'att': 1.6, 'def': 1.0, 'corners': 1.2, 'cards': 0.8},
    'Elfenbeinküste': {'att': 1.2, 'def': 1.1, 'corners': 0.9, 'cards': 1.4},
}

kader_daten = {
    'Deutschland': [('Joshua Kimmich', 0.03, 0.22), ('Jonathan Tah', 0.04, 0.25), ('Antonio Rüdiger', 0.05, 0.28), ('Florian Wirtz', 0.25, 0.10), ('Jamal Musiala', 0.20, 0.07)],
    'Elfenbeinküste': [('Wilfried Singo', 0.03, 0.24), ('Evan Ndicka', 0.04, 0.26), ('Franck Kessié', 0.15, 0.30), ('Sébastien Haller', 0.30, 0.05), ('Simon Adingra', 0.22, 0.08)]
}

if not api_key:
    st.info("Bitte gib deinen RapidAPI-Key in der Sidebar ein.")
else:
    headers = {"X-RapidAPI-Key": api_key, "X-RapidAPI-Host": "free-api-live-football-data.p.rapidapi.com"}

    @st.cache_data(ttl=300)
    def hole_sortierte_wm_spiele():
        wm_spiele = []
        for i in range(4):
            datum = (datetime.date.today() + datetime.timedelta(days=i)).strftime('%Y%m%d')
            try:
                res = requests.get("https://free-api-live-football-data.p.rapidapi.com/football-get-matches-by-date", headers=headers, params={"date": datum})
                if res.status_code == 200:
                    data = res.json().get('response', [])
                    for s in data:
                        h, a = s.get('teams', {}).get('home', {}).get('name'), s.get('teams', {}).get('away', {}).get('name')
                        if h and a: wm_spiele.append({"label": f"[{datum}] {h} vs {a}", "id": s.get('id'), "home": h, "away": a})
            except: pass
        return wm_spiele

    spiele_liste = hole_sortierte_wm_spiele()
    spiele_mapping = {s["label"]: s for s in spiele_liste}
    gewaehltes_spiel = st.selectbox("Wähle ein WM-Spiel:", list(spiele_mapping.keys()) or ["Test-Modus"])
    
    if st.button("Umfassende Expert-Simulation starten"):
        spiel = spiele_mapping.get(gewaehltes_spiel, {"id": "dummy", "home": "Deutschland", "away": "Elfenbeinküste"})
        heim, auswaerts = spiel['home'], spiel['away']
        
        # API Lineup Abruf
        kader_h, kader_a = [], []
        if spiel['id'] != "dummy":
            res = requests.get("https://free-api-live-football-data.p.rapidapi.com/football-match-lineups", headers=headers, params={"matchid": spiel['id']})
            if res.status_code == 200:
                data = res.json().get('response', [])
                if len(data) >= 2:
                    kader_h = [(p['player']['name'], 0.1, 0.1) for p in data[0].get('startXI', [])]
                    kader_a = [(p['player']['name'], 0.1, 0.1) for p in data[1].get('startXI', [])]

        # --- BERECHNUNGSLOGIK ---
        h, a = base_ratings.get(heim, {'att': 1.4, 'def': 1.0, 'corners': 1.1, 'cards': 1.0}), base_ratings.get(auswaerts, {'att': 1.2, 'def': 1.1, 'corners': 1.0, 'cards': 1.2})
        exp_h_ft = h['att'] * a['def'] * 1.35
        exp_a_ft = a['att'] * h['def'] * 1.35
        
        # Matrizen (Die fehlende Logik wiederhergestellt)
        matrix = np.zeros((6, 6))
        for i in range(6):
            for j in range(6):
                matrix[i, j] = poisson_wahrscheinlichkeit(i, exp_h_ft) * poisson_wahrscheinlichkeit(j, exp_a_ft)
        
        # Tabs
        tab1, tab2 = st.tabs(["🌍 Gesamtspiel", "🎯 Spieler & Kader"])
        
        with tab1:
            st.metric("Sieg Heim", f"{np.sum(np.tril(matrix, -1)):.1%}")
            st.metric("Unentschieden", f"{np.sum(np.diag(matrix)):.1%}")
            st.metric("Sieg Auswärts", f"{np.sum(np.triu(matrix, 1)):.1%}")
            
        with tab2:
            def zeige_kader(team, live_kader):
                st.subheader(f"Analyse für {team}")
                if live_kader:
                    st.success("Live-Daten aktiv!")
                    for name, _, _ in live_kader[:6]:
                        st.write(f"- {name}")
                else:
                    st.warning("Keine Live-Daten. Fallback auf Historie:")
                    for name, t_w, k_w in kader_daten.get(team, []):
                        st.write(f"- {name}: Tor-Ch. {1-math.exp(-(exp_h_ft*0.5*t_w)):.1%}")
            
            col1, col2 = st.columns(2)
            with col1: zeige_kader(heim, kader_h)
            with col2: zeige_kader(auswaerts, kader_a)

        st.success("Simulation vollständig geladen.")
