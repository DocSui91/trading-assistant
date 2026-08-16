import os
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title='Trading Assistant', page_icon='📈', layout='wide')

STARTER_ASSETS = [
    {'isin':'DE000WCH8881','name':'Wacker Chemie','symbol':'WCH','exchange':'XETR','status':'Depot'},
    {'isin':'US7707001027','name':'Robinhood Markets','symbol':'HOOD','exchange':'NASDAQ','status':'Depot'},
    {'isin':'US67066G1040','name':'NVIDIA','symbol':'NVDA','exchange':'NASDAQ','status':'Depot'},
    {'isin':'US4581401001','name':'Intel','symbol':'INTC','exchange':'NASDAQ','status':'Depot'},
    {'isin':'DE000ENER6Y0','name':'Siemens Energy','symbol':'ENR','exchange':'XETR','status':'Depot'},
    {'isin':'US26740W1099','name':'D-Wave Quantum','symbol':'QBTS','exchange':'NYSE','status':'Depot'},
    {'isin':'US0079031078','name':'AMD','symbol':'AMD','exchange':'NASDAQ','status':'Watchlist'},
    {'isin':'NL0009805522','name':'ASML','symbol':'ASML','exchange':'NASDAQ','status':'Watchlist'},
]
STARTER_TURBOS = [
    {'isin':'DE000JY1GWX1','name':'Turbo 1','status':'Watchlist'},
    {'isin':'DE000HM4UQX4','name':'Turbo 2','status':'Watchlist'},
    {'isin':'DE000HM5ULR4','name':'Turbo 3','status':'Watchlist'},
    {'isin':'DE000HM5BPP9','name':'Turbo 4','status':'Watchlist'},
]

def secret(name):
    try:
        return st.secrets[name]
    except Exception:
        return os.getenv(name, '')

TD_KEY = secret('TWELVE_DATA_API_KEY')
MA_KEY = secret('MARKETAUX_API_KEY')

def td(endpoint, params):
    if not TD_KEY:
        return None, 'TWELVE_DATA_API_KEY fehlt.'
    p = dict(params); p['apikey'] = TD_KEY
    try:
        r = requests.get('https://api.twelvedata.com/' + endpoint, params=p, timeout=15)
        d = r.json()
        if r.status_code >= 400 or d.get('status') == 'error':
            return None, d.get('message', f'HTTP {r.status_code}')
        return d, None
    except Exception as e:
        return None, str(e)

def marketaux(params):
    if not MA_KEY:
        return None, 'MARKETAUX_API_KEY fehlt.'
    p = dict(params); p['api_token'] = MA_KEY
    try:
        r = requests.get('https://api.marketaux.com/v1/news/all', params=p, timeout=15)
        d = r.json()
        if r.status_code >= 400 or d.get('error'):
            err = d.get('error')
            if isinstance(err, dict):
                err = err.get('message', str(err))
            return None, err or f'HTTP {r.status_code}'
        return d, None
    except Exception as e:
        return None, str(e)

def quote(asset):
    p = {'symbol': asset['symbol']}
    if asset.get('exchange'):
        p['exchange'] = asset['exchange']
    return td('quote', p)

def candles(asset):
    p = {'symbol': asset['symbol'], 'interval':'1day', 'outputsize':200, 'order':'ASC'}
    if asset.get('exchange'):
        p['exchange'] = asset['exchange']
    data, err = td('time_series', p)
    if err:
        return None, err
    df = pd.DataFrame(data.get('values', []))
    if df.empty:
        return None, 'Keine Kursdaten.'
    df['datetime'] = pd.to_datetime(df['datetime'])
    for c in ['open','high','low','close','volume']:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    return df.sort_values('datetime'), None

def technical(df):
    if len(df) < 50:
        return None
    close = df['close']
    sma20 = close.rolling(20).mean(); sma50 = close.rolling(50).mean(); sma200 = close.rolling(200).mean()
    delta = close.diff(); gain = delta.clip(lower=0).rolling(14).mean(); loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, pd.NA)
    rsi = float((100 - 100/(1+rs)).iloc[-1])
    last = float(close.iloc[-1])
    mom5 = float((last/close.iloc[-6]-1)*100); mom20 = float((last/close.iloc[-21]-1)*100)
    short = 50 + (15 if last > sma20.iloc[-1] else -10) + (15 if sma20.iloc[-1] > sma50.iloc[-1] else -10) + (10 if mom5 > 0 else -5) + (10 if 40 <= rsi <= 68 else (-5 if rsi > 75 else 0))
    medium = 50 + (15 if last > sma50.iloc[-1] else -10) + (15 if len(df) >= 200 and last > sma200.iloc[-1] else 0) + (10 if sma20.iloc[-1] > sma50.iloc[-1] else -8) + (10 if mom20 > 0 else -5)
    return {'short': max(0,min(100,round(short))), 'medium': max(0,min(100,round(medium))), 'rsi': rsi, 'mom20': mom20}

