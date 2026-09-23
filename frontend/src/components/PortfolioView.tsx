import React, { useState, useEffect, useRef } from 'react';
import { 
  Briefcase, 
  Plus, 
  Trash2, 
  TrendingUp, 
  ArrowUpRight, 
  ArrowDownRight, 
  ShieldCheck, 
  AlertTriangle,
  ChevronRight,
  ShieldAlert,
  HelpCircle,
  Search,
  Check,
  Calculator,
  Flame,
  Clock,
  Zap
} from 'lucide-react';
import { PortfolioSummaryResponse, HoldingAnalysis } from '../types';
import { api } from '../services/api';
import { PositionSizingWidget } from './PositionSizingWidget';

interface PortfolioViewProps {
  portfolio: PortfolioSummaryResponse | null;
  loading: boolean;
  onAddHolding: (holding: { symbol: string; quantity: number; buy_price: number; purchase_date: string; notes?: string }) => void;
  onDeleteHolding: (id: number) => void;
  onStockClick: (symbol: string) => void;
}

interface StockItem {
  symbol: string;
  name: string;
  sector: string;
  market_cap_category?: string;
}

// Built-in curated benchmark universe for instant suggestions (200+ NSE Equities)
const DEFAULT_STOCKS: StockItem[] = [
  // Large Cap
  { symbol: 'RELIANCE', name: 'Reliance Industries Ltd', sector: 'Energy', market_cap_category: 'LARGE_CAP' },
  { symbol: 'TCS', name: 'Tata Consultancy Services Ltd', sector: 'IT', market_cap_category: 'LARGE_CAP' },
  { symbol: 'HDFCBANK', name: 'HDFC Bank Ltd', sector: 'Banking', market_cap_category: 'LARGE_CAP' },
  { symbol: 'BHARTIARTL', name: 'Bharti Airtel Ltd', sector: 'Telecom', market_cap_category: 'LARGE_CAP' },
  { symbol: 'ICICIBANK', name: 'ICICI Bank Ltd', sector: 'Banking', market_cap_category: 'LARGE_CAP' },
  { symbol: 'INFY', name: 'Infosys Ltd', sector: 'IT', market_cap_category: 'LARGE_CAP' },
  { symbol: 'SBIN', name: 'State Bank of India', sector: 'Banking', market_cap_category: 'LARGE_CAP' },
  { symbol: 'HINDUNILVR', name: 'Hindustan Unilever Ltd', sector: 'FMCG', market_cap_category: 'LARGE_CAP' },
  { symbol: 'ITC', name: 'ITC Ltd', sector: 'FMCG', market_cap_category: 'LARGE_CAP' },
  { symbol: 'LT', name: 'Larsen & Toubro Ltd', sector: 'Infrastructure', market_cap_category: 'LARGE_CAP' },
  { symbol: 'BAJFINANCE', name: 'Bajaj Finance Ltd', sector: 'Financial Services', market_cap_category: 'LARGE_CAP' },
  { symbol: 'HCLTECH', name: 'HCL Technologies Ltd', sector: 'IT', market_cap_category: 'LARGE_CAP' },
  { symbol: 'MARUTI', name: 'Maruti Suzuki India Ltd', sector: 'Auto', market_cap_category: 'LARGE_CAP' },
  { symbol: 'SUNPHARMA', name: 'Sun Pharmaceutical Industries Ltd', sector: 'Pharma', market_cap_category: 'LARGE_CAP' },
  { symbol: 'M&M', name: 'Mahindra & Mahindra Ltd', sector: 'Auto', market_cap_category: 'LARGE_CAP' },
  { symbol: 'TATAMOTORS', name: 'Tata Motors Ltd', sector: 'Auto', market_cap_category: 'LARGE_CAP' },
  { symbol: 'NTPC', name: 'NTPC Ltd', sector: 'Power', market_cap_category: 'LARGE_CAP' },
  { symbol: 'ONGC', name: 'Oil & Natural Gas Corp Ltd', sector: 'Energy', market_cap_category: 'LARGE_CAP' },
  { symbol: 'POWERGRID', name: 'Power Grid Corp of India Ltd', sector: 'Power', market_cap_category: 'LARGE_CAP' },
  { symbol: 'AXISBANK', name: 'Axis Bank Ltd', sector: 'Banking', market_cap_category: 'LARGE_CAP' },
  { symbol: 'TITAN', name: 'Titan Company Ltd', sector: 'Consumer', market_cap_category: 'LARGE_CAP' },
  { symbol: 'ADANIENT', name: 'Adani Enterprises Ltd', sector: 'Diversified', market_cap_category: 'LARGE_CAP' },
  { symbol: 'ADANIPORTS', name: 'Adani Ports & SEZ Ltd', sector: 'Infrastructure', market_cap_category: 'LARGE_CAP' },
  { symbol: 'COALINDIA', name: 'Coal India Ltd', sector: 'Metals', market_cap_category: 'LARGE_CAP' },
  { symbol: 'TATASTEEL', name: 'Tata Steel Ltd', sector: 'Metals', market_cap_category: 'LARGE_CAP' },
  { symbol: 'JSWSTEEL', name: 'JSW Steel Ltd', sector: 'Metals', market_cap_category: 'LARGE_CAP' },
  { symbol: 'HINDALCO', name: 'Hindalco Industries Ltd', sector: 'Metals', market_cap_category: 'LARGE_CAP' },
  { symbol: 'WIPRO', name: 'Wipro Ltd', sector: 'IT', market_cap_category: 'LARGE_CAP' },
  { symbol: 'TECHM', name: 'Tech Mahindra Ltd', sector: 'IT', market_cap_category: 'LARGE_CAP' },
  { symbol: 'LTIM', name: 'LTIMindtree Ltd', sector: 'IT', market_cap_category: 'LARGE_CAP' },
  { symbol: 'KOTAKBANK', name: 'Kotak Mahindra Bank Ltd', sector: 'Banking', market_cap_category: 'LARGE_CAP' },
  { symbol: 'INDUSINDBK', name: 'IndusInd Bank Ltd', sector: 'Banking', market_cap_category: 'LARGE_CAP' },
  { symbol: 'BAJAJFINSV', name: 'Bajaj Finserv Ltd', sector: 'Financial Services', market_cap_category: 'LARGE_CAP' },
  { symbol: 'BAJAJ-AUTO', name: 'Bajaj Auto Ltd', sector: 'Auto', market_cap_category: 'LARGE_CAP' },
  { symbol: 'EICHERMOT', name: 'Eicher Motors Ltd', sector: 'Auto', market_cap_category: 'LARGE_CAP' },
  { symbol: 'TVSMOTOR', name: 'TVS Motor Company Ltd', sector: 'Auto', market_cap_category: 'LARGE_CAP' },
  { symbol: 'HEROMOTOCO', name: 'Hero MotoCorp Ltd', sector: 'Auto', market_cap_category: 'LARGE_CAP' },
  { symbol: 'DRREDDY', name: 'Dr. Reddy\'s Laboratories Ltd', sector: 'Pharma', market_cap_category: 'LARGE_CAP' },
  { symbol: 'CIPLA', name: 'Cipla Ltd', sector: 'Pharma', market_cap_category: 'LARGE_CAP' },
  { symbol: 'DIVISLAB', name: 'Divi\'s Laboratories Ltd', sector: 'Pharma', market_cap_category: 'LARGE_CAP' },
  { symbol: 'APOLLOHOSP', name: 'Apollo Hospitals Enterprise Ltd', sector: 'Healthcare', market_cap_category: 'LARGE_CAP' },
  { symbol: 'NESTLEIND', name: 'Nestle India Ltd', sector: 'FMCG', market_cap_category: 'LARGE_CAP' },
  { symbol: 'BRITANNIA', name: 'Britannia Industries Ltd', sector: 'FMCG', market_cap_category: 'LARGE_CAP' },
  { symbol: 'TATACONSUM', name: 'Tata Consumer Products Ltd', sector: 'FMCG', market_cap_category: 'LARGE_CAP' },
  { symbol: 'ASIANPAINT', name: 'Asian Paints Ltd', sector: 'Consumer', market_cap_category: 'LARGE_CAP' },
  { symbol: 'BPCL', name: 'Bharat Petroleum Corp Ltd', sector: 'Energy', market_cap_category: 'LARGE_CAP' },
  { symbol: 'IOC', name: 'Indian Oil Corporation Ltd', sector: 'Energy', market_cap_category: 'LARGE_CAP' },
  { symbol: 'GAIL', name: 'GAIL (India) Ltd', sector: 'Energy', market_cap_category: 'LARGE_CAP' },
  { symbol: 'BEL', name: 'Bharat Electronics Ltd', sector: 'Defence', market_cap_category: 'LARGE_CAP' },
  { symbol: 'HAL', name: 'Hindustan Aeronautics Ltd', sector: 'Defence', market_cap_category: 'LARGE_CAP' },
  { symbol: 'SIEMENS', name: 'Siemens Ltd', sector: 'Capital Goods', market_cap_category: 'LARGE_CAP' },
  { symbol: 'ABB', name: 'ABB India Ltd', sector: 'Capital Goods', market_cap_category: 'LARGE_CAP' },
  { symbol: 'DLF', name: 'DLF Ltd', sector: 'Realty', market_cap_category: 'LARGE_CAP' },
  { symbol: 'GODREJPROP', name: 'Godrej Properties Ltd', sector: 'Realty', market_cap_category: 'LARGE_CAP' },
  { symbol: 'VEDL', name: 'Vedanta Ltd', sector: 'Metals', market_cap_category: 'LARGE_CAP' },
  { symbol: 'JINDALSTEL', name: 'Jindal Steel & Power Ltd', sector: 'Metals', market_cap_category: 'LARGE_CAP' },
  { symbol: 'ZOMATO', name: 'Zomato Ltd', sector: 'Consumer', market_cap_category: 'LARGE_CAP' },
  { symbol: 'JIOFIN', name: 'Jio Financial Services Ltd', sector: 'Financial Services', market_cap_category: 'LARGE_CAP' },
  { symbol: 'TATAPOWER', name: 'Tata Power Company Ltd', sector: 'Power', market_cap_category: 'LARGE_CAP' },
  { symbol: 'PFC', name: 'Power Finance Corporation Ltd', sector: 'Financial Services', market_cap_category: 'LARGE_CAP' },
  { symbol: 'RECLTD', name: 'REC Ltd', sector: 'Financial Services', market_cap_category: 'LARGE_CAP' },
  { symbol: 'IRFC', name: 'Indian Railway Finance Corp', sector: 'Financial Services', market_cap_category: 'LARGE_CAP' },
  { symbol: 'BANKBARODA', name: 'Bank of Baroda', sector: 'Banking', market_cap_category: 'LARGE_CAP' },
  { symbol: 'PNB', name: 'Punjab National Bank', sector: 'Banking', market_cap_category: 'LARGE_CAP' },
  { symbol: 'CANBK', name: 'Canara Bank', sector: 'Banking', market_cap_category: 'LARGE_CAP' },
  { symbol: 'AMBUJACEM', name: 'Ambuja Cements Ltd', sector: 'Infrastructure', market_cap_category: 'LARGE_CAP' },
  { symbol: 'PIDILITIND', name: 'Pidilite Industries Ltd', sector: 'Chemicals', market_cap_category: 'LARGE_CAP' },
  { symbol: 'HAVELLS', name: 'Havells India Ltd', sector: 'Consumer', market_cap_category: 'LARGE_CAP' },
  { symbol: 'DABUR', name: 'Dabur India Ltd', sector: 'FMCG', market_cap_category: 'LARGE_CAP' },
  { symbol: 'GODREJCP', name: 'Godrej Consumer Products Ltd', sector: 'FMCG', market_cap_category: 'LARGE_CAP' },
  { symbol: 'MARICO', name: 'Marico Ltd', sector: 'FMCG', market_cap_category: 'LARGE_CAP' },
  { symbol: 'BERGEPAINT', name: 'Berger Paints India Ltd', sector: 'Consumer', market_cap_category: 'LARGE_CAP' },
  { symbol: 'SHREECEM', name: 'Shree Cement Ltd', sector: 'Infrastructure', market_cap_category: 'LARGE_CAP' },
  { symbol: 'ACC', name: 'ACC Ltd', sector: 'Infrastructure', market_cap_category: 'LARGE_CAP' },
  { symbol: 'NMDC', name: 'NMDC Ltd', sector: 'Metals', market_cap_category: 'LARGE_CAP' },
  { symbol: 'SAIL', name: 'Steel Authority of India Ltd', sector: 'Metals', market_cap_category: 'LARGE_CAP' },
  { symbol: 'NHPC', name: 'NHPC Ltd', sector: 'Power', market_cap_category: 'LARGE_CAP' },
  { symbol: 'BHEL', name: 'Bharat Heavy Electricals Ltd', sector: 'Capital Goods', market_cap_category: 'LARGE_CAP' },

  // Mid Cap
  { symbol: 'PERSISTENT', name: 'Persistent Systems Ltd', sector: 'IT', market_cap_category: 'MID_CAP' },
  { symbol: 'COFORGE', name: 'Coforge Ltd', sector: 'IT', market_cap_category: 'MID_CAP' },
  { symbol: 'POLYCAB', name: 'Polycab India Ltd', sector: 'Capital Goods', market_cap_category: 'MID_CAP' },
  { symbol: 'DIXON', name: 'Dixon Technologies Ltd', sector: 'Consumer', market_cap_category: 'MID_CAP' },
  { symbol: 'ASTRAL', name: 'Astral Ltd', sector: 'Infrastructure', market_cap_category: 'MID_CAP' },
  { symbol: 'TRENT', name: 'Trent Ltd', sector: 'Consumer', market_cap_category: 'MID_CAP' },
  { symbol: 'CHOLAFIN', name: 'Cholamandalam Investment & Finance', sector: 'Financial Services', market_cap_category: 'MID_CAP' },
  { symbol: 'LUPIN', name: 'Lupin Ltd', sector: 'Pharma', market_cap_category: 'MID_CAP' },
  { symbol: 'AUROPHARMA', name: 'Aurobindo Pharma Ltd', sector: 'Pharma', market_cap_category: 'MID_CAP' },
  { symbol: 'VOLTAS', name: 'Voltas Ltd', sector: 'Consumer', market_cap_category: 'MID_CAP' },
  { symbol: 'FEDERALBNK', name: 'Federal Bank Ltd', sector: 'Banking', market_cap_category: 'MID_CAP' },
  { symbol: 'IDFCFIRSTB', name: 'IDFC First Bank Ltd', sector: 'Banking', market_cap_category: 'MID_CAP' },
  { symbol: 'CUMMINSIND', name: 'Cummins India Ltd', sector: 'Capital Goods', market_cap_category: 'MID_CAP' },
  { symbol: 'DALBHARAT', name: 'Dalmia Bharat Ltd', sector: 'Infrastructure', market_cap_category: 'MID_CAP' },
  { symbol: 'OBEROIRLTY', name: 'Oberoi Realty Ltd', sector: 'Realty', market_cap_category: 'MID_CAP' },
  { symbol: 'PRESTIGE', name: 'Prestige Estates Projects Ltd', sector: 'Realty', market_cap_category: 'MID_CAP' },
  { symbol: 'JUBLFOOD', name: 'Jubilant FoodWorks Ltd', sector: 'Consumer', market_cap_category: 'MID_CAP' },
  { symbol: 'PIIND', name: 'PI Industries Ltd', sector: 'Chemicals', market_cap_category: 'MID_CAP' },
  { symbol: 'ASHOKLEY', name: 'Ashok Leyland Ltd', sector: 'Auto', market_cap_category: 'MID_CAP' },
  { symbol: 'SUPREMEIND', name: 'Supreme Industries Ltd', sector: 'Infrastructure', market_cap_category: 'MID_CAP' },
  { symbol: 'DEEPAKNTR', name: 'Deepak Nitrite Ltd', sector: 'Chemicals', market_cap_category: 'MID_CAP' },
  { symbol: 'TATACOMM', name: 'Tata Communications Ltd', sector: 'Telecom', market_cap_category: 'MID_CAP' },
  { symbol: 'IPCALAB', name: 'IPCA Laboratories Ltd', sector: 'Pharma', market_cap_category: 'MID_CAP' },
  { symbol: 'SUNDARMFIN', name: 'Sundaram Finance Ltd', sector: 'Financial Services', market_cap_category: 'MID_CAP' },
  { symbol: 'BATAINDIA', name: 'Bata India Ltd', sector: 'Consumer', market_cap_category: 'MID_CAP' },
  { symbol: 'RVNL', name: 'Rail Vikas Nigam Ltd', sector: 'Infrastructure', market_cap_category: 'MID_CAP' },
  { symbol: 'IREDA', name: 'Indian Renewable Energy Dev Agency', sector: 'Financial Services', market_cap_category: 'MID_CAP' },
  { symbol: 'MAZDOCK', name: 'Mazagon Dock Shipbuilders Ltd', sector: 'Defence', market_cap_category: 'MID_CAP' },
  { symbol: 'COCHINSHIP', name: 'Cochin Shipyard Ltd', sector: 'Defence', market_cap_category: 'MID_CAP' },
  { symbol: 'MAXHEALTH', name: 'Max Healthcare Institute Ltd', sector: 'Healthcare', market_cap_category: 'MID_CAP' },
  { symbol: 'MANKIND', name: 'Mankind Pharma Ltd', sector: 'Pharma', market_cap_category: 'MID_CAP' },
  { symbol: 'MUTHOOTFIN', name: 'Muthoot Finance Ltd', sector: 'Financial Services', market_cap_category: 'MID_CAP' },
  { symbol: 'LICHSGFIN', name: 'LIC Housing Finance Ltd', sector: 'Financial Services', market_cap_category: 'MID_CAP' },
  { symbol: 'HUDCO', name: 'Housing & Urban Dev Corp', sector: 'Financial Services', market_cap_category: 'MID_CAP' },
  { symbol: 'CGPOWER', name: 'CG Power and Industrial Solutions', sector: 'Capital Goods', market_cap_category: 'MID_CAP' },
  { symbol: 'KEI', name: 'KEI Industries Ltd', sector: 'Capital Goods', market_cap_category: 'MID_CAP' },
  { symbol: 'BHARATFORG', name: 'Bharat Forge Ltd', sector: 'Auto', market_cap_category: 'MID_CAP' },
  { symbol: 'MOTHERSON', name: 'Samvardhana Motherson International', sector: 'Auto', market_cap_category: 'MID_CAP' },
  { symbol: 'SRF', name: 'SRF Ltd', sector: 'Chemicals', market_cap_category: 'MID_CAP' },
  { symbol: 'NAVINFLUOR', name: 'Navin Fluorine International', sector: 'Chemicals', market_cap_category: 'MID_CAP' },
  { symbol: 'LTTS', name: 'L&T Technology Services Ltd', sector: 'IT', market_cap_category: 'MID_CAP' },
  { symbol: 'MPHASIS', name: 'Mphasis Ltd', sector: 'IT', market_cap_category: 'MID_CAP' },

  // Small Cap
  { symbol: 'CDSL', name: 'Central Depository Services (India) Ltd', sector: 'Financial Services', market_cap_category: 'SMALL_CAP' },
  { symbol: 'BSOFT', name: 'Birlasoft Ltd', sector: 'IT', market_cap_category: 'SMALL_CAP' },
  { symbol: 'KAYNES', name: 'Kaynes Technology India Ltd', sector: 'Capital Goods', market_cap_category: 'SMALL_CAP' },
  { symbol: 'SONACOMS', name: 'Sona BLW Precision Forgings Ltd', sector: 'Auto', market_cap_category: 'SMALL_CAP' },
  { symbol: 'KPITTECH', name: 'KPIT Technologies Ltd', sector: 'IT', market_cap_category: 'SMALL_CAP' },
  { symbol: 'CYIENT', name: 'Cyient Ltd', sector: 'IT', market_cap_category: 'SMALL_CAP' },
  { symbol: 'ANGELONE', name: 'Angel One Ltd', sector: 'Financial Services', market_cap_category: 'SMALL_CAP' },
  { symbol: 'SUZLON', name: 'Suzlon Energy Ltd', sector: 'Energy', market_cap_category: 'SMALL_CAP' },
  { symbol: 'TATAELXSI', name: 'Tata Elxsi Ltd', sector: 'IT', market_cap_category: 'SMALL_CAP' },
  { symbol: 'MAPMYINDIA', name: 'CE Info Systems Ltd (MapmyIndia)', sector: 'IT', market_cap_category: 'SMALL_CAP' },
  { symbol: 'ROUTE', name: 'Route Mobile Ltd', sector: 'Telecom', market_cap_category: 'SMALL_CAP' },
  { symbol: 'HAPPYFORGE', name: 'Happy Forgings Ltd', sector: 'Auto', market_cap_category: 'SMALL_CAP' },
  { symbol: 'KEC', name: 'KEC International Ltd', sector: 'Infrastructure', market_cap_category: 'SMALL_CAP' },
  { symbol: 'CENTURYPLY', name: 'Century Plyboards (India) Ltd', sector: 'Infrastructure', market_cap_category: 'SMALL_CAP' },
  { symbol: 'RADICO', name: 'Radico Khaitan Ltd', sector: 'Consumer', market_cap_category: 'SMALL_CAP' },
  { symbol: 'ZENTEC', name: 'Zen Technologies Ltd', sector: 'Defence', market_cap_category: 'SMALL_CAP' },
  { symbol: 'AFFLE', name: 'Affle (India) Ltd', sector: 'IT', market_cap_category: 'SMALL_CAP' },
  { symbol: 'TEJASNET', name: 'Tejas Networks Ltd', sector: 'Telecom', market_cap_category: 'SMALL_CAP' },
  { symbol: 'PPLPHARMA', name: 'Piramal Pharma Ltd', sector: 'Pharma', market_cap_category: 'SMALL_CAP' },
  { symbol: 'LATENTVIEW', name: 'Latent View Analytics Ltd', sector: 'IT', market_cap_category: 'SMALL_CAP' },
  { symbol: 'BSE', name: 'BSE Ltd', sector: 'Financial Services', market_cap_category: 'SMALL_CAP' },
  { symbol: 'MCX', name: 'Multi Commodity Exchange of India', sector: 'Financial Services', market_cap_category: 'SMALL_CAP' },
  { symbol: 'CAMS', name: 'Computer Age Management Services', sector: 'Financial Services', market_cap_category: 'SMALL_CAP' },
  { symbol: 'GRSE', name: 'Garden Reach Shipbuilders & Engineers', sector: 'Defence', market_cap_category: 'SMALL_CAP' },
  { symbol: 'BDL', name: 'Bharat Dynamics Ltd', sector: 'Defence', market_cap_category: 'SMALL_CAP' },
  { symbol: 'BEML', name: 'BEML Ltd', sector: 'Capital Goods', market_cap_category: 'SMALL_CAP' },
  { symbol: 'IRCTC', name: 'Indian Railway Catering & Tourism Corp', sector: 'Consumer', market_cap_category: 'SMALL_CAP' },
  { symbol: 'IEX', name: 'Indian Energy Exchange Ltd', sector: 'Energy', market_cap_category: 'SMALL_CAP' },
  { symbol: 'INOXWIND', name: 'Inox Wind Ltd', sector: 'Energy', market_cap_category: 'SMALL_CAP' },
  { symbol: 'NETWEB', name: 'Netweb Technologies India Ltd', sector: 'IT', market_cap_category: 'SMALL_CAP' },
  { symbol: 'HAPPSTMNDS', name: 'Happiest Minds Technologies', sector: 'IT', market_cap_category: 'SMALL_CAP' },
  { symbol: 'ZENSARTECH', name: 'Zensar Technologies Ltd', sector: 'IT', market_cap_category: 'SMALL_CAP' },
  { symbol: 'SONATACOMS', name: 'Sonata Software Ltd', sector: 'IT', market_cap_category: 'SMALL_CAP' },
  { symbol: 'DEVYANI', name: 'Devyani International Ltd', sector: 'Consumer', market_cap_category: 'SMALL_CAP' },
  { symbol: 'LEMONTREE', name: 'Lemon Tree Hotels Ltd', sector: 'Consumer', market_cap_category: 'SMALL_CAP' },
  { symbol: 'PVRINOX', name: 'PVR INOX Ltd', sector: 'Consumer', market_cap_category: 'SMALL_CAP' },
  { symbol: 'INDIAMART', name: 'IndiaMART InterMESH Ltd', sector: 'IT', market_cap_category: 'SMALL_CAP' },
  { symbol: 'NAUKRI', name: 'Info Edge (India) Ltd', sector: 'IT', market_cap_category: 'SMALL_CAP' },
  { symbol: 'MANAPPURAM', name: 'Manappuram Finance Ltd', sector: 'Financial Services', market_cap_category: 'SMALL_CAP' },
  { symbol: 'POONAWALLA', name: 'Poonawalla Fincorp Ltd', sector: 'Financial Services', market_cap_category: 'SMALL_CAP' },
  { symbol: 'AARTIIND', name: 'Aarti Industries Ltd', sector: 'Chemicals', market_cap_category: 'SMALL_CAP' },
  { symbol: 'ATUL', name: 'Atul Ltd', sector: 'Chemicals', market_cap_category: 'SMALL_CAP' },
  { symbol: 'CLEAN', name: 'Clean Science and Technology', sector: 'Chemicals', market_cap_category: 'SMALL_CAP' },
  { symbol: 'EXIDEIND', name: 'Exide Industries Ltd', sector: 'Auto', market_cap_category: 'SMALL_CAP' },
  { symbol: 'APOLLOTYRE', name: 'Apollo Tyres Ltd', sector: 'Auto', market_cap_category: 'SMALL_CAP' },
  { symbol: 'CEATLTD', name: 'CEAT Ltd', sector: 'Auto', market_cap_category: 'SMALL_CAP' },
  { symbol: 'TIMKEN', name: 'Timken India Ltd', sector: 'Capital Goods', market_cap_category: 'SMALL_CAP' },
  { symbol: 'SJVN', name: 'SJVN Ltd', sector: 'Power', market_cap_category: 'SMALL_CAP' },
  { symbol: 'YESBANK', name: 'Yes Bank Ltd', sector: 'Banking', market_cap_category: 'SMALL_CAP' },
];

