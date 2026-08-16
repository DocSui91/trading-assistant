import os
import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timezone

st.set_page_config(page_title="Trading Assistant", page_icon="📈", layout="wide")

COMPANY_PROFILES = {
    "WCH": {
        "company":"Wacker Chemie AG",
        "sector":"Chemie / Spezialchemie",
        "summary":"Wacker Chemie ist ein deutscher Chemiekonzern mit Schwerpunkten in Silikonen, Polymeren, Biosolutions und hochreinem Polysilicium für Halbleiter- und Solar-Anwendungen.",
        "drivers":["Chemiezyklus","Energiepreise","Nachfrage aus Bau/Industrie","Halbleiter- und Solar-Nachfrage"],
        "risk":"zyklisch"
    },
    "HOOD": {
        "company":"Robinhood Markets",
        "sector":"Fintech / Brokerage",
        "summary":"Robinhood betreibt eine digitale Handelsplattform für Aktien, Optionen, Kryptowährungen und weitere Finanzprodukte, mit Fokus auf mobile Privatanleger.",
        "drivers":["Handelsaktivität","Krypto-Märkte","Zinsumfeld","Kundenzuwachs"],
        "risk":"hoch"
    },
    "NVDA": {
        "company":"NVIDIA",
        "sector":"Halbleiter / KI-Infrastruktur",
        "summary":"NVIDIA entwickelt Grafikprozessoren, KI-Beschleuniger, Rechenzentrumsplattformen und Software. Das Unternehmen ist ein zentraler Anbieter für moderne KI-Infrastruktur.",
        "drivers":["KI-Investitionen","Rechenzentren","Produktzyklen","Exportregeln"],
        "risk":"mittel-hoch"
    },
    "INTC": {
        "company":"Intel",
        "sector":"Halbleiter",
        "summary":"Intel entwickelt Prozessoren und Halbleiterlösungen und baut parallel sein Foundry-Geschäft aus, um auch Chips für externe Kunden zu fertigen.",
        "drivers":["PC-/Server-Nachfrage","Foundry-Ausbau","Kapitalbedarf","Wettbewerb"],
        "risk":"hoch"
    },
    "ENR": {
        "company":"Siemens Energy",
        "sector":"Energie / Infrastruktur",
        "summary":"Siemens Energy liefert Technik für Stromerzeugung, Netze und Energiewende. Zum Konzern gehört auch das Windenergiegeschäft Siemens Gamesa.",
        "drivers":["Netzausbau","Energiewende","Auftragseingang","Gamesa-Turnaround"],
        "risk":"mittel-hoch"
    },
    "QBTS": {
        "company":"D-Wave Quantum",
        "sector":"Quantencomputing",
        "summary":"D-Wave entwickelt Quantencomputing-Systeme und Software, mit Fokus auf Quantum Annealing und hybride Optimierungslösungen.",
        "drivers":["Kommerzielle Aufträge","Technologieakzeptanz","Cash-Burn","Quanten-Hype"],
        "risk":"sehr hoch"
    },
    "AMD": {
        "company":"Advanced Micro Devices",
        "sector":"Halbleiter / KI",
        "summary":"AMD entwickelt CPUs, GPUs und Rechenzentrumsbeschleuniger für PCs, Server, Gaming und KI-Anwendungen.",
        "drivers":["KI-Beschleuniger","Server-Marktanteile","PC-Zyklus","Wettbewerb"],
        "risk":"mittel-hoch"
    },
    "ASML": {
        "company":"ASML",
        "sector":"Halbleiterausrüstung",
        "summary":"ASML entwickelt Lithographiesysteme für die Halbleiterindustrie und ist insbesondere bei EUV-Anlagen technologisch führend.",
        "drivers":["Chip-Investitionen","EUV-Nachfrage","Exportrestriktionen","Auftragsbestand"],
        "risk":"mittel"
    },
}

