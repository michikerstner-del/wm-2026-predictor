import streamlit as st
import requests
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

    # 1. ERWEITERTER LIVE-ABRUF FÜR ALLE LIGEN HEUTE
    @st.cache_data(ttl=60) # 1 Minute Speicherzeit
    def hole_heutige_spiele():
        url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
        import datetime
        heute = datetime.date.today().strftime('%Y-%m-%d')
        
        # Holt ALLE Spiele des aktuellen Kalendertages weltweit
        querystring = {"date": heute} 
        try:
            response = requests.get(url, headers=headers, params=querystring)
            if response.status_code == 200:
                return response.json().get('response', [])
        except:
            return []
        return []

    with st.spinner("Lade alle weltweiten Live-Spiele für heute..."):
        spiele = hole_heutige_spiele()

    spiele_auswahl = []
    spiele_mapping = {}

    if spiele:
        for s in spiele:
            # Zeigt Liga, Teams und den aktuellen Status (z.B. NS = Not Started, FT = Finished, 1H = 1. Halbzeit)
            liga_name = s['league']['name']
            status = s['fixture']['status']['short']
            label = f"[{liga_name}] {s['teams']['home']['name']} vs. {s['teams']['away']['name']} ({status})"
            spiele_auswahl.append(label)
            spiele_mapping[label] = s['fixture']['id']

    # Falls die API gar nichts liefert oder dein Limit voll ist, greift der Dummy
    if not spiele_auswahl:
        st.warning("Keine Live-Spiele über die API gefunden. Test-Spiel wird als Fallback aktiviert.")
        spiele_auswahl = ["Test-Spiel: Deutschland vs. Frankreich"]

    gewaehltes_spiel = st.selectbox("Wähle ein Live-Spiel zur Analyse aus:", spiele_auswahl)

    # 2. STARTAUFSTELLUNGEN / KADER AUS DER API ZIEHEN
    def hole_kader(fixture_id):
        url = "https://api-football-v1.p.rapidapi.com/v3/fixtures/lineups"
        querystring = {"fixture": fixture_id}
        
        kader_heim = []
        kader_ausw = []
        
        try:
            response = requests.get(url, headers=headers, params=querystring)
            if response.status_code == 200:
                daten = response.json().get('response', [])
                if daten and len(daten) >= 2:
                    # Wenn verfügbar (ca. 45 Min vor Anpfiff), nimm die Startelf (startXI)
                    for p in daten[0]['startXI']:
                        kader_heim.append((p['player']['name'], p['player']['pos']))
                    for p in daten[1]['startXI']:
                        kader_ausw.append((p['player']['name'], p['player']['pos']))
                        
                    # Falls Startelf noch nicht freigegeben ist, nimm die gemeldeten Auswechselspieler/Kader (substitutes)
                    if not kader_heim:
                        for p in daten[0]['substitutes']:
                            kader_heim.append((p['player']['name'], p['player']['pos']))
                        for p in daten[1]['substitutes']:
                            kader_ausw.append((p['player']['name'], p['player']['pos']))
        except:
            pass
                        
        return kader_heim, kader_ausw

    # Simulation triggern
    if st.button("Live-Simulation starten 🚀", type="primary", use_container_width=True):
        fixture_id = spiele_mapping.get(gewaehltes_spiel, None)
        
        if fixture_id:
            with st.spinner("Analysiere die echten Kader für das gewählte Spiel..."):
                kader_h, kader_a = hole_kader(fixture_id)
        else:
            # Fallback Dummy-Kader falls Test-Spiel aktiv
            kader_h = [("Kimmich", "D"), ("Wirtz", "M"), ("Havertz", "F"), ("Tah", "D"), ("Andrich", "M"), ("Musiala", "M")]
            kader_a = [("Mbappé", "F"), ("Griezmann", "M"), ("Saliba", "D"), ("Kanté", "M"), ("Upamecano", "D")]

        # Falls für ein echtes Spiel die Kaderdaten extrem früh noch komplett leer sein sollten
        if not kader_h and fixture_id:
            st.info("Kaderlisten sind für dieses Spiel noch nicht in der API hinterlegt. Simuliere mit Standard-Teamgewichtung.")
            kader_h = [("Stammspieler Heim 1", "M"), ("Stammspieler Heim 2", "D")]
            kader_a = [("Stammspieler Auswärts 1", "M"), ("Stammspieler Auswärts 2", "D")]

        # TEAM-RATINGS & DYNAMISCHE STRATEGIE-ANALYSE
        anzahl_verteidiger_heim = sum(1 for _, pos in kader_h if pos == 'D')
        anzahl_stuermer_heim = sum(1 for _, pos in kader_h if pos == 'F')
        
        anzahl_verteidiger_ausw = sum(1 for _, pos in kader_a if pos == 'D')
        anzahl_stuermer_ausw = sum(1 for _, pos in kader_a if pos == 'F')

        # Taktischer Faktor basierend auf Aufstellung (Weniger als 4 Verteidiger schwächt die Abwehr = Faktor steigt)
        def_faktor_h = 1.0 if anzahl_verteidiger_heim >= 4 else 1.15
        att_faktor_h = 1.0 + (anzahl_stuermer_heim * 0.05)
        
        def_faktor_a = 1.0 if anzahl_verteidiger_ausw >= 4 else 1.15
        att_faktor_a = 1.0 + (anzahl_stuermer_ausw * 0.05)

        # Erwartungswerte Tore Vollzeit (FT)
        exp_h_ft = 1.4 * att_faktor_h * (1.0 / def_faktor_a)
        exp_a_ft = 1.2 * att_faktor_a * (1.0 / def_faktor_h)
        exp_total_ft = exp_h_ft + exp_a_ft

        # Hälften-Berechnung (1. HZ = 45%, 2. HZ = 55%)
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

        # VISUALISIERUNG DER ECHTEN LIVE-KADER
        st.success("### 📊 Live-Kader-Analyse erfolgreich!")
        
        col_team_h, col_team_a = st.columns(2)
        with col_team_h:
            st.markdown(f"#### 🏠 Gefundene Aufstellung: Heim-Team")
            st.caption(f"Verteidiger: {anzahl_verteidiger_heim} | Stürmer: {anzahl_stuermer_heim}")
            for name, pos in kader_h:
                st.write(f"- `{pos}` {name}")
                
        with col_team_a:
            st.markdown(f"#### 🚀 Gefundene Aufstellung: Auswärts-Team")
            st.caption(f"Verteidiger: {anzahl_verteidiger_ausw} | Stürmer: {anzahl_stuermer_ausw}")
            for name, pos in kader_a:
                st.write(f"- `{pos}` {name}")

        st.write("---")
        
        # PROGNOSE-ERGEBNISSE
        st.subheader("🔮 Auswirkung auf die 90-Minuten-Tendenz")
        c1, c2, c3 = st.columns(3)
        c1.metric("Sieg Heim-Team", f"{ft_h_sieg:.1%}")
        c2.metric("Unentschieden (Remis)", f"{ft_remis:.1%}")
        c3.metric("Sieg Auswärts-Team", f"{ft_a_sieg:.1%}")

        # SPIELER-STATISTIKEN BASIEREND AUF LIVE-POSITIONEN
        st.write("---")
        st.subheader("🎯 Dynamische Spieler-Kartenmärkte (Live-Vorschau)")
        col_s_h, col_s_a = st.columns(2)
        
        with col_s_h:
            st.markdown("**Karten-Wahrscheinlichkeit nach Position (Heim):**")
            for name, pos in kader_h:
                # Defensivspieler und Mittelfeld erhalten mathematisch eine höhere Last
                karten_last = 0.26 if pos in ['D', 'M'] else 0.07
                st.write(f"- {name} ({pos}): **{(1 - math.exp(-karten_last)):.1%}**")
                
        with col_s_a:
            st.markdown("**Karten-Wahrscheinlichkeit nach Position (Auswärts):**")
            for name, pos in kader_a:
                karten_last = 0.26 if pos in ['D', 'M'] else 0.07
                st.write(f"- {name} ({pos}): **{(1 - math.exp(-karten_last)):.1%}**")
