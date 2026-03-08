import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import feedparser
import re
from datetime import datetime

st.set_page_config(page_title="EE Intelligence", layout="wide")
st.title("📈 EasyEquities Intelligence Dashboard")

# ═══════════════════════════════════════════════════════════════════════════════
# 🌍 MASTER REGION FILTER
# ═══════════════════════════════════════════════════════════════════════════════

REGIONS = [
    "🌐 Overview",
    "🇿🇦 South Africa",
    "🇺🇸 USA",
    "🇨🇳 China",
    "🌏 Asia",
    "🇪🇺 Europe",
    "🌍 Africa",
]

st.sidebar.header("🌍 Region")
selected_region = st.sidebar.selectbox("Select Region:", REGIONS, label_visibility="collapsed")

# ═══════════════════════════════════════════════════════════════════════════════
# 📊 DATA DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

# --- Company Data ---
SA_COMPANIES = {
    "Banks": {
        "FirstRand": "FSR.JO", "Standard Bank": "SBK.JO", "Nedbank": "NED.JO",
        "Absa": "ABG.JO", "Capitec": "CPI.JO",
    },
    "Mining": {
        "Anglo American": "AGL.JO", "Gold Fields": "GFI.JO", "Sibanye Stillwater": "SSW.JO",
        "Impala Platinum": "IMP.JO", "AngloGold Ashanti": "AU", "Kumba Iron Ore": "KIO.JO",
        "Northam Platinum": "NPH.JO", "Harmony Gold": "HAR.JO", "Exxaro Resources": "EXX.JO", "South32": "S32.JO",
    },
    "Retail": {
        "Shoprite": "SHP.JO", "Mr Price": "MRP.JO", "Woolworths": "WHL.JO",
        "Clicks Group": "CLS.JO", "Pepkor": "PPH.JO", "Dis-Chem": "DCP.JO",
    },
    "Tech & Telecoms": {
        "Naspers": "NPN.JO", "Prosus": "PRX.JO", "MTN Group": "MTN.JO",
        "Vodacom": "VOD.JO", "MultiChoice": "MCG.JO",
    },
    "Insurance & Financial Services": {
        "Sanlam": "SLM.JO", "Old Mutual": "OMU.JO", "Discovery": "DSY.JO", "Remgro": "REM.JO",
    },
    "Industrials & Energy": {
        "Sasol": "SOL.JO", "Bidvest": "BVT.JO", "Mondi": "MNP.JO", "Richemont": "CFR.JO",
    },
    "Healthcare": {"Aspen Pharmacare": "APN.JO"},
    "Property": {"Growthpoint": "GRT.JO"},
}

USA_COMPANIES = {
    "Tech": {"Apple": "AAPL", "Microsoft": "MSFT", "Nvidia": "NVDA", "Alphabet": "GOOGL", "Meta": "META"},
    "Finance": {"JPMorgan": "JPM", "Goldman Sachs": "GS", "Bank of America": "BAC", "Visa": "V", "Berkshire": "BRK-B"},
    "Healthcare & Pharma": {"Johnson & Johnson": "JNJ", "Pfizer": "PFE", "UnitedHealth": "UNH", "Abbott Labs": "ABT", "Merck": "MRK"},
    "Consumer": {"Amazon": "AMZN", "Tesla": "TSLA", "Walmart": "WMT", "Coca-Cola": "KO", "Disney": "DIS"},
}

CHINA_COMPANIES = {
    "Tech": {"Alibaba": "BABA", "Tencent": "0700.HK", "Baidu": "BIDU", "JD.com": "JD", "PDD Holdings": "PDD"},
    "EV & Manufacturing": {"BYD": "BYDDY", "NIO": "NIO", "XPeng": "XPEV", "Li Auto": "LI", "CATL": "300750.SZ"},
    "Finance": {"ICBC": "1398.HK", "China Construction Bank": "0939.HK", "Ping An": "2318.HK", "Bank of China": "3988.HK", "China Merchants Bank": "3968.HK"},
}

ASIA_COMPANIES = {
    "Japan": {"Toyota": "TM", "Sony": "SONY", "Nintendo": "NTDOY", "SoftBank": "9984.T", "Mitsubishi": "8058.T"},
    "South Korea": {"Samsung": "005930.KS", "Hyundai": "005380.KS", "SK Hynix": "000660.KS", "LG Energy": "373220.KS", "Naver": "035420.KS"},
    "India": {"Reliance": "RELIANCE.NS", "TCS": "TCS.NS", "Infosys": "INFY", "HDFC Bank": "HDB", "Tata Motors": "TATAMOTORS.NS"},
}

