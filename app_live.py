import streamlit as st
import requests
import numpy as np
import math

# EIGENE POISSON-FUNKTION
def poisson_wahrscheinlichkeit(k, lam):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam**k * math.exp(-lam)) / math.factorial(k)

def prob_mindestens_tore(bereiche, lam):
    prob_weniger = sum(poisson_wahrscheinlichkeit(i, lam) for i in range(bereiche))
    return max(0.0, min(1.0, 1.0 - prob_weniger))

st.set_page_config(page_title="WM 2026 Live Expert Simulator", page_icon="⚡", layout="wide")

st.title("⚡ WM 2026 Live Expert Simulator")
st.markdown("Diese Version ist exakt auf deine **Free API Live Football Data** Schnittstelle optimiert.")

# API-Key Abfrage in der Sidebar
st.sidebar.header("🔑 API-Konfiguration")
api_key = st.sidebar.text_input("Gib deinen RapidAPI-Key ein:", type="password")

if not api_key:
    st.info("Bitte gib deinen RapidAPI-Key in der linken Sidebar ein, um die Live-Daten zu laden.")
else:
    # Header exakt nach deinen API-Vorgaben
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "free-api-live-football-data.p.rapidapi.com"
    }

    # 1. LIVE-SPIELE AUS DEINER API LADEN
    @st.cache_data(ttl=20) # Kurzer Cache für echte Live-Daten
    def hole_aktuelle_live_spiele():
        url = "https://free-api-live-football-data.p.rapidapi.com/football-current-live"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                # Deine API strukturiert die Daten oft in einem 'status' oder direkt im 'response' Objekt
                daten = response.json()
                return daten.get('response', {}).get('live', []), "OK"
            elif response.status_code == 403:
                return [], "Key oder Abo ungültig (403)"
            else:
                return [], f"Fehler-Status: {response.status_code}"
        except Exception as e:
            return [], str(e)

    with st.spinner("Lade aktuelle Live-Matches aus deiner API..."):
        spiele, api_status = hole_aktuelle_live_spiele()

    spiele_auswahl = []
    spiele_mapping = {}

    if api_status == "OK":
        st.sidebar.success("🌐 Erfolgreich mit deiner API verbunden!")
    else:
        st.error(f"⚠️ {api_status}. Überprüfe das Abo im RapidAPI Dashboard.")

    # Spiele verarbeiten (Deine API nutzt typischerweise 'home' und 'away' Namen direkt im Match-Objekt)
    if spiele:
        for s in spiele:
            try:
                match_id = s.get('id') or s.get('matchId')
                h_name = s['teams']['home']['name']
                a_name = s['teams']['away']['name']
                status = s.get('status', {}).get('type', 'LIVE')
                label = f"{h_name} vs. {a_name} ({status})"
                spiele_auswahl.append(label)
                spiele_mapping[label] = match_id
            except:
                pass

    # Unabhängiger Fallback
    if not spiele_auswahl:
        st.warning("Aktuell keine Live-Spiele in deiner API aktiv (oder Tageslimit erreicht). Test-Spiel ist aktiv.")
        spiele_auswahl = ["Test-Spiel: Deutschland vs. Frankreich"]

    gewaehltes_spiel = st.selectbox("Wähle ein Live-Spiel zur Analyse aus:", spiele_auswahl)

    # 2. AUFSTELLUNGEN AUS DEINER API ZIEHEN
    def hole_kader(match_id):
        url = "https://free-api-live-football-data.p.rapidapi.com/football-match-lineups"
        querystring = {"matchid": match_id}
        
        kader_heim = []
        kader_ausw = []
        
        try:
            response = requests.get(url, headers=headers, params=querystring)
            if response.status_code == 200:
                daten = response.json().get('response', {})
                # Struktur-Parsing für deine spezifische Lineup-API
                lineups = daten.get('lineup', [])
                if len(lineups) >= 2:
                    # Heimteam
                    for p in lineups[0].get('startXI', []):
                        kader_heim.append((p['player']['name'], p['player'].get('position', 'M')))
                    # Auswärtsteam
                    for p in lineups[1].get('startXI', []):
                        kader_ausw.append((p['player']['name'], p['player'].get('position', 'M')))
        except:
            pass
                        
        return kader_heim, kader_ausw

    # Simulation triggern
    if st.button("Live-Simulation starten 🚀", type="primary", use_container_width=True):
        match_id = spiele_mapping.get(gewaehltes_spiel, None)
        
        if match_id and api_status == "OK":
            with st.spinner("Analysiere die echten Kader deines ausgewählten Spiels..."):
                kader_h, kader_a = hole_kader(match_id)
        else:
            kader_h = [("Kimmich", "D"), ("Wirtz", "M"), ("Havertz", "F"), ("Tah", "D"), ("Andrich", "M"), ("Musiala", "M")]
            kader_a = [("Mbappé", "F"), ("Griezmann", "M"), ("Saliba", "D"), ("Kanté", "M"), ("Upamecano", "D")]

        if not kader_h and match_id:
            st.info("Aufstellungen für dieses Spiel noch nicht live übertragen. Nutze Standard-Teamgewichtung.")
            kader_h = [("Stammspieler Heim 1", "M"), ("Stammspieler Heim 2", "D")]
            kader_a = [("Stammspieler Auswärts 1", "M"), ("Stammspieler Auswärts 2", "D")]

        # AB HIER RECHNET DIE MATHEMATIK
        anzahl_verteidiger_heim = sum(1 for _, pos in kader_h if 'D' in str(pos).upper())
        anzahl_stuermer_heim = sum(1 for _, pos in kader_h if 'F' in str(pos).upper() or 'A' in str(pos).upper())
        anzahl_verteidiger_ausw = sum(1 for _, pos in kader_a if 'D' in str(pos).upper())
        anzahl_stuermer_ausw = sum(1 for _, pos in kader_a if 'F' in str(pos).upper() or 'A' in str(pos).upper())

        def_faktor_h = 1.0 if anzahl_verteidiger_heim >= 4 else 1.15
        att_faktor_h = 1.0 + (anzahl_stuermer_heim * 0.05)
        def_faktor_a = 1.0 if anzahl_verteidiger_ausw >= 4 else 1.15
        att_faktor_a = 1.0 + (anzahl_stuermer_ausw * 0.05)

        exp_h_ft = 1.4 * att_faktor_h * (1.0 / def_faktor_a)
        exp_a_ft = 1.2 * att_faktor_a * (1.0 / def_faktor_h)

        max_tore = 6
        matrix_ft = np.zeros((max_tore, max_tore))
        for hc in range(max_tore):
            for ac in range(max_tore):
                matrix_ft[hc, ac] = poisson_wahrscheinlichkeit(hc, exp_h_ft) * poisson_wahrscheinlichkeit(ac, exp_a_ft)

        ft_h_sieg = np.sum(np.tril(matrix_ft, -1))
        ft_remis = np.sum(np.diag(matrix_ft))
        ft_a_sieg = np.sum(np.triu(matrix_ft, 1))

        st.success("### 📊 Live-Kader-Analyse erfolgreich!")
        col_team_h, col_team_a = st.columns(2)
        with col_team_h:
            st.markdown(f"#### 🏠 Gefundene Aufstellung: Heim-Team")
            for name, pos in kader_h: st.write(f"- `{pos}` {name}")
        with col_team_a:
            st.markdown(f"#### 🚀 Gefundene Aufstellung: Auswärts-Team")
            for name, pos in kader_a: st.write(f"- `{pos}` {name}")

        st.write("---")
        st.subheader("🔮 Auswirkung auf die 90-Minuten-Tendenz")
        c1, c2, c3 = st.columns(3)
        c1.metric("Sieg Heim-Team", f"{ft_h_sieg:.1%}")
        c2.metric("Unentschieden (Remis)", f"{ft_remis:.1%}")
        c3.metric("Sieg Auswärts-Team", f"{ft_a_sieg:.1%}")