export const PortfolioView: React.FC<PortfolioViewProps> = ({
  portfolio,
  loading,
  onAddHolding,
  onDeleteHolding,
  onStockClick,
}) => {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [symbol, setSymbol] = useState('');
  const [quantityStr, setQuantityStr] = useState('10');
  const [buyPriceStr, setBuyPriceStr] = useState('1000');
  const [purchaseDate, setPurchaseDate] = useState(new Date().toISOString().split('T')[0]);
  const [notes, setNotes] = useState('');
  const [showCalculator, setShowCalculator] = useState(false);

  const [selectedThesisHolding, setSelectedThesisHolding] = useState<HoldingAnalysis | null>(null);

  // Auto-suggest state
  const [universeList, setUniverseList] = useState<StockItem[]>(DEFAULT_STOCKS);
  const [filteredSuggestions, setFilteredSuggestions] = useState<StockItem[]>(DEFAULT_STOCKS.slice(0, 10));
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load complete universe list dynamically
  useEffect(() => {
    let isMounted = true;
    api.getUniverse()
      .then((data) => {
        if (isMounted && data && data.length > 0) {
          // Merge with default stocks to ensure comprehensive list
          const symbolSet = new Set(data.map(d => d.symbol.toUpperCase()));
          const combined = [...data];
          for (const s of DEFAULT_STOCKS) {
            if (!symbolSet.has(s.symbol.toUpperCase())) {
              combined.push(s);
            }
          }
          setUniverseList(combined);
        }
      })
      .catch((err) => console.warn('Using default stock catalog for auto-suggest:', err));
    return () => {
      isMounted = false;
    };
  }, []);

  // Filter suggestions dynamically
  useEffect(() => {
    if (!symbol.trim()) {
      setFilteredSuggestions(universeList.slice(0, 10));
      return;
    }
    const q = symbol.toUpperCase().trim();
    const matches = universeList.filter(
      (item) => item.symbol.toUpperCase().includes(q) || item.name.toLowerCase().includes(symbol.toLowerCase())
    );
    
    // If not exact match, add dynamic custom stock option
    const exactMatch = matches.some(m => m.symbol.toUpperCase() === q);
    if (!exactMatch && q.length >= 2) {
      setFilteredSuggestions([
        {
          symbol: q,
          name: `${q} — Custom Stock Lookup`,
          sector: 'Equities',
          market_cap_category: 'EQUITY'
        },
        ...matches.slice(0, 9)
      ]);
    } else {
      setFilteredSuggestions(matches.slice(0, 10));
    }
    setHighlightedIndex(-1);
  }, [symbol, universeList]);

  // Click outside listener for suggestion dropdown
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectStock = async (stock: StockItem) => {
    setSymbol(stock.symbol);
    setIsDropdownOpen(false);
    // Instant fast quote lookup to pre-fill buy price (sub-50ms)
    try {
      const quote = await api.getQuote(stock.symbol);
      if (quote && quote.price > 0) {
        setBuyPriceStr(String(quote.price));
      }
    } catch {
      // Keep default buy price
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isDropdownOpen || filteredSuggestions.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightedIndex((prev) => (prev < filteredSuggestions.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : filteredSuggestions.length - 1));
    } else if (e.key === 'Enter') {
      if (highlightedIndex >= 0 && highlightedIndex < filteredSuggestions.length) {
        e.preventDefault();
        handleSelectStock(filteredSuggestions[highlightedIndex]);
      }
    } else if (e.key === 'Escape') {
      setIsDropdownOpen(false);
    }
  };

  // Quick Date Setter
  const setDaysAgo = (days: number) => {
    const d = new Date();
    d.setDate(d.getDate() - days);
    setPurchaseDate(d.toISOString().split('T')[0]);
  };

  // Safe defaults if portfolio is loading initial data
  if (loading && !portfolio) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-10 bg-slate-200 dark:bg-slate-800 rounded w-1/4"></div>
        <div className="h-32 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
        <div className="h-64 bg-slate-200 dark:bg-slate-800 rounded-xl"></div>
      </div>
    );
  }

  // Ensure safe default values
  const safePortfolio = portfolio || {
    total_invested: 0,
    current_value: 0,
    total_pnl: 0,
    total_pnl_pct: 0,
    holdings_count: 0,
    strengthening_count: 0,
    stable_count: 0,
    weakening_count: 0,
    broken_count: 0,
    sector_exposure_breakdown: {},
    holdings: [],
    what_changed_feed: ['No active holdings. Add your stocks to begin tracking.'],
    last_updated: new Date().toISOString()
  };

  const { 
    total_invested, 
    current_value, 
    total_pnl, 
    total_pnl_pct, 
    holdings, 
    strengthening_count, 
    stable_count, 
    weakening_count, 
    broken_count 
  } = safePortfolio;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!symbol.trim()) return;
    const qty = parseInt(quantityStr, 10);
    const price = parseFloat(buyPriceStr);
    if (isNaN(qty) || qty <= 0) {
      alert('Please enter a valid quantity greater than 0');
      return;
    }
    if (isNaN(price) || price <= 0) {
      alert('Please enter a valid buy price');
      return;
    }

    onAddHolding({
      symbol: symbol.toUpperCase().trim(),
      quantity: qty,
      buy_price: price,
      purchase_date: purchaseDate,
      notes: notes.trim() || undefined,
    });
    setIsAddModalOpen(false);
    setSymbol('');
    setNotes('');
  };

  const getThesisBadge = (status?: string) => {
    switch (status) {
      case 'STRENGTHENING':
        return {
          bg: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30',
          dot: 'bg-emerald-500',
        };
      case 'STABLE':
        return {
          bg: 'bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-500/30',
          dot: 'bg-blue-500',
        };
      case 'WEAKENING':
        return {
          bg: 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30',
          dot: 'bg-amber-500',
        };
      case 'BROKEN':
      default:
        return {
          bg: 'bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30',
          dot: 'bg-rose-500',
        };
    }
  };

  const getSignalBadge = (signal?: string) => {
    switch (signal) {
      case 'BUY MORE':
        return 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30';
      case 'HOLD':
        return 'bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-500/30';
      case 'WATCH':
        return 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30';
      case 'REDUCE':
      case 'SELL':
        return 'bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30';
      default:
        return 'bg-slate-500/15 text-slate-600 dark:text-slate-400 border-slate-500/30';
    }
  };

  const formatINR = (val?: number) => (val !== undefined && val !== null ? Number(val).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00');
  const formatPct = (val?: number) => (val !== undefined && val !== null ? Number(val).toFixed(2) : '0.00');

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              My Investments & Thesis Monitor
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Continuous quantitative monitoring of your swing positions. Evaluates structural thesis integrity, dynamic levels, and clear decision support.
          </p>
        </div>

        <button
          onClick={() => {
            setIsAddModalOpen(true);
            setSymbol('');
            setQuantity(10);
            setBuyPrice(1000);
            setIsDropdownOpen(true);
          }}
          className="flex items-center justify-center space-x-2 px-5 py-2.5 rounded-xl font-bold text-sm bg-blue-600 hover:bg-blue-500 text-white shadow-subtle transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>Add Holding</span>
        </button>
      </div>

      {/* Aggregate Overview Cards (5 Columns with Portfolio Heat) */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Invested */}
        <div className="p-4 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle">
          <span className="text-xs uppercase font-medium text-slate-500">Total Invested</span>
          <div className="text-xl font-bold font-mono text-slate-900 dark:text-white mt-1">
            ₹{formatINR(total_invested)}
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block">{holdings.length} Active Holdings</span>
        </div>

        {/* Current Value */}
        <div className="p-4 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle">
          <span className="text-xs uppercase font-medium text-slate-500">Current Valuation</span>
          <div className="text-xl font-bold font-mono text-slate-900 dark:text-white mt-1">
            ₹{formatINR(current_value)}
          </div>
          <span className="text-[11px] text-emerald-500 mt-1 block font-mono">Real-time Upstox Feed</span>
        </div>

        {/* Total P&L */}
        <div className="p-4 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle">
          <span className="text-xs uppercase font-medium text-slate-500">Unrealized P&L</span>
          <div className={`text-xl font-bold font-mono mt-1 ${
            total_pnl >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'
          }`}>
            {total_pnl >= 0 ? '+' : ''}₹{formatINR(Math.abs(total_pnl))}
          </div>
          <span className={`text-[11px] font-mono font-semibold mt-1 block ${
            total_pnl >= 0 ? 'text-emerald-500' : 'text-rose-500'
          }`}>
            {total_pnl >= 0 ? '+' : ''}{formatPct(total_pnl_pct)}% Overall
          </span>
        </div>

        {/* Thesis Breakdown */}
        <div className="p-4 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle">
          <span className="text-xs uppercase font-medium text-slate-500">Thesis Health</span>
          <div className="flex items-center space-x-2 mt-2 font-mono text-xs">
            <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 font-bold">
              {strengthening_count} Strong
            </span>
            <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20 font-bold">
              {stable_count} Stable
            </span>
            {(weakening_count > 0 || broken_count > 0) && (
              <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 font-bold">
                {weakening_count + broken_count} Alert
              </span>
            )}
          </div>
        </div>

        {/* Portfolio Heat Meter */}
        <div className={`p-4 rounded-xl border shadow-subtle ${
          (safePortfolio.portfolio_heat?.heat_status === 'DANGEROUS_OVEREXPOSURE')
            ? 'bg-rose-500/10 border-rose-500/30'
            : (safePortfolio.portfolio_heat?.heat_status === 'MODERATE')
            ? 'bg-amber-500/10 border-amber-500/30'
            : 'bg-background-cardLight dark:bg-background-cardDark border-border-light dark:border-border-dark'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-xs uppercase font-medium text-slate-500">Portfolio Heat</span>
            <Flame className={`w-3.5 h-3.5 ${
              (safePortfolio.portfolio_heat?.heat_status === 'DANGEROUS_OVEREXPOSURE') ? 'text-rose-500' : 'text-amber-500'
            }`} />
          </div>
          <div className="text-xl font-bold font-mono mt-1 text-slate-900 dark:text-white">
            {safePortfolio.portfolio_heat?.portfolio_heat_pct ?? 0}% <span className="text-xs font-normal text-slate-400 font-sans">/ 6% Max</span>
          </div>
          <span className={`text-[10px] font-semibold mt-1 block ${
            (safePortfolio.portfolio_heat?.heat_status === 'DANGEROUS_OVEREXPOSURE') ? 'text-rose-500 font-bold' : 'text-emerald-500'
          }`}>
            ₹{formatINR(safePortfolio.portfolio_heat?.total_open_risk_inr ?? 0)} Open Risk
          </span>
        </div>
      </div>

      {/* Correlated Sector Warning Banner */}
      {safePortfolio.portfolio_heat?.correlated_sector_warnings && safePortfolio.portfolio_heat.correlated_sector_warnings.length > 0 && (
        <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center space-x-2 text-xs text-amber-600 dark:text-amber-400">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{safePortfolio.portfolio_heat.correlated_sector_warnings.join(' • ')}</span>
        </div>
      )}

      {/* Sector Exposure Breakdown */}
      {safePortfolio.sector_exposure_breakdown && Object.keys(safePortfolio.sector_exposure_breakdown).length > 0 && (
        <div className="p-4 rounded-xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle space-y-2">
          <span className="text-xs uppercase font-medium text-slate-500">Portfolio Sector Exposure (Max 30% cap)</span>
          <div className="flex flex-wrap gap-2">
            {Object.entries(safePortfolio.sector_exposure_breakdown).map(([sec, pct]) => (
              <span key={sec} className={`px-2.5 py-1 rounded-lg text-xs font-mono border ${
                pct > 30 
                  ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30' 
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-border-light dark:border-border-dark'
              }`}>
                {sec}: <strong className="font-bold">{pct}%</strong>
                {pct > 30 && <span className="ml-1 text-[10px] font-sans text-rose-500 font-semibold">(Overweight)</span>}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Holdings Analysis Cards */}
      <div className="space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          Position Health & Action Recommendations
        </h2>

        {holdings.length === 0 ? (
          <div className="p-10 text-center rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark shadow-subtle space-y-3">
            <div className="w-12 h-12 rounded-xl bg-blue-500/10 text-blue-500 flex items-center justify-center mx-auto">
              <Briefcase className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              No active stock positions yet
            </h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto leading-relaxed">
              Add your current swing holdings to get real-time price tracking, thesis health assessments, and quantitative exit targets.
            </p>
            <button
              onClick={() => {
                setIsAddModalOpen(true);
                setSymbol('');
                setQuantity(10);
                setBuyPrice(1000);
                setIsDropdownOpen(true);
              }}
              className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white shadow-subtle"
            >
              <Plus className="w-4 h-4" />
              <span>Add First Stock</span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {holdings.map((h) => {
              const thesis = getThesisBadge(h.thesis_status);
              return (
                <div
                  key={h.id}
                  className="p-5 rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark hover:border-blue-500/40 shadow-subtle transition-all"
                >
                  {/* Top Row: Symbol, Price, P&L, Signal, Thesis */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-border-light dark:border-border-dark">
                    <div className="flex items-center space-x-3">
                      <div 
                        onClick={() => onStockClick(h.symbol)}
                        className="w-10 h-10 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center font-bold text-sm text-slate-800 dark:text-slate-200 font-mono cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900/30 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                      >
                        {h.symbol.slice(0, 3)}
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <span 
                            onClick={() => onStockClick(h.symbol)}
                            className="text-lg font-bold text-slate-900 dark:text-white font-mono hover:text-blue-600 dark:hover:text-blue-400 cursor-pointer"
                          >
                            {h.symbol}
                          </span>
                          <span className={`text-xs font-bold uppercase px-2.5 py-0.5 rounded border ${getSignalBadge(h.signal)}`}>
                            {h.signal}
                          </span>
                          <button
                            onClick={() => setSelectedThesisHolding(h)}
                            className={`flex items-center space-x-1 text-[11px] font-semibold uppercase px-2.5 py-0.5 rounded-full border ${thesis.bg}`}
                          >
                            <span className={`w-1.5 h-1.5 rounded-full ${thesis.dot}`}></span>
                            <span>Thesis: {h.thesis_status}</span>
                          </button>
                        </div>
                        <span className="text-xs text-slate-500 dark:text-slate-400">
                          {h.quantity} shares bought @ ₹{formatINR(h.buy_price)} on {String(h.purchase_date)}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center space-x-4">
                      <div className="text-right font-mono">
                        <div className="text-lg font-bold text-slate-900 dark:text-white">
                          ₹{formatINR(h.current_price)}
                        </div>
                        <div className={`text-xs font-semibold flex items-center justify-end space-x-0.5 ${
                          (h.unrealized_pnl ?? 0) >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'
                        }`}>
                          {(h.unrealized_pnl ?? 0) >= 0 ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                          <span>{(h.unrealized_pnl ?? 0) >= 0 ? '+' : ''}₹{formatINR(Math.abs(h.unrealized_pnl ?? 0))} ({(h.unrealized_pnl_pct ?? 0) >= 0 ? '+' : ''}{formatPct(h.unrealized_pnl_pct)}%)</span>
                        </div>
                      </div>

                      <button
                        onClick={() => onDeleteHolding(h.id)}
                        className="p-2 rounded-lg text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors"
                        title="Remove holding"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Staged Exit & Trailing Stop Guidance Banner */}
                  {h.staged_exit_plan && (
                    <div className={`p-3 rounded-xl border my-3 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2 ${
                      h.staged_exit_plan.current_stage === 'T1_PROFIT_TAKEN_BREAKEVEN_ACTIVE' || h.staged_exit_plan.current_stage === 'T2_PROFIT_TAKEN_RUNNER_ACTIVE' || h.staged_exit_plan.current_stage === 'T3_COMPLETED'
                        ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-800 dark:text-emerald-300'
                        : h.staged_exit_plan.current_stage === 'TIME_DECAY_EXIT_TRIGGERED'
                        ? 'bg-amber-500/10 border-amber-500/30 text-amber-800 dark:text-amber-300'
                        : h.staged_exit_plan.current_stage === 'STOP_LOSS_EXIT'
                        ? 'bg-rose-500/10 border-rose-500/30 text-rose-800 dark:text-rose-300'
                        : 'bg-blue-500/5 border-blue-500/20 text-slate-800 dark:text-slate-200'
                    }`}>
                      <div className="space-y-0.5">
                        <div className="flex items-center space-x-2">
                          <span className="font-bold uppercase tracking-wider text-[10px] px-2 py-0.5 rounded bg-black/10 dark:bg-white/10 font-mono">
                            Stage: {h.staged_exit_plan.stage_label}
                          </span>
                          {h.staged_exit_plan.is_risk_free && (
                            <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-emerald-500 text-white font-mono">
                              100% RISK-FREE
                            </span>
                          )}
                        </div>
                        <p className="text-xs font-medium mt-1">
                          {h.staged_exit_plan.recommended_action}
                        </p>
                      </div>

                      <div className="text-right flex-shrink-0 font-mono">
                        <span className="text-[10px] text-slate-500 uppercase block font-sans">Active Trailing Stop</span>
                        <span className="text-xs font-bold text-rose-600 dark:text-rose-400">
                          {h.staged_exit_plan.trailing_stop_display || (h.levels?.stop_loss ? `₹${formatINR(h.levels.stop_loss)}` : '—')}
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Quantitative Levels & Expected Horizon */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 py-3 border-b border-border-light dark:border-border-dark font-mono text-xs">
                    <div>
                      <span className="text-[10px] uppercase font-sans text-slate-500 font-semibold">Target 1 & 2</span>
                      <div className="text-emerald-600 dark:text-emerald-400 font-bold mt-0.5">
                        T1: {h.levels?.target_1 ? `₹${formatINR(h.levels.target_1)}` : '—'} | T2: {h.levels?.target_2 ? `₹${formatINR(h.levels.target_2)}` : '—'}
                      </div>
                    </div>

                    <div>
                      <span className="text-[10px] uppercase font-sans text-slate-500 font-semibold">Trailing Stop</span>
                      <div className="text-rose-600 dark:text-rose-400 font-bold mt-0.5">
                        {h.staged_exit_plan?.trailing_stop_display || (h.levels?.stop_loss ? `₹${formatINR(h.levels.stop_loss)}` : '—')}
                      </div>
                    </div>

                    <div>
                      <span className="text-[10px] uppercase font-sans text-slate-500 font-semibold">Holding Window</span>
                      <div className="text-slate-700 dark:text-slate-300 font-medium mt-0.5 font-sans">
                        {h.expected_holding_period || '5–10 trading days'}
                      </div>
                    </div>

                    <div>
                      <span className="text-[10px] uppercase font-sans text-slate-500 font-semibold">Volume Activity</span>
                      <div className="text-slate-700 dark:text-slate-300 font-medium mt-0.5 font-sans">
                        {h.volume_condition || 'Normal'}
                      </div>
                    </div>
                  </div>

                  {/* Footer action link */}
                  <div className="pt-2 flex justify-between items-center text-xs">
                    <span className="text-slate-500">
                      RS vs NIFTY (20D): <strong className={h.relative_strength_20d >= 0 ? 'text-emerald-500' : 'text-rose-500'}>
                        {h.relative_strength_20d >= 0 ? '+' : ''}{h.relative_strength_20d}%
                      </strong>
                    </span>
                    <button
                      onClick={() => onStockClick(h.symbol)}
                      className="font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center space-x-1"
                    >
                      <span>Deep Quantitative Breakdown</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Modal: Add Holding with Real-time Auto-Suggestions */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark p-6 space-y-4 shadow-premium">
            <div className="flex items-center justify-between pb-3 border-b border-border-light dark:border-border-dark">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center space-x-2">
                <Briefcase className="w-4 h-4 text-blue-500" />
                <span>Add Stock Holding</span>
              </h3>
              <button
                onClick={() => setIsAddModalOpen(false)}
                className="text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Stock Symbol Auto-suggest Input */}
              <div className="relative" ref={dropdownRef}>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                    NSE Symbol / Company Name
                  </label>
                  <span className="text-[10px] text-blue-500 font-mono">
                    {universeList.length} Indian Equities Available
                  </span>
                </div>

                <div className="relative">
                  <input
                    ref={inputRef}
                    type="text"
                    required
                    value={symbol}
                    list="stocks-datalist"
                    onChange={(e) => {
                      setSymbol(e.target.value.toUpperCase());
                      setIsDropdownOpen(true);
                    }}
                    onFocus={() => setIsDropdownOpen(true)}
                    onClick={() => setIsDropdownOpen(true)}
                    onKeyDown={handleKeyDown}
                    className="w-full pl-9 pr-3 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-900 border border-border-light dark:border-border-dark text-sm font-mono focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 uppercase tracking-wide text-slate-900 dark:text-white"
                    placeholder="Type symbol (e.g. TCS, RELIANCE, PERSISTENT, CDSL)"
                    autoComplete="off"
                  />
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
                </div>

                {/* HTML5 Native Datalist Failsafe */}
                <datalist id="stocks-datalist">
                  {universeList.map((item) => (
                    <option key={item.symbol} value={item.symbol}>
                      {item.name} ({item.sector})
                    </option>
                  ))}
                </datalist>

                {/* Popular Quick Suggestions Chips */}
                <div className="flex flex-wrap gap-1.5 mt-2">
                  <span className="text-[10px] text-slate-400 self-center mr-1">Popular:</span>
                  {['RELIANCE', 'TCS', 'HDFCBANK', 'PERSISTENT', 'CDSL', 'KAYNES', 'SUZLON'].map((sym) => (
                    <button
                      key={sym}
                      type="button"
                      onClick={() => {
                        const match = universeList.find(u => u.symbol === sym);
                        if (match) handleSelectStock(match);
                        else setSymbol(sym);
                      }}
                      className="px-2 py-0.5 rounded-md text-[10px] font-mono font-medium bg-slate-100 dark:bg-slate-800 hover:bg-blue-500 hover:text-white text-slate-600 dark:text-slate-300 transition-colors border border-slate-200 dark:border-slate-700"
                    >
                      {sym}
                    </button>
                  ))}
                </div>

                {/* Floating Suggestions Dropdown */}
                {isDropdownOpen && filteredSuggestions.length > 0 && (
                  <div className="absolute left-0 right-0 top-full mt-1.5 z-[100] max-h-60 overflow-y-auto rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 shadow-2xl divide-y divide-slate-100 dark:divide-slate-800">
                    {filteredSuggestions.map((item, idx) => {
                      const isHighlighted = idx === highlightedIndex;
                      return (
                        <div
                          key={item.symbol}
                          onMouseDown={(e) => {
                            e.preventDefault();
                            handleSelectStock(item);
                          }}
                          onClick={() => handleSelectStock(item)}
                          className={`p-3 flex items-center justify-between cursor-pointer transition-colors ${
                            isHighlighted
                              ? 'bg-blue-50 dark:bg-blue-900/50 text-blue-600 dark:text-blue-300'
                              : 'hover:bg-slate-50 dark:hover:bg-slate-800/80 text-slate-900 dark:text-slate-100'
                          }`}
                        >
                          <div>
                            <div className="flex items-center space-x-2">
                              <span className="font-mono font-bold text-xs">
                                {item.symbol}
                              </span>
                              {item.market_cap_category && (
                                <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-semibold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                                  {item.market_cap_category.replace('_', ' ')}
                                </span>
                              )}
                            </div>
                            <span className="text-[11px] text-slate-500 dark:text-slate-400 block truncate max-w-[240px] mt-0.5">
                              {item.name}
                            </span>
                          </div>

                          <div className="text-right pl-2">
                            <span className="text-[10px] font-semibold text-slate-400 block">
                              {item.sector}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Position Sizer Toggle */}
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-blue-500/10 border border-blue-500/20">
                <div className="flex items-center space-x-2 text-xs text-blue-600 dark:text-blue-300">
                  <Calculator className="w-4 h-4 text-blue-500 flex-shrink-0" />
                  <span className="font-semibold">1% Account Risk Sizer</span>
                </div>
                <button
                  type="button"
                  onClick={() => setShowCalculator(!showCalculator)}
                  className="px-2.5 py-1 rounded-lg text-xs font-bold bg-blue-600 text-white hover:bg-blue-500 transition-colors"
                >
                  {showCalculator ? 'Hide Sizer' : 'Calculate Shares'}
                </button>
              </div>

              {showCalculator && (
                <PositionSizingWidget
                  levels={{
                    current_price: parseFloat(buyPriceStr) || 1000,
                    reference_entry: parseFloat(buyPriceStr) || 1000,
                    stop_loss: (parseFloat(buyPriceStr) || 1000) * 0.965,
                    target_1: (parseFloat(buyPriceStr) || 1000) * 1.06,
                    stop_method: 'SWING_LOW',
                    stop_reason: '1% Risk Boundary',
                    levels_reasoning: []
                  }}
                  currentPrice={parseFloat(buyPriceStr) || 1000}
                  onApplyQuantity={(qty) => {
                    setQuantityStr(String(qty));
                    setShowCalculator(false);
                  }}
                />
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Quantity (Shares)
                    </label>
                  </div>
                  <input
                    type="text"
                    inputMode="numeric"
                    required
                    value={quantityStr}
                    onFocus={(e) => e.target.select()}
                    onChange={(e) => {
                      const val = e.target.value;
                      if (val === '' || /^[0-9]+$/.test(val)) {
                        const clean = val.replace(/^0+(?=\d)/, '');
                        setQuantityStr(clean);
                      }
                    }}
                    placeholder="e.g. 25"
                    className="w-full px-3 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-900 border border-border-light dark:border-border-dark text-sm font-mono focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-slate-900 dark:text-white"
                  />
                  {/* Quick Quantity Pills */}
                  <div className="flex flex-wrap gap-1 mt-1.5">
                    {[10, 25, 50, 100, 250].map((q) => (
                      <button
                        key={q}
                        type="button"
                        onClick={() => setQuantityStr(String(q))}
                        className={`px-2 py-0.5 rounded text-[10px] font-mono transition-colors border ${
                          quantityStr === String(q)
                            ? 'bg-blue-600 text-white border-blue-600 font-bold'
                            : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700'
                        }`}
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                      Buy Price (₹)
                    </label>
                    <span className="text-[10px] text-slate-400 font-mono">Per Share</span>
                  </div>
                  <input
                    type="text"
                    inputMode="decimal"
                    required
                    value={buyPriceStr}
                    onFocus={(e) => e.target.select()}
                    onChange={(e) => {
                      const val = e.target.value;
                      if (val === '' || /^[0-9]*\.?[0-9]*$/.test(val)) {
                        const clean = val.replace(/^0+(?=[1-9])/, '');
                        setBuyPriceStr(clean);
                      }
                    }}
                    placeholder="e.g. 2950.50"
                    className="w-full px-3 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-900 border border-border-light dark:border-border-dark text-sm font-mono focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-slate-900 dark:text-white"
                  />
                  {/* Quick Rounding or LTP indication */}
                  <div className="text-[10px] text-slate-400 mt-1.5 flex items-center justify-between">
                    <span>Clean numeric value</span>
                    {buyPriceStr && !isNaN(parseFloat(buyPriceStr)) && (
                      <span className="text-emerald-500 font-mono font-semibold">₹{parseFloat(buyPriceStr).toFixed(2)}</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Purchase Date with Quick Date Presets */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Purchase Date
                  </label>
                  <span className="text-[11px] text-blue-500 font-mono">
                    {(() => {
                      try {
                        const [y, m, d] = purchaseDate.split('-').map(Number);
                        const dateObj = new Date(y, m - 1, d);
                        return dateObj.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
                      } catch {
                        return purchaseDate;
                      }
                    })()}
                  </span>
                </div>

                <input
                  type="date"
                  required
                  value={purchaseDate}
                  onChange={(e) => setPurchaseDate(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-border-light dark:border-border-dark text-sm font-mono focus:outline-none focus:border-blue-500 text-slate-900 dark:text-white"
                />

                {/* Quick Date Presets */}
                <div className="flex flex-wrap gap-1.5 pt-1">
                  <span className="text-[10px] text-slate-400 self-center mr-1">Presets:</span>
                  {[
                    { label: 'Today', days: 0 },
                    { label: 'Yesterday', days: 1 },
                    { label: '3D Ago', days: 3 },
                    { label: '1W Ago', days: 7 },
                    { label: '15D Ago', days: 15 },
                    { label: '1M Ago', days: 30 },
                  ].map((p) => (
                    <button
                      key={p.label}
                      type="button"
                      onClick={() => setDaysAgo(p.days)}
                      className="px-2 py-0.5 rounded-md text-[10px] font-mono font-medium bg-slate-100 dark:bg-slate-800 hover:bg-blue-500 hover:text-white text-slate-600 dark:text-slate-300 transition-colors border border-slate-200 dark:border-slate-700"
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Total Investment Live Calculation Preview */}
              <div className="p-3 rounded-xl bg-slate-100 dark:bg-slate-900 border border-border-light dark:border-border-dark flex items-center justify-between text-xs">
                <span className="text-slate-500 font-medium">Total Capital Outlay:</span>
                <span className="font-mono font-bold text-sm text-slate-900 dark:text-white">
                  ₹{((parseInt(quantityStr, 10) || 0) * (parseFloat(buyPriceStr) || 0)).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Investment Notes (Optional)
                </label>
                <input
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-900 border border-border-light dark:border-border-dark text-sm focus:outline-none focus:border-blue-500"
                  placeholder="e.g. Swing breakout entry on 20 EMA bounce"
                />
              </div>

              <div className="pt-2 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white shadow-subtle"
                >
                  Add Holding
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Thesis Details */}
      {selectedThesisHolding && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md rounded-2xl bg-background-cardLight dark:bg-background-cardDark border border-border-light dark:border-border-dark p-6 space-y-4 shadow-premium">
            <div className="flex items-center justify-between pb-3 border-b border-border-light dark:border-border-dark">
              <h3 className="text-base font-bold text-slate-900 dark:text-white font-mono">
                {selectedThesisHolding.symbol} — Thesis State ({selectedThesisHolding.thesis_status})
              </h3>
              <button
                onClick={() => setSelectedThesisHolding(null)}
                className="text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
              >
                ✕
              </button>
            </div>

            <div className="space-y-2.5 text-xs text-slate-600 dark:text-slate-300">
              {selectedThesisHolding.thesis_points && selectedThesisHolding.thesis_points.map((pt, idx) => (
                <div key={idx} className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 leading-relaxed">
                  • {pt}
                </div>
              ))}
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedThesisHolding(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-slate-200 hover:bg-slate-300 dark:hover:bg-slate-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