EUROPE_COMPANIES = {
    "Luxury & Consumer": {"LVMH": "MC.PA", "Nestle": "NESN.SW", "Unilever": "ULVR.L", "Adidas": "ADS.DE", "L'Oréal": "OR.PA"},
    "Auto & Industrial": {"BMW": "BMW.DE", "Siemens": "SIE.DE", "Shell": "SHEL.L", "TotalEnergies": "TTE.PA", "ASML": "ASML.AS"},
    "Finance": {"HSBC": "HSBA.L", "BNP Paribas": "BNP.PA", "Barclays": "BARC.L", "UBS": "UBSG.SW", "Allianz": "ALV.DE"},
    "Pharma": {"AstraZeneca": "AZN.L", "Novo Nordisk": "NOVO-B.CO", "Roche": "ROG.SW", "Sanofi": "SAN.PA", "GSK": "GSK.L"},
}

AFRICA_COMPANIES = {
    "Nigeria": {"Dangote Cement": "DANGCEM.LG", "MTN Nigeria": "MTNN.LG", "Zenith Bank": "ZENITHBA.LG", "GTBank": "GUARANTY.LG", "BUA Cement": "BUACEMENT.LG"},
    "Kenya": {"Safaricom": "SCOM.NR", "Equity Group": "EQTY.NR", "KCB Group": "KCB.NR", "East African Breweries": "EABL.NR", "Co-operative Bank": "COOP.NR"},
    "Egypt": {"Commercial Intl Bank": "COMI.CA", "Eastern Company": "EAST.CA", "Telecom Egypt": "ETEL.CA", "EFG Hermes": "HRHO.CA", "Fawry": "FWRY.CA"},
}

REGION_COMPANY_MAP = {
    "🇿🇦 South Africa": ("🇿🇦 South African Companies — JSE Top 40", SA_COMPANIES),
    "🇺🇸 USA": ("🇺🇸 USA Companies", USA_COMPANIES),
    "🇨🇳 China": ("🇨🇳 China Companies", CHINA_COMPANIES),
    "🌏 Asia": ("🌏 Asia (Japan, Korea, India)", ASIA_COMPANIES),
    "🇪🇺 Europe": ("🇪🇺 European Companies", EUROPE_COMPANIES),
    "🌍 Africa": ("🌍 Africa (Nigeria, Kenya, Egypt)", AFRICA_COMPANIES),
}

# --- Stock Analysis Universe ---
STOCK_UNIVERSE = {
    "🇿🇦 South Africa": {
        "FirstRand": "FSR.JO", "Standard Bank": "SBK.JO", "Nedbank": "NED.JO", "Absa": "ABG.JO", "Capitec": "CPI.JO",
        "Anglo American": "AGL.JO", "Gold Fields": "GFI.JO", "Sibanye Stillwater": "SSW.JO", "Impala Platinum": "IMP.JO",
        "AngloGold Ashanti": "AU", "Kumba Iron Ore": "KIO.JO", "Northam Platinum": "NPH.JO", "Harmony Gold": "HAR.JO",
        "Exxaro Resources": "EXX.JO", "South32": "S32.JO", "Naspers": "NPN.JO", "Prosus": "PRX.JO",
        "MTN Group": "MTN.JO", "Vodacom": "VOD.JO", "Shoprite": "SHP.JO", "Mr Price": "MRP.JO",
        "Woolworths": "WHL.JO", "Clicks Group": "CLS.JO", "Pepkor": "PPH.JO", "Dis-Chem": "DCP.JO",
        "Sasol": "SOL.JO", "Bidvest": "BVT.JO", "Mondi": "MNP.JO", "Richemont": "CFR.JO",
        "Sanlam": "SLM.JO", "Old Mutual": "OMU.JO", "Discovery": "DSY.JO", "Remgro": "REM.JO",
        "MultiChoice": "MCG.JO", "Aspen Pharmacare": "APN.JO", "Growthpoint": "GRT.JO",
    },
    "🇺🇸 USA": {
        "Apple": "AAPL", "Microsoft": "MSFT", "Nvidia": "NVDA", "Amazon": "AMZN", "Alphabet": "GOOGL",
        "Meta": "META", "Tesla": "TSLA", "JPMorgan": "JPM", "Berkshire Hathaway": "BRK-B",
        "Johnson & Johnson": "JNJ", "Visa": "V", "Walmart": "WMT", "ExxonMobil": "XOM",
        "Pfizer": "PFE", "Coca-Cola": "KO", "Disney": "DIS", "Netflix": "NFLX", "AMD": "AMD",
        "Boeing": "BA", "Goldman Sachs": "GS",
    },
    "🇨🇳 China": {
        "Alibaba": "BABA", "Tencent": "0700.HK", "Baidu": "BIDU", "JD.com": "JD", "PDD Holdings": "PDD",
        "BYD": "BYDDY", "NIO": "NIO", "XPeng": "XPEV", "Li Auto": "LI", "CATL": "300750.SZ",
        "ICBC": "1398.HK", "Ping An": "2318.HK",
    },
    "🌏 Asia": {
        "Toyota": "TM", "Sony": "SONY", "Samsung": "005930.KS", "Hyundai": "005380.KS",
        "SK Hynix": "000660.KS", "Reliance": "RELIANCE.NS", "HDFC Bank": "HDB", "Infosys": "INFY",
        "Tata Motors": "TATAMOTORS.NS", "Nintendo": "NTDOY", "SoftBank": "9984.T",
        "Mitsubishi": "8058.T", "TSMC": "TSM",
    },
    "🇪🇺 Europe": {
        "LVMH": "MC.PA", "ASML": "ASML.AS", "Nestle": "NESN.SW", "Shell": "SHEL.L",
        "AstraZeneca": "AZN.L", "Siemens": "SIE.DE", "Novo Nordisk": "NOVO-B.CO",
        "BMW": "BMW.DE", "Unilever": "ULVR.L", "HSBC": "HSBA.L", "Barclays": "BARC.L",
        "BNP Paribas": "BNP.PA", "Roche": "ROG.SW", "Sanofi": "SAN.PA", "Allianz": "ALV.DE",
    },
    "🌍 Africa": {
        "Dangote Cement (Nigeria)": "DANGCEM.LG", "MTN Nigeria": "MTNN.LG",
        "Zenith Bank (Nigeria)": "ZENITHBA.LG", "GTBank (Nigeria)": "GUARANTY.LG",
        "Safaricom (Kenya)": "SCOM.NR", "Equity Group (Kenya)": "EQTY.NR",
        "KCB Group (Kenya)": "KCB.NR", "Commercial Intl Bank (Egypt)": "COMI.CA",
        "Telecom Egypt": "ETEL.CA", "East African Breweries (Kenya)": "EABL.NR",
    },
}

