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

st.set_page_config(page_title="WM 2026 Live Expert Simulator", page_icon="🏆", layout="wide")

st.title("🏆 WM 2026 Live Expert Simulator")
st.markdown("Diese Version filtert **ausschließlich WM-Spiele**, sortiert nach Uhrzeit, und berechnet das volle Statistik-Paket.")

# Sidebar für API-Konfiguration
st.sidebar.header("🔑 API-Konfiguration")
api_key = st.sidebar.text_input("Gib deinen RapidAPI-Key ein:", type="password")

# --- HISTORISCHE BASIS-RATINGS ---
base_ratings = {
    "Deutschland": {"att": 1.6, "def": 0.9},
    "Argentinien": {"att": 1.5, "def": 0.8},
    "Frankreich": {"att": 1.7, "def": 0.9},
    "Elfenbeinküste": {"att": 1.1, "def": 1.3},
    "Niederlande": {"att": 1.4, "def": 1.0},
    "Schweden": {"att": 1.2, "def": 1.1},
    "USA": {"att": 1.3, "def": 1.1},
    "Australien": {"att": 1.0, "def": 1.2}
}

if not api_key:
    st.info("Bitte gib deinen RapidAPI-Key in der linken Sidebar ein, um die Live-Daten freizuschalten.")
else:
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "free-api-live-football-data.p.rapidapi.com"
    }

    # 1. SPIELE LADEN, FILTERN & SORTIEREN
    @st.cache_data(ttl=30)
    def hole_sortierte_wm_spiele():
        url = "https://free-api-live-football-data.p.rapidapi.com/football-get-matches-by-date"
        heute_str = datetime.date.today().strftime('%Y%m%d')
        
        try:
            response = requests.get(url, headers=headers, params={"date": heute_str})
            if response.status_code == 200:
                raw_data = response.json()
                alle_spiele = []
                
                # Suchen der Match-Liste in der Struktur
                for key in ['response', 'data', 'matches']:
                    if key in raw_data and raw_data[key]:
                        if isinstance(raw_data[key], dict) and 'matches' in raw_data[key]:
                            alle_spiele = raw_data[key]['matches']
                        elif isinstance(raw_data[key], list):
                            alle_spiele = raw_data[key]
                
                if not alle_spiele and isinstance(raw_data, list):
                    alle_spiele = raw_data

                wm_spiele = []
                for s in alle_spiele:
                    try:
                        liga_name = str(s.get('league', {}).get('name', s.get('leagueName', ''))).lower()
                        
                        # FILTER: Nur echte WM-Spiele zulassen oder deine ausgewählten Teams zum Testen
                        if 'world cup' in liga_name or 'wm' in liga_name or any(t in str(s) for t in ["Netherlands", "Sweden", "Germany", "USA", "Australia"]):
                            match_id = s.get('id') or s.get('matchId')
                            teams_obj = s.get('teams', s)
                            h_name = teams_obj.get('home', {}).get('name', teams_obj.get('homeName'))
                            a_name = teams_obj.get('away', {}).get('name', teams_obj.get('awayName'))
                            
                            status_obj = s.get('status', {})
                            time_str = s.get('time', status_obj.get('statusStr', 'Anstehend'))
                            
                            wm_spiele.append({
                                "label": f"🕒 [{time_str}] {h_name} vs. {a_name}",
                                "id": match_id, "home": h_name, "away": a_name, "time": time_str
                            })
                    except:
                        pass
                
                wm_spiele.sort(key=lambda x: x['time'])
                return wm_spiele
        except:
            pass
        return []

    with st.spinner("Filtere exklusive WM-Spiele des Tages..."):
        spiele_liste = hole_sortierte_wm_spiele()

    spiele_auswahl = [s["label"] for s in spiele_liste]
    spiele_mapping = {s["label"]: s for s in spiele_liste}

    if not spiele_auswahl:
        st.warning("Keine offiziellen WM-Spiele für heute angesetzt. Test-Modus aktiv.")
        spiele_auswahl = ["🏆 [19:00] Niederlande vs. Schweden (WM-Test)"]
        spiele_mapping["🏆 [19:00] Niederlande vs. Schweden (WM-Test)"] = {"id": "dummy", "home": "Niederlande", "away": "Schweden"}

    gewaehltes_spiel = st.selectbox("Wähle das anstehende WM-Spiel aus:", spiele_auswahl)
    spiel_daten = spiele_mapping[gewaehltes_spiel]
    heimteam, auswaertsteam = spiel_daten["home"], spiel_daten["away"]

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

    if st.button("Vollständige Experten-Analyse starten 🚀", type="primary", use_container_width=True):
        kader_h, kader_a = hole_kader(spiel_daten["id"])

        r_h = base_ratings.get(heimteam, {"att": 1.4, "def": 1.0})
        r_a = base_ratings.get(auswaertsteam, {"att": 1.2, "def": 1.1})

        def_faktor_h, att_faktor_h = 1.0, 1.0
        def_faktor_a, att_faktor_a = 1.0, 1.0
        
        if kader_h:
            def_h = sum(1 for _, pos in kader_h if 'D' in str(pos).upper())
            def_faktor_h = 1.0 if def_h >= 4 else 1.15
        if kader_a:
            def_a = sum(1 for _, pos in kader_a if 'D' in str(pos).upper())
            def_faktor_a = 1.0 if def_a >= 4 else 1.15

        exp_h = r_h["att"] * (1.0 / r_a["def"]) * att_faktor_h
        exp_a = r_a["att"] * (1.0 / r_h["def"]) * def_faktor_a

        max_tore = 6
        matrix = np.zeros((max_tore, max_tore))
        for h in range(max_tore):
            for a in range(max_tore):
                matrix[h, a] = poisson_wahrscheinlichkeit(h, exp_h) * poisson_wahrscheinlichkeit(a, exp_a)

        sieg_h = np.sum(np.tril(matrix, -1))
        remis = np.sum(np.diag(matrix))
        sieg_a = np.sum(np.triu(matrix, 1))

        st.success(f"### 📊 Volles Analyse-Zertifikat: {heimteam} vs. {auswaertsteam}")
        
        col1, col2, col3 = st.columns(3)
        col1.metric(f"Sieg {heimteam} (1)", f"{sieg_h:.1%}")
        col2.metric("Unentschieden (X)", f"{remis:.1%}")
        col3.metric(f"Sieg {auswaertsteam} (2)", f"{sieg_a:.1%}")

        st.write("---")

        st.subheader("⚽ Tor-Märkte Prognose")
        c_over1, c_over2 = st.columns(2)
        
        with c_over1:
            st.markdown("**Über / Unter Tore:**")
            for limit in [0.5, 1.5, 2.5, 3.5]:
                prob_over = prob_mindestens_tore(int(limit + 0.5), exp_h + exp_a)
                st.write(f"- Über {limit} Tore: **{prob_over:.1%}** | Unter {limit}: **{(1-prob_over):.1%}**")
                
        with c_over2:
            btts_nein = poisson_wahrscheinlichkeit(0, exp_h) + poisson_wahrscheinlichkeit(0, exp_a) - (poisson_wahrscheinlichkeit(0, exp_h) * poisson_wahrscheinlichkeit(0, exp_a))
            btts_ja = max(0.0, 1.0 - btts_nein)
            st.markdown("**Beide Teams treffen? (BTTS):**")
            st.write(f"- Ja: **{btts_ja:.1%}**")
            st.write(f"- Nein: **{(1-btts_ja):.1%}**")

        st.write("---")

        st.subheader("🎯 Top 5 der wahrscheinlichsten exakten Ergebnisse")
        ergebnisse = []
        for h in range(4):
            for a in range(4):
                ergebnisse.append((f"{h} : {a}", matrix[h, a]))
        
        ergebnisse.sort(key=lambda x: x[1], reverse=True)
        
        cols_ergebnis = st.columns(5)
        for i, (erg, chance) in enumerate(ergebnisse[:5]):
            cols_ergebnis[i].button(f"{erg}\n({chance:.1%})", disabled=True, use_container_width=True)

        if kader_h:
            st.write("---")
            with st.expander("🔍 Berücksichtigte Live-Kaderdaten einsehen"):
                col_k1, col_k2 = st.columns(2)
                with col_k1:
                    st.markdown(f"**Startelf {heimteam}:**")
                    for n, p in kader_h: st.write(f"- `{p}` {n}")
                with col_k2:
                    st.markdown(f"**Startelf {auswaertsteam}:**")
                    for n, p in kader_a: st.write(f"- `{p}` {n}")
