import streamlit as st
import numpy as np
import math

# EIGENE POISSON-FUNKTION
def poisson_wahrscheinlichkeit(k, lam):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam**k * math.exp(-lam)) / math.factorial(k)

# Hilfsfunktion für "Mindestens X Tore" (Kumulierte Poisson-Wahrscheinlichkeit)
def prob_mindestens_tore(bereiche, lam):
    # bereiche = 1, 2 oder 3 Tore
    prob_weniger = sum(poisson_wahrscheinlichkeit(i, lam) for i in range(bereiche))
    return max(0.0, min(1.0, 1.0 - prob_weniger))

st.set_page_config(page_title="WM 2026 Ultimate Simulator", page_icon="🏆", layout="wide")

st.title("🏆 WM 2026 Ultimate Expert Simulator")
st.markdown("Das komplette Analyse-Paket mit getrennten Team-Stats, Halbzeit-Tendenzen und HZ-Torschützen.")

# 1. Datenbank aller 48 WM-Teilnehmer 2026
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

torschuetzen_daten = {
    'Deutschland': [
        ('Florian Wirtz', 0.25), ('Kai Havertz', 0.22), ('Jamal Musiala', 0.20), 
        ('Niclas Füllkrug', 0.18), ('Leroy Sané', 0.10), ('Joshua Kimmich', 0.03)
    ],
    'Argentinien': [
        ('Lionel Messi', 0.30), ('Lautaro Martínez', 0.25), ('Julián Álvarez', 0.20), 
        ('Alexis Mac Allister', 0.12), ('Rodrigo de Paul', 0.05), ('Enzo Fernández', 0.04)
    ],
    'Frankreich': [
        ('Kylian Mbappé', 0.35), ('Olivier Giroud', 0.20), ('Antoine Griezmann', 0.18), 
        ('Ousmane Dembélé', 0.12), ('Marcus Thuram', 0.10), ('Theo Hernández', 0.03)
    ],
    'Elfenbeinküste': [
        ('Sébastien Haller', 0.30), ('Simon Adingra', 0.22), ('Oumar Diakité', 0.18), 
        ('Franck Kessié', 0.15), ('Seko Fofana', 0.10), ('Wilfried Singo', 0.03)
    ]
}

st.header("🔮 Berechne ein Spiel")
alle_teams = sorted([team for gruppe in gruppen_daten.values() for team in gruppe])

col1, col2 = st.columns(2)
with col1:
    heim = st.selectbox("Heimteam wählen:", alle_teams, index=alle_teams.index('Deutschland') if 'Deutschland' in alle_teams else 0)
with col2:
    auswaerts = st.selectbox("Auswärtsteam wählen:", alle_teams, index=alle_teams.index('Elfenbeinküste') if 'Elfenbeinküste' in alle_teams else 0)