# --- News Feeds ---
NEWS_FEEDS = {
    "🇿🇦 South Africa": {
        "Moneyweb": "https://www.moneyweb.co.za/feed/",
        "BusinessDay SA": "https://www.businesslive.co.za/rss/",
    },
    "🇺🇸 USA": {
        "Reuters Business": "https://feeds.reuters.com/reuters/businessNews",
        "CNBC Top News": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
        "MarketWatch": "https://feeds.marketwatch.com/marketwatch/topstories/",
    },
    "🇨🇳 China": {
        "China Daily Business": "https://www.chinadaily.com.cn/rss/business_rss.xml",
    },
    "🌏 Asia": {
        "Reuters Business": "https://feeds.reuters.com/reuters/businessNews",
    },
    "🇪🇺 Europe": {
        "DW Business": "https://rss.dw.com/xml/rss-en-bus",
        "BBC Business": "https://feeds.bbci.co.uk/news/business/rss.xml",
    },
    "🌍 Africa": {
        "BBC Africa": "https://feeds.bbci.co.uk/news/world/africa/rss.xml",
        "Reuters Africa": "https://feeds.reuters.com/reuters/AFRICANews",
    },
}

# --- Exchange Announcement Feeds ---
EXCHANGE_FEEDS = {
    "🇿🇦 South Africa": {
        "ProfileData SENS": "https://www.profiledata.co.za/rss/sens.aspx",
        "ShareData SENS": "https://www.sharedata.co.za/Scripts/RSS.aspx",
        "Moneyweb SENS": "https://www.moneyweb.co.za/feed/",
    },
    "🇺🇸 USA": {
        "SEC EDGAR 8-K": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=8-K&dateb=&owner=include&count=20&search_text=&action=getcompany&output=atom",
        "PR Newswire Finance": "https://www.prnewswire.com/rss/financial-services-latest-news.rss",
    },
    "🇨🇳 China": {
        "HKEX News": "https://www.hkex.com.hk/eng/newsconsul/newsfeed/rss.xml",
        "China Daily Business": "https://www.chinadaily.com.cn/rss/business_rss.xml",
    },
    "🌏 Asia": {
        "Reuters Business": "https://feeds.reuters.com/reuters/businessNews",
    },
    "🇪🇺 Europe": {
        "DW Business": "https://rss.dw.com/xml/rss-en-bus",
        "FT Companies": "https://www.ft.com/companies?format=rss",
    },
    "🌍 Africa": {
        "BBC Africa": "https://feeds.bbci.co.uk/news/world/africa/rss.xml",
    },
}

