import os, json, hashlib, calendar
from pathlib import Path
from datetime import datetime
import requests
import pandas as pd
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Trading Assistant", page_icon="📈", layout="wide")

# ---------- Stammdaten ----------
COMPANY_PROFILES = {
 "WCH":{"company":"Wacker Chemie AG","sector":"Chemie / Spezialchemie","summary":"Wacker Chemie ist ein deutscher Chemiekonzern mit Schwerpunkten in Silikonen, Polymeren, Biosolutions und hochreinem Polysilicium.","drivers":["Chemiezyklus","Energiepreise","Industrienachfrage","Halbleiter/Solar"],"risk":"zyklisch"},
 "HOOD":{"company":"Robinhood Markets","sector":"Fintech / Brokerage","summary":"Robinhood betreibt eine digitale Handelsplattform für Aktien, Optionen, Kryptowährungen und weitere Finanzprodukte.","drivers":["Handelsaktivität","Krypto-Märkte","Zinsumfeld","Kundenzuwachs"],"risk":"hoch"},
 "NVDA":{"company":"NVIDIA","sector":"Halbleiter / KI-Infrastruktur","summary":"NVIDIA entwickelt GPUs, KI-Beschleuniger, Rechenzentrumsplattformen und Software für moderne KI-Infrastruktur.","drivers":["KI-Investitionen","Rechenzentren","Produktzyklen","Exportregeln"],"risk":"mittel-hoch"},
 "INTC":{"company":"Intel","sector":"Halbleiter","summary":"Intel entwickelt Prozessoren und Halbleiterlösungen und baut parallel sein Foundry-Geschäft aus.","drivers":["PC-/Server-Nachfrage","Foundry-Ausbau","Kapitalbedarf","Wettbewerb"],"risk":"hoch"},
 "ENR":{"company":"Siemens Energy","sector":"Energie / Infrastruktur","summary":"Siemens Energy liefert Technik für Stromerzeugung, Netze und Energiewende; zum Konzern gehört Siemens Gamesa.","drivers":["Netzausbau","Energiewende","Auftragseingang","Gamesa-Turnaround"],"risk":"mittel-hoch"},
 "QBTS":{"company":"D-Wave Quantum","sector":"Quantencomputing","summary":"D-Wave entwickelt Quantencomputing-Systeme und Software mit Fokus auf Quantum Annealing und hybride Optimierung.","drivers":["Kommerzielle Aufträge","Technologieakzeptanz","Cash-Burn","Quanten-Hype"],"risk":"sehr hoch"},
 "AMD":{"company":"Advanced Micro Devices","sector":"Halbleiter / KI","summary":"AMD entwickelt CPUs, GPUs und Rechenzentrumsbeschleuniger für PCs, Server, Gaming und KI.","drivers":["KI-Beschleuniger","Server-Marktanteile","PC-Zyklus","Wettbewerb"],"risk":"mittel-hoch"},
 "ASML":{"company":"ASML","sector":"Halbleiterausrüstung","summary":"ASML entwickelt Lithographiesysteme für die Halbleiterindustrie und ist insbesondere bei EUV-Anlagen technologisch führend.","drivers":["Chip-Investitionen","EUV-Nachfrage","Exportrestriktionen","Auftragsbestand"],"risk":"mittel"},
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

SERVICE_CATALOG = {
    "Twelve Data": {
        "zweck":"Kursdaten / technische Analyse",
        "verwaltung":"https://twelvedata.com/account",
        "preise":"https://twelvedata.com/pricing",
        "default_status":"Kostenlos",
        "default_cost":0.0,
    },
    "Marketaux": {
        "zweck":"Finanznachrichten / Sentiment",
        "verwaltung":"https://www.marketaux.com/account",
        "preise":"https://www.marketaux.com/pricing",
        "default_status":"Kostenlos",
        "default_cost":0.0,
    },
    "OpenAI API": {
        "zweck":"Deutsche KI-Zusammenfassung / Einordnung",
        "verwaltung":"https://platform.openai.com/settings/organization/billing/overview",
        "preise":"https://openai.com/api/pricing/",
        "default_status":"Nicht eingerichtet",
        "default_cost":0.0,
    },
}

GERMAN_RESEARCH = [
    {"name":"finanzen.net","focus":"Deutschsprachige Aktien-News, Analystenmeldungen und Marktnachrichten","url":"https://www.finanzen.net/nachrichten/ressort/aktien","cost":"kostenlos nutzbar"},
    {"name":"boerse.de","focus":"Deutschsprachige Finanznachrichten, Analysen und Aktieninformationen","url":"https://www.boerse.de/finanznachrichten/","cost":"kostenlos nutzbar"},
    {"name":"Tagesschau Finanzen","focus":"Deutsche Markt- und Börsennachrichten mit makroökonomischem Fokus","url":"https://www.tagesschau.de/wirtschaft/finanzen/","cost":"kostenlos"},
]

# ---------- Konfiguration ----------
DEFAULT_MONTHLY_LIMIT_EUR = 2.00
DEFAULT_DAILY_AI_LIMIT = 25
MIN_RELEVANCE_AI = 5
PUSH_RELEVANCE = 8
USD_TO_EUR_BUFFER = 0.95   # konservative Näherung für die lokale Kostenschätzung
# Kostenschätzung passend zur ursprünglich geplanten GPT-5-mini-Kalkulation.
INPUT_USD_PER_M = 0.25
OUTPUT_USD_PER_M = 2.00
MODEL = "gpt-5-mini"

DATA_DIR = Path(".trading_assistant_data")
DATA_DIR.mkdir(exist_ok=True)
SETTINGS_FILE = DATA_DIR / "settings.json"
USAGE_FILE = DATA_DIR / "usage.json"
CACHE_FILE = DATA_DIR / "ai_cache.json"
SERVICES_FILE = DATA_DIR / "services.json"

def load_json(path, default):
    try:
        if path.exists(): return json.loads(path.read_text(encoding="utf-8"))
    except Exception: pass
    return default

def save_json(path, data):
    try: path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception: pass

def secret(name):
    try: return st.secrets[name]
    except Exception: return os.getenv(name, "")

TD_KEY=secret("TWELVE_DATA_API_KEY")
MA_KEY=secret("MARKETAUX_API_KEY")
OPENAI_KEY=secret("OPENAI_API_KEY")

settings=load_json(SETTINGS_FILE, {"monthly_limit_eur":DEFAULT_MONTHLY_LIMIT_EUR,"daily_ai_limit":DEFAULT_DAILY_AI_LIMIT})
usage=load_json(USAGE_FILE, {})
ai_cache=load_json(CACHE_FILE, {})
services=load_json(SERVICES_FILE, {
    name:{
        "status":cfg["default_status"],
        "monthly_cost":cfg["default_cost"],
        "next_renewal":"",
        "notes":""
    } for name,cfg in SERVICE_CATALOG.items()
})

def month_key(): return datetime.now().strftime("%Y-%m")
def day_key(): return datetime.now().strftime("%Y-%m-%d")
def month_usage():
    return usage.get(month_key(), {"estimated_eur":0.0,"calls":0,"days":{}})
def daily_calls():
    return month_usage().get("days",{}).get(day_key(),0)

def can_use_ai():
    u=month_usage()
    if not OPENAI_KEY: return False,"OPENAI_API_KEY fehlt."
    if u.get("estimated_eur",0)>=float(settings["monthly_limit_eur"]): return False,"Monatslimit erreicht."
    if daily_calls()>=int(settings["daily_ai_limit"]): return False,"Tageslimit erreicht."
    return True,""

def register_usage(input_tokens, output_tokens):
    est_usd=(input_tokens/1_000_000)*INPUT_USD_PER_M+(output_tokens/1_000_000)*OUTPUT_USD_PER_M
    est_eur=est_usd/USD_TO_EUR_BUFFER
    mk=month_key(); dk=day_key()
    u=usage.setdefault(mk,{"estimated_eur":0.0,"calls":0,"days":{}})
    u["estimated_eur"]=round(u.get("estimated_eur",0)+est_eur,6)
    u["calls"]=u.get("calls",0)+1
    u.setdefault("days",{})[dk]=u.get("days",{}).get(dk,0)+1
    save_json(USAGE_FILE,usage)
    return est_eur

def td(endpoint,params):
    if not TD_KEY:return None,"TWELVE_DATA_API_KEY fehlt."
    p=dict(params);p["apikey"]=TD_KEY
    try:
        r=requests.get("https://api.twelvedata.com/"+endpoint,params=p,timeout=15);d=r.json()
        if r.status_code>=400 or d.get("status")=="error":return None,d.get("message",f"HTTP {r.status_code}")
        return d,None
    except Exception as e:return None,str(e)

def marketaux(params):
    if not MA_KEY:return None,"MARKETAUX_API_KEY fehlt."
    p=dict(params);p["api_token"]=MA_KEY
    try:
        r=requests.get("https://api.marketaux.com/v1/news/all",params=p,timeout=15);d=r.json()
        if r.status_code>=400 or d.get("error"):return None,str(d.get("error",f"HTTP {r.status_code}"))
        return d,None
    except Exception as e:return None,str(e)

def quote(a):
    p={"symbol":a["symbol"]}
    if a.get("exchange"):p["exchange"]=a["exchange"]
    return td("quote",p)

def candles(a):
    p={"symbol":a["symbol"],"interval":"1day","outputsize":200,"order":"ASC"}
    if a.get("exchange"):p["exchange"]=a["exchange"]
    d,e=td("time_series",p)
    if e:return None,e
    df=pd.DataFrame(d.get("values",[]))
    if df.empty:return None,"Keine Kursdaten."
    df["datetime"]=pd.to_datetime(df["datetime"])
    for c in ["open","high","low","close","volume"]:
        if c in df:df[c]=pd.to_numeric(df[c],errors="coerce")
    return df.sort_values("datetime"),None

def technical(df):
    if len(df)<50:return None
    c=df.close;s20=c.rolling(20).mean();s50=c.rolling(50).mean();s200=c.rolling(200).mean()
    d=c.diff();g=d.clip(lower=0).rolling(14).mean();l=(-d.clip(upper=0)).rolling(14).mean()
    rsi=float((100-100/(1+g/l.replace(0,pd.NA))).iloc[-1]);last=float(c.iloc[-1])
    m5=(last/c.iloc[-6]-1)*100;m20=(last/c.iloc[-21]-1)*100
    short=50+(15 if last>s20.iloc[-1] else -10)+(15 if s20.iloc[-1]>s50.iloc[-1] else -10)+(10 if m5>0 else -5)+(8 if 42<=rsi<=67 else -10 if rsi>=80 else -5 if rsi>=73 else 3 if rsi<=35 else 0)
    medium=50+(15 if last>s50.iloc[-1] else -10)+(15 if len(df)>=200 and last>s200.iloc[-1] else 0)+(10 if s20.iloc[-1]>s50.iloc[-1] else -8)+(10 if m20>0 else -5)
    risk=35+(35 if rsi>=80 else 20 if rsi>=73 else 10 if rsi<=30 else 0)+min(25,abs(m5)*2.2)
    return {"short":max(0,min(100,round(short))),"medium":max(0,min(100,round(medium))),"rsi":rsi,"risk":max(0,min(100,round(risk)))}

def news_for(symbol,limit=6):
    return marketaux({"symbols":symbol,"filter_entities":"true","must_have_entities":"true","language":"en","limit":limit,"sort":"published_at","sort_order":"desc"})

def article_sentiment(article,symbol=None):
    vals=[]
    for e in article.get("entities",[]):
        if symbol and e.get("symbol") and e.get("symbol")!=symbol:continue
        try:
            if e.get("sentiment_score") is not None:vals.append(float(e["sentiment_score"]))
        except Exception:pass
    return sum(vals)/len(vals) if vals else None

def relevance(article,symbol=None):
    score=4;text=((article.get("title") or "")+" "+(article.get("description") or "")).lower()
    for w in ["earnings","guidance","forecast","acquisition","merger","lawsuit","investigation","approval","partnership","contract","order","recall","ceo","cfo","dividend","buyback","offering","export","ban","regulation","profit warning"]:
        if w in text:score+=1
    s=article_sentiment(article,symbol)
    if s is not None and abs(s)>=.55:score+=1
    return max(1,min(10,score))

def cache_key(asset,article):
    raw=(asset["symbol"]+"|"+str(article.get("url",""))+"|"+str(article.get("title",""))).encode()
    return hashlib.sha256(raw).hexdigest()

def ai_news(asset,article,rel):
    key=cache_key(asset,article)
    if key in ai_cache:return ai_cache[key],None,True
    ok,why=can_use_ai()
    if not ok:return None,why,False
    if rel<MIN_RELEVANCE_AI:return None,"Unterhalb der KI-Relevanzschwelle.",False
    client=OpenAI(api_key=OPENAI_KEY)
    prompt=f"""Analysiere ausschließlich die folgende Börsenmeldung. Schreibe vollständig auf Deutsch.
Unternehmen: {asset['name']} ({asset['symbol']})
Status: {asset['status']}
Vorbewertete Relevanz: {rel}/10
Titel: {article.get('title','')}
Beschreibung: {article.get('description','')}

Antworte ausschließlich als gültiges JSON mit:
deutsche_ueberschrift, kurzfassung, auswirkung (positiv|neutral|negativ),
relevanz (1-10), zeithorizont (kurzfristig|mittelfristig|beides),
begruendung, hinweis.
Der Hinweis darf keine definitive Kauf-/Verkaufsanweisung sein, sondern soll beschreiben, was beobachtet oder geprüft werden sollte.
Keine Fakten ergänzen, die nicht in der Meldung stehen."""
    try:
        resp=client.responses.create(model=MODEL,input=prompt,max_output_tokens=350)
        text=resp.output_text.strip()
        if text.startswith("```"):text=text.replace("```json","").replace("```","").strip()
        result=json.loads(text)
        inp=getattr(resp.usage,"input_tokens",0) if getattr(resp,"usage",None) else 0
        out=getattr(resp.usage,"output_tokens",0) if getattr(resp,"usage",None) else 0
        register_usage(inp,out)
        ai_cache[key]=result;save_json(CACHE_FILE,ai_cache)
        return result,None,False
    except Exception as e:return None,f"KI-Auswertung fehlgeschlagen: {e}",False

def combined(tech,sent):
    ns=50 if sent is None else max(0,min(100,50+sent*50))
    base=.48*tech["short"]+.34*tech["medium"]+.18*ns
    return max(0,min(100,round(base-max(0,tech["risk"]-70)*.22)))

def action(score,risk,rsi):
    if risk>=80 and score>=70:return "🟡 Stark, aber überhitzt – Rücksetzer abwarten"
    if score>=82 and rsi<73:return "🟢 Einstiegszone prüfen"
    if score>=70:return "🟢 Einstieg beobachten"
    if score>=55:return "🟡 Halten / abwarten"
    if score>=40:return "🟠 Risiko erhöht – Position prüfen"
    return "🔴 Aktuell kein attraktives Einstiegssignal"

if "assets" not in st.session_state:st.session_state.assets=[x.copy() for x in STARTER_ASSETS]
if "turbos" not in st.session_state:st.session_state.turbos=[x.copy() for x in STARTER_TURBOS]

st.title("📈 Trading Assistant")
st.caption("Version 2.4 • Original-News + deutsche KI-Ergänzung + Kostenbremse + Diensteübersicht")

with st.sidebar:
    st.header("⚙️ Datenquellen")
    st.success("Twelve Data verbunden") if TD_KEY else st.error("Twelve Data fehlt")
    st.success("Marketaux verbunden") if MA_KEY else st.warning("Marketaux fehlt")
    st.success("OpenAI verbunden") if OPENAI_KEY else st.warning("OpenAI-Key fehlt")

tabs=st.tabs(["📊 Dashboard","📈 Aktien","⚡ Turbos","📰 News","🔎 Analyse","🔥 Hype Radar","🔗 Dienste & Abos","💶 KI-Kosten"])
dashboard,stocks,turbos,news_tab,analysis,radar,services_tab,costs=tabs

with dashboard:
    st.subheader("Meine Werte")
    rows=[]
    for a in st.session_state.assets:
        q,_=quote(a)
        rows.append({"Wert":a["name"],"ISIN":a["isin"],"Status":a["status"],"Kurs":q.get("close","—") if q else "—","Heute %":q.get("percent_change","—") if q else "—"})
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    st.info("Neu: relevante englische News können per KI vollständig auf Deutsch aufbereitet werden.")
    st.warning("Algorithmische Testsignale – keine Anlageberatung.")

    st.divider()
    st.subheader("🔗 Meine App-Dienste & Abos")
    st.caption("Überblick über externe Dienste, Kosten und offizielle Verwaltungslinks.")

    service_rows=[]
    total_cost=0.0
    for service_name,cfg in SERVICE_CATALOG.items():
        entry=services.get(service_name,{})
        cost=float(entry.get("monthly_cost",0.0) or 0.0)
        total_cost+=cost
        service_rows.append({
            "Dienst":service_name,
            "Zweck":cfg["zweck"],
            "Status":entry.get("status","—"),
            "Monatskosten (€)":round(cost,2),
            "Nächste Verlängerung":entry.get("next_renewal","") or "—",
        })

    st.dataframe(pd.DataFrame(service_rows),use_container_width=True,hide_index=True)
    st.metric("Erfasste externe Monatskosten",f"{total_cost:.2f} €")

    for service_name,cfg in SERVICE_CATALOG.items():
        with st.expander(f"{service_name} verwalten"):
            st.write(f"**Verwendung:** {cfg['zweck']}")
            c1,c2=st.columns(2)
            with c1:
                st.link_button("⚙️ Offizielle Verwaltung / Kündigung",cfg["verwaltung"],use_container_width=True)
            with c2:
                st.link_button("🔄 Tarif / Reaktivierung",cfg["preise"],use_container_width=True)
            st.caption("Die App führt dich nur zur offiziellen Seite. Kündigung oder Reaktivierung bestätigst du dort selbst.")

    st.divider()
    st.subheader("🇩🇪 Kostenlose deutschsprachige Recherche")
    for item in GERMAN_RESEARCH:
        c1,c2=st.columns([4,1])
        with c1:
            st.markdown(f"**{item['name']}**")
            st.write(item["focus"])
            st.caption(item["cost"])
        with c2:
            st.link_button("Öffnen",item["url"],use_container_width=True)

with stocks:
    st.subheader("Aktien verwalten")
    isin=st.text_input("ISIN");c1,c2,c3=st.columns(3)
    with c1:symbol=st.text_input("Ticker")
    with c2:exchange=st.text_input("Börse")
    with c3:status=st.selectbox("Kategorie",["Watchlist","Depot"])
    name=st.text_input("Name (optional)")
    if st.button("➕ Aktie hinzufügen",type="primary"):
        if isin or symbol:
            st.session_state.assets.append({"isin":isin.upper(),"name":name or symbol.upper() or isin.upper(),"symbol":symbol.upper(),"exchange":exchange.upper(),"status":status});st.rerun()
    for i,a in list(enumerate(st.session_state.assets)):
        c1,c2,c3,c4=st.columns([3,2,2,1]);c1.write(f"{a['name']} — {a['isin']}");c2.write(a["symbol"]);c3.write(a["status"])
        if c4.button("🗑️",key=f"a{i}"):st.session_state.assets.pop(i);st.rerun()

with turbos:
    st.subheader("Turbos / Knock-outs")
    ti=st.text_input("Turbo-/Knock-out-ISIN")
    if st.button("➕ Turbo hinzufügen") and ti:st.session_state.turbos.append({"isin":ti.upper(),"name":"Neuer Turbo","status":"Watchlist"});st.rerun()
    for i,t in list(enumerate(st.session_state.turbos)):
        c1,c2=st.columns([6,1]);c1.write(t["isin"])
        if c2.button("🗑️",key=f"t{i}"):st.session_state.turbos.pop(i);st.rerun()

with news_tab:
    st.subheader("📰 Deutsches News Center")
    st.caption(f"KI wird erst ab Relevanz {MIN_RELEVANCE_AI}/10 verwendet; ab {PUSH_RELEVANCE}/10 ist eine Meldung später Push-Kandidat.")
    scope=st.selectbox("Bereich",["Alle","Depot","Watchlist"],key="news_scope")
    assets=st.session_state.assets if scope=="Alle" else [a for a in st.session_state.assets if a["status"]==scope]
    if not MA_KEY:st.warning("Marketaux-Key fehlt.")
    else:
        for a in assets:
            nd,ne=news_for(a["symbol"],4)
            if ne:continue
            for art in (nd or {}).get("data",[]):
                rel=relevance(art,a["symbol"])
                if rel<MIN_RELEVANCE_AI:continue
                st.markdown(f"### {a['name']} • Relevanz {rel}/10")

                # Original-News bleiben immer sichtbar, damit der Nutzer sein Englisch trainieren kann.
                st.markdown("#### 🇬🇧 Original auf Englisch")
                st.write(f"**{art.get('title','Ohne Titel')}**")
                original_text=(art.get("description") or "").strip()
                if original_text:
                    st.write(original_text)
                else:
                    st.caption("Kein englischer Beschreibungstext verfügbar.")
                st.caption(f"Quelle: {art.get('source','—')} • {art.get('published_at','—')}")

                result,err,cached=ai_news(a,art,rel)
                if result:
                    st.markdown("#### 🇩🇪 Deutsche Übersetzung & Einordnung")
                    st.write(f"**{result.get('deutsche_ueberschrift',art.get('title',''))}**")
                    st.write(result.get("kurzfassung",""))
                    st.write(f"**Auswirkung:** {result.get('auswirkung','neutral')} • **Zeithorizont:** {result.get('zeithorizont','—')} • **KI-Relevanz:** {result.get('relevanz',rel)}/10")
                    st.write(f"**Einordnung:** {result.get('begruendung','')}")
                    st.write(f"**Was prüfen?** {result.get('hinweis','')}")
                    if cached:st.caption("Aus Cache – keine neuen KI-Kosten.")
                    if rel>=PUSH_RELEVANCE:st.warning("🔔 Push-Kandidat: hohe Relevanz")
                else:
                    st.info(err)

                if art.get("url"):st.markdown(f"[Originalartikel öffnen]({art['url']})")
                st.divider()

with analysis:
    st.subheader("Einzelanalyse")
    opts={f"{a['name']} ({a['symbol']})":a for a in st.session_state.assets};a=opts[st.selectbox("Wert",list(opts))]
    if st.button("🔎 Analyse starten",type="primary"):
        df,e=candles(a)
        if e:st.error(e)
        else:
            tech=technical(df);nd,_=news_for(a["symbol"],5) if MA_KEY else (None,None)
            vals=[article_sentiment(x,a["symbol"]) for x in (nd or {}).get("data",[])];vals=[x for x in vals if x is not None]
            sent=sum(vals)/len(vals) if vals else None;score=combined(tech,sent)
            p=COMPANY_PROFILES.get(a["symbol"],{"company":a["name"],"summary":"Noch kein festes Unternehmensprofil hinterlegt.","sector":"—","drivers":[],"risk":"—"})
            st.subheader(p["company"]);st.write(p["summary"]);st.caption(f"Branche: {p['sector']} • Grundrisiko: {p['risk']}")
            c1,c2,c3,c4=st.columns(4);c1.metric("Gesamt",f"{score}/100");c2.metric("Kurzfristig",f"{tech['short']}/100");c3.metric("Mittelfristig",f"{tech['medium']}/100");c4.metric("Risiko",f"{tech['risk']}/100")
            st.markdown(f"### {action(score,tech['risk'],tech['rsi'])}")
            st.line_chart(df.set_index("datetime")[["close"]].rename(columns={"close":"Kurs"}))

with radar:
    st.subheader("🔥 Hype Radar")
    rows=[]
    if MA_KEY:
        for a in st.session_state.assets:
            nd,_=news_for(a["symbol"],5);count=len((nd or {}).get("data",[]))
            vals=[article_sentiment(x,a["symbol"]) for x in (nd or {}).get("data",[])];vals=[x for x in vals if x is not None]
            sent=sum(vals)/len(vals) if vals else None;df,_=candles(a);tech=technical(df) if df is not None else None
            if tech:
                sent_score=50 if sent is None else max(0,min(100,50+sent*50));hype=round(.4*min(100,25+count*12)+.25*sent_score+.35*tech["short"])
                rows.append({"Aktie":a["name"],"Hype":hype,"Einstieg":combined(tech,sent),"Risiko":tech["risk"],"RSI":round(tech["rsi"],1),"News":count})
    if rows:st.dataframe(pd.DataFrame(rows).sort_values("Hype",ascending=False),use_container_width=True,hide_index=True)

with services_tab:
    st.subheader("🔗 Dienste & Abos verwalten")
    st.write("Pflege hier Status, Kosten und Verlängerungsdatum deiner externen Dienste.")

    status_options=["Kostenlos","Kostenpflichtig","Gekündigt","Pausiert","Nicht eingerichtet"]
    for service_name,cfg in SERVICE_CATALOG.items():
        current=services.get(service_name,{
            "status":cfg["default_status"],
            "monthly_cost":cfg["default_cost"],
            "next_renewal":"",
            "notes":""
        })

        with st.expander(service_name,expanded=True):
            st.write(f"**Zweck:** {cfg['zweck']}")
            c1,c2=st.columns(2)
            with c1:
                current_status=current.get("status","Kostenlos")
                idx=status_options.index(current_status) if current_status in status_options else 0
                new_status=st.selectbox("Status",status_options,index=idx,key=f"status_{service_name}")
                new_cost=st.number_input(
                    "Monatskosten (€)",
                    min_value=0.0,
                    max_value=1000.0,
                    value=float(current.get("monthly_cost",0.0) or 0.0),
                    step=0.50,
                    key=f"cost_{service_name}"
                )
            with c2:
                new_renewal=st.text_input(
                    "Nächste Verlängerung (optional)",
                    value=current.get("next_renewal",""),
                    placeholder="z. B. 15.09.2026",
                    key=f"renew_{service_name}"
                )
                new_notes=st.text_input(
                    "Notiz (optional)",
                    value=current.get("notes",""),
                    key=f"notes_{service_name}"
                )

            b1,b2,b3=st.columns(3)
            with b1:
                if st.button("💾 Speichern",key=f"save_{service_name}",use_container_width=True):
                    services[service_name]={
                        "status":new_status,
                        "monthly_cost":float(new_cost),
                        "next_renewal":new_renewal.strip(),
                        "notes":new_notes.strip()
                    }
                    save_json(SERVICES_FILE,services)
                    st.success(f"{service_name} gespeichert.")
            with b2:
                st.link_button("⚙️ Kündigen / Verwalten",cfg["verwaltung"],use_container_width=True)
            with b3:
                st.link_button("🔄 Tarif / Reaktivieren",cfg["preise"],use_container_width=True)

            st.caption("Aus Sicherheitsgründen werden externe Abos nicht automatisch gekündigt oder reaktiviert.")

    st.divider()
    total=sum(float(x.get("monthly_cost",0.0) or 0.0) for x in services.values())
    st.metric("Erfasste Monatskosten aller Dienste",f"{total:.2f} €")
    st.caption("Die Summe basiert auf deinen manuellen Angaben.")

    st.subheader("🇩🇪 Kostenlose deutschsprachige Seiten")
    for item in GERMAN_RESEARCH:
        c1,c2=st.columns([4,1])
        with c1:
            st.markdown(f"**{item['name']}**")
            st.write(item["focus"])
            st.caption(item["cost"])
        with c2:
            st.link_button("Öffnen",item["url"],use_container_width=True)

with costs:
    st.subheader("💶 KI-Kostenbremse")
    u=month_usage();limit=float(settings["monthly_limit_eur"]);spent=float(u.get("estimated_eur",0))
    c1,c2,c3=st.columns(3)
    c1.metric("Geschätzte Kosten diesen Monat",f"{spent:.3f} €")
    c2.metric("Dein Monatslimit",f"{limit:.2f} €")
    c3.metric("KI-Auswertungen heute",f"{daily_calls()} / {settings['daily_ai_limit']}")
    st.progress(min(1.0,spent/limit) if limit>0 else 1.0)

    st.markdown("### Monatslimit selbst ändern")
    st.write("Du kannst das Limit jederzeit ändern – z. B. diesen Monat 3 €, nächsten Monat 5 €. Die Änderung beeinflusst nur die App-interne Kostenbremse.")
    new_limit=st.number_input("Maximale geschätzte KI-Kosten pro Monat (€)",min_value=0.0,max_value=100.0,value=limit,step=0.50)
    new_daily=st.number_input("Maximale neue KI-Auswertungen pro Tag",min_value=1,max_value=500,value=int(settings["daily_ai_limit"]),step=5)
    if st.button("💾 Kostenlimit speichern",type="primary"):
        settings["monthly_limit_eur"]=float(new_limit);settings["daily_ai_limit"]=int(new_daily);save_json(SETTINGS_FILE,settings)
        st.success("Kostenbremse gespeichert.");st.rerun()

    st.warning("Wichtig: Diese Anzeige ist eine lokale Schätzung der Modellkosten und kein Abrechnungsbeleg. Für eine harte Kontosperre solltest du zusätzlich ein Budget/Limits im OpenAI-API-Konto setzen.")
    if spent>=limit and limit>0:st.error("🛑 Monatslimit erreicht. Neue KI-Auswertungen sind gestoppt; bereits gespeicherte Zusammenfassungen bleiben verfügbar.")

st.divider()
st.caption("Trading Assistant • Version 2.4")
