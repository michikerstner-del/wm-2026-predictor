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
st.markdown("Das vollendete Analyse-Paket powered by Live-API-Kaderdaten und exklusivem WM-Filter!")

# Sidebar für API-Konfiguration
st.sidebar.header("🔑 API-Konfiguration")
api_key = st.sidebar.text_input("Gib deinen RapidAPI-Key ein:", type="password")

# --- HISTORISCHE BASIS-RATINGS (Aus deiner Grund-App) ---
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

# Kader-Datenbank mit Gewichtung für Tore und Karten (Aus deiner Grund-App)
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
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "free-api-live-football-data.p.rapidapi.com"
    }

    # 1. SPIELE LADEN, FILTERN & SORTIEREN (Erweitert auf 3 Tage)
    @st.cache_data(ttl=30)
    def hole_sortierte_wm_spiele():
        url = "https://free-api-live-football-data.p.rapidapi.com/football-get-matches-by-date"
        wm_spiele = []
        
        # Schleife über 3 Tage: heute, morgen, übermorgen
        for tag_offset in range(3):
            datum = (datetime.date.today() + datetime.timedelta(days=tag_offset)).strftime('%Y%m%d')
            try:
                response = requests.get(url, headers=headers, params={"date": datum})
                if response.status_code == 200:
                    raw_data = response.json()
                    alle_spiele = []
                    
                    for key in ['response', 'data', 'matches']:
                        if key in raw_data and raw_data[key]:
                            if isinstance(raw_data[key], dict) and 'matches' in raw_data[key]:
                                alle_spiele = raw_data[key]['matches']
                            elif isinstance(raw_data[key], list):
                                alle_spiele = raw_data[key]
                    
                    if not alle_spiele and isinstance(raw_data, list):
                        alle_spiele = raw_data

                    for s in alle_spiele:
                        try:
                            liga_name = str(s.get('league', {}).get('name', s.get('leagueName', ''))).lower()
                            if 'world cup' in liga_name or 'wm' in liga_name or any(t in str(s) for t in ["Netherlands", "Sweden", "Germany", "USA", "Australia", "Ivory Coast"]):
                                match_id = s.get('id') or s.get('matchId')
                                teams_obj = s.get('teams', s)
                                h_name = teams_obj.get('home', {}).get('name', teams_obj.get('homeName'))
                                a_name = teams_obj.get('away', {}).get('name', teams_obj.get('awayName'))
                                status_obj = s.get('status', {})
                                time_str = s.get('time', status_obj.get('statusStr', 'Anstehend'))
                                
                                wm_spiele.append({
                                    "label": f"🕒 [{datum}] {time_str} | {h_name} vs. {a_name}",
                                    "id": match_id, "home": h_name, "away": a_name, "time": time_str
                                })
                        except: pass
            except: pass
        
        wm_spiele.sort(key=lambda x: x['time'])
        return wm_spiele

    with st.spinner("Filtere exklusive WM-Spiele (3-Tage-Vorschau)..."):
        spiele_liste = hole_sortierte_wm_spiele()

    spiele_auswahl = [s["label"] for s in spiele_liste]
    spiele_mapping = {s["label"]: s for s in spiele_liste}

    if not spiele_auswahl:
        st.warning("Keine offiziellen WM-Spiele gefunden. Test-Modus aktiv.")
        spiele_auswahl = ["🏆 [19:00] Deutschland vs. Elfenbeinküste (WM-Test)"]
        spiele_mapping["🏆 [19:00] Deutschland vs. Elfenbeinküste (WM-Test)"] = {"id": "dummy", "home": "Deutschland", "away": "Elfenbeinküste"}

    st.subheader("🔮 Berechne ein Spiel")
    gewaehltes_spiel = st.selectbox("Wähle das anstehende WM-Spiel aus:", spiele_auswahl)
    spiel_daten = spiele_mapping[gewaehltes_spiel]
    heim, auswaerts = spiel_daten["home"], spiel_daten["away"]

    # 2. LINEUP-ABRUF
    def hole_kader(match_id):
        if not match_id or match_id == "dummy":
            return [], []
        url = "https://free-api-live-football-data.p.rapidapi.com/football-match-lineups"
        try:
            res = requests.get(url, headers=headers, params={"matchid": match_id})
            if res.status_code == 200:
                raw_lineup = res.json()
                lineups = raw_lineup.get('response', raw_lineup.get('data', {})).get('lineup', [])
                if len(lineups) >= 2:
                    k_h = [(p['player']['name'], p['player'].get('position', 'M')) for p in lineups[0].get('startXI', [])]
                    k_a = [(p['player']['name'], p['player'].get('position', 'M')) for p in lineups[1].get('startXI', [])]
                    return k_h, k_a
        except:
            pass
        return [], []

    if st.button("Umfassende Expert-Simulation starten 🎲", type="primary", use_container_width=True):
        kader_h, kader_a = hole_kader(spiel_daten["id"])

        # Fallback auf Standardwerte falls Teams dynamisch aus der API kommen und fehlen
        h = base_ratings.get(heim, {'att': 1.4, 'def': 1.0, 'corners': 1.1, 'cards': 1.0})
        a = base_ratings.get(auswaerts, {'att': 1.2, 'def': 1.1, 'corners': 1.0, 'cards': 1.2})

        # --- DYNAMISCHER LIVE-TAKTIK-FAKTOR DURCH KADERABGLEICH ---
        def_faktor_h, att_faktor_h = 1.0, 1.0
        def_faktor_a, att_faktor_a = 1.0, 1.0
        
        if kader_h:
            def_h = sum(1 for _, pos in kader_h if 'D' in str(pos).upper())
            def_faktor_h = 1.0 if def_h >= 4 else 1.15
        if kader_a:
            def_a = sum(1 for _, pos in kader_a if 'D' in str(pos).upper())
            def_faktor_a = 1.0 if def_a >= 4 else 1.15

        # Erwartungswerte Tore Vollzeit (FT) mit Live-Anpassung
        exp_h_ft = h['att'] * a['def'] * 1.35 * att_faktor_h
        exp_a_ft = a['att'] * h['def'] * 1.35 * def_faktor_h
        exp_total_ft = exp_h_ft + exp_a_ft
        
        # Aufteilung der Hälften (1. HZ = 45%, 2. HZ = 55%)
        exp_h_hz1, exp_a_hz1 = exp_h_ft * 0.45, exp_a_ft * 0.45
        exp_total_hz1 = exp_h_hz1 + exp_a_hz1
        
        exp_h_hz2, exp_a_hz2 = exp_h_ft * 0.55, exp_a_ft * 0.55
        exp_total_hz2 = exp_h_hz2 + exp_a_hz2

        # Ecken-Erwartungswerte (90 Min)
        exp_ecken_h_ft = h['corners'] * 4.8
        exp_ecken_a_ft = a['corners'] * 3.7
        exp_ecken_total_ft = exp_ecken_h_ft + exp_ecken_a_ft

        # Ecken-Aufteilung nach Hälften (1. HZ = 47%, 2. HZ = 53%)
        exp_ecken_h_hz1, exp_ecken_h_hz2 = exp_ecken_h_ft * 0.47, exp_ecken_h_ft * 0.53
        exp_ecken_a_hz1, exp_ecken_a_hz2 = exp_ecken_a_ft * 0.47, exp_ecken_a_ft * 0.53
        exp_ecken_total_hz1 = exp_ecken_h_hz1 + exp_ecken_a_hz1
        exp_ecken_total_hz2 = exp_ecken_h_hz2 + exp_ecken_a_hz2

        # Matrizen generieren
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

        # Gesamttor-Wahrscheinlichkeiten (Über/Unter 1.5 - 4.5)
        ou_stats = {}
        for limit in [1.5, 2.5, 3.5, 4.5]:
            over_prob = sum(matrix_ft[hc, ac] for hc in range(max_tore) for ac in range(max_tore) if hc + ac > limit)
            ou_stats[limit] = {"over": over_prob, "under": 1.0 - over_prob}

        # Karten-Erwartungswerte
        exp_karten_h = h['cards'] * 2.0
        exp_karten_a = a['cards'] * 2.2

        # Handicap-Absicherung Logik
        def berechne_handicap_safe(matrix, fuer_heim=True):
            hc_ergebnisse = {}
            for tore_abstand in range(1, 6):
                wahrscheinlichkeit = 0.0
                for hc in range(max_tore):
                    for ac in range(max_tore):
                        if fuer_heim:
                            if hc >= ac or (ac - hc) < tore_abstand: wahrscheinlichkeit += matrix[hc, ac]
                        else:
                            if ac >= hc or (hc - ac) < tore_abstand: wahrscheinlichkeit += matrix[hc, ac]
                hc_ergebnisse[tore_abstand] = wahrscheinlichkeit
            return hc_ergebnisse

        hc_heim = berechne_handicap_safe(matrix_ft, fuer_heim=True)
        hc_ausw = berechne_handicap_safe(matrix_ft, fuer_heim=False)

        st.success("### 📊 Ultimative Simulationsergebnisse")
        
        # REITER-STRUKTUR WIEDER AKTIVIEREN
        tab_gesamt, tab_heim, tab_auswaerts = st.tabs(["🌍 Gesamtspiel-Märkte", f"🏠 {heim} (Heim)", f"🚀 {auswaerts} (Auswärts)"])
        
        with tab_gesamt:
            st.subheader("⚽ Gesamtspiel (90 Min) Tendenz & Ergebnis")
            c1, c2, c3 = st.columns(3)
            c1.metric(f"Sieg {heim} (FT)", f"{ft_h_sieg:.1%}")
            c2.metric("Unentschieden (FT)", f"{ft_remis:.1%}")
            c3.metric(f"Sieg {auswaerts} (FT)", f"{ft_a_sieg:.1%}")
            st.markdown(f"🎯 **Wahrscheinlichstes Endergebnis:** {ft_h_tipp} : {ft_a_tipp} (Chance: {matrix_ft[ft_h_tipp, ft_a_tipp]:.1%})")
            
            st.write("---")

            st.subheader("📊 Gesamttor-Wahrscheinlichkeiten (Über / Unter)")
            col_ou1, col_ou2, col_ou3, col_ou4 = st.columns(4)
            with col_ou1: st.metric("Tore über 1.5", f"{ou_stats[1.5]['over']:.1%}", f"Unter: {ou_stats[1.5]['under']:.1%}", delta_color="inverse")
            with col_ou2: st.metric("Tore über 2.5", f"{ou_stats[2.5]['over']:.1%}", f"Unter: {ou_stats[2.5]['under']:.1%}", delta_color="inverse")
            with col_ou3: st.metric("Tore über 3.5", f"{ou_stats[3.5]['over']:.1%}", f"Unter: {ou_stats[3.5]['under']:.1%}", delta_color="inverse")
            with col_ou4: st.metric("Tore über 4.5", f"{ou_stats[4.5]['over']:.1%}", f"Unter: {ou_stats[4.5]['under']:.1%}", delta_color="inverse")

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

            st.subheader("🏳️ Ecken-Märkte (Gesamtspiel)")
            col_ec1, col_ec2, col_ec3 = st.columns(3)
            col_ec1.metric("Erwartete Ecken 1. HZ", f"{exp_ecken_total_hz1:.1f}")
            col_ec2.metric("Erwartete Ecken 2. HZ", f"{exp_ecken_total_hz2:.1f}")
            col_ec3.metric("Gesamtecken (90 Min)", f"{exp_ecken_total_ft:.1f}")
                
            st.write("---")
                
            st.subheader("⚽ Tor-Stufen pro Halbzeit (Gesamtspiel)")
            col_z1, col_z2 = st.columns(2)
            with col_z1:
                st.markdown("**1. Halbzeit - Tore Gesamt**")
                st.write(f"- Mindestens 1+ Tore: **{prob_mindestens_tore(1, exp_total_hz1):.1%}** | 2+ Tore: **{prob_mindestens_tore(2, exp_total_hz1):.1%}** | 3+ Tore: **{prob_mindestens_tore(3, exp_total_hz1):.1%}**")
            with col_z2:
                st.markdown("**2. Halbzeit - Tore Gesamt**")
                st.write(f"- Mindestens 1+ Tore: **{prob_mindestens_tore(1, exp_total_hz2):.1%}** | 2+ Tore: **{prob_mindestens_tore(2, exp_total_hz2):.1%}** | 3+ Tore: **{prob_mindestens_tore(3, exp_total_hz2):.1%}**")

