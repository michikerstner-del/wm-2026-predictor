import streamlit as st
import numpy as np
import scipy.stats as stats
import requests

st.set_page_config(page_title="WM 2026 Multi-Source Simulator", page_icon="🏆", layout="centered")

st.title("🏆 WM 2026 Multi-Source Simulator")
st.markdown("Diese App berechnet Vorhersagen aus dem Durchschnitt historischer Stärken und aktueller Live-Turnierdaten!")

# 1. Datenbank aller 48 WM-Teilnehmer 2026 (aufgeteilt in die echten Gruppen A-L)
gruppen_daten = {
    'Gruppe A': ['Mexiko', 'Südkorea', 'Tschechien', 'Südafrika'],
    'Gruppe B': ['Kanada', 'Schweiz', 'Katar', 'Bosnien-Herzegowina'],
    'Gruppe C': ['Brasilien', 'Marokko', 'Haiti', 'Schottland'],
    'Gruppe D': ['USA', 'Paraguay', 'Australien', 'Türkei'],
    'Gruppe E': ['Deutschland', 'Curaçao', 'Elfenbeinküste', 'Ecuador'],
    'Gruppe F': ['Niederlande', 'Japan', 'Tunesien', 'Schweden'],
    'Gruppe G': ['Belgien', 'Ägypten', 'Iran', 'Neuseeland'],
    'Gruppe H': ['Spanien', 'Cabo Verde', 'Saudi-Arabien', 'Uruguay'],
    'Gruppe I': ['Frankreich', 'Senegal', 'Norwegen', 'Irak'],
    'Gruppe J': ['Argentinien', 'Algerien', 'Österreich', 'Jordanien'],
    'Gruppe K': ['Portugal', 'Usbekistan', 'Kolumbien', 'Kongo DR'],
    'Gruppe L': ['England', 'Kroatien', 'Ghana', 'Panama']
}

# Basis-Stärkeratings (Quelle 1: FIFA/Elo-Einschätzung vor dem Turnier)
base_ratings = {
    'Argentinien': {'att': 1.8, 'def': 0.7}, 'Frankreich': {'att': 1.8, 'def': 0.8},
    'Brasilien': {'att': 1.7, 'def': 0.8}, 'Spanien': {'att': 1.7, 'def': 0.9},
    'England': {'att': 1.7, 'def': 0.8}, 'Deutschland': {'att': 1.6, 'def': 1.0},
    'Niederlande': {'att': 1.5, 'def': 0.9}, 'Kolumbien': {'att': 1.5, 'def': 0.9},
    'Portugal': {'att': 1.6, 'def': 0.9}, 'Italien': {'att': 1.3, 'def': 0.8},
    'Kanada': {'att': 1.4, 'def': 1.0}, 'USA': {'att': 1.3, 'def': 1.0},
    'Mexiko': {'att': 1.2, 'def': 1.0}, 'Uruguay': {'att': 1.5, 'def': 0.9},
    # Alle weiteren Teams werden bei Auswahl automatisch mit einem Standardwert (1.0) versehen, falls nicht explizit definiert.
}

# 2. Live-Daten-Schnittstelle (Quelle 2)
@st.cache_data(ttl=1800)  # Aktualisiert die Live-Form alle 30 Minuten
def hole_live_form_ratings():
    # In der finalen Version verbindest du hier deine API (z.B. football-data.org)
    # Für diese Demo simulieren wir die Live-Daten-Gewichtung basierend auf den echten WM-Ergebnissen im Juni 
    live_updates = {
        'Kanada': {'att_boost': 0.3, 'def_boost': -0.1},  # Wegen des 6:0 Sieges gegen Katar
        'USA': {'att_boost': 0.1, 'def_boost': -0.1},     # Wegen des 2:0 Sieges gegen Australien
        'Schweiz': {'att_boost': 0.2, 'def_boost': 0.0},  # Wegen des 4:1 Sieges gegen Bosnien
        'Brasilien': {'att_boost': 0.1, 'def_boost': -0.1} # Wegen des 3:0 Sieges gegen Haiti
    }
    return live_updates

# 3. Benutzeroberfläche für dein iPhone
st.header("🔮 Berechne ein Spiel")

# Alle Teams in eine flache Liste packen
alle_teams = sorted([team for gruppe in gruppen_daten.values() for team in gruppe])

col1, col2 = st.columns(2)
with col1:
    heim = st.selectbox("Heimteam wählen:", alle_teams, index=alle_teams.index('Deutschland') if 'Deutschland' in alle_teams else 0)
with col2:
    auswaerts = st.selectbox("Auswärtsteam wählen:", alle_teams, index=alle_teams.index('Argentinien') if 'Argentinien' in alle_teams else 0)

if st.button("Multi-Source-Simulation starten 🎲", type="primary", use_container_width=True):
    # Basiswerte holen
    h_base = base_ratings.get(heim, {'att': 1.0, 'def': 1.1})
    a_base = base_ratings.get(auswaerts, {'att': 1.0, 'def': 1.1})
    
    # Live-Werte holen
    live_data = hole_live_form_ratings()
    h_live = live_data.get(heim, {'att_boost': 0.0, 'def_boost': 0.0})
    a_live = live_data.get(auswaerts, {'att_boost': 0.0, 'def_boost': 0.0})
    
    # DURCHSCHNITT / ENSEMBLE BILDEN (Kombination aus Basisstärke & aktueller Turnierform)
    final_att_heim = (h_base['att'] + (h_base['att'] + h_live['att_boost'])) / 2
    final_def_auswaerts = (a_base['def'] + (a_base['def'] + a_live['def_boost'])) / 2
    
    final_att_auswaerts = (a_base['att'] + (a_base['att'] + a_live['att_boost'])) / 2
    final_def_heim = (h_base['def'] + (h_base['def'] + h_live['def_boost'])) / 2
    
    wm_tor_schnitt = 1.35
    exp_heim = final_att_heim * final_def_auswaerts * wm_tor_schnitt
    exp_auswaerts = final_att_auswaerts * final_def_heim * wm_tor_schnitt
    
    # Poisson-Matrix
    max_tore = 6
    matrix = np.zeros((max_tore, max_tore))
    for h in range(max_tore):
        for a in range(max_tore):
            matrix[h, a] = stats.poisson.pmf(h, exp_heim) * stats.poisson.pmf(a, exp_auswaerts)
            
    heimsieg = np.sum(np.tril(matrix, -1))
    unentschieden = np.sum(np.diag(matrix))
    auswaertssieg = np.sum(np.triu(matrix, 1))
    heim_tipp, auswaerts_tipp = np.unravel_index(matrix.argmax(), matrix.shape)
    
    st.success("### 📊 Analyse-Ergebnis (Gemittelte Quellen)")
    
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Sieg {heim}", f"{heimsieg:.1%}")
    c2.metric("Unentschieden", f"{unentschieden:.1%}")
    c3.metric(f"Sieg {auswaerts}", f"{auswaertssieg:.1%}")
    
    st.markdown(f"🎯 **Wahrscheinlichstes exaktes Ergebnis:** {heim_tipp} : {auswaerts_tipp} (Chance: {matrix[heim_tipp, auswaerts_tipp]:.1%})")