STARTER_ASSETS = [
    {"isin":"DE000WCH8881","name":"Wacker Chemie","symbol":"WCH","exchange":"XETR","status":"Depot"},
    {"isin":"US7707001027","name":"Robinhood Markets","symbol":"HOOD","exchange":"NASDAQ","status":"Depot"},
    {"isin":"US67066G1040","name":"NVIDIA","symbol":"NVDA","exchange":"NASDAQ","status":"Depot"},
    {"isin":"US4581401001","name":"Intel","symbol":"INTC","exchange":"NASDAQ","status":"Depot"},
    {"isin":"DE000ENER6Y0","name":"Siemens Energy","symbol":"ENR","exchange":"XETR","status":"Depot"},
    {"isin":"US26740W1099","name":"D-Wave Quantum","symbol":"QBTS","exchange":"NYSE","status":"Depot"},
    {"isin":"US0079031078","name":"AMD","symbol":"AMD","exchange":"NASDAQ","status":"Watchlist"},
    {"isin":"NL0009805522","name":"ASML","symbol":"ASML","exchange":"NASDAQ","status":"Watchlist"},
]

STARTER_TURBOS = [
    {"isin":"DE000JY1GWX1","name":"Turbo 1","status":"Watchlist"},
    {"isin":"DE000HM4UQX4","name":"Turbo 2","status":"Watchlist"},
    {"isin":"DE000HM5ULR4","name":"Turbo 3","status":"Watchlist"},
    {"isin":"DE000HM5BPP9","name":"Turbo 4","status":"Watchlist"},
]

def secret(name):
    try:
        return st.secrets[name]
    except Exception:
        return os.getenv(name, "")

TD_KEY = secret("TWELVE_DATA_API_KEY")
MA_KEY = secret("MARKETAUX_API_KEY")

def td(endpoint, params):
    if not TD_KEY:
        return None, "TWELVE_DATA_API_KEY fehlt."
    p = dict(params)
    p["apikey"] = TD_KEY
    try:
        r = requests.get("https://api.twelvedata.com/" + endpoint, params=p, timeout=15)
        d = r.json()
        if r.status_code >= 400 or d.get("status") == "error":
            return None, d.get("message", f"HTTP {r.status_code}")
        return d, None
    except Exception as e:
        return None, str(e)

def marketaux(params):
    if not MA_KEY:
        return None, "MARKETAUX_API_KEY fehlt."
    p = dict(params)
    p["api_token"] = MA_KEY
    try:
        r = requests.get("https://api.marketaux.com/v1/news/all", params=p, timeout=15)
        d = r.json()
        if r.status_code >= 400 or d.get("error"):
            err = d.get("error")
            if isinstance(err, dict):
                err = err.get("message", str(err))
            return None, err or f"HTTP {r.status_code}"
        return d, None
    except Exception as e:
        return None, str(e)

def quote(asset):
    p = {"symbol": asset["symbol"]}
    if asset.get("exchange"):
        p["exchange"] = asset["exchange"]
    return td("quote", p)

def candles(asset):
    p = {"symbol": asset["symbol"], "interval":"1day", "outputsize":200, "order":"ASC"}
    if asset.get("exchange"):
        p["exchange"] = asset["exchange"]
    data, err = td("time_series", p)
    if err:
        return None, err
    df = pd.DataFrame(data.get("values", []))
    if df.empty:
        return None, "Keine Kursdaten."
    df["datetime"] = pd.to_datetime(df["datetime"])
    for c in ["open","high","low","close","volume"]:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.sort_values("datetime"), None

