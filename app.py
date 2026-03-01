import streamlit as st
import requests

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

st.info("Simulation mode only — no real money traded. For strategy testing.")

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

# Expert signal input with dropdown
st.subheader("Enter Your Expert Signal")
col_market, col_adj = st.columns([3, 2])
with col_market:
    selected_market = st.selectbox("Select Market", known_markets, index=0)
with col_adj:
    adjustment = st.number_input("Adjustment (e.g. +0.24 for +24% beat)", value=0.0, step=0.01, format="%.2f")

if st.button("Scan Markets with Signal"):
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
                    
                    if edge > 0.10:
                        dir = "BUY YES" if adj > 0 else "SELL YES"
                        size = min(max_risk, vol / 50000 * 1000)
                        results.append({
                            "Market": m["question"],
                            "Volume": f"${vol:,}",
                            "Your Signal": f"{adj:+.2f}",
                            "Fair Guess": f"${fair:,.0f}M",
                            "Edge": f"{edge*100:.1f}%",
                            "Trade Idea": f"{dir} ~${size:,.0f}",
                            "Retrading": "Yes – anytime before resolution"
                        })
            
            # Fallback: add known markets if API scan was empty or low
            if not found_in_api or len(results) == 0:
                st.warning("Limited results from API scan — showing known active markets.")
                for known in known_markets:
                    adj = adjustment if selected_market == known else 0.0
                    crowd = 59.0 if "Scream 7" in known else 10.0 if "GOAT" in known else 100.0
                    fair = crowd * (1 + adj)
                    edge = 0.10 + adj * 3
                    if edge > 0.10:
                        dir = "BUY YES" if adj > 0 else "SELL YES"
                        size = min(max_risk, 10000)  # conservative fallback size
                        results.append({
                            "Market": known,
                            "Volume": "N/A (fallback)",
                            "Your Signal": f"{adj:+.2f}",
                            "Fair Guess": f"${fair:,.0f}M",
                            "Edge": f"{edge*100:.1f}%",
                            "Trade Idea": f"{dir} ~${size:,.0f}",
                            "Retrading": "Yes – anytime before resolution"
                        })
            
            if results:
                st.success(f"Found {len(results)} result(s)!")
                st.table(results)
            else:
                st.info("No strong edge yet — try a higher adjustment or different market.")
        
        except Exception as e:
            st.error(f"Scan failed: {str(e)}. Check internet or try again.")

st.markdown("---")
st.caption("Private tool — built for PG's network. Simulation only. Do not share credentials.")