# --- Earnings Key Takeaways ---
KEY_TAKEAWAYS = {
    "FSR.JO": {"sector": "SA Banks", "what_to_watch": "Net interest income growth, credit loss ratio, ROE target 18-22%, digital banking adoption, dividend payout."},
    "SBK.JO": {"sector": "SA Banks", "what_to_watch": "Africa Regions contribution, cost-to-income ratio, headline EPS, CIB revenue growth."},
    "NED.JO": {"sector": "SA Banks", "what_to_watch": "Managed Operations transformation, net interest margin, non-interest revenue, digital client growth."},
    "ABG.JO": {"sector": "SA Banks", "what_to_watch": "CIB market share, retail banking growth, pre-provision operating profit."},
    "CPI.JO": {"sector": "SA Banks", "what_to_watch": "Client growth rate, cost of credit, business banking expansion, headline earnings growth."},
    "AGL.JO": {"sector": "SA Mining", "what_to_watch": "Demerger updates, copper production growth, iron ore prices, cost per tonne, capital allocation."},
    "GFI.JO": {"sector": "SA Mining", "what_to_watch": "All-in sustaining costs (AISC), gold production, South Deep performance, net debt, dividend yield."},
    "SSW.JO": {"sector": "SA Mining", "what_to_watch": "PGM basket price impact, US recycling ops, battery metals strategy, free cash flow."},
    "IMP.JO": {"sector": "SA Mining", "what_to_watch": "PGM production volumes, unit cost performance, Zimbabwe ops, capex guidance."},
    "SHP.JO": {"sector": "SA Retail", "what_to_watch": "Market share gains, Checkers Sixty60 growth, trading profit margin, African expansion."},
    "NPN.JO": {"sector": "SA Tech", "what_to_watch": "Prosus NAV discount, Tencent stake value, e-commerce profitability, share buyback progress."},
    "MTN.JO": {"sector": "SA Telecoms", "what_to_watch": "Nigerian subscriber growth, data revenue, fintech (MoMo) volumes, tower monetisation."},
    "SOL.JO": {"sector": "SA Energy", "what_to_watch": "Oil price sensitivity, chemicals margins, Secunda operations, Lake Charles project."},
    "AAPL": {"sector": "US Tech", "what_to_watch": "iPhone revenue %, Services revenue growth, gross margin expansion, AI integration, China demand."},
    "MSFT": {"sector": "US Tech", "what_to_watch": "Azure cloud growth, AI (Copilot) revenue contribution, Office 365 seats, operating margin."},
    "NVDA": {"sector": "US Tech", "what_to_watch": "Data centre revenue, AI GPU demand (H100/B100), gaming segment, forward guidance."},
    "TSLA": {"sector": "US Auto", "what_to_watch": "Vehicle deliveries vs production, automotive gross margin, energy storage, FSD progress."},
    "BABA": {"sector": "China Tech", "what_to_watch": "China commerce recovery, cloud computing growth, international commerce, shareholder returns."},
    "MC.PA": {"sector": "EU Luxury", "what_to_watch": "Organic revenue by region, Fashion & Leather Goods margin, China demand recovery."},
}

# --- Indices ---
INDICES = {
    'JSE Top 40': 'STX40.JO', 'S&P 500': '^GSPC', 'FTSE 100 (UK)': '^FTSE',
    'DAX (Germany)': '^GDAXI', 'Nikkei (Japan)': '^N225',
}

COMMODITIES = {
    "Gold": "GC=F", "Silver": "SI=F", "Platinum": "PL=F",
    "Brent Crude Oil": "BZ=F", "WTI Crude Oil": "CL=F", "Copper": "HG=F",
}

CURRENCIES = {
    "USD/ZAR": "ZAR=X", "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X", "AUD/USD": "AUDUSD=X", "USD/CNY": "CNY=X",
    "EUR/GBP": "EURGBP=X", "EUR/ZAR": "EURZAR=X", "GBP/ZAR": "GBPZAR=X",
    "USD/CHF": "CHF=X", "USD/CAD": "CAD=X", "USD/INR": "INR=X",
    "USD/BRL": "BRL=X", "EUR/JPY": "EURJPY=X", "BTC/USD": "BTC-USD",
}

GEOPOLITICAL_FEEDS = {
    "Reuters World": "https://feeds.reuters.com/Reuters/worldNews",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "BBC World": "https://feeds.bbci.co.uk/news/world/rss.xml",
}

HIGH_IMPACT_KEYWORDS = [
    "war", "invasion", "sanctions", "tariff", "nuclear", "missile",
    "embargo", "coup", "military strike", "blockade", "ceasefire",
    "nato", "opec", "oil crisis", "debt default", "currency crash",
]
MEDIUM_IMPACT_KEYWORDS = [
    "election", "trade deal", "trade war", "summit", "treaty",
    "protest", "inflation", "interest rate", "central bank",
    "diplomatic", "refugee", "border", "regulation", "gdp",
]