def technical(df):
    if len(df) < 50:
        return None
    close = df["close"]
    sma20 = close.rolling(20).mean()
    sma50 = close.rolling(50).mean()
    sma200 = close.rolling(200).mean()
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, pd.NA)
    rsi = float((100 - 100/(1+rs)).iloc[-1])
    last = float(close.iloc[-1])
    mom5 = float((last/close.iloc[-6]-1)*100)
    mom20 = float((last/close.iloc[-21]-1)*100)

    short = 50
    short += 15 if last > sma20.iloc[-1] else -10
    short += 15 if sma20.iloc[-1] > sma50.iloc[-1] else -10
    short += 10 if mom5 > 0 else -5
    short += 8 if 42 <= rsi <= 67 else (-10 if rsi >= 80 else -5 if rsi >= 73 else 3 if rsi <= 35 else 0)

    medium = 50
    medium += 15 if last > sma50.iloc[-1] else -10
    medium += 15 if len(df) >= 200 and last > sma200.iloc[-1] else 0
    medium += 10 if sma20.iloc[-1] > sma50.iloc[-1] else -8
    medium += 10 if mom20 > 0 else -5

    risk = 35
    if rsi >= 80:
        risk += 35
    elif rsi >= 73:
        risk += 20
    elif rsi <= 30:
        risk += 10
    risk += min(25, abs(mom5) * 2.2)
    risk = max(0, min(100, round(risk)))

    return {
        "short": max(0, min(100, round(short))),
        "medium": max(0, min(100, round(medium))),
        "rsi": rsi,
        "mom5": mom5,
        "mom20": mom20,
        "risk": risk,
    }

def news_for(symbol, limit=6):
    return marketaux({
        "symbols": symbol,
        "filter_entities": "true",
        "must_have_entities": "true",
        "language": "en",
        "limit": limit,
        "sort": "published_at",
        "sort_order": "desc",
    })

def sentiment_values(data):
    vals = []
    for article in (data or {}).get("data", []):
        for entity in article.get("entities", []):
            score = entity.get("sentiment_score")
            if score is not None:
                try:
                    vals.append(float(score))
                except Exception:
                    pass
    return vals

def news_metrics(data):
    vals = sentiment_values(data)
    sent = sum(vals)/len(vals) if vals else None
    count = len((data or {}).get("data", []))
    sentiment_score = 50 if sent is None else max(0, min(100, round(50 + sent*50)))
    activity_score = min(100, 25 + count*12)
    return sent, sentiment_score, activity_score, count

def compact_summary(article):
    text = (article.get("description") or article.get("title") or "").strip()
    text = " ".join(text.split())
    if len(text) > 300:
        text = text[:297].rsplit(" ",1)[0] + "..."
    return text or "Keine Kurzbeschreibung verfügbar."

def article_sentiment(article, symbol=None):
    vals=[]
    for entity in article.get("entities",[]):
        if symbol and entity.get("symbol") and entity.get("symbol") != symbol:
            continue
        s=entity.get("sentiment_score")
        if s is not None:
            try: vals.append(float(s))
            except Exception: pass
    if not vals:
        return None
    return sum(vals)/len(vals)

def news_tone(score):
    if score is None:
        return "⚪ neutral/unklar"
    if score >= 0.30:
        return "🟢 positiv"
    if score <= -0.30:
        return "🔴 negativ"
    return "🟡 gemischt/neutral"

def relevance_score(article, symbol=None):
    score = 4
    title=(article.get("title") or "").lower()
    desc=(article.get("description") or "").lower()
    combined=title+" "+desc

    strong_words = [
        "earnings","guidance","forecast","acquisition","merger","lawsuit","investigation",
        "approval","partnership","contract","order","recall","ceo","cfo","dividend",
        "buyback","offering","capital raise","export","ban","regulation","profit warning"
    ]
    for w in strong_words:
        if w in combined:
            score += 1

    sent = article_sentiment(article, symbol)
    if sent is not None and abs(sent) >= 0.55:
        score += 1

    if len(title) > 20:
        score += 1

    return max(1,min(10,score))

def profile_for(asset):
    return COMPANY_PROFILES.get(asset["symbol"],{
        "company":asset["name"],
        "sector":"Nicht hinterlegt",
        "summary":"Für diese neu hinzugefügte Aktie ist noch kein festes Unternehmensprofil hinterlegt.",
        "drivers":["Kursentwicklung","News","Branchenlage"],
        "risk":"nicht klassifiziert",
    })