def signal(score):
    if score >= 82: return '🟢 Kaufzone / Aufstocken'
    if score >= 70: return '🟢 Einstieg suchen'
    if score >= 55: return '🟡 Halten / beobachten'
    if score >= 40: return '🟠 Risiko erhöht'
    return '🔴 Kein Einstieg / reduzieren'

def news_for(symbol, limit=5):
    return marketaux({'symbols':symbol,'filter_entities':'true','must_have_entities':'true','language':'en','limit':limit,'sort':'published_at','sort_order':'desc'})

def news_sentiment(data):
    vals = []
    for article in (data or {}).get('data', []):
        for entity in article.get('entities', []):
            score = entity.get('sentiment_score')
            if score is not None:
                try: vals.append(float(score))
                except Exception: pass
    return sum(vals)/len(vals) if vals else None

if 'assets' not in st.session_state: st.session_state.assets = [x.copy() for x in STARTER_ASSETS]
if 'turbos' not in st.session_state: st.session_state.turbos = [x.copy() for x in STARTER_TURBOS]

st.title('📈 Trading Assistant')
st.caption('Version 2 • Kurse + technische Analyse + News/Sentiment + Hype Radar')

with st.sidebar:
    st.header('⚙️ Datenquellen')
    st.success('Twelve Data verbunden') if TD_KEY else st.error('Twelve Data fehlt')
    st.success('Marketaux verbunden') if MA_KEY else st.warning('Marketaux fehlt')
    st.caption('API-Keys werden ausschließlich aus Streamlit Secrets gelesen.')

dashboard, stocks, turbos, analysis, radar = st.tabs(['📊 Dashboard','📈 Aktien','⚡ Turbos','🔎 Analyse','🔥 Hype Radar'])

with dashboard:
    st.subheader('Meine Werte')
    rows = []
    for asset in st.session_state.assets:
        data, err = quote(asset)
        rows.append({'Wert': asset['name'], 'ISIN': asset['isin'], 'Status': asset['status'], 'Kurs': data.get('close','—') if data else '—', 'Heute %': data.get('percent_change','—') if data else '—'})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.warning('Die Bewertungen sind algorithmische Testsignale und keine Anlageberatung.')

with stocks:
    st.subheader('Aktien verwalten')
    isin = st.text_input('ISIN', placeholder='z. B. US0079031078')
    c1,c2,c3 = st.columns(3)
    with c1: symbol = st.text_input('Ticker', placeholder='AMD')
    with c2: exchange = st.text_input('Börse', placeholder='NASDAQ / XETR')
    with c3: status = st.selectbox('Kategorie', ['Watchlist','Depot'])
    name = st.text_input('Name (optional)')
    if st.button('➕ Aktie hinzufügen', type='primary'):
        if not isin and not symbol: st.error('Bitte ISIN oder Ticker eingeben.')
        else:
            st.session_state.assets.append({'isin': isin.strip().upper(), 'name': name.strip() or symbol.strip().upper() or isin.strip().upper(), 'symbol': symbol.strip().upper(), 'exchange': exchange.strip().upper(), 'status': status})
            st.rerun()
    st.divider()
    for i, asset in list(enumerate(st.session_state.assets)):
        c1,c2,c3,c4 = st.columns([3,2,2,1])
        c1.markdown(f"**{asset['name']}**  \n`{asset['isin']}`"); c2.write(asset['symbol']); c3.write(asset['status'])
        if c4.button('🗑️', key=f'asset_del_{i}'):
            st.session_state.assets.pop(i); st.rerun()

with turbos:
    st.subheader('Turbos / Knock-outs')
    st.info('Die Watchlist ist angelegt. Basiswert, Long/Short, Knock-out, Hebel und Bezugsverhältnis werden im Zertifikatemodul ergänzt.')
    turbo_isin = st.text_input('Turbo-/Knock-out-ISIN')
    if st.button('➕ Turbo hinzufügen', type='primary') and turbo_isin:
        st.session_state.turbos.append({'isin': turbo_isin.strip().upper(), 'name':'Neuer Turbo', 'status':'Watchlist'}); st.rerun()
    st.divider()
    for i, turbo in list(enumerate(st.session_state.turbos)):
        c1,c2,c3 = st.columns([4,2,1])
        c1.markdown(f"**{turbo['name']}**  \n`{turbo['isin']}`"); c2.write(turbo['status'])
        if c3.button('🗑️', key=f'turbo_del_{i}'):
            st.session_state.turbos.pop(i); st.rerun()