def generiere_team_ansicht(team_name, exp_ft, exp_hz1, exp_hz2, e_ft, e_hz1, e_hz2, exp_cards_team, hc_daten):
    # ... (der erste Teil der Funktion bleibt identisch wie vorher) ...

    st.subheader("🎯 Spieler-Spezialmärkte (Tore & Karten)")
    
    # Mapping der API-Namen auf deine Datenbank-Keys
    name_mapping = {
        "Germany": "Deutschland", "Ivory Coast": "Elfenbeinküste", "Netherlands": "Niederlande",
        "Argentina": "Argentinien", "France": "Frankreich", "Brazil": "Brasilien",
        "Spain": "Spanien", "England": "England", "Canada": "Kanada", "USA": "USA"
    }
    
    db_key = name_mapping.get(team_name, team_name)
    aktuelle_spieler = kader_daten.get(db_key, [])
    
    if not aktuelle_spieler:
        st.info(f"Für {team_name} (API: {team_name}) sind aktuell keine Spielerprofile hinterlegt.")
    else:
        col_ts1, col_ts2, col_ts3 = st.columns(3)
        with col_ts1:
            st.markdown("**Trifft in 1. HZ:**")
            for spieler, t_anteil, _ in aktuelle_spieler:
                prob_hz1 = 1 - math.exp(-(exp_hz1 * t_anteil))
                st.write(f"- {spieler}: **{prob_hz1:.1%}**")
        with col_ts2:
            st.markdown("**Trifft in 2. HZ:**")
            for spieler, t_anteil, _ in aktuelle_spieler:
                prob_hz2 = 1 - math.exp(-(exp_hz2 * t_anteil))
                st.write(f"- {spieler}: **{prob_hz2:.1%}**")
        with col_ts3:
            st.markdown("**Karte (Anytime):**")
            for spieler, _, k_anteil in aktuelle_spieler:
                prob_karte = 1 - math.exp(-(exp_cards_team * k_anteil))
                st.write(f"- {spieler}: **{prob_karte:.1%}**")

        # AUFRUF DER FUNKTIONEN (Muss auf der gleichen Ebene wie 'with tab_heim' stehen)
        
        with tab_heim:
            generiere_team_ansicht(heim, exp_h_ft, exp_h_hz1, exp_h_hz2, exp_ecken_h_ft, exp_ecken_h_hz1, exp_ecken_h_hz2, exp_karten_h, hc_heim)
            
        with tab_auswaerts:
            generiere_team_ansicht(auswaerts, exp_a_ft, exp_a_hz1, exp_a_hz2, exp_ecken_a_ft, exp_ecken_a_hz1, exp_ecken_a_hz2, exp_karten_a, hc_ausw)