def combined_score(tech, sentiment_score, activity_score):
    base = 0.42*tech["short"] + 0.30*tech["medium"] + 0.18*sentiment_score + 0.10*activity_score
    penalty = max(0, tech["risk"] - 70) * 0.22
    return max(0, min(100, round(base - penalty)))

def action_label(score, risk, rsi):
    if risk >= 80 and score >= 70:
        return "🟡 Starkes Signal, aber überhitzt – Rücksetzer abwarten"
    if score >= 82 and rsi < 73:
        return "🟢 Kaufzone / Aufstocken prüfen"
    if score >= 70:
        return "🟢 Einstieg beobachten"
    if score >= 55:
        return "🟡 Halten / abwarten"
    if score >= 40:
        return "🟠 Risiko erhöht – Position prüfen"
    return "🔴 Kein Einstieg / reduzieren"

def news_action(relevance, tone, status):
    if relevance >= 8 and tone == "negative":
        return "Position prüfen / Neueinstieg abwarten"
    if relevance >= 8 and tone == "positive":
        return "Kursreaktion beobachten / Einstieg prüfen"
    if status == "Depot":
        return "Keine Aktion ohne Bestätigung durch Kurs/Technik"
    return "Beobachten"

def tone_code(score):
    if score is None:
        return "neutral"
    if score >= 0.30:
        return "positive"
    if score <= -0.30:
        return "negative"
    return "neutral"

if "assets" not in st.session_state:
    st.session_state.assets = [x.copy() for x in STARTER_ASSETS]
if "turbos" not in st.session_state:
    st.session_state.turbos = [x.copy() for x in STARTER_TURBOS]

st.title("📈 Trading Assistant")
st.caption("Version 2.2 • Technik + Unternehmensprofile + News Center + Hype Radar")

with st.sidebar:
    st.header("⚙️ Datenquellen")
    st.success("Twelve Data verbunden") if TD_KEY else st.error("Twelve Data fehlt")
    st.success("Marketaux verbunden") if MA_KEY else st.warning("Marketaux fehlt")
    st.caption("API-Keys werden ausschließlich aus Streamlit Secrets gelesen.")

dashboard, stocks, turbos, news_tab, analysis, radar = st.tabs([
    "📊 Dashboard","📈 Aktien","⚡ Turbos","📰 News","🔎 Analyse","🔥 Hype Radar"
])

with dashboard:
    st.subheader("Meine Werte")
    rows=[]
    for asset in st.session_state.assets:
        q,_=quote(asset)
        rows.append({
            "Wert":asset["name"],
            "ISIN":asset["isin"],
            "Status":asset["status"],
            "Kurs":q.get("close","—") if q else "—",
            "Heute %":q.get("percent_change","—") if q else "—",
        })
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    st.info("Neu in V2.2: eigener 📰 News-Reiter mit Relevanz, Stimmung und Handlungseinschätzung.")
    st.warning("Algorithmische Testsignale – keine Anlageberatung.")

with stocks:
    st.subheader("Aktien verwalten")
    isin=st.text_input("ISIN",placeholder="z. B. US0079031078")
    c1,c2,c3=st.columns(3)
    with c1:
        symbol=st.text_input("Ticker",placeholder="AMD")
    with c2:
        exchange=st.text_input("Börse",placeholder="NASDAQ / XETR")
    with c3:
        status=st.selectbox("Kategorie",["Watchlist","Depot"])
    name=st.text_input("Name (optional)")
    if st.button("➕ Aktie hinzufügen",type="primary"):
        if not isin and not symbol:
            st.error("Bitte ISIN oder Ticker eingeben.")
        else:
            st.session_state.assets.append({
                "isin":isin.strip().upper(),
                "name":name.strip() or symbol.strip().upper() or isin.strip().upper(),
                "symbol":symbol.strip().upper(),
                "exchange":exchange.strip().upper(),
                "status":status,
            })
            st.rerun()
    st.divider()
    for i,asset in list(enumerate(st.session_state.assets)):
        c1,c2,c3,c4=st.columns([3,2,2,1])
        c1.markdown(f"**{asset['name']}**  \n`{asset['isin']}`")
        c2.write(asset["symbol"])
        c3.write(asset["status"])
        if c4.button("🗑️",key=f"asset_del_{i}"):
            st.session_state.assets.pop(i)
            st.rerun()

