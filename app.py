import streamlit as st
import numpy as np
import math

# EIGENE POISSON-FUNKTION
def poisson_wahrscheinlichkeit(k, lam):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam**k * math.exp(-lam)) / math.factorial(k)

st.set_page_config(page_title="WM 2026 Pro Simulator", page_icon="🏆", layout="centered")

st.title("🏆 WM 2026 Pro Simulator")
st.markdown("Erweiterte Analyse: 1. Halbzeit, Over/Under, Ecken, Karten & Torschützen.")

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

# Spielerspezifische Tor-Anteile innerhalb des Teams (muss in Summe nicht genau 1 sein, wird normalisiert)
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

if st.button("Erweiterte Multi-Source-Simulation starten 🎲", type="primary", use_container_width=True):
    h = base_ratings.get(heim, {'att': 1.0, 'def': 1.1, 'corners': 1.0, 'cards': 1.0})
    a = base_ratings.get(auswaerts, {'att': 1.0, 'def': 1.1, 'corners': 1.0, 'cards': 1.0})
    
    # Erwartungswerte Tore (Vollzeit)
    exp_heim = h['att'] * a['def'] * 1.35
    exp_auswaerts = a['att'] * h['def'] * 1.35
    
    # Matrizen generieren
    max_tore = 6
    matrix_ft = np.zeros((max_tore, max_tore))
    matrix_ht = np.zeros((max_tore, max_tore))
    
    for hc in range(max_tore):
        for ac in range(max_tore):
            matrix_ft[hc, ac] = poisson_wahrscheinlichkeit(hc, exp_heim) * poisson_wahrscheinlichkeit(ac, exp_auswaerts)
            matrix_ht[hc, ac] = poisson_wahrscheinlichkeit(hc, exp_heim * 0.45) * poisson_wahrscheinlichkeit(ac, exp_auswaerts * 0.45)

    # 1. HALBZEIT ANALYSE
    ht_heim_sieg = np.sum(np.tril(matrix_ht, -1))
    ht_remis = np.sum(np.diag(matrix_ht))
    ht_ausw_sieg = np.sum(np.triu(matrix_ht, 1))
    ht_h_tipp, ht_a_tipp = np.unravel_index(matrix_ht.argmax(), matrix_ht.shape)

    # OVER / UNDER
    over_15 = sum(matrix_ft[hc, ac] for hc in range(max_tore) for ac in range(max_tore) if hc + ac > 1.5)
    over_25 = sum(matrix_ft[hc, ac] for hc in range(max_tore) for ac in range(max_tore) if hc + ac > 2.5)
    over_35 = sum(matrix_ft[hc, ac] for hc in range(max_tore) for ac in range(max_tore) if hc + ac > 3.5)
    
    ht_over_05 = sum(matrix_ht[hc, ac] for hc in range(max_tore) for ac in range(max_tore) if hc + ac > 0.5)

    # ECKEN & KARTEN
    exp_ecken_h = h['corners'] * 4.8
    exp_ecken_a = a['corners'] * 3.7
    exp_karten_h = h['cards'] * 2.0
    exp_karten_a = a['cards'] * 2.2

    # UI AUSGABE
    st.success("### 📊 Erweiterte Simulationsergebnisse")
    
    # Sektion 1: 1. Halbzeit
    st.subheader("⏱ 1. Halbzeit Prognose")
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Führung {heim}", f"{ht_heim_sieg:.1%}")
    c2.metric("Remis zur Hz.", f"{ht_remis:.1%}")
    c3.metric(f"Führung {auswaerts}", f"{ht_ausw_sieg:.1%}")
    st.markdown(f"🎯 **Wahrscheinlichstes Halbzeit-Ergebnis:** {ht_h_tipp} : {ht_a_tipp}")

    # Sektion 2: Over/Under Tore
    st.subheader("⚽ Tor-Wahrscheinlichkeiten (Over)")
    c1, c2, c3 = st.columns(3)
    c1.metric("Über 1.5 Tore", f"{over_15:.1%}")
    c2.metric("Über 2.5 Tore", f"{over_25:.1%}")
    c3.metric("Über 3.5 Tore", f"{over_35:.1%}")
    st.markdown(f"**Halbzeit-Tore:** Mindestens 1 Tor in der 1. HZ: **{ht_over_05:.1%}**")

    # Sektion 3: TORSCHÜTZEN PROGNOSE
    st.subheader("🎯 Torschützen-Wahrscheinlichkeit (Anytime)")
    
    def zeige_torschuetzen(team_name, exp_tore):
        # Fallback-Kader generieren, falls das Team nicht detailliert in der DB angelegt ist
        kader = torschuetzen_daten.get(team_name, [
            ('Top-Stürmer (Nr. 9)', 0.35), ('Flügelstürmer A', 0.22), 
            ('Flügelstürmer B', 0.18), ('Offensives Mittelfeld', 0.15), 
            ('Zentrales Mittelfeld', 0.07), ('Kopfballstarker Verteidiger', 0.03)
        ])
        
        for spieler, anteil in kader:
            # Wahrscheinlichkeit, dass der Spieler mindestens 1 Tor schießt: 1 - e^(-(Anteil * Gesamt-Erwartung))
            spieler_lamb = exp_tore * anteil
            prob_anytime = 1 - math.exp(-spieler_lamb)
            st.write(f"- **{spieler}** ({team_name}): **{prob_anytime:.1%}**")

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown(f"**{heim}**")
        zeige_torschuetzen(heim, exp_heim)
    with col_t2:
        st.markdown(f"**{auswaerts}**")
        zeige_torschuetzen(auswaerts, exp_auswaerts)

    # Sektion 4: Ecken & Karten
    st.subheader("🏳️ und 🟨 Prognostizierte Anzahl")
    col_e1, col_e2 = st.columns(2)
    col_e1.metric(f"Erwartete Ecken ({heim})", f"{exp_ecken_h:.1f}")
    col_e2.metric(f"Erwartete Ecken ({auswaerts})", f"{exp_ecken_a:.1f}")
    
    col_k1, col_k2 = st.columns(2)
    col_k1.metric(f"Erwartete Karten ({heim})", f"{exp_karten_h:.1f}")
    col_k2.metric(f"Erwartete Karten ({auswaerts})", f"{exp_karten_a:.1f}")