INVESTMENT_MAP = {
    "war": {"assets": ["Gold (GC=F)", "Gold Fields (GFI.JO)", "AngloGold Ashanti (AU)"], "rationale": "Military conflict drives safe-haven demand for gold and boosts SA gold miners.", "icon": "⚔️"},
    "sanctions": {"assets": ["Brent Crude Oil (BZ=F)", "Platinum (PL=F)", "Impala Platinum (IMP.JO)", "Sasol (SOL.JO)"], "rationale": "Sanctions disrupt commodity supply chains — SA miners and energy benefit.", "icon": "🚫"},
    "tariff": {"assets": ["Shoprite (SHP.JO)", "Vodacom (VOD.JO)", "Gold (GC=F)"], "rationale": "Tariffs favour domestic-focused SA companies and gold as a hedge.", "icon": "📋"},
    "nuclear": {"assets": ["Gold (GC=F)", "Gold Fields (GFI.JO)", "Silver (SI=F)"], "rationale": "Nuclear escalation is the ultimate risk-off event — precious metals surge.", "icon": "☢️"},
    "opec": {"assets": ["Brent Crude Oil (BZ=F)", "WTI Crude Oil (CL=F)", "Sasol (SOL.JO)"], "rationale": "OPEC decisions directly move oil prices — Sasol is a direct play.", "icon": "🛢️"},
    "inflation": {"assets": ["FirstRand (FSR.JO)", "Standard Bank (SBK.JO)", "Capitec (CPI.JO)", "Gold (GC=F)"], "rationale": "Higher inflation → higher rates → SA banks earn more. Gold hedges purchasing power.", "icon": "📈"},
    "interest rate": {"assets": ["FirstRand (FSR.JO)", "Standard Bank (SBK.JO)", "Nedbank (NED.JO)"], "rationale": "Rate changes directly impact bank net interest margins.", "icon": "🏦"},
    "election": {"assets": ["JSE Top 40 (JTOPI.JO)", "Naspers (NPN.JO)", "FirstRand (FSR.JO)"], "rationale": "Elections bring policy uncertainty — broad JSE captures eventual direction.", "icon": "🗳️"},
    "coup": {"assets": ["Gold (GC=F)", "Gold Fields (GFI.JO)", "Platinum (PL=F)"], "rationale": "Political instability triggers safe-haven flows into precious metals.", "icon": "⚔️"},
    "currency crash": {"assets": ["Gold (GC=F)", "Anglo American (AGL.JO)", "Gold Fields (GFI.JO)"], "rationale": "Currency weakness benefits rand-hedged SA miners with USD revenue.", "icon": "💸"},
    "missile": {"assets": ["Gold (GC=F)", "Brent Crude Oil (BZ=F)"], "rationale": "Military escalation spikes risk-off assets and oil on supply fears.", "icon": "⚔️"},
}

SECTOR_ICONS = {
    "Banks": "🏦", "Finance": "🏦", "Mining": "⛏️", "Retail": "🛒",
    "Tech": "💻", "Tech & Telecoms": "📡", "Healthcare & Pharma": "💊", "Healthcare": "💊",
    "Consumer": "🛍️", "EV & Manufacturing": "🚗", "Auto & Industrial": "🏭",
    "Luxury & Consumer": "👜", "Pharma": "💊", "Property": "🏠",
    "Insurance & Financial Services": "🛡️", "Industrials & Energy": "🏭",
    "Japan": "🇯🇵", "South Korea": "🇰🇷", "India": "🇮🇳",
    "Nigeria": "🇳🇬", "Kenya": "🇰🇪", "Egypt": "🇪🇬",
}

# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def display_metric_cards(items_dict, row_size=5):
    """Display price/change metric cards in rows."""
    items = list(items_dict.items())
    for row_start in range(0, len(items), row_size):
        row = items[row_start:row_start + row_size]
        cols = st.columns(len(row))
        for col, (name, ticker) in zip(cols, row):
            try:
                data = yf.Ticker(ticker).history(period="5d")
                if not data.empty and len(data) >= 2:
                    current = data['Close'].iloc[-1]
                    prev = data['Close'].iloc[-2]
                    pct = ((current - prev) / prev) * 100
                    if ".JO" in ticker:
                        p = f"R{current:,.2f}"
                    elif ".L" in ticker:
                        p = f"£{current:,.2f}"
                    elif any(x in ticker for x in [".PA", ".DE", ".AS"]):
                        p = f"€{current:,.2f}"
                    elif current < 100 and "=X" in ticker:
                        p = f"{current:,.4f}"
                    elif any(x in ticker for x in [".T", ".KS", ".HK", ".NS", ".SS", ".SZ", ".SW", ".CO"]):
                        p = f"{current:,.2f}"
                    else:
                        p = f"${current:,.2f}"
                    col.metric(name, p, f"{pct:.2f}%")
                else:
                    col.metric(name, "N/A", "")
            except Exception:
                col.metric(name, "N/A", "")


def display_company_section(title, companies_by_sector):
    """Display companies grouped by sector with metric cards."""
    st.header(title)
    for sector, stocks in companies_by_sector.items():
        icon = SECTOR_ICONS.get(sector, "📊")
        st.subheader(f"{icon} {sector}")
        display_metric_cards(stocks, row_size=5)


def classify_impact(text):
    text_lower = text.lower()
    for kw in HIGH_IMPACT_KEYWORDS:
        if kw in text_lower:
            return "🔴 High"
    for kw in MEDIUM_IMPACT_KEYWORDS:
        if kw in text_lower:
            return "🟡 Medium"
    return "🟢 Low"


@st.cache_data(ttl=900)
def fetch_geopolitical_events():
    events = []
    for source, url in GEOPOLITICAL_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                title = entry.get("title", "")
                summary = re.sub(r"<[^>]+>", "", entry.get("summary", entry.get("description", "")))
                published = entry.get("published", "")
                link = entry.get("link", "")
                combined = f"{title} {summary}"
                impact = classify_impact(combined)
                events.append({"Impact": impact, "Headline": title, "Source": source, "Date": published, "Summary": summary[:300], "Link": link})
        except Exception:
            continue
    impact_order = {"🔴 High": 0, "🟡 Medium": 1, "🟢 Low": 2}
    events.sort(key=lambda e: impact_order.get(e["Impact"], 3))
    return pd.DataFrame(events)