with turbos:
    st.subheader("Turbos / Knock-outs")
    st.info("Verwaltung ist aktiv. Basiswert, Long/Short, Knock-out, Hebel und Bezugsverhältnis folgen im Zertifikatemodul.")
    turbo_isin=st.text_input("Turbo-/Knock-out-ISIN")
    if st.button("➕ Turbo hinzufügen",type="primary") and turbo_isin:
        st.session_state.turbos.append({"isin":turbo_isin.strip().upper(),"name":"Neuer Turbo","status":"Watchlist"})
        st.rerun()
    st.divider()
    for i,turbo in list(enumerate(st.session_state.turbos)):
        c1,c2,c3=st.columns([4,2,1])
        c1.markdown(f"**{turbo['name']}**  \n`{turbo['isin']}`")
        c2.write(turbo["status"])
        if c3.button("🗑️",key=f"turbo_del_{i}"):
            st.session_state.turbos.pop(i)
            st.rerun()

with news_tab:
    st.subheader("📰 News Center")
    st.write("Neuigkeiten zu Depot und Watchlist mit Relevanz, Stimmung und Handlungseinschätzung.")

    if not MA_KEY:
        st.warning("Marketaux-Key fehlt.")
    else:
        c1,c2,c3 = st.columns(3)
        with c1:
            scope = st.selectbox("Bereich",["Alle","Depot","Watchlist"])
        with c2:
            tone_filter = st.selectbox("Stimmung",["Alle","Positiv","Neutral","Negativ"])
        with c3:
            min_rel = st.slider("Mindest-Relevanz",1,10,5)

        assets = st.session_state.assets
        if scope != "Alle":
            assets = [a for a in assets if a["status"] == scope]

        cards=[]
        for asset in assets:
            ndata,nerr = news_for(asset["symbol"],limit=5)
            if nerr or not ndata:
                continue
            for article in ndata.get("data",[]):
                s = article_sentiment(article,asset["symbol"])
                tone = tone_code(s)
                if tone_filter == "Positiv" and tone != "positive":
                    continue
                if tone_filter == "Negativ" and tone != "negative":
                    continue
                if tone_filter == "Neutral" and tone != "neutral":
                    continue

                rel = relevance_score(article,asset["symbol"])
                if rel < min_rel:
                    continue

                cards.append({
                    "asset":asset,
                    "article":article,
                    "sentiment":s,
                    "tone":tone,
                    "relevance":rel,
                })

        cards.sort(key=lambda x:(x["relevance"], x["article"].get("published_at","")), reverse=True)

        if not cards:
            st.info("Für den aktuellen Filter wurden keine passenden Meldungen gefunden.")
        else:
            for card in cards:
                asset=card["asset"]
                article=card["article"]
                rel=card["relevance"]
                s=card["sentiment"]
                tone=card["tone"]

                st.markdown(f"### {asset['name']} ({asset['symbol']})")
                st.write(f"**{article.get('title','Ohne Titel')}**")
                st.write(compact_summary(article))
                st.write(f"**Stimmung:** {news_tone(s)}")
                st.write(f"**Relevanz:** {rel}/10")
                st.write(f"**Handlung:** {news_action(rel,tone,asset['status'])}")
                st.caption(f"{asset['status']} • {article.get('source','—')} • {article.get('published_at','—')}")
                if rel >= 8:
                    st.warning("Diese Meldung erfüllt bereits die spätere Push-Logik: hohe Relevanz.")
                if article.get("url"):
                    st.markdown(f"[Originalartikel öffnen]({article['url']})")
                st.divider()

