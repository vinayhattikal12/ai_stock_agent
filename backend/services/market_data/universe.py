import logging
from datetime import date, datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger("universe")

# =====================================================================
# SEBI/AMFI Categorized Universe Registry (Semiannual Reclassification)
# Large Cap: Top 1-100 by market capitalization
# Mid Cap: 101-250 by market capitalization
# Small Cap: 251st onward by market capitalization
# Classification Source: AMFI / SEBI Semiannual Reclassification
# =====================================================================

CLASSIFICATION_SOURCE = "SEBI/AMFI Semiannual Framework"
CLASSIFICATION_DATE = date(2024, 12, 31)

NSE_RANKED_UNIVERSE: List[Dict[str, Any]] = [
    # -------------------------------------------------------------
    # 1. TOP LARGE-CAP STOCKS (Ranks 1 to 100)
    # -------------------------------------------------------------
    {"symbol": "RELIANCE", "name": "Reliance Industries Ltd", "sector": "Energy", "instrument_key": "NSE_EQ|INE002A01018", "market_cap_category": "LARGE_CAP", "market_cap_rank": 1},
    {"symbol": "TCS", "name": "Tata Consultancy Services Ltd", "sector": "IT", "instrument_key": "NSE_EQ|INE467B01029", "market_cap_category": "LARGE_CAP", "market_cap_rank": 2},
    {"symbol": "HDFCBANK", "name": "HDFC Bank Ltd", "sector": "Banking", "instrument_key": "NSE_EQ|INE040A01034", "market_cap_category": "LARGE_CAP", "market_cap_rank": 3},
    {"symbol": "BHARTIARTL", "name": "Bharti Airtel Ltd", "sector": "Telecom", "instrument_key": "NSE_EQ|INE397D01024", "market_cap_category": "LARGE_CAP", "market_cap_rank": 4},
    {"symbol": "ICICIBANK", "name": "ICICI Bank Ltd", "sector": "Banking", "instrument_key": "NSE_EQ|INE090A01021", "market_cap_category": "LARGE_CAP", "market_cap_rank": 5},
    {"symbol": "INFY", "name": "Infosys Ltd", "sector": "IT", "instrument_key": "NSE_EQ|INE009A01021", "market_cap_category": "LARGE_CAP", "market_cap_rank": 6},
    {"symbol": "SBIN", "name": "State Bank of India", "sector": "Banking", "instrument_key": "NSE_EQ|INE062A01020", "market_cap_category": "LARGE_CAP", "market_cap_rank": 7},
    {"symbol": "HINDUNILVR", "name": "Hindustan Unilever Ltd", "sector": "FMCG", "instrument_key": "NSE_EQ|INE030A01027", "market_cap_category": "LARGE_CAP", "market_cap_rank": 8},
    {"symbol": "ITC", "name": "ITC Ltd", "sector": "FMCG", "instrument_key": "NSE_EQ|INE154A01025", "market_cap_category": "LARGE_CAP", "market_cap_rank": 9},
    {"symbol": "LT", "name": "Larsen & Toubro Ltd", "sector": "Infrastructure", "instrument_key": "NSE_EQ|INE018A01030", "market_cap_category": "LARGE_CAP", "market_cap_rank": 10},
    {"symbol": "BAJFINANCE", "name": "Bajaj Finance Ltd", "sector": "Financial Services", "instrument_key": "NSE_EQ|INE296A01024", "market_cap_category": "LARGE_CAP", "market_cap_rank": 11},
    {"symbol": "HCLTECH", "name": "HCL Technologies Ltd", "sector": "IT", "instrument_key": "NSE_EQ|INE860A01027", "market_cap_category": "LARGE_CAP", "market_cap_rank": 12},
    {"symbol": "MARUTI", "name": "Maruti Suzuki India Ltd", "sector": "Auto", "instrument_key": "NSE_EQ|INE585B01010", "market_cap_category": "LARGE_CAP", "market_cap_rank": 13},
    {"symbol": "SUNPHARMA", "name": "Sun Pharmaceutical Industries Ltd", "sector": "Pharma", "instrument_key": "NSE_EQ|INE044A01036", "market_cap_category": "LARGE_CAP", "market_cap_rank": 14},
    {"symbol": "M&M", "name": "Mahindra & Mahindra Ltd", "sector": "Auto", "instrument_key": "NSE_EQ|INE101A01026", "market_cap_category": "LARGE_CAP", "market_cap_rank": 15},
    {"symbol": "TATAMOTORS", "name": "Tata Motors Ltd", "sector": "Auto", "instrument_key": "NSE_EQ|INE155A01022", "market_cap_category": "LARGE_CAP", "market_cap_rank": 16},
    {"symbol": "NTPC", "name": "NTPC Ltd", "sector": "Power", "instrument_key": "NSE_EQ|INE733E01010", "market_cap_category": "LARGE_CAP", "market_cap_rank": 17},
    {"symbol": "ONGC", "name": "Oil & Natural Gas Corp Ltd", "sector": "Energy", "instrument_key": "NSE_EQ|INE213A01029", "market_cap_category": "LARGE_CAP", "market_cap_rank": 18},
    {"symbol": "POWERGRID", "name": "Power Grid Corp of India Ltd", "sector": "Power", "instrument_key": "NSE_EQ|INE752E01010", "market_cap_category": "LARGE_CAP", "market_cap_rank": 19},
    {"symbol": "AXISBANK", "name": "Axis Bank Ltd", "sector": "Banking", "instrument_key": "NSE_EQ|INE238A01034", "market_cap_category": "LARGE_CAP", "market_cap_rank": 20},
    {"symbol": "TITAN", "name": "Titan Company Ltd", "sector": "Consumer", "instrument_key": "NSE_EQ|INE280A01028", "market_cap_category": "LARGE_CAP", "market_cap_rank": 21},
    {"symbol": "ADANIENT", "name": "Adani Enterprises Ltd", "sector": "Diversified", "instrument_key": "NSE_EQ|INE423A01024", "market_cap_category": "LARGE_CAP", "market_cap_rank": 22},
    {"symbol": "ADANIPORTS", "name": "Adani Ports & SEZ Ltd", "sector": "Infrastructure", "instrument_key": "NSE_EQ|INE742F01042", "market_cap_category": "LARGE_CAP", "market_cap_rank": 23},
    {"symbol": "COALINDIA", "name": "Coal India Ltd", "sector": "Metals", "instrument_key": "NSE_EQ|INE522F01014", "market_cap_category": "LARGE_CAP", "market_cap_rank": 24},
    {"symbol": "TATASTEEL", "name": "Tata Steel Ltd", "sector": "Metals", "instrument_key": "NSE_EQ|INE081A01020", "market_cap_category": "LARGE_CAP", "market_cap_rank": 25},
    {"symbol": "JSWSTEEL", "name": "JSW Steel Ltd", "sector": "Metals", "instrument_key": "NSE_EQ|INE019A01038", "market_cap_category": "LARGE_CAP", "market_cap_rank": 26},
    {"symbol": "HINDALCO", "name": "Hindalco Industries Ltd", "sector": "Metals", "instrument_key": "NSE_EQ|INE038A01020", "market_cap_category": "LARGE_CAP", "market_cap_rank": 27},
    {"symbol": "WIPRO", "name": "Wipro Ltd", "sector": "IT", "instrument_key": "NSE_EQ|INE075A01022", "market_cap_category": "LARGE_CAP", "market_cap_rank": 28},
    {"symbol": "TECHM", "name": "Tech Mahindra Ltd", "sector": "IT", "instrument_key": "NSE_EQ|INE669C01036", "market_cap_category": "LARGE_CAP", "market_cap_rank": 29},
    {"symbol": "LTIM", "name": "LTIMindtree Ltd", "sector": "IT", "instrument_key": "NSE_EQ|INE214T01019", "market_cap_category": "LARGE_CAP", "market_cap_rank": 30},
    {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank Ltd", "sector": "Banking", "instrument_key": "NSE_EQ|INE237A01028", "market_cap_category": "LARGE_CAP", "market_cap_rank": 31},
    {"symbol": "INDUSINDBK", "name": "IndusInd Bank Ltd", "sector": "Banking", "instrument_key": "NSE_EQ|INE095A01012", "market_cap_category": "LARGE_CAP", "market_cap_rank": 32},
    {"symbol": "BAJAJFINSV", "name": "Bajaj Finserv Ltd", "sector": "Financial Services", "instrument_key": "NSE_EQ|INE918I01026", "market_cap_category": "LARGE_CAP", "market_cap_rank": 33},
    {"symbol": "BAJAJ-AUTO", "name": "Bajaj Auto Ltd", "sector": "Auto", "instrument_key": "NSE_EQ|INE917I01010", "market_cap_category": "LARGE_CAP", "market_cap_rank": 34},
    {"symbol": "EICHERMOT", "name": "Eicher Motors Ltd", "sector": "Auto", "instrument_key": "NSE_EQ|INE066A01021", "market_cap_category": "LARGE_CAP", "market_cap_rank": 35},
    {"symbol": "TVSMOTOR", "name": "TVS Motor Company Ltd", "sector": "Auto", "instrument_key": "NSE_EQ|INE494B01023", "market_cap_category": "LARGE_CAP", "market_cap_rank": 36},
    {"symbol": "HEROMOTOCO", "name": "Hero MotoCorp Ltd", "sector": "Auto", "instrument_key": "NSE_EQ|INE158A01026", "market_cap_category": "LARGE_CAP", "market_cap_rank": 37},
    {"symbol": "DRREDDY", "name": "Dr. Reddy's Laboratories Ltd", "sector": "Pharma", "instrument_key": "NSE_EQ|INE089A01023", "market_cap_category": "LARGE_CAP", "market_cap_rank": 38},
    {"symbol": "CIPLA", "name": "Cipla Ltd", "sector": "Pharma", "instrument_key": "NSE_EQ|INE059A01026", "market_cap_category": "LARGE_CAP", "market_cap_rank": 39},
    {"symbol": "DIVISLAB", "name": "Divi's Laboratories Ltd", "sector": "Pharma", "instrument_key": "NSE_EQ|INE361B01024", "market_cap_category": "LARGE_CAP", "market_cap_rank": 40},
    {"symbol": "APOLLOHOSP", "name": "Apollo Hospitals Enterprise Ltd", "sector": "Healthcare", "instrument_key": "NSE_EQ|INE437A01024", "market_cap_category": "LARGE_CAP", "market_cap_rank": 41},
    {"symbol": "NESTLEIND", "name": "Nestle India Ltd", "sector": "FMCG", "instrument_key": "NSE_EQ|INE239A01024", "market_cap_category": "LARGE_CAP", "market_cap_rank": 42},
    {"symbol": "BRITANNIA", "name": "Britannia Industries Ltd", "sector": "FMCG", "instrument_key": "NSE_EQ|INE216A01030", "market_cap_category": "LARGE_CAP", "market_cap_rank": 43},
    {"symbol": "TATACONSUM", "name": "Tata Consumer Products Ltd", "sector": "FMCG", "instrument_key": "NSE_EQ|INE192A01025", "market_cap_category": "LARGE_CAP", "market_cap_rank": 44},
    {"symbol": "ASIANPAINT", "name": "Asian Paints Ltd", "sector": "Consumer", "instrument_key": "NSE_EQ|INE021A01026", "market_cap_category": "LARGE_CAP", "market_cap_rank": 45},
    {"symbol": "BPCL", "name": "Bharat Petroleum Corp Ltd", "sector": "Energy", "instrument_key": "NSE_EQ|INE029A01011", "market_cap_category": "LARGE_CAP", "market_cap_rank": 46},
    {"symbol": "IOC", "name": "Indian Oil Corporation Ltd", "sector": "Energy", "instrument_key": "NSE_EQ|INE242A01010", "market_cap_category": "LARGE_CAP", "market_cap_rank": 47},
    {"symbol": "GAIL", "name": "GAIL (India) Ltd", "sector": "Energy", "instrument_key": "NSE_EQ|INE129A01019", "market_cap_category": "LARGE_CAP", "market_cap_rank": 48},
    {"symbol": "BEL", "name": "Bharat Electronics Ltd", "sector": "Defence", "instrument_key": "NSE_EQ|INE263A01024", "market_cap_category": "LARGE_CAP", "market_cap_rank": 49},
    {"symbol": "HAL", "name": "Hindustan Aeronautics Ltd", "sector": "Defence", "instrument_key": "NSE_EQ|INE066F01020", "market_cap_category": "LARGE_CAP", "market_cap_rank": 50},
    {"symbol": "SIEMENS", "name": "Siemens Ltd", "sector": "Capital Goods", "instrument_key": "NSE_EQ|INE003A01024", "market_cap_category": "LARGE_CAP", "market_cap_rank": 51},
    {"symbol": "ABB", "name": "ABB India Ltd", "sector": "Capital Goods", "instrument_key": "NSE_EQ|INE117A01022", "market_cap_category": "LARGE_CAP", "market_cap_rank": 52},
    {"symbol": "DLF", "name": "DLF Ltd", "sector": "Realty", "instrument_key": "NSE_EQ|INE271C01023", "market_cap_category": "LARGE_CAP", "market_cap_rank": 53},
    {"symbol": "GODREJPROP", "name": "Godrej Properties Ltd", "sector": "Realty", "instrument_key": "NSE_EQ|INE484J01027", "market_cap_category": "LARGE_CAP", "market_cap_rank": 54},
    {"symbol": "VEDL", "name": "Vedanta Ltd", "sector": "Metals", "instrument_key": "NSE_EQ|INE205A01025", "market_cap_category": "LARGE_CAP", "market_cap_rank": 55},
    {"symbol": "JINDALSTEL", "name": "Jindal Steel & Power Ltd", "sector": "Metals", "instrument_key": "NSE_EQ|INE749A01030", "market_cap_category": "LARGE_CAP", "market_cap_rank": 56},
    {"symbol": "ZOMATO", "name": "Zomato Ltd", "sector": "Consumer", "instrument_key": "NSE_EQ|INE758T01015", "market_cap_category": "LARGE_CAP", "market_cap_rank": 57},
    {"symbol": "JIOFIN", "name": "Jio Financial Services Ltd", "sector": "Financial Services", "instrument_key": "NSE_EQ|INE758E01017", "market_cap_category": "LARGE_CAP", "market_cap_rank": 58},
    {"symbol": "TATAPOWER", "name": "Tata Power Company Ltd", "sector": "Power", "instrument_key": "NSE_EQ|INE245A01021", "market_cap_category": "LARGE_CAP", "market_cap_rank": 59},
    {"symbol": "PFC", "name": "Power Finance Corporation Ltd", "sector": "Financial Services", "instrument_key": "NSE_EQ|INE134E01011", "market_cap_category": "LARGE_CAP", "market_cap_rank": 60},
    {"symbol": "RECLTD", "name": "REC Ltd", "sector": "Financial Services", "instrument_key": "NSE_EQ|INE020B01018", "market_cap_category": "LARGE_CAP", "market_cap_rank": 61},
    {"symbol": "IRFC", "name": "Indian Railway Finance Corp", "sector": "Financial Services", "instrument_key": "NSE_EQ|INE053F01010", "market_cap_category": "LARGE_CAP", "market_cap_rank": 62},
    {"symbol": "BANKBARODA", "name": "Bank of Baroda", "sector": "Banking", "instrument_key": "NSE_EQ|INE077A01010", "market_cap_category": "LARGE_CAP", "market_cap_rank": 63},
    {"symbol": "PNB", "name": "Punjab National Bank", "sector": "Banking", "instrument_key": "NSE_EQ|INE160A01022", "market_cap_category": "LARGE_CAP", "market_cap_rank": 64},
    {"symbol": "CANBK", "name": "Canara Bank", "sector": "Banking", "instrument_key": "NSE_EQ|INE476A01022", "market_cap_category": "LARGE_CAP", "market_cap_rank": 65},
    {"symbol": "AMBUJACEM", "name": "Ambuja Cements Ltd", "sector": "Infrastructure", "instrument_key": "NSE_EQ|INE079A01024", "market_cap_category": "LARGE_CAP", "market_cap_rank": 66},
    {"symbol": "PIDILITIND", "name": "Pidilite Industries Ltd", "sector": "Chemicals", "instrument_key": "NSE_EQ|INE318A01026", "market_cap_category": "LARGE_CAP", "market_cap_rank": 67},
    {"symbol": "HAVELLS", "name": "Havells India Ltd", "sector": "Consumer", "instrument_key": "NSE_EQ|INE176B01034", "market_cap_category": "LARGE_CAP", "market_cap_rank": 68},
    {"symbol": "DABUR", "name": "Dabur India Ltd", "sector": "FMCG", "instrument_key": "NSE_EQ|INE016A01026", "market_cap_category": "LARGE_CAP", "market_cap_rank": 69},
    {"symbol": "NMDC", "name": "NMDC Ltd", "sector": "Metals", "instrument_key": "NSE_EQ|INE584A01023", "market_cap_category": "LARGE_CAP", "market_cap_rank": 70},
    {"symbol": "BHEL", "name": "Bharat Heavy Electricals Ltd", "sector": "Capital Goods", "instrument_key": "NSE_EQ|INE257A01026", "market_cap_category": "LARGE_CAP", "market_cap_rank": 71},

    # -------------------------------------------------------------
    # 2. TOP MID-CAP STOCKS (Ranks 101 to 250)
    # -------------------------------------------------------------
    {"symbol": "PERSISTENT", "name": "Persistent Systems Ltd", "sector": "IT", "instrument_key": "NSE_EQ|INE262H01013", "market_cap_category": "MID_CAP", "market_cap_rank": 101},
    {"symbol": "COFORGE", "name": "Coforge Ltd", "sector": "IT", "instrument_key": "NSE_EQ|INE591G01017", "market_cap_category": "MID_CAP", "market_cap_rank": 102},
    {"symbol": "POLYCAB", "name": "Polycab India Ltd", "sector": "Capital Goods", "instrument_key": "NSE_EQ|INE455K01017", "market_cap_category": "MID_CAP", "market_cap_rank": 103},
    {"symbol": "DIXON", "name": "Dixon Technologies Ltd", "sector": "Consumer", "instrument_key": "NSE_EQ|INE935N01020", "market_cap_category": "MID_CAP", "market_cap_rank": 104},
    {"symbol": "ASTRAL", "name": "Astral Ltd", "sector": "Infrastructure", "instrument_key": "NSE_EQ|INE006I01046", "market_cap_category": "MID_CAP", "market_cap_rank": 105},
    {"symbol": "TRENT", "name": "Trent Ltd", "sector": "Consumer", "instrument_key": "NSE_EQ|INE849A01020", "market_cap_category": "MID_CAP", "market_cap_rank": 106},
    {"symbol": "CHOLAFIN", "name": "Cholamandalam Investment & Finance", "sector": "Financial Services", "instrument_key": "NSE_EQ|INE121A01024", "market_cap_category": "MID_CAP", "market_cap_rank": 107},
    {"symbol": "LUPIN", "name": "Lupin Ltd", "sector": "Pharma", "instrument_key": "NSE_EQ|INE326A01037", "market_cap_category": "MID_CAP", "market_cap_rank": 108},
    {"symbol": "AUROPHARMA", "name": "Aurobindo Pharma Ltd", "sector": "Pharma", "instrument_key": "NSE_EQ|INE406A01037", "market_cap_category": "MID_CAP", "market_cap_rank": 109},
    {"symbol": "VOLTAS", "name": "Voltas Ltd", "sector": "Consumer", "instrument_key": "NSE_EQ|INE226A01021", "market_cap_category": "MID_CAP", "market_cap_rank": 110},
    {"symbol": "FEDERALBNK", "name": "Federal Bank Ltd", "sector": "Banking", "instrument_key": "NSE_EQ|INE171A01029", "market_cap_category": "MID_CAP", "market_cap_rank": 111},
    {"symbol": "IDFCFIRSTB", "name": "IDFC First Bank Ltd", "sector": "Banking", "instrument_key": "NSE_EQ|INE092T01019", "market_cap_category": "MID_CAP", "market_cap_rank": 112},
    {"symbol": "CUMMINSIND", "name": "Cummins India Ltd", "sector": "Capital Goods", "instrument_key": "NSE_EQ|INE299A01018", "market_cap_category": "MID_CAP", "market_cap_rank": 113},
    {"symbol": "DALBHARAT", "name": "Dalmia Bharat Ltd", "sector": "Infrastructure", "instrument_key": "NSE_EQ|INE00R701025", "market_cap_category": "MID_CAP", "market_cap_rank": 114},
    {"symbol": "OBEROIRLTY", "name": "Oberoi Realty Ltd", "sector": "Realty", "instrument_key": "NSE_EQ|INE093I01010", "market_cap_category": "MID_CAP", "market_cap_rank": 115},
    {"symbol": "PRESTIGE", "name": "Prestige Estates Projects Ltd", "sector": "Realty", "instrument_key": "NSE_EQ|INE811K01011", "market_cap_category": "MID_CAP", "market_cap_rank": 116},
    {"symbol": "JUBLFOOD", "name": "Jubilant FoodWorks Ltd", "sector": "Consumer", "instrument_key": "NSE_EQ|INE797F01022", "market_cap_category": "MID_CAP", "market_cap_rank": 117},
    {"symbol": "PIIND", "name": "PI Industries Ltd", "sector": "Chemicals", "instrument_key": "NSE_EQ|INE603J01030", "market_cap_category": "MID_CAP", "market_cap_rank": 118},
    {"symbol": "ASHOKLEY", "name": "Ashok Leyland Ltd", "sector": "Auto", "instrument_key": "NSE_EQ|INE214A01026", "market_cap_category": "MID_CAP", "market_cap_rank": 119},
    {"symbol": "SUPREMEIND", "name": "Supreme Industries Ltd", "sector": "Infrastructure", "instrument_key": "NSE_EQ|INE195A01028", "market_cap_category": "MID_CAP", "market_cap_rank": 120},
    {"symbol": "DEEPAKNTR", "name": "Deepak Nitrite Ltd", "sector": "Chemicals", "instrument_key": "NSE_EQ|INE288B01029", "market_cap_category": "MID_CAP", "market_cap_rank": 121},
    {"symbol": "TATACOMM", "name": "Tata Communications Ltd", "sector": "Telecom", "instrument_key": "NSE_EQ|INE151A01013", "market_cap_category": "MID_CAP", "market_cap_rank": 122},
    {"symbol": "IPCALAB", "name": "IPCA Laboratories Ltd", "sector": "Pharma", "instrument_key": "NSE_EQ|INE571A01038", "market_cap_category": "MID_CAP", "market_cap_rank": 123},
    {"symbol": "SUNDARMFIN", "name": "Sundaram Finance Ltd", "sector": "Financial Services", "instrument_key": "NSE_EQ|INE660A01013", "market_cap_category": "MID_CAP", "market_cap_rank": 124},
    {"symbol": "BATAINDIA", "name": "Bata India Ltd", "sector": "Consumer", "instrument_key": "NSE_EQ|INE176A01028", "market_cap_category": "MID_CAP", "market_cap_rank": 125},
    {"symbol": "RVNL", "name": "Rail Vikas Nigam Ltd", "sector": "Infrastructure", "instrument_key": "NSE_EQ|INE415G01027", "market_cap_category": "MID_CAP", "market_cap_rank": 126},
    {"symbol": "IREDA", "name": "Indian Renewable Energy Dev Agency", "sector": "Financial Services", "instrument_key": "NSE_EQ|INE202E01016", "market_cap_category": "MID_CAP", "market_cap_rank": 127},
    {"symbol": "MAZDOCK", "name": "Mazagon Dock Shipbuilders Ltd", "sector": "Defence", "instrument_key": "NSE_EQ|INE249Z01020", "market_cap_category": "MID_CAP", "market_cap_rank": 128},
    {"symbol": "COCHINSHIP", "name": "Cochin Shipyard Ltd", "sector": "Defence", "instrument_key": "NSE_EQ|INE704P01025", "market_cap_category": "MID_CAP", "market_cap_rank": 129},
    {"symbol": "MAXHEALTH", "name": "Max Healthcare Institute Ltd", "sector": "Healthcare", "instrument_key": "NSE_EQ|INE027H01010", "market_cap_category": "MID_CAP", "market_cap_rank": 130},

    # -------------------------------------------------------------
    # 3. TOP SMALL-CAP STOCKS (Ranks 251+)
    # -------------------------------------------------------------
    {"symbol": "CDSL", "name": "Central Depository Services (India) Ltd", "sector": "Financial Services", "instrument_key": "NSE_EQ|INE736A01011", "market_cap_category": "SMALL_CAP", "market_cap_rank": 251},
    {"symbol": "BSOFT", "name": "Birlasoft Ltd", "sector": "IT", "instrument_key": "NSE_EQ|INE836A01035", "market_cap_category": "SMALL_CAP", "market_cap_rank": 252},
    {"symbol": "KAYNES", "name": "Kaynes Technology India Ltd", "sector": "Capital Goods", "instrument_key": "NSE_EQ|INE918Z01012", "market_cap_category": "SMALL_CAP", "market_cap_rank": 253},
    {"symbol": "SONACOMS", "name": "Sona BLW Precision Forgings Ltd", "sector": "Auto", "instrument_key": "NSE_EQ|INE073K01018", "market_cap_category": "SMALL_CAP", "market_cap_rank": 254},
    {"symbol": "KPITTECH", "name": "KPIT Technologies Ltd", "sector": "IT", "instrument_key": "NSE_EQ|INE04I401011", "market_cap_category": "SMALL_CAP", "market_cap_rank": 255},
    {"symbol": "CYIENT", "name": "Cyient Ltd", "sector": "IT", "instrument_key": "NSE_EQ|INE136B01020", "market_cap_category": "SMALL_CAP", "market_cap_rank": 256},
    {"symbol": "ANGELONE", "name": "Angel One Ltd", "sector": "Financial Services", "instrument_key": "NSE_EQ|INE732I01013", "market_cap_category": "SMALL_CAP", "market_cap_rank": 257},
    {"symbol": "SUZLON", "name": "Suzlon Energy Ltd", "sector": "Energy", "instrument_key": "NSE_EQ|INE040H01021", "market_cap_category": "SMALL_CAP", "market_cap_rank": 258},
    {"symbol": "TATAELXSI", "name": "Tata Elxsi Ltd", "sector": "IT", "instrument_key": "NSE_EQ|INE670A01012", "market_cap_category": "SMALL_CAP", "market_cap_rank": 259},
    {"symbol": "MAPMYINDIA", "name": "CE Info Systems Ltd (MapmyIndia)", "sector": "IT", "instrument_key": "NSE_EQ|INE0BV301023", "market_cap_category": "SMALL_CAP", "market_cap_rank": 260},
    {"symbol": "ROUTE", "name": "Route Mobile Ltd", "sector": "Telecom", "instrument_key": "NSE_EQ|INE450U01017", "market_cap_category": "SMALL_CAP", "market_cap_rank": 261},
    {"symbol": "HAPPYFORGE", "name": "Happy Forgings Ltd", "sector": "Auto", "instrument_key": "NSE_EQ|INE0Q8501019", "market_cap_category": "SMALL_CAP", "market_cap_rank": 262},
    {"symbol": "KEC", "name": "KEC International Ltd", "sector": "Infrastructure", "instrument_key": "NSE_EQ|INE389H01022", "market_cap_category": "SMALL_CAP", "market_cap_rank": 263},
    {"symbol": "CENTURYPLY", "name": "Century Plyboards (India) Ltd", "sector": "Infrastructure", "instrument_key": "NSE_EQ|INE348B01021", "market_cap_category": "SMALL_CAP", "market_cap_rank": 264},
    {"symbol": "RADICO", "name": "Radico Khaitan Ltd", "sector": "Consumer", "instrument_key": "NSE_EQ|INE944F01028", "market_cap_category": "SMALL_CAP", "market_cap_rank": 265},
    {"symbol": "ZENTEC", "name": "Zen Technologies Ltd", "sector": "Defence", "instrument_key": "NSE_EQ|INE251B01027", "market_cap_category": "SMALL_CAP", "market_cap_rank": 266},
    {"symbol": "AFFLE", "name": "Affle (India) Ltd", "sector": "IT", "instrument_key": "NSE_EQ|INE00WC01027", "market_cap_category": "SMALL_CAP", "market_cap_rank": 267},
    {"symbol": "TEJASNET", "name": "Tejas Networks Ltd", "sector": "Telecom", "instrument_key": "NSE_EQ|INE010J01012", "market_cap_category": "SMALL_CAP", "market_cap_rank": 268},
    {"symbol": "PPLPHARMA", "name": "Piramal Pharma Ltd", "sector": "Pharma", "instrument_key": "NSE_EQ|INE0DK501011", "market_cap_category": "SMALL_CAP", "market_cap_rank": 269},
    {"symbol": "LATENTVIEW", "name": "Latent View Analytics Ltd", "sector": "IT", "instrument_key": "NSE_EQ|INE0I7C01011", "market_cap_category": "SMALL_CAP", "market_cap_rank": 270},
    {"symbol": "BSE", "name": "BSE Ltd", "sector": "Financial Services", "instrument_key": "NSE_EQ|INE118H01025", "market_cap_category": "SMALL_CAP", "market_cap_rank": 271},
    {"symbol": "MCX", "name": "Multi Commodity Exchange of India", "sector": "Financial Services", "instrument_key": "NSE_EQ|INE745G01035", "market_cap_category": "SMALL_CAP", "market_cap_rank": 272},
    {"symbol": "CAMS", "name": "Computer Age Management Services", "sector": "Financial Services", "instrument_key": "NSE_EQ|INE596I01012", "market_cap_category": "SMALL_CAP", "market_cap_rank": 273},
    {"symbol": "GRSE", "name": "Garden Reach Shipbuilders & Engineers", "sector": "Defence", "instrument_key": "NSE_EQ|INE719Z01011", "market_cap_category": "SMALL_CAP", "market_cap_rank": 274},
    {"symbol": "BDL", "name": "Bharat Dynamics Ltd", "sector": "Defence", "instrument_key": "NSE_EQ|INE171Z01018", "market_cap_category": "SMALL_CAP", "market_cap_rank": 275},
    {"symbol": "BEML", "name": "BEML Ltd", "sector": "Capital Goods", "instrument_key": "NSE_EQ|INE258A01016", "market_cap_category": "SMALL_CAP", "market_cap_rank": 276},
    {"symbol": "IRCTC", "name": "Indian Railway Catering & Tourism Corp", "sector": "Consumer", "instrument_key": "NSE_EQ|INE335Y01012", "market_cap_category": "SMALL_CAP", "market_cap_rank": 277},
    {"symbol": "IEX", "name": "Indian Energy Exchange Ltd", "sector": "Energy", "instrument_key": "NSE_EQ|INE022Q01020", "market_cap_category": "SMALL_CAP", "market_cap_rank": 278},
    {"symbol": "INOXWIND", "name": "Inox Wind Ltd", "sector": "Energy", "instrument_key": "NSE_EQ|INE066P01011", "market_cap_category": "SMALL_CAP", "market_cap_rank": 279},
    {"symbol": "NETWEB", "name": "Netweb Technologies India Ltd", "sector": "IT", "instrument_key": "NSE_EQ|INE0NT901020", "market_cap_category": "SMALL_CAP", "market_cap_rank": 280},
    {"symbol": "HAPPSTMNDS", "name": "Happiest Minds Technologies", "sector": "IT", "instrument_key": "NSE_EQ|INE419U01012", "market_cap_category": "SMALL_CAP", "market_cap_rank": 281},
    {"symbol": "ZENSARTECH", "name": "Zensar Technologies Ltd", "sector": "IT", "instrument_key": "NSE_EQ|INE520A01027", "market_cap_category": "SMALL_CAP", "market_cap_rank": 282},
    {"symbol": "SONATACOMS", "name": "Sonata Software Ltd", "sector": "IT", "instrument_key": "NSE_EQ|INE269A01021", "market_cap_category": "SMALL_CAP", "market_cap_rank": 283},
    {"symbol": "DEVYANI", "name": "Devyani International Ltd", "sector": "Consumer", "instrument_key": "NSE_EQ|INE872J01023", "market_cap_category": "SMALL_CAP", "market_cap_rank": 284},
    {"symbol": "LEMONTREE", "name": "Lemon Tree Hotels Ltd", "sector": "Consumer", "instrument_key": "NSE_EQ|INE970X01018", "market_cap_category": "SMALL_CAP", "market_cap_rank": 285},
    {"symbol": "PVRINOX", "name": "PVR INOX Ltd", "sector": "Consumer", "instrument_key": "NSE_EQ|INE191H01014", "market_cap_category": "SMALL_CAP", "market_cap_rank": 286},
    {"symbol": "INDIAMART", "name": "IndiaMART InterMESH Ltd", "sector": "IT", "instrument_key": "NSE_EQ|INE933S01016", "market_cap_category": "SMALL_CAP", "market_cap_rank": 287},
    {"symbol": "NAUKRI", "name": "Info Edge (India) Ltd", "sector": "IT", "instrument_key": "NSE_EQ|INE663F01024", "market_cap_category": "SMALL_CAP", "market_cap_rank": 288},
    {"symbol": "MANAPPURAM", "name": "Manappuram Finance Ltd", "sector": "Financial Services", "instrument_key": "NSE_EQ|INE522D01027", "market_cap_category": "SMALL_CAP", "market_cap_rank": 289},
    {"symbol": "POONAWALLA", "name": "Poonawalla Fincorp Ltd", "sector": "Financial Services", "instrument_key": "NSE_EQ|INE511C01022", "market_cap_category": "SMALL_CAP", "market_cap_rank": 290},
    {"symbol": "AARTIIND", "name": "Aarti Industries Ltd", "sector": "Chemicals", "instrument_key": "NSE_EQ|INE769A01020", "market_cap_category": "SMALL_CAP", "market_cap_rank": 291},
    {"symbol": "ATUL", "name": "Atul Ltd", "sector": "Chemicals", "instrument_key": "NSE_EQ|INE100A01010", "market_cap_category": "SMALL_CAP", "market_cap_rank": 292},
    {"symbol": "CLEAN", "name": "Clean Science and Technology", "sector": "Chemicals", "instrument_key": "NSE_EQ|INE227W01023", "market_cap_category": "SMALL_CAP", "market_cap_rank": 293},
    {"symbol": "EXIDEIND", "name": "Exide Industries Ltd", "sector": "Auto", "instrument_key": "NSE_EQ|INE302A01020", "market_cap_category": "SMALL_CAP", "market_cap_rank": 294},
    {"symbol": "APOLLOTYRE", "name": "Apollo Tyres Ltd", "sector": "Auto", "instrument_key": "NSE_EQ|INE438A01022", "market_cap_category": "SMALL_CAP", "market_cap_rank": 295},
    {"symbol": "CEATLTD", "name": "CEAT Ltd", "sector": "Auto", "instrument_key": "NSE_EQ|INE482A01020", "market_cap_category": "SMALL_CAP", "market_cap_rank": 296},
    {"symbol": "TIMKEN", "name": "Timken India Ltd", "sector": "Capital Goods", "instrument_key": "NSE_EQ|INE325A01013", "market_cap_category": "SMALL_CAP", "market_cap_rank": 297},
    {"symbol": "SJVN", "name": "SJVN Ltd", "sector": "Power", "instrument_key": "NSE_EQ|INE002L01015", "market_cap_category": "SMALL_CAP", "market_cap_rank": 298},
    {"symbol": "YESBANK", "name": "Yes Bank Ltd", "sector": "Banking", "instrument_key": "NSE_EQ|INE528G01035", "market_cap_category": "SMALL_CAP", "market_cap_rank": 299},
]

# Benchmark Sector Indices on NSE
NSE_SECTOR_KEYS: List[Dict[str, str]] = [
    {"name": "NIFTY IT", "symbol": "NIFTY IT", "key": "NSE_INDEX|Nifty IT", "sector": "IT"},
    {"name": "NIFTY BANK", "symbol": "NIFTY BANK", "key": "NSE_INDEX|Nifty Bank", "sector": "Banking"},
    {"name": "NIFTY AUTO", "symbol": "NIFTY AUTO", "key": "NSE_INDEX|Nifty Auto", "sector": "Auto"},
    {"name": "NIFTY PHARMA", "symbol": "NIFTY PHARMA", "key": "NSE_INDEX|Nifty Pharma", "sector": "Pharma"},
    {"name": "NIFTY FMCG", "symbol": "NIFTY FMCG", "key": "NSE_INDEX|Nifty FMCG", "sector": "FMCG"},
    {"name": "NIFTY METAL", "symbol": "NIFTY METAL", "key": "NSE_INDEX|Nifty Metal", "sector": "Metals"},
    {"name": "NIFTY ENERGY", "symbol": "NIFTY ENERGY", "key": "NSE_INDEX|Nifty Energy", "sector": "Energy"},
    {"name": "NIFTY INFRA", "symbol": "NIFTY INFRA", "key": "NSE_INDEX|Nifty Infra", "sector": "Infrastructure"},
    {"name": "NIFTY REALTY", "symbol": "NIFTY REALTY", "key": "NSE_INDEX|Nifty Realty", "sector": "Realty"},
    {"name": "NIFTY FIN SERVICE", "symbol": "NIFTY FIN SERVICE", "key": "NSE_INDEX|Nifty Fin Service", "sector": "Financial Services"},
]

# Backward compatibility alias
NSE_EQUITY_UNIVERSE = NSE_RANKED_UNIVERSE

def seed_instrument_master_if_empty(db_session):
    """
    Populates and synchronizes DBInstrumentMaster table from authoritative universe.
    """
    from backend.models.database import DBInstrumentMaster
    for item in NSE_RANKED_UNIVERSE:
        existing = db_session.query(DBInstrumentMaster).filter(DBInstrumentMaster.symbol == item["symbol"]).first()
        if not existing:
            master_entry = DBInstrumentMaster(
                symbol=item["symbol"],
                name=item["name"],
                sector=item["sector"],
                instrument_key=item["instrument_key"],
                market_cap_category=item["market_cap_category"],
                market_cap_rank=item.get("market_cap_rank"),
                classification_source=CLASSIFICATION_SOURCE,
                classification_date=CLASSIFICATION_DATE,
                is_active=True
            )
            db_session.add(master_entry)
        else:
            if existing.instrument_key != item["instrument_key"]:
                existing.instrument_key = item["instrument_key"]
                existing.name = item["name"]
                existing.sector = item["sector"]
                existing.market_cap_category = item["market_cap_category"]
                existing.market_cap_rank = item.get("market_cap_rank")
    db_session.commit()
    logger.info("DBInstrumentMaster verified and synchronized with latest ISIN keys.")


def get_or_fetch_active_universe(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Returns the active tradeable classified universe.
    Dynamically prioritizes live DBInstrumentMaster entries to prevent staleness & survivorship bias.
    """
    try:
        from backend.models.database import SessionLocal, DBInstrumentMaster
        db = SessionLocal()
        try:
            query = db.query(DBInstrumentMaster).filter(DBInstrumentMaster.is_active == True)
            if category:
                query = query.filter(DBInstrumentMaster.market_cap_category.ilike(category.upper()))
            records = query.order_by(DBInstrumentMaster.market_cap_rank.asc()).all()
            if records and len(records) >= 50:
                return [{
                    "symbol": r.symbol.upper(),
                    "name": r.name or r.symbol,
                    "sector": r.sector or "Equity",
                    "instrument_key": r.instrument_key,
                    "market_cap_category": r.market_cap_category or "EQUITY",
                    "market_cap_rank": r.market_cap_rank,
                    "classification_source": r.classification_source,
                    "classification_date": str(r.classification_date) if r.classification_date else str(date.today())
                } for r in records]
        finally:
            db.close()
    except Exception as e:
        logger.debug(f"Could not load universe from DBInstrumentMaster: {e}")

    # Fallback to seeded ranked universe if DB query fails
    if category:
        return [s for s in NSE_RANKED_UNIVERSE if s["market_cap_category"].upper() == category.upper()]
    return list(NSE_RANKED_UNIVERSE)

def get_classified_universe() -> Dict[str, List[Dict[str, Any]]]:
    """
    Returns dictionary with items segregated by market cap category from live database.
    """
    return {
        "LARGE_CAP": get_or_fetch_active_universe("LARGE_CAP"),
        "MID_CAP": get_or_fetch_active_universe("MID_CAP"),
        "SMALL_CAP": get_or_fetch_active_universe("SMALL_CAP"),
    }
