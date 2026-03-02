import streamlit as st
import requests
import time
import pandas as pd

st.set_page_config(page_title="Hollywood Gross Oracle - PG", layout="wide")

st.title("Hollywood Gross Oracle")
st.markdown("**Your private Polymarket edge tool** — simulation only. Powered by your insider network.")

# Bankroll & risk settings
col1, col2 = st.columns(2)
with col1:
    bankroll = st.number_input("Simulation Bankroll ($)", min_value=10000, value=250000, step=50000)
with col2:
    risk_pct = st.slider("Max risk per trade (%)", min_value=1.0, max_value=10.0, value=5.0, step=0.5)
max_risk = bankroll * (risk_pct / 100)
st.markdown(f"**Max risk per trade: ${max_risk:,.0f}** ({risk_pct}% rule)")

st.info("Simulation mode only — no real money traded. Auto-scans every 10 minutes.")

# Known markets for dropdown + fallback
known_markets = [
    "Scream 7 Opening Weekend Box Office",
    "Highest Grossing Movie in 2026",
    "Biggest Opening Weekend in 2026",
    "Avengers: Doomsday Opening Weekend",
    "The Super Mario Galaxy Movie Opening Weekend",
    "Spider-Man: Brand New Day Opening Weekend",
    "How to Make a Killing Opening Weekend",
    "GOAT Third Weekend Box Office",
    "Wuthering Heights Third Weekend Box Office"
]

# Session state for auto-scan
if 'last_scan_time' not in st.session_state:
    st.session_state.last_scan_time = time.time()
if 'selected_market' not in st.session_state:
    st.session_state.selected_market = known_markets[0]
if 'adjustment' not in st.session_state:
    st.session_state.adjustment = 0.0

# Signal input
st.subheader("Enter Your Expert Signal")
col_market, col_adj = st.columns([3, 2])
with col_market:
    selected_market = st.selectbox("Select Market", known_markets, index=known_markets.index(st.session_state.selected_market))
with col_adj:
    adjustment = st.number_input("Adjustment (e.g. +0.24 for +24% beat)", value=st.session_state.adjustment, step=0.01, format="%.2f")

st.session_state.selected_market = selected_market
st.session_state.adjustment = adjustment

# Countdown
current_time = time.time()
time_since_last_scan = current_time - st.session_state.last_scan_time
minutes_left = 10 - int(time_since_last_scan // 60)
seconds_left = 60 - int(time_since_last_scan % 60)
st.markdown(f"**Next auto-scan in {minutes_left} min {seconds_left} sec** (refreshes automatically)")

should_scan = st.button("Scan Now") or time_since_last_scan >= 600

if should_scan:
    with st.spinner("Scanning Polymarket..."):
        url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=200&order=volume&ascending=false"
        try:
            resp = requests.get(url)
            markets = resp.json()
            
            results = []
            found_in_api = False
            
            for m in markets:
                q = m.get("question", "").lower()
                vol = round(float(m.get("volume", 0)))
                keywords = ["gross", "box office", "opening weekend", "scream", "avengers", "mario", "spider-man", "highest grossing", "grossing", "domestic gross", "opening", "weekend", "goat"]
                if any(kw in q for kw in keywords):
                    found_in_api = True
                    adj = adjustment if selected_market.lower() in q else 0.0
                    crowd = 59.0 if "scream" in q else 10.0 if "goat" in q else 100.0
                    fair = crowd * (1 + adj)
                    edge = 0.10 + adj * 3
                    
                    dir = "BUY YES" if adj > 0 else "SELL YES" if adj < 0 else "HOLD / MONITOR"
                    size = min(max_risk, vol / 50000 * 1000) if edge > 0.10 else 0
                    trade_idea = f"{dir} ~${size:,.0f}" if edge > 0.10 else "No strong edge"
                    
                    market_slug = m.get("slug", "")
                    polymarket_url = f"https://polymarket.com/event/{market_slug}" if market_slug else "https://polymarket.com"
                    
                    results.append({
                        "Market": m["question"],
                        "Polymarket URL": polymarket_url,
                        "Volume": f"${vol:,}",
                        "Your Signal": f"{adj:+.2f}",
                        "Crowd Guess": f"${crowd:,.0f}M",
                        "Fair Guess": f"${fair:,.0f}M",
                        "Edge": f"{edge*100:.1f}%",
                        "Trade Idea": trade_idea,
                        "Retrading": "Yes – anytime before resolution"
                    })
            
            # Fallback
            if not found_in_api or len(results) == 0:
                st.warning("Limited API results — showing known active markets.")
                for known in known_markets:
                    adj = adjustment if selected_market == known else 0.0
                    crowd = 59.0 if "Scream 7" in known else 10.0 if "GOAT" in known else 100.0
                    fair = crowd * (1 + adj)
                    edge = 0.10 + adj * 3
                    
                    dir = "BUY YES" if adj > 0 else "SELL YES" if adj < 0 else "HOLD / MONITOR"
                    size = min(max_risk, 10000) if edge > 0.10 else 0
                    trade_idea = f"{dir} ~${size:,.0f}" if edge > 0.10 else "No strong edge"
                    
                    slug = known.lower().replace(" ", "-").replace(":", "").replace("(", "").replace(")", "")
                    polymarket_url = f"https://polymarket.com/event/{slug}"
                    
                    results.append({
                        "Market": known,
                        "Polymarket URL": polymarket_url,
                        "Volume": "N/A (fallback)",
                        "Your Signal": f"{adj:+.2f}",
                        "Crowd Guess": f"${crowd:,.0f}M",
                        "Fair Guess": f"${fair:,.0f}M",
                        "Edge": f"{edge*100:.1f}%",
                        "Trade Idea": trade_idea,
                        "Retrading": "Yes – anytime before resolution"
                    })
            
            st.session_state.last_scan_time = current_time
            
            if results:
                st.success(f"Showing {len(results)} market(s) — edge >10% highlighted")
                df = pd.DataFrame(results)
                
                # Hide link column
                df_display = df.drop(columns=["Polymarket URL"])
                
                # Style
                def highlight_trade(val):
                    if 'BUY' in str(val):
                        return 'color: green; font-weight: bold'
                    elif 'SELL' in str(val):
                        return 'color: red; font-weight: bold'
                    return ''
                
                def highlight_edge(val):
                    try:
                        if float(val.strip('%')) > 10:
                            return 'background-color: rgba(0, 255, 0, 0.2); font-weight: bold'
                    except:
                        pass
                    return ''
                
                def make_clickable(val, row):
                    link = row['Polymarket URL']
                    return f'<a href="{link}" target="_blank">{val}</a>'
                
                # Apply styles
                styled_df = df_display.style.applymap(highlight_trade, subset=['Trade Idea']) \
                                            .applymap(highlight_edge, subset=['Edge']) \
                                            .format({"Market": lambda x: make_clickable(x, df.loc[df_display['Market'] == x].iloc[0])})
                
                st.dataframe(styled_df, use_container_width=True)
            else:
                st.info("No markets matched. Try a different adjustment or market.")
        
        except Exception as e:
            st.error(f"Scan failed: {str(e)}. Check internet or try again.")

st.markdown("---")
st.caption("Private tool — built for PG's network. Simulation only. Do not share credentials.")
