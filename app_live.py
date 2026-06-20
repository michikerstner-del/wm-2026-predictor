import streamlit as st
import requests
import numpy as np
import math
import datetime

# --- MATHEMATISCHE GRUND-FUNKTIONEN (POISSON) ---
def poisson_wahrscheinlichkeit(k, lam):
    if lam <= 0: return 1.0 if k == 0 else 0.0
    return (lam**k * math.exp(-lam)) / math.factorial(k)

def prob_mindestens_tore(bereiche, lam):
    prob_weniger = sum(poisson_wahrscheinlichkeit(i, lam) for i in range(bereiche))
    return max(0.0, min(1.0, 1.0 - prob_weniger))

st.set_page_config(page_title="WM 2026 Ultimate Live Expert Simulator", page_icon="🏆", layout="wide")
st.title("🏆 WM 2026 Ultimate Live Expert Simulator")
st.markdown("Das vollendete Analyse-Paket powered by Live-API-Kaderdaten und exklusivem WM-Filter!")

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
    st.info("Bitte gib deinen RapidAPI-Key in der linken Sidebar ein, um die Live-Daten freizuschalten.")
else:
    headers = {"X-RapidAPI-Key": api_key, "X-RapidAPI-Host": "free-api-live-football-data.p.rapidapi.com"}

    @st.cache_data(ttl=30)
    def hole_sortierte_wm_spiele():
        url = "https://free-api-live-football-data.p.rapidapi.com/football-get-matches-by-date"
        heute_str = datetime.date.today().strftime('%Y%m%d')
        try:
            response = requests.get(url, headers=headers, params={"date": heute_str})
            if response.status_code == 200:
                raw_data = response.json()
                alle_spiele = raw_data.get('response', raw_data.get('data', raw_data.get('matches', [])))
                wm_spiele = []
                for s in alle_spiele:
                    h_name = s.get('teams', {}).get('home', {}).get('name')
                    a_name = s.get('teams', {}).get('away', {}).get('name')
                    if h_name and a_name:
                        wm_spiele.append({"label": f"🕒 {h_name} vs. {a_name}", "id": s.get('id'), "home": h_name, "away": a_name})
                return wm_spiele
        except: pass
        return []

    spiele_liste = hole_sortierte_wm_spiele()
    spiele_mapping = {s["label"]: s for s in spiele_liste}
    gewaehltes_spiel = st.selectbox("Wähle das anstehende WM-Spiel aus:", list(spiele_mapping.keys()) or ["Keine Spiele verfügbar"])
    
    if gewaehltes_spiel != "Keine Spiele verfügbar" and st.button("Umfassende Expert-Simulation starten 🎲"):
        spiel_daten = spiele_mapping[gewaehltes_spiel]
        heim, auswaerts = spiel_daten["home"], spiel_daten["away"]

        # Kader abrufen
        def hole_kader(match_id):
            try:
                res = requests.get("https://free-api-live-football-data.p.rapidapi.com/football-match-lineups", headers=headers, params={"matchid": match_id})
                if res.status_code == 200:
                    data = res.json().get('response', {})
                    if data: return data[0].get('startXI', []), data[1].get('startXI', [])
            except: pass
            return [], []

        kader_h, kader_a = hole_kader(spiel_daten["id"])
        h = base_ratings.get(heim, {'att': 1.4, 'def': 1.0, 'corners': 1.1, 'cards': 1.0})
        a = base_ratings.get(auswaerts, {'att': 1.2, 'def': 1.1, 'corners': 1.0, 'cards': 1.2})
        
        exp_h_ft = h['att'] * a['def'] * 1.35
        exp_a_ft = a['att'] * h['def'] * 1.35
        exp_h_hz1, exp_h_hz2 = exp_h_ft * 0.45, exp_h_ft * 0.55
        exp_a_hz1, exp_a_hz2 = exp_a_ft * 0.45, exp_a_ft * 0.55
        exp_karten_h, exp_karten_a = h['cards'] * 2.0, a['cards'] * 2.2

        tab_gesamt, tab_heim, tab_auswaerts = st.tabs(["🌍 Gesamtspiel-Märkte", f"🏠 {heim}", f"🚀 {auswaerts}"])

        def generiere_spieler_ansicht(team_name, kader_live, exp_hz1, exp_hz2, exp_karten):
            st.subheader(f"🎯 Spieler-Spezialmärkte ({team_name})")
            # Falls Live-Kader existiert, nutze diesen, sonst Fallback
            if kader_live:
                st.info("Live-Kader Daten aktiv.")
                for p in kader_live[:8]: # Anzeige der ersten 8
                    name = p['player']['name']
                    # API-Daten Mapping (hier Standard-Gewichtung falls keine Live-Statistik vorhanden)
                    st.write(f"- {name}: Tor (HZ1) **{1-math.exp(-(exp_hz1*0.15)):.1%}** | Karte: **{1-math.exp(-(exp_karten*0.10)):.1%}**")
            else:
                st.warning("Kein Live-Kader verfügbar. Nutze statistische Standard-Werte:")
                for name, t_w, k_w in kader_daten.get(team_name, []):
                    st.write(f"- {name}: Tor (HZ1) **{1-math.exp(-(exp_hz1*t_w)):.1%}** | Karte: **{1-math.exp(-(exp_karten*k_w)):.1%}**")

        with tab_heim:
            generiere_spieler_ansicht(heim, kader_h, exp_h_hz1, exp_h_hz2, exp_karten_h)
        with tab_auswaerts:
            generiere_spieler_ansicht(auswaerts, kader_a, exp_a_hz1, exp_a_hz2, exp_karten_a)