with analysis:
    st.subheader('Einzelanalyse')
    options = {f"{a['name']} ({a['symbol']})": a for a in st.session_state.assets}
    asset = options[st.selectbox('Wert auswählen', list(options))]
    if st.button('🔎 Analyse starten', type='primary'):
        df, err = candles(asset)
        if err: st.error(err)
        else:
            tech = technical(df)
            if not tech: st.warning('Nicht genügend Kursdaten.')
            else:
                ndata, nerr = news_for(asset['symbol']) if MA_KEY else (None, None)
                sent = news_sentiment(ndata) if ndata else None
                news_score = 50 if sent is None else round(max(0,min(100,50+sent*50)))
                overall = round(0.45*tech['short'] + 0.35*tech['medium'] + 0.20*news_score)
                c1,c2,c3,c4,c5 = st.columns(5)
                c1.metric('Kurzfristig', f"{tech['short']}/100"); c2.metric('Mittelfristig', f"{tech['medium']}/100"); c3.metric('News', f'{news_score}/100'); c4.metric('RSI', f"{tech['rsi']:.1f}"); c5.metric('Gesamt', f'{overall}/100')
                st.write('**Handlung:**', signal(overall))
                st.write('**Kurz zum Unternehmen:**', f"{asset['name']} ({asset['symbol']}) wird im MVP anhand von Kursmomentum, technischen Signalen und aktuellen Nachrichten bewertet. Ein separates Fundamentaldaten-/Unternehmensprofil-Modul ist als nächste Ausbaustufe vorgesehen.")
                st.line_chart(df.set_index('datetime')[['close']].rename(columns={'close':'Kurs'}))
                st.subheader('📰 Aktuelle Nachrichten')
                if not MA_KEY: st.info('Marketaux-Key fehlt. Hinterlege MARKETAUX_API_KEY in Streamlit Secrets.')
                elif nerr: st.error(nerr)
                else:
                    if sent is not None: st.caption(f'Durchschnittliches News-Sentiment: {sent:+.2f}')
                    for item in ndata.get('data', []):
                        st.markdown(f"**{item.get('title','Ohne Titel')}**")
                        st.caption(item.get('description','') or '')
                        st.write(f"Quelle: {item.get('source','—')} • {item.get('published_at','—')}")
                        if item.get('url'): st.markdown(f"[Artikel öffnen]({item['url']})")
                        st.divider()

with radar:
    st.subheader('🔥 Hype Radar')
    st.write('Der V2-Radar bewertet zunächst deine beobachteten Werte aus News-Menge, News-Sentiment und technischem Momentum. Ein breiter Markt-Scanner außerhalb deiner Watchlist ist als nächster Ausbau vorgesehen.')
    if not MA_KEY: st.warning('Hinterlege MARKETAUX_API_KEY in Streamlit Secrets.')
    else:
        radar_rows = []
        for asset in st.session_state.assets:
            ndata, _ = news_for(asset['symbol'], limit=5)
            sent = news_sentiment(ndata) if ndata else None
            n = len((ndata or {}).get('data', []))
            df, _ = candles(asset)
            tech = technical(df) if df is not None else None
            momentum = tech['short'] if tech else 50
            sentiment_component = 50 if sent is None else max(0,min(100,50+sent*50))
            activity_component = min(100,30+n*14)
            hype = round(0.45*activity_component + 0.30*sentiment_component + 0.25*momentum)
            radar_rows.append({'Aktie':asset['name'],'Ticker':asset['symbol'],'Hype-Score':hype,'News':n,'Sentiment':'—' if sent is None else round(sent,2),'Bewertung':signal(hype)})
        rdf = pd.DataFrame(radar_rows).sort_values('Hype-Score', ascending=False)
        st.dataframe(rdf, use_container_width=True, hide_index=True)
        if not rdf.empty:
            top = rdf.iloc[0]
            st.subheader('🔥 Aktuell auffälligster Wert')
            st.write(f"**{top['Aktie']} ({top['Ticker']})** — Hype-Score **{top['Hype-Score']}/100**")
            st.caption('Hype bedeutet nicht automatisch Kauf. Ein hoher Wert kann gleichzeitig technisch überhitzt sein.')

st.divider()
st.caption('Trading Assistant • Version 2')