if st.button("Umfassende Expert-Simulation starten 🎲", type="primary", use_container_width=True):
    h = base_ratings.get(heim, {'att': 1.0, 'def': 1.1, 'corners': 1.0, 'cards': 1.0})
    a = base_ratings.get(auswaerts, {'att': 1.0, 'def': 1.1, 'corners': 1.0, 'cards': 1.0})
    
    # Erwartungswerte Tore Vollzeit (FT)
    exp_h_ft = h['att'] * a['def'] * 1.35
    exp_a_ft = a['att'] * h['def'] * 1.35
    exp_total_ft = exp_h_ft + exp_a_ft
    
    # Aufteilung der Hälften (1. HZ = 45%, 2. HZ = 55%)
    exp_h_hz1 = exp_h_ft * 0.45
    exp_a_hz1 = exp_a_ft * 0.45
    exp_total_hz1 = exp_h_hz1 + exp_a_hz1
    
    exp_h_hz2 = exp_h_ft * 0.55
    exp_a_hz2 = exp_a_ft * 0.55
    exp_total_hz2 = exp_h_hz2 + exp_a_hz2

    # Matrizen für Tendenzen (1. HZ und 2. HZ separat)
    max_tore = 6
    matrix_hz1 = np.zeros((max_tore, max_tore))
    matrix_hz2 = np.zeros((max_tore, max_tore))
    for hc in range(max_tore):
        for ac in range(max_tore):
            matrix_hz1[hc, ac] = poisson_wahrscheinlichkeit(hc, exp_h_hz1) * poisson_wahrscheinlichkeit(ac, exp_a_hz1)
            matrix_hz2[hc, ac] = poisson_wahrscheinlichkeit(hc, exp_h_hz2) * poisson_wahrscheinlichkeit(ac, exp_a_hz2)

    # Tendenzen Berechnen
    hz1_h_sieg, hz1_remis, hz1_a_sieg = np.sum(np.tril(matrix_hz1, -1)), np.sum(np.diag(matrix_hz1)), np.sum(np.triu(matrix_hz1, 1))
    hz2_h_sieg, hz2_remis, hz2_a_sieg = np.sum(np.tril(matrix_hz2, -1)), np.sum(np.diag(matrix_hz2)), np.sum(np.triu(matrix_hz2, 1))

    st.success("### 📊 Ultimative Simulationsergebnisse")
    
    # TABELLEN-STRUKTUR FÜR DIE ÜBERSICHT
    tab_gesamt, tab_heim, tab_auswaerts = st.tabs(["🌍 Gesamtspiel-Märkte", f"🏠 {heim} (Heim)", f"🚀 {auswaerts} (Auswärts)"])
    
    with tab_gesamt:
        st.subheader("⏱ Halbzeit-Tendenzen (Wer gewinnt die HZ?)")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**1. Halbzeit Tendenz**")
            st.write(f"- Sieg {heim}: **{hz1_h_sieg:.1%}** | Remis: **{hz1_remis:.1%}** | Sieg {auswaerts}: **{hz1_a_sieg:.1%}**")
        with c2:
            st.markdown("**2. Halbzeit Tendenz (separat gewertet)**")
            st.write(f"- Sieg {heim}: **{hz2_h_sieg:.1%}** | Remis: **{hz2_remis:.1%}** | Sieg {auswaerts}: **{hz2_a_sieg:.1%}**")
            
        st.subheader("⚽ Tor-Stufen pro Halbzeit (Gesamtspiel)")
        col_z1, col_z2 = st.columns(2)
        with col_z1:
            st.markdown("**1. Halbzeit - Tore Gesamt**")
            st.write(f"- Mindestens 1+ Tore: **{prob_mindestens_tore(1, exp_total_hz1):.1%}**")
            st.write(f"- Mindestens 2+ Tore: **{prob_mindestens_tore(2, exp_total_hz1):.1%}**")
            st.write(f"- Mindestens 3+ Tore: **{prob_mindestens_tore(3, exp_total_hz1):.1%}**")
        with col_z2:
            st.markdown("**2. Halbzeit - Tore Gesamt**")
            st.write(f"- Mindestens 1+ Tore: **{prob_mindestens_tore(1, exp_total_hz2):.1%}**")
            st.write(f"- Mindestens 2+ Tore: **{prob_mindestens_tore(2, exp_total_hz2):.1%}**")
            st.write(f"- Mindestens 3+ Tore: **{prob_mindestens_tore(3, exp_total_hz2):.1%}**")

    def generiere_team_ansicht(team_name, exp_ft, exp_hz1, exp_hz2, corners, cards):
        st.subheader(f"⚽ Tor-Stufen für {team_name}")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**1. Halbzeit Teamtore**")
            st.write(f"- Mindestens 1+ Teamtor: **{prob_mindestens_tore(1, exp_hz1):.1%}**")
            st.write(f"- Mindestens 2+ Teamtore: **{prob_mindestens_tore(2, exp_hz1):.1%}**")
        with c2:
            st.markdown("**2. Halbzeit Teamtore**")
            st.write(f"- Mindestens 1+ Teamtor: **{prob_mindestens_tore(1, exp_hz2):.1%}**")
            st.write(f"- Mindestens 2+ Teamtore: **{prob_mindestens_tore(2, exp_hz2):.1%}**")
            
        st.subheader("🏳️ und 🟨 Standard-Stats")
        st.write(f"- Erwartete Ecken über 90 Min: **{corners:.1f}**")
        st.write(f"- Erwartete Gelbe Karten über 90 Min: **{cards:.1f}**")

        st.subheader("🎯 Torschützen nach Spielabschnitt")
        kader = torschuetzen_daten.get(team_name, [
            ('Top-Stürmer (Nr. 9)', 0.35), ('Flügelstürmer A', 0.22), 
            ('Flügelstürmer B', 0.18), ('Offensives Mittelfeld', 0.15)
        ])
        
        # Spalten für HZ1 und HZ2 Torschützen
        col_ts1, col_ts2 = st.columns(2)
        with col_ts1:
            st.markdown("**Trifft in der 1. Halbzeit:**")
            for spieler, anteil in kader:
                prob = 1 - math.exp(-(exp_hz1 * anteil))
                st.write(f"- {spieler}: **{prob:.1%}**")
        with col_ts2:
            st.markdown("**Trifft in der 2. Halbzeit:**")
            for spieler, anteil in kader:
                prob = 1 - math.exp(-(exp_hz2 * anteil))
                st.write(f"- {spieler}: **{prob:.1%}**")

    with tab_heim:
        generiere_team_ansicht(heim, exp_h_ft, exp_h_hz1, exp_h_hz2, h['corners'] * 4.8, h['cards'] * 2.0)
        
    with tab_auswaerts:
        generiere_team_ansicht(auswaerts, exp_a_ft, exp_a_hz1, exp_a_hz2, a['corners'] * 3.7, a['cards'] * 2.2)
