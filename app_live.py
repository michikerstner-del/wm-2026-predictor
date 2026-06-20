import streamlit as st
import requests
import numpy as np
import math

# POISSON-FUNKTIONEN
def poisson_wahrscheinlichkeit(k, lam):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam**k * math.exp(-lam)) / math.factorial(k)

def prob_mindestens_tore(bereiche, lam):
    prob_weniger = sum(poisson_wahrscheinlichkeit(i, lam) for i in range(bereiche))
    return max(0.0, min(1.0, 1.0 - prob_weniger))

st.set_page_config(page_title="WM 2026 Live Expert Simulator", page_icon="⚡", layout="wide")

st.title("⚡ WM 2026 Live Expert Simulator")
st.markdown("Diese Version zieht Echtzeit-Kader und Startaufstellungen über deine API-Football Schnittstelle.")

# API-Key Abfrage in der Sidebar (Sicher vor GitHub-Blicken)
st.sidebar.header("🔑 API-Konfiguration")
api_key = st.sidebar.text_input("Gib deinen RapidAPI-Key ein:", type="password")

if not api_key:
    st.info("Bitte gib deinen RapidAPI-Key in der linken Sidebar ein, um die Live-Daten zu laden.")
else:
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    # 1. LIVE-SPIELE DES TAGES LADEN (WM 2026 = League ID 1)
    # Für den Test laden wir hier standardmäßig alle Spiele von HEUTE
    @st.cache_data(ttl=60) # 1 Minute Cache, um dein API-Limit zu schonen
    def hole_heutige_spiele():
        url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
        # Wir nutzen das aktuelle Datum (2026)
        import datetime
        heute = datetime.date.today().strftime('%Y-%m-%d')
        
        # Parameter für Weltmeisterschaft (League 1) oder alle aktuellen Live-Spiele
        querystring = {"date": heute} 
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            return response.json().get('response', [])
        return []

    with st.spinner("Lade aktuelle Spiele des Tages..."):
        spiele = hole_heutige_spiele()

    if not spiele:
        st.warning("Keine aktuellen Spiele für heute in der API gefunden oder Limit erreicht. (WM-ID oder Datum prüfen)")
        # Fallback-Dummys, damit die App nicht abstürzt, wenn die API leer ist
        spiele_auswahl = ["Test-Spiel: Deutschland vs. Frankreich"]
    else:
        spiele_auswahl = []
        spiele_mapping = {}
        for s in spiele:
            label = f"{s['teams']['home']['name']} vs. {s['teams']['away']['name']} ({s['fixture']['status']['short']})"
            spiele_auswahl.append(label)
            spiele_mapping[label] = s['fixture']['id']

    gewaehltes_spiel = st.selectbox("Wähle ein Live-Spiel zur Analyse aus:", spiele_auswahl)

    # 2. STARTAUFSTELLUNGEN / KADER AUS DER API ZIEHEN
    def hole_kader(fixture_id):
        url = "https://api-football-v1.p.rapidapi.com/v3/fixtures/lineups"
        querystring = {"fixture": fixture_id}
        response = requests.get(url, headers=headers, params=querystring)
        
        kader_heim = []
        kader_ausw = []
        
        if response.status_code == 200:
            daten = response.json().get('response', [])
            if daten and len(daten) >= 2:
                # 15 Minuten vor Anpfiff ist 'startXI' gefüllt!
                for p in daten[0]['startXI']:
                    kader_heim.append((p['player']['name'], p['player']['pos']))
                for p in daten[1]['startXI']:
                    kader_ausw.append((p['player']['name'], p['player']['pos']))
                    
                # Falls Startelf noch nicht da ist, nimm die gemeldeten Spieler (Squad/Substitutes)
                if not kader_heim:
                    for p in daten[0]['substitutes']:
                        kader_heim.append((p['player']['name'], p['player']['pos']))
                    for p in daten[1]['substitutes']:
                        kader_ausw.append((p['player']['name'], p['player']['pos']))
                        
        return kader_heim, kader_ausw

    # Simulation triggern
    if st.button("Live-Simulation starten 🚀", type="primary", use_container_width=True):
        fixture_id = spiele_mapping.get(gewaehltes_spiel, None)
        
        if fixture_id:
            with st.spinner("Analysiere die echten Kader 15 Minuten vor Anpfiff..."):
                kader_h, kader_a = hole_kader(fixture_id)
        else:
            # Fallback Dummy-Kader falls Test-Spiel aktiv
            kader_h = [("Wirtz", "M"), ("Havertz", "F"), ("Tah", "D"), ("Andrich", "M")]
            kader_a = [("Mbappé", "F"), ("Griezmann", "M"), ("Saliba", "D"), ("Kanté", "M")]

        # TEAM-RATINGS (Theoretische Live-Zuweisung basierend auf den Aufstellungen)
        # Wenn defensive Spieler fehlen, verschieben wir hier die Werte dynamisch!
        anzahl_verteidiger_heim = sum(1 for _, pos in kader_h if pos == 'D')
        anzahl_stuermer_heim = sum(1 for _, pos in kader_h if pos == 'F')

        # DYNAMISCHER STRATEGIE-FAKTOR: Stehen z.B. weniger als 4 Verteidiger auf dem Platz, 
        # schwächt das die Abwehr theoretisch ab (+0.15 Tore für den Gegner)
        def_faktor_h = 1.0 if anzahl_verteidiger_heim >= 4 else 1.2
        att_faktor_h = 1.0 + (anzahl_stuermer_heim * 0.05)

        # Beispielwerte für die Simulation (analog zu deinen Ratings)
        exp_h_ft = 1.5 * att_faktor_h * 0.9  
        exp_a_ft = 1.2 * def_faktor_h
        exp_total_ft = exp_h_ft + exp_a_ft

        # Hälften-Berechnung (45% zu 55%)
        exp_h_hz1, exp_h_hz2 = exp_h_ft * 0.45, exp_h_ft * 0.55
        exp_a_hz1, exp_a_hz2 = exp_a_ft * 0.45, exp_a_ft * 0.55
        
        # EXAKTE MATHEMATISCHE MATRIZEN GENERIEREN
        max_tore = 6
        matrix_ft = np.zeros((max_tore, max_tore))
        for hc in range(max_tore):
            for ac in range(max_tore):
                matrix_ft[hc, ac] = poisson_wahrscheinlichkeit(hc, exp_h_ft) * poisson_wahrscheinlichkeit(ac, exp_a_ft)

        ft_h_sieg = np.sum(np.tril(matrix_ft, -1))
        ft_remis = np.sum(np.diag(matrix_ft))
        ft_a_sieg = np.sum(np.triu(matrix_ft, 1))

        # VISUALISIERUNG DER LIVE-KADER
        st.success("### 📊 Live-Kader-Analyse erfolgreich!")
        
        col_team_h, col_team_a = st.columns(2)
        with col_team_h:
            st.markdown(f"#### 🏠 Aufstellung Heim-Team (Live)")
            if kader_h:
                for name, pos in kader_h:
                    st.write(f"- `{pos}` {name}")
            else:
                st.write("Kader wird geladen, sobald von der FIFA freigegeben.")
                
        with col_team_a:
            st.markdown(f"#### 🚀 Aufstellung Auswärts-Team (Live)")
            if kader_a:
                for name, pos in kader_a:
                    st.write(f"- `{pos}` {name}")
            else:
                st.write("Kader wird geladen, sobald von der FIFA freigegeben.")

        st.write("---")
        st.subheader("🔮 Auswirkung auf die 90-Minuten-Tendenz")
        c1, c2, c3 = st.columns(3)
        c1.metric("Sieg Heim", f"{ft_h_sieg:.1%}")
        c2.metric("Unentschieden", f"{ft_remis:.1%}")
        c3.metric("Sieg Auswärts", f"{ft_a_sieg:.1%}")

        # SPIELER TORE UND KARTEN DYNAMISCH GEWICHTEN
        st.write("---")
        st.subheader("🎯 Dynamische Spieler-Märkte")
        col_s_h, col_s_a = st.columns(2)
        
        with col_s_h:
            st.markdown("**Heimteam - Karten-Risiko nach Position:**")
            for name, pos in kader_h:
                # Abwehr/Mittelfeld erhalten statistisch eine höhere Last
                karten_chance = 0.28 if pos in ['D', 'M'] else 0.08
                st.write(f"- {name} ({pos}): **{(1 - math.exp(-karten_chance)):.1%}**")
                
        with col_s_a:
            st.markdown("**Auswärtsteam - Karten-Risiko nach Position:**")
            for name, pos in kader_a:
                karten_chance = 0.28 if pos in ['D', 'M'] else 0.08
                st.write(f"- {name} ({pos}): **{(1 - math.exp(-karten_chance)):.1%}**")