@st.cache_data(ttl=900)
def fetch_news(feeds_dict, max_per_source=8):
    articles = []
    for source, url in feeds_dict.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_per_source]:
                title = entry.get("title", "")
                summary = re.sub(r"<[^>]+>", "", entry.get("summary", entry.get("description", "")))
                published = entry.get("published", entry.get("updated", ""))
                link = entry.get("link", "")
                articles.append({"Headline": title, "Source": source, "Date": published, "Summary": summary[:300], "Link": link})
        except Exception:
            continue
    return articles


def generate_investment_signals(events_dataframe):
    if events_dataframe.empty:
        return []
    recommendations, seen = [], set()
    for _, event in events_dataframe.iterrows():
        text = f"{event.get('Headline', '')} {event.get('Summary', '')}".lower()
        for keyword, mapping in INVESTMENT_MAP.items():
            if keyword in text and keyword not in seen:
                seen.add(keyword)
                recommendations.append({
                    "icon": mapping["icon"], "trigger": keyword.title(),
                    "headline": event.get("Headline", ""), "assets": mapping["assets"],
                    "rationale": mapping["rationale"], "impact": event.get("Impact", ""),
                })
    return recommendations


@st.cache_data(ttl=3600)
def fetch_earnings_dates(ticker_dict):
    results = []
    for name, ticker in ticker_dict.items():
        try:
            stock = yf.Ticker(ticker)
            cal = stock.calendar
            next_date = "TBA"
            if cal is not None and not (isinstance(cal, pd.DataFrame) and cal.empty):
                if isinstance(cal, dict):
                    ed = cal.get("Earnings Date", [None])
                    if isinstance(ed, list) and len(ed) > 0:
                        next_date = str(ed[0])[:10]
                    elif ed:
                        next_date = str(ed)[:10]
                elif isinstance(cal, pd.DataFrame) and "Earnings Date" in cal.index:
                    next_date = str(cal.loc["Earnings Date"].iloc[0])[:10]
            tk = KEY_TAKEAWAYS.get(ticker, {})
            results.append({
                "Company": name, "Ticker": ticker, "Next Earnings": next_date,
                "Sector": tk.get("sector", ""), "Key Takeaways": tk.get("what_to_watch", "Monitor headline earnings, revenue growth, and management guidance."),
            })
        except Exception:
            tk = KEY_TAKEAWAYS.get(ticker, {})
            results.append({"Company": name, "Ticker": ticker, "Next Earnings": "TBA", "Sector": tk.get("sector", ""), "Key Takeaways": tk.get("what_to_watch", "Monitor headline earnings, revenue growth, and guidance.")})
    results.sort(key=lambda x: x["Next Earnings"] if x["Next Earnings"] != "TBA" else "9999")
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 📱 MOBILE ACCESS INFO (sidebar)
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar.expander("📱 Access on Phone"):
    st.markdown("""
**Same WiFi (local):**
1. Run `streamlit run dashboard.py --server.address 0.0.0.0`
2. Find your PC's IP: `ipconfig` in cmd
3. Open `http://<YOUR-IP>:8501` on phone

**Public (Streamlit Cloud):**
1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo → deploy → access anywhere
    """)


# ═══════════════════════════════════════════════════════════════════════════════
# 🌐 SECTION 1: GLOBAL OVERVIEW (always visible)
# ═══════════════════════════════════════════════════════════════════════════════

st.header("🌐 Global & Local Indices")
display_metric_cards(INDICES, row_size=5)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: COMPANIES (filtered by region)
# ═══════════════════════════════════════════════════════════════════════════════

if selected_region != "🌐 Overview":
    if selected_region in REGION_COMPANY_MAP:
        title, companies = REGION_COMPANY_MAP[selected_region]
        display_company_section(title, companies)
        st.markdown("---")
else:
    # Overview shows a summary: one metric per region index
    st.caption("Select a region from the sidebar to see detailed company data, news, and analysis.")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: COMMODITIES & CURRENCIES (always visible)
# ═══════════════════════════════════════════════════════════════════════════════

st.header("📦 Commodities")
display_metric_cards(COMMODITIES, row_size=6)

selected_commodity = st.selectbox("📊 View commodity chart:", list(COMMODITIES.keys()))
if selected_commodity:
    comm_data = yf.download(COMMODITIES[selected_commodity], period="3mo")
    if not comm_data.empty:
        fig_c = go.Figure()
        fig_c.add_trace(go.Scatter(
            x=comm_data.index, y=comm_data['Close'].squeeze(), mode='lines', name=selected_commodity,
            line=dict(color='#FFD700' if 'Gold' in selected_commodity else '#2196F3', width=2),
            fill='tozeroy', fillcolor='rgba(255,215,0,0.1)' if 'Gold' in selected_commodity else 'rgba(33,150,243,0.1)',
        ))
        fig_c.update_layout(title=f"{selected_commodity} — 3 Month Price", template="plotly_dark", height=350)
        st.plotly_chart(fig_c, use_container_width=True)