with analysis:
    st.subheader("Einzelanalyse")
    options={f"{a['name']} ({a['symbol']})":a for a in st.session_state.assets}
    asset=options[st.selectbox("Wert auswählen",list(options))]

    if st.button("🔎 Analyse starten",type="primary"):
        df,err=candles(asset)
        if err:
            st.error(err)
        else:
            tech=technical(df)
            if not tech:
                st.warning("Nicht genügend Kursdaten.")
            else:
                ndata,nerr=news_for(asset["symbol"]) if MA_KEY else (None,None)
                sent,sentiment_score,activity_score,article_count = news_metrics(ndata) if ndata else (None,50,25,0)
                overall=combined_score(tech,sentiment_score,activity_score)
                profile=profile_for(asset)

                st.subheader(profile["company"])
                st.write(profile["summary"])
                st.caption(f"Branche: {profile['sector']} • Grundrisiko: {profile['risk']}")
                st.write("**Wichtige Kurstreiber:** "+", ".join(profile["drivers"]))

                c1,c2,c3,c4,c5,c6=st.columns(6)
                c1.metric("Gesamt",f"{overall}/100")
                c2.metric("Kurzfristig",f"{tech['short']}/100")
                c3.metric("Mittelfristig",f"{tech['medium']}/100")
                c4.metric("News",f"{sentiment_score}/100")
                c5.metric("RSI",f"{tech['rsi']:.1f}")
                c6.metric("Risiko",f"{tech['risk']}/100")

                st.markdown(f"### {action_label(overall,tech['risk'],tech['rsi'])}")
                if tech["rsi"] >= 73:
                    st.warning("Technisch stark gelaufen – ein hoher Score ist kein automatisches Kaufsignal.")

                st.line_chart(df.set_index("datetime")[["close"]].rename(columns={"close":"Kurs"}))

                st.subheader("📰 News-Zusammenfassung")
                if nerr:
                    st.error(nerr)
                elif ndata and ndata.get("data"):
                    if sent is not None:
                        st.write(f"**Gesamtbild:** {news_tone(sent)}")
                    st.write(f"**News-Aktivität:** {article_count} gefundene Artikel")
                    for item in ndata.get("data",[]):
                        rel = relevance_score(item,asset["symbol"])
                        s = article_sentiment(item,asset["symbol"])
                        st.markdown(f"**{item.get('title','Ohne Titel')}**")
                        st.write(compact_summary(item))
                        st.caption(f"Relevanz {rel}/10 • {news_tone(s)} • {item.get('source','—')}")
                        st.divider()

with radar:
    st.subheader("🔥 Hype Radar")
    st.write("Der Radar trennt Aufmerksamkeit von tatsächlicher Einstiegsqualität.")
    if not MA_KEY:
        st.warning("Marketaux-Key fehlt.")
    else:
        rows=[]
        for asset in st.session_state.assets:
            ndata,_=news_for(asset["symbol"],limit=5)
            sent,sent_score,activity_score,count = news_metrics(ndata) if ndata else (None,50,25,0)
            df,_=candles(asset)
            tech=technical(df) if df is not None else None
            if tech:
                hype=round(0.45*activity_score+0.25*sent_score+0.30*tech["short"])
                invest=combined_score(tech,sent_score,activity_score)
                rows.append({
                    "Aktie":asset["name"],
                    "Ticker":asset["symbol"],
                    "Hype":hype,
                    "Einstieg":invest,
                    "Risiko":tech["risk"],
                    "RSI":round(tech["rsi"],1),
                    "News":count,
                    "Bewertung":action_label(invest,tech["risk"],tech["rsi"]),
                })
        rdf=pd.DataFrame(rows)
        if not rdf.empty:
            rdf=rdf.sort_values(["Hype","Einstieg"],ascending=False)
            st.dataframe(rdf,use_container_width=True,hide_index=True)

st.divider()
st.caption("Trading Assistant • Version 2.2")
