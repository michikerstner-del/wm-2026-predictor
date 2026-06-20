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
    prob_weniger = sum(poisson_wahrscheinlichkeit(i, lam) for i in range(bereiche))
    return max(0.0, min(1.0, 1.0 - prob_weniger))

st.set_page_config(page_title="WM 2026 Ultimate Simulator", page_icon="🏆", layout="wide")

st.title("🏆 WM 2026 Ultimate Expert Simulator")
st.markdown("Das komplette Analyse-Paket inklusive Spieler-Karten und Handicap-Absicherungen.")

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

# Kader-Datenbank mit Gewichtung für Tore und Karten (Name, Tor-Gewicht, Karten-Gewicht)
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

    # Matrizen für exakte Ergebnisse und Tendenzen generieren
    max_tore = 6
    matrix_ft = np.zeros((max_tore, max_tore))
    matrix_hz1 = np.zeros((max_tore, max_tore))
    matrix_hz2 = np.zeros((max_tore, max_tore))
    
    for hc in range(max_tore):
        for ac in range(max_tore):
            matrix_ft[hc, ac] = poisson_wahrscheinlichkeit(hc, exp_h_ft) * poisson_wahrscheinlichkeit(ac, exp_a_ft)
            matrix_hz1[hc, ac] = poisson_wahrscheinlichkeit(hc, exp_h_hz1) * poisson_wahrscheinlichkeit(ac, exp_a_hz1)
            matrix_hz2[hc, ac] = poisson_wahrscheinlichkeit(hc, exp_h_hz2) * poisson_wahrscheinlichkeit(ac, exp_a_hz2)

    # Tendenzen Berechnen
    ft_h_sieg, ft_remis, ft_a_sieg = np.sum(np.tril(matrix_ft, -1)), np.sum(np.diag(matrix_ft)), np.sum(np.triu(matrix_ft, 1))
    hz1_h_sieg, hz1_remis, hz1_a_sieg = np.sum(np.tril(matrix_hz1, -1)), np.sum(np.diag(matrix_hz1)), np.sum(np.triu(matrix_hz1, 1))
    hz2_h_sieg, hz2_remis, hz2_a_sieg = np.sum(np.tril(matrix_hz2, -1)), np.sum(np.diag(matrix_hz2)), np.sum(np.triu(matrix_hz2, 1))

    # Exakte Tipps
    ft_h_tipp, ft_a_tipp = np.unravel_index(matrix_ft.argmax(), matrix_ft.shape)
    hz1_h_tipp, hz1_a_tipp = np.unravel_index(matrix_hz1.argmax(), matrix_hz1.shape)
    hz2_h_tipp, hz2_a_tipp = np.unravel_index(matrix_hz2.argmax(), matrix_hz2.shape)

    # Karten-Erwartungswerte
    exp_karten_h = h['cards'] * 2.0
    exp_karten_a = a['cards'] * 2.2

    # HANDICAP-ABSCHERUNG RECHNEN (Verliert nicht mit mehr als X Toren Unterschied)
    def berechne_handicap_safe(matrix, fuer_heim=True):
        hc_ergebnisse = {}
        for tore_abstand in range(1, 6): # 1 bis 5 Tore Abstand
            wahrscheinlichkeit = 0.0
            for hc in range(max_tore):
                for ac in range(max_tore):
                    if fuer_heim:
                        # Heim-Sieg, Remis ODER verliert, aber Abstand ist kleiner als das Handicap
                        if hc >= ac or (ac - hc) < tore_abstand:
                            wahrscheinlichkeit += matrix[hc, ac]
                    else:
                        # Auswärts-Sieg, Remis ODER verliert, aber Abstand ist kleiner als das Handicap
                        if ac >= hc or (hc - ac) < tore_abstand:
                            wahrscheinlichkeit += matrix[hc, ac]
            hc_ergebnisse[tore_abstand] = wahrscheinlichkeit
        return hc_ergebnisse

    hc_heim = berechne_handicap_safe(matrix_ft, fuer_heim=True)
    hc_ausw = berechne_handicap_safe(matrix_ft, fuer_heim=False)

    st.success("### 📊 Ultimative Simulationsergebnisse")
    
    # TABELLEN-STRUKTUR
    tab_gesamt, tab_heim, tab_auswaerts = st.tabs(["🌍 Gesamtspiel-Märkte", f"🏠 {heim} (Heim)", f"🚀 {auswaerts} (Auswärts)"])
    
    with tab_gesamt:
        st.subheader("⚽ Gesamtspiel (90 Min) Tendenz & Ergebnis")
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Sieg {heim} (FT)", f"{ft_h_sieg:.1%}")
        c2.metric("Unentschieden (FT)", f"{ft_remis:.1%}")
        c3.metric(f"Sieg {auswaerts} (FT)", f"{ft_a_sieg:.1%}")
        st.markdown(f"🎯 **Wahrscheinlichstes Endergebnis:** {ft_h_tipp} : {ft_a_tipp} (Chance: {matrix_ft[ft_h_tipp, ft_a_tipp]:.1%})")
        
        st.write("---")

        st.subheader("⏱ Halbzeit-Märkte im Vergleich")
        col_hz1, col_hz2 = st.columns(2)
        with col_hz1:
            st.markdown("#### **1. Halbzeit**")
            st.write(f"- 🏠 Führung {heim}: **{hz1_h_sieg:.1%}** | 🤝 Remis: **{hz1_remis:.1%}** | 🚀 Führung {auswaerts}: **{hz1_a_sieg:.1%}**")
            st.markdown(f"🎯 **Exakter HZ1-Tipp:** {hz1_h_tipp} : {hz1_a_tipp} (Chance: {matrix_hz1[hz1_h_tipp, hz1_a_tipp]:.1%})")
        with col_hz2:
            st.markdown("#### **2. Halbzeit (separat)**")
            st.write(f"- 🏠 Sieg {heim}: **{hz2_h_sieg:.1%}** | 🤝 Remis: **{hz2_remis:.1%}** | 🚀 Sieg {auswaerts}: **{hz2_a_sieg:.1%}**")
            st.markdown(f"🎯 **Exakter HZ2-Tipp:** {hz2_h_tipp} : {hz2_a_tipp} (Chance: {matrix_hz2[hz2_h_tipp, hz2_a_tipp]:.1%})")
            
        st.write("---")
            
        st.subheader("⚽ Tor-Stufen pro Halbzeit (Gesamtspiel)")
        col_z1, col_z2 = st.columns(2)
        with col_z1:
            st.markdown("**1. Halbzeit - Tore Gesamt**")
            st.write(f"- Mindestens 1+ Tore: **{prob_mindestens_tore(1, exp_total_hz1):.1%}** | 2+ Tore: **{prob_mindestens_tore(2, exp_total_hz1):.1%}** | 3+ Tore: **{prob_mindestens_tore(3, exp_total_hz1):.1%}**")
        with col_z2:
            st.markdown("**2. Halbzeit - Tore Gesamt**")
            st.write(f"- Mindestens 1+ Tore: **{prob_mindestens_tore(1, exp_total_hz2):.1%}** | 2+ Tore: **{prob_mindestens_tore(2, exp_total_hz2):.1%}** | 3+ Tore: **{prob_mindestens_tore(3, exp_total_hz2):.1%}**")

    def generiere_team_ansicht(team_name, exp_hz1, exp_hz2, corners, cards, exp_cards_team, hc_daten):
        # 1. TOR-STUFEN
        st.subheader(f"⚽ Tor-Stufen für {team_name}")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**1. Halbzeit**")
            st.write(f"- 1+ Teamtor: **{prob_mindestens_tore(1, exp_hz1):.1%}** | 2+ Teamtore: **{prob_mindestens_tore(2, exp_hz1):.1%}**")
        with c2:
            st.markdown("**2. Halbzeit**")
            st.write(f"- 1+ Teamtor: **{prob_mindestens_tore(1, exp_hz2):.1%}** | 2+ Teamtore: **{prob_mindestens_tore(2, exp_hz2):.1%}**")
            
        # 2. HANDICAP-ABSICHERUNG
        st.subheader("🛡 Handicap-Absicherung")
        st.write(f"- Verliert nicht mit mehr als **1 Tor** Abstand: **{hc_daten[1]:.1%}**")
        st.write(f"- Verliert nicht mit mehr als **2 Toren** Abstand: **{hc_daten[2]:.1%}**")
        st.write(f"- Verliert nicht mit mehr als **3 Toren** Abstand: **{hc_daten[3]:.1%}**")
        st.write(f"- Verliert nicht mit mehr als **4 Toren** Abstand: **{hc_daten[4]:.1%}**")
        st.write(f"- Verliert nicht mit mehr als **5 Toren** Abstand: **{hc_daten[5]:.1%}**")

        # 3. SPIELER STATS (TORE UND KARTEN)
        st.subheader("🎯 Spieler-Spezialmärkte (Tore & Karten)")
        kader = kader_daten.get(team_name, [
            ('Abwehrchef (Nr. 4)', 0.03, 0.28), ('Aggressive-Sechser', 0.05, 0.35),
            ('Top-Stürmer (Nr. 9)', 0.35, 0.05), ('Flügelstürmer A', 0.22, 0.10)
        ])
        
        col_ts1, col_ts2 = st.columns(2)
        with col_ts1:
            st.markdown("**Torschützen (Anytime):**")
            for spieler, t_anteil, _ in kader:
                prob_tor = 1 - math.exp(-((exp_hz1 + exp_hz2) * t_anteil))
                st.write(f"- {spieler}: **{prob_tor:.1%}**")
        with col_ts2:
            st.markdown("**Erhält eine Karte (Anytime Card):**")
            for spieler, _, k_anteil in kader:
                # Nutzt die Karten-Erwartung des Teams, gewichtet nach Spieler-Aggressivität
                prob_karte = 1 - math.exp(-(exp_cards_team * k_anteil))
                st.write(f"- {spieler}: **{prob_karte:.1%}**")

        st.subheader("🏳️ und 🟨 Team-Eckwerte")
        st.write(f"- Erwartete Ecken: **{corners:.1f}** | Erwartete Karten: **{cards:.1f}**")

    with tab_heim:
        generiere_team_ansicht(heim, exp_h_hz1, exp_h_hz2, h['corners'] * 4.8, h['cards'] * 2.0, exp_karten_h, hc_heim)
        
    with tab_auswaerts:
        generiere_team_ansicht(auswaerts, exp_a_hz1, exp_a_hz2, a['corners'] * 3.7, a['cards'] * 2.2, exp_karten_a, hc_ausw)