st.markdown("---")

st.header("💱 Major Currencies")
display_metric_cards(CURRENCIES, row_size=5)

selected_currency = st.selectbox("📊 View currency chart:", list(CURRENCIES.keys()))
if selected_currency:
    curr_data = yf.download(CURRENCIES[selected_currency], period="3mo")
    if not curr_data.empty:
        fig_fx = go.Figure()
        fig_fx.add_trace(go.Scatter(
            x=curr_data.index, y=curr_data['Close'].squeeze(), mode='lines', name=selected_currency,
            line=dict(color='#00E676', width=2), fill='tozeroy', fillcolor='rgba(0,230,118,0.1)',
        ))
        fig_fx.update_layout(title=f"{selected_currency} — 3 Month Exchange Rate", template="plotly_dark", height=350)
        st.plotly_chart(fig_fx, use_container_width=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: GEOPOLITICAL EVENTS (always visible)
# ═══════════════════════════════════════════════════════════════════════════════

st.header("🌍 Geopolitical Events Tracker")

impact_filter = st.sidebar.selectbox("Geopolitical Impact Filter:", ["All", "🔴 High", "🟡 Medium", "🟢 Low"])

events_df = fetch_geopolitical_events()

if events_df.empty:
    st.info("⏳ Unable to fetch geopolitical events right now. Please try again later.")
else:
    filtered_df = events_df if impact_filter == "All" else events_df[events_df["Impact"] == impact_filter]
    st.caption(f"Showing {len(filtered_df)} events  •  Auto-refreshes every 15 min")
    st.dataframe(filtered_df[["Impact", "Headline", "Source", "Date"]], use_container_width=True, hide_index=True)

    high_impact = filtered_df[filtered_df["Impact"] == "🔴 High"]
    if not high_impact.empty:
        st.subheader("⚠️ High-Impact Event Details")
        for _, row in high_impact.iterrows():
            with st.expander(f"🔴 {row['Headline']}"):
                st.write(f"**Source:** {row['Source']}  |  **Date:** {row['Date']}")
                st.write(row["Summary"])
                if row["Link"]:
                    st.markdown(f"[Read full article →]({row['Link']})")
                st.warning("⚡ This event may cause significant market volatility.")

st.markdown("---")

# Investment Intelligence
st.header("🧠 Where to Look — Investment Intelligence")
signals = generate_investment_signals(events_df)

if not signals:
    st.info("No specific investment signals detected from current events.")
else:
    for sig in signals:
        label = f"{sig['icon']} {sig['trigger']} — \"{sig['headline'][:80]}\"" if len(sig['headline']) > 80 else f"{sig['icon']} {sig['trigger']} — \"{sig['headline']}\""
        with st.expander(label):
            st.markdown(f"**Triggered by:** {sig['impact']} impact event")
            st.markdown(f"**💡 Rationale:** {sig['rationale']}")
            st.markdown("**📌 Assets to watch:**")
            asset_cols = st.columns(min(len(sig['assets']), 4))
            for i, asset in enumerate(sig['assets']):
                asset_cols[i % 4].success(f"✅ {asset}")
    st.info("⚠️ **Disclaimer:** These signals are for educational purposes only — not financial advice.")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5: NEWS & ANNOUNCEMENTS (filtered by region)
# ═══════════════════════════════════════════════════════════════════════════════

if selected_region != "🌐 Overview" and selected_region in NEWS_FEEDS:
    st.header(f"📰 {selected_region} News")
    news = fetch_news(NEWS_FEEDS[selected_region])
    if news:
        for article in news[:12]:
            with st.expander(f"📌 {article['Headline']}"):
                st.caption(f"{article['Source']}  •  {article['Date']}")
                st.write(article['Summary'])
                if article['Link']:
                    st.markdown(f"[Read full article →]({article['Link']})")
    else:
        st.info("⏳ Unable to load news right now.")
    st.markdown("---")

if selected_region != "🌐 Overview" and selected_region in EXCHANGE_FEEDS:
    st.header(f"📢 {selected_region} Company Announcements")
    announcements = fetch_news(EXCHANGE_FEEDS[selected_region])
    if announcements:
        for ann in announcements[:10]:
            with st.expander(f"📋 {ann['Headline']}"):
                st.caption(f"{ann['Source']}  •  {ann['Date']}")
                st.write(ann['Summary'])
                if ann['Link']:
                    st.markdown(f"[View full announcement →]({ann['Link']})")
    else:
        st.info("⏳ Unable to load announcements right now.")
    st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6: STOCK ANALYSIS (filtered by region)
# ═══════════════════════════════════════════════════════════════════════════════

if selected_region != "🌐 Overview":
    region_key = selected_region
    if region_key in STOCK_UNIVERSE:
        region_stocks = STOCK_UNIVERSE[region_key]
        stock_names = list(region_stocks.keys())

        st.sidebar.markdown("---")
        st.sidebar.header("📊 Stock Analysis")
        selected_name = st.sidebar.selectbox("Select Stock:", stock_names)
        custom_ticker = st.sidebar.text_input("Or enter a custom ticker:", "")

        if custom_ticker.strip():
            analysis_ticker = custom_ticker.strip().upper()
            analysis_label = analysis_ticker
        else:
            analysis_ticker = region_stocks[selected_name]
            analysis_label = f"{selected_name} ({analysis_ticker})"

        st.header(f"📊 Stock Analysis — {selected_region}")

        if analysis_ticker:
            df = yf.download(analysis_ticker, period="1y")
            if not df.empty:
                df['SMA_50'] = df['Close'].rolling(window=50).mean()
                df['SMA_200'] = df['Close'].rolling(window=200).mean()
                latest_close = float(df['Close'].values[-1])
                sma_50 = float(df['SMA_50'].values[-1])
                sma_200 = float(df['SMA_200'].values[-1])

                if sma_50 > sma_200 and latest_close > sma_50:
                    signal = "🟢 BUY (Bullish Trend)"
                    explanation = (
                        f"The **50-day SMA ({sma_50:,.2f})** is above the **200-day SMA ({sma_200:,.2f})**, "
                        f"forming a **Golden Cross**. Price ({latest_close:,.2f}) is above both — strong upward momentum. "
                        f"Buyers are in control."
                    )
                elif sma_50 < sma_200 and latest_close < sma_50:
                    signal = "🔴 SELL (Bearish Trend)"
                    explanation = (
                        f"The **50-day SMA ({sma_50:,.2f})** crossed below the **200-day SMA ({sma_200:,.2f})**, "
                        f"forming a **Death Cross**. Price ({latest_close:,.2f}) is below both — sustained selling pressure."
                    )
                else:
                    signal = "🟡 HODL (Consolidating)"
                    explanation = (
                        f"The stock is **consolidating**. The 50-day SMA ({sma_50:,.2f}) and 200-day SMA ({sma_200:,.2f}) "
                        f"aren't giving a clear signal, with price ({latest_close:,.2f}) caught between them. Wait for breakout."
                    )

                st.subheader(f"{analysis_label} Intelligence")
                c1, c2, c3 = st.columns(3)
                c1.metric("Price", f"{latest_close:,.2f}")
                c2.metric("50-Day SMA", f"{sma_50:,.2f}")
                c3.metric("200-Day SMA", f"{sma_200:,.2f}")
                st.markdown(f"**Current Signal:** {signal}")

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'].squeeze(), mode='lines', name='Close Price'))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'].squeeze(), mode='lines', name='50-Day SMA', line=dict(dash='dot')))
                fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'].squeeze(), mode='lines', name='200-Day SMA', line=dict(dash='dash')))
                fig.update_layout(title=f"{analysis_label} — 1 Year Price Action", template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

                st.markdown("---")
                st.subheader("📖 Why This Signal?")
                st.markdown(explanation)
                st.caption("Based on SMA crossover analysis. 50-day SMA = short-term momentum, 200-day SMA = long-term trend. For educational purposes only.")
            else:
                st.warning(f"Could not load data for {analysis_ticker}.")

        st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7: EARNINGS TRACKER (filtered by region)
# ═══════════════════════════════════════════════════════════════════════════════

if selected_region != "🌐 Overview" and selected_region in STOCK_UNIVERSE:
    st.header(f"📅 Earnings & AFS Tracker — {selected_region}")
    st.caption("Upcoming earnings releases and key things to watch")

    earnings_tickers = STOCK_UNIVERSE[selected_region]
    with st.spinner("Fetching earnings calendar..."):
        earnings_data = fetch_earnings_dates(earnings_tickers)

    if earnings_data:
        earns_df = pd.DataFrame(earnings_data)
        st.dataframe(earns_df[["Company", "Ticker", "Next Earnings", "Sector"]], use_container_width=True, hide_index=True)

        st.subheader("🔍 Key Takeaways")
        for entry in earnings_data:
            status_icon = "🟢" if entry["Next Earnings"] != "TBA" else "⏳"
            with st.expander(f"{status_icon} {entry['Company']} ({entry['Ticker']}) — {entry['Next Earnings']}"):
                st.markdown(f"**Sector:** {entry['Sector'] or 'N/A'}")
                st.markdown(f"**Next Earnings / AFS:** {entry['Next Earnings']}")
                st.markdown("**🔑 Key Things to Watch:**")
                st.info(entry["Key Takeaways"])

    if "South Africa" in selected_region:
        st.caption(
            "📌 JSE companies must publish AFS within 3 months of year-end. "
            "SA banks typically report in March (interim) and September (full year). "
            "Mining companies typically report in February and August."
        )