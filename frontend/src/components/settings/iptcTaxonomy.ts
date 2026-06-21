export interface TaxonomyNode {
  id: string;
  name: string;
  color?: string;
  keywords?: string[];
  prompt?: string;
  children?: TaxonomyNode[];
}

export const IPTC_TAXONOMY: TaxonomyNode[] = [
  {
    id: "01",
    name: "Arts, entertainment and media",
    color: "#ec4899",
    keywords: ["arts", "culture", "entertainment", "media", "film", "music", "television", "streaming", "fashion", "gaming", "literature"],
    prompt: "Articles about arts, culture, entertainment, and the media industry. Covers film, music, television, literature, visual arts, gaming, fashion, and the business of media. Assign when the primary subject is a cultural product, creative work, entertainment event, or media organisation.",
    children: [
      {
        id: "01.01", name: "Cinema and film",
        keywords: ["film", "movie", "cinema", "director", "box office", "Hollywood", "Oscar", "Cannes", "release", "screenplay", "studio", "actor"],
        prompt: "Articles about cinema and the film industry. Covers new releases, box office performance, filmmakers, awards season, film festivals, and studio business. Assign when the subject is a specific film, filmmaker, or the movie industry.",
      },
      {
        id: "01.02", name: "Dance",
        keywords: ["dance", "ballet", "choreography", "performance", "dance company", "contemporary dance", "hip-hop", "ballroom", "touring", "dancer"],
        prompt: "Articles about dance as a performing art. Covers ballet, contemporary, hip-hop, and other dance forms, choreographers, dance companies, and competitions. Assign when the primary subject is a dance performance, artist, or the dance world.",
      },
      {
        id: "01.03", name: "Fashion and beauty",
        keywords: ["fashion", "designer", "runway", "collection", "couture", "style", "beauty", "cosmetics", "trend", "luxury", "fashion week", "LVMH"],
        prompt: "Articles about the fashion and beauty industries. Covers runway shows, designer collections, fashion weeks, beauty products, and the fashion business. Assign when the article focuses on clothing, accessories, cosmetics, or fashion as an industry rather than broader retail.",
      },
      {
        id: "01.04", name: "Gaming and video games",
        keywords: ["video game", "gaming", "PlayStation", "Xbox", "Nintendo", "PC gaming", "esports", "game release", "developer", "Steam", "Valve", "indie game"],
        prompt: "Articles about video games and the gaming industry. Covers game releases, studios, esports, gaming hardware, and gaming culture. Assign when the primary subject is a specific game, gaming platform, or the business of game development and publishing.",
      },
      {
        id: "01.05", name: "Literature and poetry",
        keywords: ["book", "novel", "author", "literature", "fiction", "nonfiction", "poetry", "publisher", "bestseller", "Booker Prize", "literary award"],
        prompt: "Articles about books, literature, and poetry. Covers new publications, author profiles, literary prizes, publishing industry news, and reading culture. Assign when the article's focus is on a specific book, author, or the world of literary publishing.",
      },
      {
        id: "01.06", name: "Music",
        keywords: ["music", "album", "artist", "concert", "tour", "Grammy", "chart", "band", "singer", "record label", "Spotify", "festival", "streaming"],
        prompt: "Articles about music and the music industry. Covers album releases, concert tours, streaming numbers, artist news, genre trends, music awards, and the business of record labels and music distribution.",
      },
      {
        id: "01.07", name: "Photography",
        keywords: ["photography", "photographer", "exhibition", "camera", "portrait", "photojournalism", "lens", "photo award", "gallery", "Magnum", "image"],
        prompt: "Articles about photography as an art form or profession. Covers photographers, exhibitions, photojournalism, camera technology, and the photo industry. Assign when photography itself—not photos that merely illustrate another story—is the subject.",
      },
      {
        id: "01.08", name: "Radio",
        keywords: ["radio", "broadcast", "station", "listener", "FM", "AM", "BBC Radio", "terrestrial radio", "digital radio", "DAB", "audio"],
        prompt: "Articles about radio broadcasting and audio media. Covers radio stations, presenters, listener ratings, and the radio industry. Assign when radio as a medium—rather than a specific programme's content—is the subject.",
      },
      {
        id: "01.09", name: "Television and streaming",
        keywords: ["TV", "television", "streaming", "Netflix", "HBO", "Disney+", "series", "episode", "ratings", "showrunner", "commission", "broadcast"],
        prompt: "Articles about television and video streaming services. Covers TV shows, streaming platform performance, viewership, commissioning decisions, and the TV industry. Assign when the subject is a specific programme, TV channel, or streaming service.",
      },
      {
        id: "01.10", name: "Theatre and performing arts",
        keywords: ["theatre", "play", "Broadway", "West End", "musical", "stage", "opera", "performance", "production", "Tony Awards", "casting", "touring"],
        prompt: "Articles about theatre and live performing arts. Covers stage plays, musicals, opera, Broadway, West End, touring productions, and theatre companies. Assign when the subject is a specific production, venue, or the performing arts world.",
      },
      {
        id: "01.11", name: "Visual arts",
        keywords: ["art", "painting", "sculpture", "gallery", "museum", "exhibition", "artist", "auction", "contemporary art", "installation", "Christie's", "Sotheby's"],
        prompt: "Articles about the visual arts. Covers painting, sculpture, contemporary art, gallery exhibitions, auction results, and the art market. Assign when the primary subject is a work of art, artist, gallery, museum, or the art market.",
      },
      {
        id: "01.12", name: "Entertainment",
        keywords: ["celebrity", "entertainment", "awards", "red carpet", "premiere", "pop culture", "fame", "gossip", "public figure", "entertainment industry"],
        prompt: "Articles about entertainment broadly—celebrity culture, award shows, and pop culture events not covered by more specific subcategories. Assign when the article covers celebrity news or entertainment industry developments that span across film, music, and TV.",
      },
      {
        id: "01.13",
        name: "Media",
        keywords: ["media", "journalism", "press", "publisher", "news industry", "media ownership", "press freedom", "newsroom", "editorial", "media company"],
        prompt: "Articles about the media industry as a business or institution. Covers media ownership, press freedom, journalism practices, and trends in content distribution. Assign when the subject is the media sector itself rather than specific content it produces.",
        children: [
          {
            id: "01.13.01", name: "Broadcasting",
            keywords: ["broadcaster", "network", "ratings", "FCC", "Ofcom", "terrestrial", "satellite", "cable", "broadcast rights", "viewership", "transmission"],
            prompt: "Articles about broadcast media networks and their business. Covers television and radio networks, regulatory environment, programming strategy, and broadcast rights. Assign for industry-level broadcasting news rather than coverage of specific programmes.",
          },
          {
            id: "01.13.02", name: "Journalism and news",
            keywords: ["journalism", "reporter", "press freedom", "investigative", "editorial", "newsroom", "journalist safety", "media ethics", "Pulitzer", "fact-checking"],
            prompt: "Articles about journalism as a practice and profession. Covers press freedom, investigative reporting, newsroom management, journalist safety, and media ethics. Assign when journalism itself—not a specific story's content—is the subject.",
          },
          {
            id: "01.13.03", name: "Online media and publishing",
            keywords: ["digital media", "online news", "publisher", "newsletter", "Substack", "paywall", "digital advertising", "content monetisation", "audience growth"],
            prompt: "Articles about digital publishing and online news outlets. Covers paywalls, newsletter platforms, digital advertising, audience metrics, and the economics of online journalism and content creation.",
          },
          {
            id: "01.13.04", name: "Social media and influencers",
            keywords: ["social media", "influencer", "TikTok", "Instagram", "YouTube", "viral", "content creator", "algorithm", "platform policy", "X", "creator economy"],
            prompt: "Articles about social media platforms and content creators. Covers platform policies, algorithm changes, influencer marketing, viral trends, and the creator economy. Assign when social media platforms or individual creators are the primary subject.",
          },
        ],
      },
    ],
  },
  {
    id: "02",
    name: "Crime, law and justice",
    color: "#ef4444",
    keywords: ["crime", "law", "court", "justice", "arrest", "trial", "verdict", "sentence", "police", "prosecution", "legal", "criminal"],
    prompt: "Articles about crime, the legal system, and justice. Covers criminal cases, court proceedings, law enforcement, legislation, and incarceration. Assign when the primary subject is a crime, legal proceeding, law enforcement action, or the justice system.",
    children: [
      {
        id: "02.01", name: "Courts and judiciary",
        keywords: ["court", "judge", "verdict", "trial", "ruling", "appeal", "Supreme Court", "lawsuit", "sentence", "hearing", "justice", "litigation"],
        prompt: "Articles about court cases and judicial proceedings. Covers verdicts, rulings, appeals, Supreme Court decisions, and the judiciary system. Assign when the article centres on a specific legal case, court ruling, or the functioning of courts.",
      },
      {
        id: "02.02",
        name: "Crime",
        keywords: ["crime", "criminal", "offender", "victim", "investigation", "murder", "robbery", "theft", "assault", "perpetrator"],
        prompt: "Articles about criminal activity. Covers specific crimes, criminal investigations, and criminal networks. Assign when the article's focus is on the commission of a crime or the criminal actors involved. Use subcategories for specific crime types.",
        children: [
          {
            id: "02.02.01", name: "Cybercrime and hacking",
            keywords: ["hacking", "data breach", "malware", "ransomware", "phishing", "cybercrime", "dark web", "exploit", "botnet", "identity theft"],
            prompt: "Articles about cybercrime and malicious hacking. Covers data breaches, ransomware attacks, phishing campaigns, criminal hacking groups, and digital fraud. Assign when the crime primarily occurs in or through digital systems. Do not assign for state-sponsored cyber operations—use Cyberwarfare instead.",
          },
          {
            id: "02.02.02", name: "Drug trafficking",
            keywords: ["drug trafficking", "narcotics", "cartel", "fentanyl", "smuggling", "DEA", "seizure", "cocaine", "heroin", "drug bust"],
            prompt: "Articles about the illegal drug trade. Covers drug trafficking networks, cartels, major seizures, and law enforcement operations against narcotics smuggling. Assign when the article focuses on the criminal supply and distribution of illegal drugs.",
          },
          {
            id: "02.02.03", name: "Financial crime and fraud",
            keywords: ["fraud", "money laundering", "Ponzi scheme", "embezzlement", "financial crime", "SEC enforcement", "insider trading", "scam", "corruption"],
            prompt: "Articles about financial crime. Covers fraud, money laundering, embezzlement, Ponzi schemes, insider trading, and corruption. Assign when the article focuses on criminal financial misconduct rather than civil regulatory enforcement.",
          },
          {
            id: "02.02.04", name: "Organized crime",
            keywords: ["organized crime", "mafia", "cartel", "gang", "criminal network", "mob", "extortion", "protection racket", "racketeering", "syndicate"],
            prompt: "Articles about organised criminal networks. Covers mafia organisations, criminal gangs, cartels, and other structured criminal enterprises. Assign when the article's subject is a criminal organisation rather than an individual crime or criminal.",
          },
          {
            id: "02.02.05", name: "Terrorism",
            keywords: ["terrorism", "attack", "bomb", "ISIS", "al-Qaeda", "extremism", "counter-terrorism", "threat", "radicalisation", "suicide bomber"],
            prompt: "Articles about terrorist acts and organisations. Covers attacks, plots, terrorist groups, radicalisation, and counter-terrorism measures. Assign for crimes motivated by political, ideological, or religious extremism. Use Terrorism and insurgency (16.04) for ongoing conflict contexts.",
          },
          {
            id: "02.02.06", name: "Violent crime",
            keywords: ["murder", "shooting", "violence", "assault", "homicide", "armed robbery", "stabbing", "gun violence", "mass shooting", "manslaughter"],
            prompt: "Articles about violent crimes against persons. Covers murder, assault, armed robbery, gun violence, and mass shootings. Assign when the article is primarily about acts of violence as criminal matters rather than in a conflict or terrorism context.",
          },
        ],
      },
      {
        id: "02.03", name: "Law enforcement and policing",
        keywords: ["police", "arrest", "FBI", "investigation", "officer", "law enforcement", "search warrant", "SWAT", "patrol", "detective", "misconduct"],
        prompt: "Articles about law enforcement agencies and policing. Covers police operations, arrests, investigations, police reform, misconduct, and the relationship between law enforcement and communities.",
      },
      {
        id: "02.04", name: "Legislation and legal proceedings",
        keywords: ["law", "legislation", "statute", "bill", "amendment", "legal proceedings", "lawmaker", "legal reform", "act", "ordinance", "code"],
        prompt: "Articles about the making and application of law. Covers new legislation, legal reform, landmark statutes, and the formal processes of legal proceedings outside of specific criminal cases. Assign when the subject is a law or the legislative process rather than a court case.",
      },
      {
        id: "02.05", name: "Prisons and incarceration",
        keywords: ["prison", "jail", "sentencing", "parole", "incarceration", "inmate", "correctional", "death penalty", "solitary confinement", "prison reform"],
        prompt: "Articles about prisons, detention, and incarceration. Covers prison conditions, sentencing policy, parole, prison reform, and the correctional system. Assign when the article's primary focus is on the imprisonment or detention of individuals rather than the crimes that led to incarceration.",
      },
    ],
  },
  {
    id: "03",
    name: "Disaster, accident and emergency",
    color: "#f97316",
    keywords: ["disaster", "accident", "emergency", "casualties", "rescue", "evacuation", "fatalities", "relief", "crisis", "damage"],
    prompt: "Articles about disasters, accidents, and emergencies. Covers natural disasters, industrial accidents, transport crashes, and emergency response. Assign when the article reports on a specific harmful event and its immediate consequences.",
    children: [
      {
        id: "03.01", name: "Aviation accident",
        keywords: ["plane crash", "aviation accident", "airline", "flight", "passengers", "NTSB", "FAA", "investigation", "crash landing", "mid-air collision"],
        prompt: "Articles about aviation accidents and incidents. Covers aircraft crashes, emergency landings, mid-air collisions, and aviation safety investigations. Assign for civil aviation incidents; use Ground operations for military aircraft.",
      },
      {
        id: "03.02", name: "Fire and explosion",
        keywords: ["fire", "explosion", "blaze", "arson", "firefighter", "evacuation", "inferno", "detonation", "gas leak", "building fire"],
        prompt: "Articles about fires and explosions causing harm or damage. Covers structural fires, industrial explosions, arson, and firefighting operations. Assign for man-made fires and explosions; use Wildfire for uncontrolled vegetation fires.",
      },
      {
        id: "03.03", name: "Industrial and nuclear accident",
        keywords: ["industrial accident", "chemical spill", "nuclear accident", "radiation", "plant explosion", "contamination", "toxic leak", "oil spill", "refinery"],
        prompt: "Articles about accidents at industrial or nuclear facilities. Covers chemical spills, refinery explosions, nuclear plant incidents, and hazardous material releases. Assign when the accident originates from an industrial or energy production facility.",
      },
      {
        id: "03.04",
        name: "Natural disaster",
        keywords: ["natural disaster", "disaster relief", "casualties", "evacuation", "emergency response", "FEMA", "aid", "affected", "damage"],
        prompt: "Articles about natural disasters. Covers the event itself, casualty reports, emergency response, and relief efforts. Use the most specific subcategory available. Assign the parent category when the article covers multiple disaster types or general disaster preparedness.",
        children: [
          {
            id: "03.04.01", name: "Drought",
            keywords: ["drought", "water shortage", "crop failure", "arid", "rainfall deficit", "groundwater", "water crisis", "dry season", "famine risk"],
            prompt: "Articles about droughts and water scarcity caused by prolonged dry conditions. Covers impacts on agriculture, water supplies, and affected communities. Assign when drought is the primary cause of the crisis described.",
          },
          {
            id: "03.04.02", name: "Earthquake and tsunami",
            keywords: ["earthquake", "tsunami", "seismic", "magnitude", "tremor", "fault line", "aftershock", "richter", "tectonic", "epicentre"],
            prompt: "Articles about earthquakes and tsunamis. Covers seismic events, their magnitude, casualties, structural damage, and triggered tsunamis. Assign when an earthquake or tsunami is the primary event causing harm.",
          },
          {
            id: "03.04.03", name: "Flood",
            keywords: ["flood", "flooding", "storm surge", "river burst", "dam failure", "inundation", "displacement", "flash flood", "levee"],
            prompt: "Articles about flooding and its consequences. Covers river flooding, storm surges, flash floods, dam failures, and the displacement of affected populations. Assign when flooding is the primary disaster event.",
          },
          {
            id: "03.04.04", name: "Hurricane and tropical storm",
            keywords: ["hurricane", "typhoon", "cyclone", "tropical storm", "Category 5", "landfall", "storm surge", "evacuation", "wind speed", "NHC"],
            prompt: "Articles about tropical storms, hurricanes, and typhoons. Covers storm development, landfall, wind and surge damage, evacuations, and aftermath. Assign for tropical cyclone events regardless of basin or naming convention.",
          },
          {
            id: "03.04.05", name: "Wildfire",
            keywords: ["wildfire", "forest fire", "bushfire", "blaze", "containment", "evacuation", "acres burned", "firefighter", "air quality", "fire season"],
            prompt: "Articles about uncontrolled fires in wildland or vegetation areas. Covers wildfire spread, containment efforts, evacuations, property destruction, and smoke impacts. Assign for naturally or accidentally ignited uncontrolled fires.",
          },
          {
            id: "03.04.06", name: "Volcanic eruption",
            keywords: ["volcano", "eruption", "lava", "ash cloud", "pyroclastic", "seismic activity", "magma", "evacuation", "crater", "caldera"],
            prompt: "Articles about volcanic eruptions and volcanic activity. Covers eruption events, lava flows, ash dispersal, air travel disruptions, and evacuations of surrounding populations.",
          },
        ],
      },
      {
        id: "03.05", name: "Transport accident",
        keywords: ["crash", "collision", "road accident", "train derailment", "ship sinking", "fatalities", "road safety", "pile-up", "motorway", "bridge collapse"],
        prompt: "Articles about accidents involving road, rail, and maritime transport. Covers vehicle crashes, train derailments, ship collisions, and their casualties. Assign for civilian transport accidents; use the relevant warfare subcategory for military transport incidents.",
      },
    ],
  },
  {
    id: "04",
    name: "Economy, business and finance",
    color: "#f59e0b",
    keywords: ["economy", "business", "finance", "market", "company", "investment", "profit", "earnings", "GDP", "growth", "industry", "trade"],
    prompt: "Articles about economics, business, and financial markets. Covers corporate news, economic indicators, financial markets, industry sectors, and business strategy. Assign when the primary subject is economic activity, a company's business, or financial markets.",
    children: [
      {
        id: "04.01", name: "Agriculture and food industry",
        keywords: ["agriculture", "farming", "crop", "harvest", "food supply", "commodity prices", "livestock", "irrigation", "agribusiness", "food production"],
        prompt: "Articles about agriculture, farming, and the commercial food supply chain. Covers crop yields, commodity prices, farm policy, agribusiness, and food production economics. Assign when the agricultural or food production industry is the primary subject.",
      },
      {
        id: "04.02",
        name: "Banking and financial services",
        keywords: ["bank", "banking", "financial services", "lending", "deposit", "interest rate", "credit", "liquidity", "balance sheet", "financial institution"],
        prompt: "Articles about banks and the broader financial services industry. Covers bank earnings, lending activity, interest rates, financial stability, and the business of financial institutions. Use subcategories for more specific banking topics.",
        children: [
          {
            id: "04.02.01", name: "Central banking and monetary policy",
            keywords: ["central bank", "interest rates", "Fed", "ECB", "inflation", "monetary policy", "rate hike", "quantitative easing", "reserve", "Federal Reserve"],
            prompt: "Articles about central banks and monetary policy decisions. Covers interest rate decisions by the Fed, ECB, and other central banks, inflation targeting, quantitative easing, and the broader conduct of monetary policy.",
          },
          {
            id: "04.02.02", name: "Consumer finance and lending",
            keywords: ["mortgage", "loan", "credit card", "personal finance", "lending", "consumer debt", "auto loan", "student loan", "CFPB", "credit score"],
            prompt: "Articles about consumer financial products and household debt. Covers mortgages, personal loans, credit cards, student debt, and consumer lending trends. Assign when the subject is financial products used by individuals rather than institutional finance.",
          },
          {
            id: "04.02.03", name: "Investment banking",
            keywords: ["IPO", "underwriting", "Goldman Sachs", "Morgan Stanley", "M&A advisory", "securities", "deal", "capital markets", "bond issuance", "investment bank"],
            prompt: "Articles about investment banking activities. Covers IPO underwriting, mergers and acquisitions advisory, capital markets activity, and the businesses of major investment banks. Distinguish from retail banking and asset management.",
          },
        ],
      },
      {
        id: "04.03",
        name: "Computing and information technology",
        keywords: ["technology", "software", "hardware", "IT", "tech company", "platform", "digital", "Silicon Valley", "startup", "cloud", "data"],
        prompt: "Articles about the computing and IT industry as a business sector. Covers technology companies, product launches, industry competition, and the commercial side of technology. Use subcategories for specific technology domains.",
        children: [
          {
            id: "04.03.01", name: "Artificial intelligence",
            keywords: ["AI", "machine learning", "LLM", "ChatGPT", "OpenAI", "Anthropic", "neural network", "model", "generative AI", "foundation model", "inference", "GPU"],
            prompt: "Articles about artificial intelligence as a commercial and industrial force. Covers AI product launches, company competition, enterprise adoption, AI investment, and business impacts of AI. For academic AI research, use Artificial intelligence research (13.04.02).",
          },
          {
            id: "04.03.02", name: "Cloud computing and infrastructure",
            keywords: ["cloud", "AWS", "Azure", "Google Cloud", "data centre", "servers", "SaaS", "IaaS", "PaaS", "colocation", "hyperscaler", "cloud revenue"],
            prompt: "Articles about cloud computing services and digital infrastructure. Covers cloud provider competition, data centre investment, cloud adoption by enterprises, and the business of hyperscalers like AWS, Azure, and Google Cloud.",
          },
          {
            id: "04.03.03", name: "Cybersecurity",
            keywords: ["cybersecurity", "hack", "vulnerability", "breach", "ransomware", "CVE", "zero-day", "CISA", "cyber defence", "infosec", "patch", "threat actor"],
            prompt: "Articles about cybersecurity threats, incidents, and defences. Covers newly disclosed vulnerabilities, ransomware attacks, data breaches, nation-state intrusions, security research, and the cybersecurity industry. For state-level cyber conflict use Cyberwarfare (16.01.02).",
          },
          {
            id: "04.03.04", name: "Hardware and semiconductors",
            keywords: ["chip", "semiconductor", "NVIDIA", "Intel", "AMD", "TSMC", "processor", "GPU", "silicon", "wafer", "fab", "supply chain", "HBM"],
            prompt: "Articles about computer hardware and the semiconductor industry. Covers chip design, manufacturing, supply chain issues, fab capacity, new processor architectures, and competition among chip companies. Assign when silicon or physical hardware is the subject.",
          },
          {
            id: "04.03.05", name: "Internet and e-commerce",
            keywords: ["e-commerce", "Amazon", "Shopify", "online retail", "marketplace", "digital commerce", "website", "platform", "internet business", "online sales"],
            prompt: "Articles about internet businesses and e-commerce. Covers online retail, digital marketplaces, platform economics, and the commercial internet. Assign when the business model is primarily internet-based and product-focused rather than software-as-a-service.",
          },
          {
            id: "04.03.06", name: "Software and apps",
            keywords: ["software", "app", "SaaS", "developer tools", "update", "release", "platform", "open source", "SDK", "API", "enterprise software", "productivity"],
            prompt: "Articles about the software industry and application development. Covers enterprise software, productivity apps, developer tools, SaaS businesses, and software company earnings. Assign for software as a commercial product or service.",
          },
        ],
      },
      {
        id: "04.04", name: "Cryptocurrency and digital assets",
        keywords: ["Bitcoin", "Ethereum", "crypto", "blockchain", "DeFi", "NFT", "stablecoin", "token", "exchange", "wallet", "Layer 2", "Web3", "on-chain"],
        prompt: "Articles about cryptocurrency and digital assets as financial instruments. Covers Bitcoin and Ethereum price action, crypto exchanges, DeFi protocols, stablecoins, regulatory actions against crypto, and the crypto market broadly.",
      },
      {
        id: "04.05",
        name: "Energy and resources",
        keywords: ["energy", "oil", "gas", "OPEC", "renewable", "power", "grid", "electricity", "pipeline", "refinery", "fuel", "energy market"],
        prompt: "Articles about the energy sector and natural resource industries. Covers energy markets, production, and policy across fossil fuels, nuclear, and renewables. Use subcategories for specific energy types.",
        children: [
          {
            id: "04.05.01", name: "Fossil fuels",
            keywords: ["oil", "gas", "OPEC", "crude oil", "natural gas", "petroleum", "pipeline", "LNG", "refinery", "carbon", "coal", "drilling"],
            prompt: "Articles about the fossil fuel industry. Covers oil and gas production, OPEC decisions, pipeline projects, energy company earnings, LNG trade, and the economics of coal, oil, and natural gas. For climate aspects of fossil fuels use Climate change (06.01).",
          },
          {
            id: "04.05.02", name: "Nuclear energy",
            keywords: ["nuclear", "reactor", "uranium", "fission", "power plant", "NRC", "SMR", "nuclear waste", "decommission", "plant life extension"],
            prompt: "Articles about nuclear power as an energy source. Covers reactor construction, plant operations, uranium supply, small modular reactors, waste management, and nuclear energy policy. For nuclear weapons use Arms and weapons programmes (11.01.01).",
          },
          {
            id: "04.05.03", name: "Renewable energy",
            keywords: ["solar", "wind", "renewable", "clean energy", "grid", "battery storage", "EV", "offshore wind", "photovoltaic", "turbine", "green hydrogen"],
            prompt: "Articles about renewable energy as an industry. Covers solar and wind project development, grid-scale battery storage, offshore wind auctions, renewable energy company news, and clean energy investment. For policy aspects use Environmental regulation (11.04.03).",
          },
        ],
      },
      {
        id: "04.06",
        name: "Financial markets",
        keywords: ["financial markets", "trading", "investor", "market", "assets", "portfolio", "volatility", "returns", "capital", "exchange"],
        prompt: "Articles about financial markets and investing. Covers market movements, investor sentiment, asset prices, and trading activity. Use subcategories for specific asset classes.",
        children: [
          {
            id: "04.06.01", name: "Bonds and fixed income",
            keywords: ["bond", "yield", "Treasury", "sovereign debt", "credit rating", "fixed income", "bond market", "spreads", "Moody's", "gilts", "coupon"],
            prompt: "Articles about bond markets and fixed income investing. Covers government and corporate bond yields, credit ratings, debt issuance, and the broader fixed income market. Assign when bonds or interest rate-sensitive instruments are the primary subject.",
          },
          {
            id: "04.06.02", name: "Commodities",
            keywords: ["commodity", "gold", "oil prices", "copper", "agricultural futures", "commodity market", "spot price", "futures", "lithium", "wheat", "silver"],
            prompt: "Articles about commodity markets. Covers prices and trading of raw materials including metals, energy commodities, and agricultural products. Assign when the article focuses on commodity prices and the markets that trade them.",
          },
          {
            id: "04.06.03", name: "Currencies and forex",
            keywords: ["currency", "forex", "dollar", "euro", "yuan", "exchange rate", "FX", "yen", "sterling", "devaluation", "reserve currency", "DXY"],
            prompt: "Articles about currency markets and exchange rates. Covers foreign exchange trading, currency appreciation or depreciation, central bank intervention in FX markets, and the geopolitics of reserve currencies.",
          },
          {
            id: "04.06.04", name: "Equities and stock markets",
            keywords: ["stock", "shares", "S&P 500", "earnings", "market cap", "valuation", "Nasdaq", "FTSE", "index", "dividends", "analyst", "equity market"],
            prompt: "Articles about equity markets and individual stocks. Covers stock market performance, individual company earnings, valuations, analyst ratings, and the dynamics of stock exchanges. Assign when stocks or equity indices are the primary financial subject.",
          },
          {
            id: "04.06.05", name: "Private equity and venture capital",
            keywords: ["venture capital", "private equity", "funding round", "seed", "Series A", "LBO", "buyout", "portfolio company", "exit", "fund raising", "LP"],
            prompt: "Articles about private equity and venture capital as financial industries. Covers fund raising, portfolio company performance, buyouts, VC funding rounds, and the business of private markets investing. Assign when private capital structures—rather than public markets—are the subject.",
          },
        ],
      },
      {
        id: "04.07", name: "Healthcare industry",
        keywords: ["hospital", "health insurance", "Medicare", "Medicaid", "healthcare costs", "medical device", "health system", "payer", "provider", "HMO"],
        prompt: "Articles about the healthcare industry as a business sector. Covers hospital networks, health insurance companies, medical device manufacturers, healthcare costs, and industry consolidation. For clinical or scientific health news use Health (07).",
      },
      {
        id: "04.08", name: "Housing and real estate",
        keywords: ["housing market", "real estate", "mortgage rates", "home prices", "construction", "property", "rent", "landlord", "developer", "commercial real estate"],
        prompt: "Articles about housing and real estate markets. Covers home prices, mortgage rates, residential construction, commercial property, rental markets, and real estate investment. Assign when property as an economic asset or market is the primary subject.",
      },
      {
        id: "04.09", name: "Manufacturing and industry",
        keywords: ["manufacturing", "factory", "supply chain", "industrial output", "production", "automation", "reshoring", "plant", "assembly", "workforce"],
        prompt: "Articles about manufacturing and industrial production. Covers factory output, supply chain management, industrial capacity, reshoring trends, and the economics of physical goods production. Assign for industrial processes and manufacturing businesses.",
      },
      {
        id: "04.10", name: "Media and entertainment industry",
        keywords: ["media company", "streaming revenue", "advertising", "content", "studio", "rights", "merger", "media business", "subscriptions", "distribution"],
        prompt: "Articles about the media and entertainment industry as a business. Covers streaming service revenue, advertising markets, content rights deals, studio strategy, and media company mergers. For the content itself use Arts, entertainment and media (01).",
      },
      {
        id: "04.11", name: "Mergers and acquisitions",
        keywords: ["acquisition", "merger", "takeover", "deal", "acquisition price", "antitrust", "buyout", "bid", "hostile takeover", "due diligence", "synergies"],
        prompt: "Articles about corporate mergers and acquisitions. Covers announced and completed deals, hostile takeovers, regulatory approval or blockage of mergers, and the strategic rationale and financial terms of significant transactions.",
      },
      {
        id: "04.12", name: "Pharmaceutical industry",
        keywords: ["pharma", "drug", "FDA approval", "clinical trial", "biotech", "pipeline", "patent", "generic", "blockbuster", "GLP-1", "oncology drug"],
        prompt: "Articles about the pharmaceutical and biotechnology industries as business sectors. Covers drug development pipelines, FDA approvals from a commercial perspective, patent cliffs, biotech company news, and pharma mergers. For clinical research aspects use Medical research (07.04).",
      },
      {
        id: "04.13", name: "Retail and consumer goods",
        keywords: ["retail", "consumer spending", "sales", "store", "brand", "e-commerce", "consumer", "FMCG", "grocery", "department store", "outlet", "fashion retail"],
        prompt: "Articles about retail businesses and consumer goods companies. Covers retail sales data, brand performance, store openings and closures, consumer spending trends, and the business of selling goods to end consumers.",
      },
      {
        id: "04.14", name: "Startups and entrepreneurship",
        keywords: ["startup", "founder", "funding", "venture capital", "unicorn", "accelerator", "pitch", "growth stage", "Y Combinator", "entrepreneur", "scale-up"],
        prompt: "Articles about startups and the entrepreneurship ecosystem. Covers early-stage companies, founder stories, fundraising rounds, accelerator programmes, unicorn valuations, and the broader startup culture. Assign when an early-stage or growth-stage company—rather than its specific product—is the focus.",
      },
      {
        id: "04.15", name: "Trade and tariffs",
        keywords: ["tariff", "trade", "import", "export", "trade war", "WTO", "trade deficit", "customs", "trade deal", "free trade", "protectionism", "supply chain"],
        prompt: "Articles about international trade and tariff policy. Covers trade agreements, tariff impositions, trade deficits, WTO disputes, and the economics of cross-border commerce. Assign when trade as an economic and policy issue is the primary subject.",
      },
      {
        id: "04.16", name: "Transport and logistics",
        keywords: ["shipping", "logistics", "supply chain", "freight", "port", "container", "airline", "trucking", "rail freight", "warehouse", "last mile"],
        prompt: "Articles about the commercial transport and logistics sector. Covers shipping rates, port congestion, logistics company earnings, freight markets, and the supply chain industry. Assign for the business of moving goods rather than passenger transport.",
      },
    ],
  },
  {
    id: "05",
    name: "Education",
    color: "#84cc16",
    keywords: ["education", "school", "university", "students", "learning", "curriculum", "teacher", "campus", "degree", "academic", "teaching"],
    prompt: "Articles about education at all levels. Covers schools, universities, educational policy, learning methods, and the education sector. Assign when the primary subject is an educational institution, learning system, or educational outcomes.",
    children: [
      {
        id: "05.01", name: "Higher education and universities",
        keywords: ["university", "college", "tuition", "degree", "enrollment", "campus", "research university", "student loans", "graduation", "faculty", "academic"],
        prompt: "Articles about universities, colleges, and higher education. Covers admissions, tuition costs, campus life, university research, funding, and debates over higher education access and value. Assign for postsecondary education institutions and policy.",
      },
      {
        id: "05.02", name: "Online and digital learning",
        keywords: ["online learning", "MOOC", "EdTech", "Coursera", "e-learning", "digital education", "virtual classroom", "remote learning", "skills platform"],
        prompt: "Articles about online and technology-enabled education. Covers MOOC platforms, EdTech companies, virtual learning environments, and the shift toward digital education delivery. Assign when technology-mediated learning is the distinguishing feature.",
      },
      {
        id: "05.03", name: "School education",
        keywords: ["school", "K-12", "curriculum", "students", "teachers", "standardised testing", "charter school", "public school", "school funding", "classroom"],
        prompt: "Articles about primary and secondary (K-12) school education. Covers curricula, school funding, standardised testing, school choice, teacher recruitment, and the challenges facing school-age education systems.",
      },
      {
        id: "05.04", name: "Teaching and pedagogy",
        keywords: ["teaching", "pedagogy", "classroom", "educational methods", "teacher training", "curriculum design", "assessment", "learning outcomes", "STEM"],
        prompt: "Articles about teaching methods and educational practice. Covers pedagogical approaches, teacher professional development, curriculum design, and research into effective learning. Assign when educational methods themselves—rather than institutions—are the subject.",
      },
      {
        id: "05.05", name: "Vocational training",
        keywords: ["vocational", "apprenticeship", "trade school", "skills training", "workforce development", "certification", "technical education", "trades", "TVET"],
        prompt: "Articles about vocational and technical education. Covers apprenticeship programmes, trade schools, skills training, workforce development initiatives, and pathways to employment that do not require a university degree.",
      },
    ],
  },
  {
    id: "06",
    name: "Environment",
    color: "#22c55e",
    keywords: ["environment", "climate", "ecology", "nature", "conservation", "emissions", "pollution", "sustainability", "ecosystem", "biodiversity"],
    prompt: "Articles about the natural environment and environmental issues. Covers climate change, conservation, pollution, and the health of ecosystems. Assign when the primary subject is environmental impact, natural systems, or environmental policy.",
    children: [
      {
        id: "06.01", name: "Climate change",
        keywords: ["climate change", "global warming", "CO2", "emissions", "IPCC", "Paris Agreement", "temperature rise", "carbon budget", "net zero", "fossil fuels", "sea level"],
        prompt: "Articles about climate change science, impacts, and policy. Covers temperature records, IPCC reports, emissions trajectories, climate negotiations, and adaptation to climate impacts. Assign when climate change—rather than a specific disaster or energy type—is the central subject.",
      },
      {
        id: "06.02", name: "Conservation and biodiversity",
        keywords: ["conservation", "biodiversity", "habitat", "species", "protected area", "WWF", "deforestation", "rewilding", "national park", "endangered", "wildlife corridor"],
        prompt: "Articles about conservation efforts and biodiversity. Covers species protection, habitat preservation, rewilding projects, protected area policy, and the biodiversity crisis. Assign when protecting natural systems and species is the primary subject.",
      },
      {
        id: "06.03", name: "Natural resources",
        keywords: ["natural resources", "water", "forests", "minerals", "land use", "deforestation", "mining", "groundwater", "fisheries", "timber"],
        prompt: "Articles about the use and management of natural resources. Covers water supply, forest management, mineral extraction, land use policy, and sustainable resource management. Assign when the exploitation or stewardship of natural resources is the central theme.",
      },
      {
        id: "06.04",
        name: "Pollution",
        keywords: ["pollution", "contamination", "toxic", "waste", "discharge", "environmental damage", "clean-up", "health impact", "regulatory fine"],
        prompt: "Articles about pollution and environmental contamination. Covers specific pollution events, long-term contamination, environmental clean-up, and health impacts. Use subcategories for specific pollution types.",
        children: [
          {
            id: "06.04.01", name: "Air quality and air pollution",
            keywords: ["air quality", "smog", "particulate matter", "PM2.5", "emissions", "WHO limits", "ozone", "NOx", "indoor air quality", "clean air"],
            prompt: "Articles about air pollution and air quality. Covers particulate matter levels, smog events, emissions standards, and the health impacts of poor air quality. Assign when air pollution itself—rather than its regulatory or climate dimensions—is the primary focus.",
          },
          {
            id: "06.04.02", name: "Plastic and waste pollution",
            keywords: ["plastic", "waste", "recycling", "microplastics", "landfill", "ocean plastic", "single-use", "packaging", "circular economy", "e-waste"],
            prompt: "Articles about plastic and solid waste pollution. Covers ocean plastic, microplastic contamination, waste management failures, recycling infrastructure, and policies to reduce plastic use.",
          },
          {
            id: "06.04.03", name: "Water pollution",
            keywords: ["water quality", "contamination", "runoff", "wastewater", "ocean pollution", "PFAS", "toxic spill", "drinking water", "algal bloom", "sewage"],
            prompt: "Articles about water pollution and contamination. Covers polluted waterways, drinking water safety, industrial discharge, PFAS contamination, and wastewater management. Assign when water as a medium of pollution is the primary subject.",
          },
        ],
      },
      {
        id: "06.05", name: "Renewable energy and clean tech",
        keywords: ["solar", "wind", "renewable", "clean tech", "green energy", "transition", "battery", "EV", "electrification", "decarbonisation", "clean power"],
        prompt: "Articles about renewable energy and clean technology from an environmental perspective. Covers the deployment of clean energy as a solution to environmental problems, green tech innovation, and the energy transition. For industry business news use Renewable energy (04.05.03).",
      },
      {
        id: "06.06", name: "Wildlife and ecosystems",
        keywords: ["wildlife", "species", "habitat", "coral reef", "biodiversity", "extinction", "animal", "ecosystem", "marine life", "migration", "poaching"],
        prompt: "Articles about wildlife and natural ecosystems. Covers animal populations, species decline, ecosystem health, coral reef bleaching, and poaching. Assign when the focus is on specific animals or natural ecosystems rather than broader conservation policy.",
      },
    ],
  },
  {
    id: "07",
    name: "Health",
    color: "#06b6d4",
    keywords: ["health", "medicine", "disease", "treatment", "patient", "hospital", "doctor", "medical", "clinical", "public health", "healthcare"],
    prompt: "Articles about human health, medicine, and healthcare. Covers diseases, treatments, public health, medical research, and healthcare systems. Assign when the primary subject is human health, a medical condition, or the delivery of healthcare.",
    children: [
      {
        id: "07.01", name: "Epidemics and pandemics",
        keywords: ["pandemic", "outbreak", "virus", "WHO", "epidemic", "infection", "transmission", "mortality", "quarantine", "contagion", "contact tracing"],
        prompt: "Articles about infectious disease outbreaks and pandemics. Covers disease spread, outbreak containment, pandemic preparedness, and the global health response. Assign when a specific outbreak or its management is the primary focus.",
      },
      {
        id: "07.02", name: "Healthcare policy and access",
        keywords: ["healthcare reform", "health insurance", "universal healthcare", "NHS", "ACA", "Medicaid", "Medicare", "health spending", "coverage", "co-pay"],
        prompt: "Articles about healthcare policy and access to medical care. Covers health system reform, insurance coverage debates, healthcare costs, universal health programmes, and disparities in healthcare access. Assign when health policy rather than clinical medicine is the primary subject.",
      },
      {
        id: "07.03", name: "Healthcare technology and digital health",
        keywords: ["telehealth", "digital health", "wearables", "EHR", "health app", "AI diagnostics", "remote monitoring", "medical AI", "health tech", "FDA software"],
        prompt: "Articles about technology applied to healthcare delivery. Covers telemedicine, digital health apps, AI-assisted diagnostics, electronic health records, wearable health devices, and health tech companies. Assign when technology as a means of delivering care is the subject.",
      },
      {
        id: "07.04",
        name: "Medical research",
        keywords: ["medical research", "study", "findings", "journal", "researcher", "breakthrough", "discovery", "clinical", "trial", "peer-reviewed"],
        prompt: "Articles about medical and biomedical research. Covers research findings, clinical study results, and scientific advances relevant to human health. Use subcategories for specific research areas. Assign when a research finding or scientific advance in medicine is the primary subject.",
        children: [
          {
            id: "07.04.01", name: "Cancer research",
            keywords: ["cancer", "tumour", "oncology", "immunotherapy", "chemotherapy", "trials", "remission", "metastatic", "carcinoma", "targeted therapy"],
            prompt: "Articles about cancer research and oncology. Covers new findings in cancer biology, immunotherapy breakthroughs, clinical trial results for cancer treatments, and advances in early detection.",
          },
          {
            id: "07.04.02", name: "Drug development and clinical trials",
            keywords: ["clinical trial", "FDA", "phase 3", "drug approval", "efficacy", "placebo", "double-blind", "EMA", "regulatory approval", "primary endpoint"],
            prompt: "Articles about the development and testing of new drugs. Covers clinical trial results, regulatory approval processes, drug efficacy and safety data, and the pipeline from discovery to market. For commercial pharma news use Pharmaceutical industry (04.12).",
          },
          {
            id: "07.04.03", name: "Genetics and genomics",
            keywords: ["CRISPR", "gene therapy", "genomics", "DNA", "sequencing", "genetic disorder", "gene editing", "RNA", "mutation", "epigenetics"],
            prompt: "Articles about genetics and genomic medicine. Covers gene editing research, whole genome sequencing studies, genetic disease research, and the application of genomics to personalised medicine.",
          },
          {
            id: "07.04.04", name: "Medical devices and diagnostics",
            keywords: ["medical device", "diagnostic", "imaging", "MRI", "ultrasound", "biomarker", "wearable", "implant", "prosthetic", "FDA clearance"],
            prompt: "Articles about medical devices and diagnostic tools. Covers new diagnostic technologies, medical device approvals, imaging advances, surgical tools, and the research behind physical medical equipment.",
          },
          {
            id: "07.04.05", name: "Neuroscience and brain research",
            keywords: ["neuroscience", "brain", "Alzheimer's", "Parkinson's", "neural", "cognitive", "synapse", "neurodegeneration", "brain imaging", "dementia"],
            prompt: "Articles about neuroscience and brain health research. Covers discoveries in brain biology, neurological disease research, cognitive science findings, and advances in understanding conditions like Alzheimer's and Parkinson's.",
          },
        ],
      },
      {
        id: "07.05", name: "Mental health and psychiatry",
        keywords: ["mental health", "depression", "anxiety", "psychiatry", "therapy", "suicide prevention", "wellbeing", "burnout", "trauma", "PTSD", "mental illness"],
        prompt: "Articles about mental health, psychiatric conditions, and psychological wellbeing. Covers mental illness prevalence, treatment approaches, mental health policy, and the stigma around mental health. Assign when psychological and psychiatric topics are the primary subject.",
      },
      {
        id: "07.06", name: "Nutrition and fitness",
        keywords: ["nutrition", "diet", "obesity", "exercise", "fitness", "public health", "food safety", "calorie", "metabolic", "weight", "physical activity"],
        prompt: "Articles about nutrition, diet, and physical fitness. Covers dietary research, obesity trends, fitness culture, food safety guidance, and public health campaigns related to diet and activity. Assign when nutrition or physical fitness—rather than clinical medicine—is the focus.",
      },
      {
        id: "07.07", name: "Pharmaceutical drugs",
        keywords: ["drug", "medication", "FDA approval", "generic", "patent", "side effects", "pharmacology", "dosage", "prescription", "OTC", "drug safety"],
        prompt: "Articles about specific pharmaceutical drugs as medical interventions. Covers drug approvals, safety signals, side effects, drug interactions, and access to medications. For the business of pharma companies use Pharmaceutical industry (04.12).",
      },
      {
        id: "07.08", name: "Public health",
        keywords: ["public health", "prevention", "vaccination", "epidemiology", "disease control", "CDC", "screening", "health promotion", "immunisation", "health disparity"],
        prompt: "Articles about public health measures and population health. Covers vaccination programmes, disease surveillance, health promotion campaigns, public health infrastructure, and efforts to prevent disease at a population level.",
      },
    ],
  },
  {
    id: "08",
    name: "Human interest",
    color: "#fb923c",
    keywords: ["human interest", "personal story", "community", "inspiring", "unusual", "heartwarming", "social", "profile", "people"],
    prompt: "Articles focused on individual people, their stories, or broader human experiences. Covers celebrity culture, personal profiles, and unusual or heartwarming stories. Assign when an article's primary appeal is its human subject rather than a news event.",
    children: [
      {
        id: "08.01", name: "Animals",
        keywords: ["animal", "pet", "wildlife rescue", "zoo", "veterinary", "animal welfare", "dog", "cat", "exotic animal", "animal sanctuary", "RSPCA"],
        prompt: "Articles about animals in a human-interest context. Covers pet stories, animal rescue, zoo animals, animal welfare, and unusual animal behaviour. Assign for stories where the animal itself—rather than conservation or ecology—is the human-interest focus.",
      },
      {
        id: "08.02", name: "Celebrity and public figures",
        keywords: ["celebrity", "star", "actor", "musician", "social media star", "fame", "public figure", "tabloid", "red carpet", "personal life", "gossip"],
        prompt: "Articles about celebrities and their personal lives. Covers celebrity relationships, public appearances, personal controversies, and human-interest stories involving famous people. Assign when a famous person's personal story—rather than their professional work—is the focus.",
      },
      {
        id: "08.03", name: "People and profiles",
        keywords: ["profile", "interview", "biography", "human story", "personal journey", "feature", "portrait", "life story", "community", "ordinary people"],
        prompt: "Articles profiling individuals or telling human stories. Covers in-depth profiles, personal journeys, community stories, and feature interviews where the subject's humanity is the primary interest rather than a specific news event.",
      },
      {
        id: "08.04", name: "Royalty and nobility",
        keywords: ["royal family", "monarchy", "King", "Queen", "palace", "coronation", "royal wedding", "heir", "duchess", "prince", "succession"],
        prompt: "Articles about royal families and monarchies around the world. Covers royal events, succession, royal family relationships, state occasions, and the institution of monarchy. Assign for royal family coverage rather than political constitutions regarding royalty.",
      },
    ],
  },
  {
    id: "09",
    name: "Labour and employment",
    color: "#8b5cf6",
    keywords: ["labour", "employment", "jobs", "workers", "wages", "workforce", "hiring", "unemployment", "union", "workplace"],
    prompt: "Articles about labour markets, employment, and worker rights. Covers jobs data, wages, unions, and workplace issues. Assign when the primary subject is work, workers, or the employment relationship rather than broader economic conditions.",
    children: [
      {
        id: "09.01", name: "Employment and jobs",
        keywords: ["jobs", "unemployment", "hiring", "workforce", "employment rate", "layoffs", "job market", "payroll", "labour market", "job creation", "redundancy"],
        prompt: "Articles about the jobs market and employment conditions. Covers jobs reports, unemployment rates, hiring trends, mass layoffs, and the state of the labour market. Assign when the jobs market and employment data are the primary focus.",
      },
      {
        id: "09.02", name: "Labour relations and disputes",
        keywords: ["strike", "labor dispute", "industrial action", "collective bargaining", "walkout", "lockout", "union negotiation", "contract dispute", "work-to-rule"],
        prompt: "Articles about disputes between workers and employers. Covers strikes, lockouts, collective bargaining negotiations, industrial action, and labour relations. Assign when a conflict between workers and management is the primary subject.",
      },
      {
        id: "09.03", name: "Trade unions",
        keywords: ["union", "AFL-CIO", "trade union", "workers' rights", "collective agreement", "union membership", "union election", "organising", "TUC"],
        prompt: "Articles about trade unions as organisations. Covers union membership trends, union elections, organising campaigns, and the political role of labour unions. Assign when a union itself—rather than a specific dispute it is involved in—is the subject.",
      },
      {
        id: "09.04", name: "Wages, benefits and pensions",
        keywords: ["wages", "salary", "minimum wage", "benefits", "pension", "retirement", "pay gap", "compensation", "bonus", "living wage", "pay rise"],
        prompt: "Articles about worker pay, benefits, and retirement. Covers minimum wage debates, pay gap research, pension fund performance, executive compensation, and trends in worker benefits and retirement security.",
      },
      {
        id: "09.05", name: "Working conditions",
        keywords: ["working conditions", "workplace safety", "remote work", "hours", "ergonomics", "burnout", "gig economy", "contractor", "four-day week", "OSHA"],
        prompt: "Articles about the conditions under which people work. Covers workplace safety, remote and hybrid work, working hours, the gig economy, worker wellbeing, and regulatory standards for the workplace.",
      },
    ],
  },
  {
    id: "10",
    name: "Lifestyle and leisure",
    color: "#10b981",
    keywords: ["lifestyle", "leisure", "hobby", "travel", "food", "home", "wellness", "consumer", "trend", "culture", "recreation"],
    prompt: "Articles about lifestyle, leisure pursuits, and consumer culture. Covers food, travel, home, hobbies, and consumer trends. Assign when the article is primarily about how people spend their non-work time or money.",
    children: [
      {
        id: "10.01", name: "Food and drink",
        keywords: ["food", "restaurant", "cuisine", "chef", "recipe", "dining", "beverage", "culinary trend", "Michelin", "cocktail", "wine", "food culture"],
        prompt: "Articles about food, drink, and dining culture. Covers restaurant news, chef profiles, culinary trends, food and drink reviews, and the culture of eating and drinking. Assign when food or beverages as a leisure or cultural topic—rather than as a commodity or health issue—is the focus.",
      },
      {
        id: "10.02", name: "Hobbies and crafts",
        keywords: ["hobby", "crafts", "DIY", "collecting", "gardening", "model making", "knitting", "woodworking", "amateur", "pastime", "leisure activity"],
        prompt: "Articles about hobbies and craft activities. Covers DIY projects, craft trends, collecting communities, and specialist leisure pursuits. Assign when the article is about a hobby or craft activity rather than a professional or commercial endeavour.",
      },
      {
        id: "10.03", name: "Home and living",
        keywords: ["home", "interior design", "renovation", "decoration", "furniture", "home improvement", "architecture", "living space", "smart home"],
        prompt: "Articles about the home as a personal space. Covers interior design, home renovation, decoration trends, furniture, and home improvement. Assign when the home as a living environment—rather than as real estate investment—is the primary subject.",
      },
      {
        id: "10.04", name: "Outdoor activities",
        keywords: ["hiking", "camping", "adventure", "outdoor", "nature", "trail", "climbing", "kayaking", "cycling leisure", "birdwatching", "orienteering"],
        prompt: "Articles about outdoor recreation and adventure activities. Covers hiking, camping, climbing, water sports, and other outdoor pursuits. Assign when outdoor leisure activity is the primary subject rather than professional sport.",
      },
      {
        id: "10.05", name: "Shopping and consumer trends",
        keywords: ["shopping", "consumer", "retail trend", "brand", "product launch", "Black Friday", "deal", "luxury goods", "consumer behaviour", "impulse buy"],
        prompt: "Articles about consumer shopping behaviour and retail trends. Covers consumer spending patterns, new product launches, retail seasonal events, and shifting consumer preferences. Assign when the consumer experience of shopping—rather than the retail industry's business—is the focus.",
      },
      {
        id: "10.06", name: "Travel and tourism",
        keywords: ["travel", "tourism", "destination", "hotel", "flight", "passport", "tourism industry", "vacation", "backpacking", "cruise", "resort", "visa"],
        prompt: "Articles about travel and tourism. Covers travel destinations, hotel and airline experiences, visa policies, and travel trends. Assign when travel as a personal leisure activity or the tourism industry serving travellers is the primary subject.",
      },
    ],
  },
  {
    id: "11",
    name: "Politics",
    color: "#f43f5e",
    keywords: ["politics", "government", "policy", "election", "parliament", "congress", "minister", "legislation", "political", "power", "diplomacy"],
    prompt: "Articles about politics, government, and public policy. Covers elections, legislation, government decisions, international relations, and regulation. Assign when the primary subject is the exercise of political power or the making of public policy.",
    children: [
      {
        id: "11.01",
        name: "Defence and military policy",
        keywords: ["defence", "military", "armed forces", "defence budget", "NATO", "security", "strategy", "deterrence", "army", "navy", "air force"],
        prompt: "Articles about defence policy and military affairs outside of active conflict. Covers defence budgets, military strategy, arms procurement, and security alliances. For active warfare use Conflict, war and peace (16).",
        children: [
          {
            id: "11.01.01", name: "Arms and weapons programmes",
            keywords: ["arms", "weapons", "missile", "nuclear weapons", "defence contract", "military spending", "arms race", "ICBM", "fighter jet", "procurement"],
            prompt: "Articles about weapons development and arms policy. Covers nuclear weapons programmes, conventional arms procurement, missile systems, defence contracts, and arms control treaties. Assign when the development or proliferation of weapons is the primary subject.",
          },
          {
            id: "11.01.02", name: "Intelligence and espionage",
            keywords: ["intelligence", "CIA", "NSA", "espionage", "spy", "surveillance", "classified", "intelligence agency", "counterintelligence", "GCHQ", "signals intelligence"],
            prompt: "Articles about intelligence services and espionage. Covers intelligence agency activities, spy operations, surveillance programmes, and counterintelligence. Assign when intelligence or spying activities are the primary subject rather than a crime or cyberattack.",
          },
          {
            id: "11.01.03", name: "Military technology",
            keywords: ["drone", "military tech", "stealth", "defence technology", "autonomous weapons", "satellite", "defence contractor", "AI warfare", "hypersonic"],
            prompt: "Articles about technology developed for military applications. Covers military drones, autonomous weapons systems, stealth technology, satellite surveillance, and defence technology research and procurement.",
          },
        ],
      },
      {
        id: "11.02",
        name: "Domestic politics",
        keywords: ["domestic politics", "government", "party", "politician", "poll", "cabinet", "prime minister", "president", "administration", "opposition"],
        prompt: "Articles about politics within a single country. Covers government decisions, political party affairs, and domestic political events. Use subcategories for elections, legislation, or party-focused stories.",
        children: [
          {
            id: "11.02.01", name: "Elections and voting",
            keywords: ["election", "vote", "ballot", "campaign", "polling", "candidate", "electoral", "constituency", "swing state", "primary", "turnout"],
            prompt: "Articles about elections and the democratic process. Covers electoral campaigns, polling, results, voter turnout, electoral systems, and the conduct of elections. Assign when an election or voting process is the primary subject.",
          },
          {
            id: "11.02.02", name: "Government and governance",
            keywords: ["government", "cabinet", "administration", "official", "minister", "policy", "decree", "governance", "accountability", "civil service"],
            prompt: "Articles about the operation of government. Covers cabinet decisions, policy announcements, government appointments, the exercise of executive power, and the functioning of public institutions. Assign for government actions and decisions not covered by other subcategories.",
          },
          {
            id: "11.02.03", name: "Legislation and lawmaking",
            keywords: ["legislation", "bill", "law", "Congress", "parliament", "vote", "amendment", "filibuster", "Senate", "debate", "committee", "statute"],
            prompt: "Articles about the legislative process. Covers bills moving through parliament or congress, parliamentary debates, amendments, and the passage or defeat of legislation. Assign when the creation of law—rather than its enforcement—is the primary subject.",
          },
          {
            id: "11.02.04", name: "Political parties and movements",
            keywords: ["political party", "Democrat", "Republican", "coalition", "populism", "movement", "manifesto", "party leadership", "far right", "progressive"],
            prompt: "Articles about political parties and ideological movements. Covers party leadership contests, manifestos, intra-party dynamics, and political movements. Assign when a political party or ideological movement—rather than a specific policy or election—is the focus.",
          },
        ],
      },
      {
        id: "11.03",
        name: "International relations and diplomacy",
        keywords: ["international relations", "diplomacy", "foreign minister", "summit", "geopolitics", "bilateral", "multilateral", "global governance", "UN"],
        prompt: "Articles about relations between countries and international diplomacy. Covers summits, diplomatic talks, international agreements, and the conduct of foreign affairs. Use subcategories for specific aspects of international relations.",
        children: [
          {
            id: "11.03.01", name: "Alliances and multilateral organizations",
            keywords: ["NATO", "UN", "EU", "G7", "G20", "multilateral", "alliance", "bloc", "ASEAN", "AU", "international body", "treaty organisation"],
            prompt: "Articles about international alliances and multilateral organisations. Covers NATO, the UN, the EU, and other international bodies—their decisions, membership, and internal politics. Assign when an international organisation rather than a bilateral relationship is the subject.",
          },
          {
            id: "11.03.02", name: "Bilateral diplomacy",
            keywords: ["bilateral talks", "summit", "envoy", "ambassador", "diplomatic relations", "state visit", "foreign secretary", "consulate", "embassy"],
            prompt: "Articles about diplomatic relations between two specific countries. Covers state visits, bilateral summits, ambassadorial appointments, and the state of relations between particular nations.",
          },
          {
            id: "11.03.03", name: "Foreign policy",
            keywords: ["foreign policy", "State Department", "foreign minister", "strategic interests", "geopolitical", "influence", "soft power", "doctrine", "national interest"],
            prompt: "Articles about a country's foreign policy strategy. Covers the foreign policy goals and strategies of major powers, shifts in strategic priorities, and the doctrinal frameworks guiding a state's international behaviour.",
          },
          {
            id: "11.03.04", name: "Sanctions and trade restrictions",
            keywords: ["sanctions", "export controls", "ban", "blacklist", "OFAC", "trade restriction", "asset freeze", "entity list", "embargo", "designation"],
            prompt: "Articles about economic sanctions and export controls. Covers sanctions imposed on countries, companies, or individuals, export control rules, and their economic and political effects. Assign when sanctions as a policy tool are the primary subject.",
          },
        ],
      },
      {
        id: "11.04",
        name: "Regulation and policy",
        keywords: ["regulation", "regulator", "policy", "rule", "compliance", "enforcement", "watchdog", "agency", "framework", "directive"],
        prompt: "Articles about government regulation across sectors. Covers new rules, regulatory enforcement actions, and regulatory policy debates. Use subcategories for specific regulatory domains.",
        children: [
          {
            id: "11.04.01", name: "Antitrust and competition law",
            keywords: ["antitrust", "competition", "monopoly", "FTC", "DOJ", "cartel", "market power", "merger review", "consumer welfare", "dominant position", "CMA"],
            prompt: "Articles about antitrust enforcement and competition policy. Covers investigations into monopolistic behaviour, merger reviews by competition authorities, cartel enforcement, and debates over market power in digital markets.",
          },
          {
            id: "11.04.02", name: "Data protection and privacy",
            keywords: ["GDPR", "privacy", "data protection", "personal data", "consent", "ICO", "CCPA", "data regulator", "surveillance", "tracking", "biometric"],
            prompt: "Articles about data privacy regulation and policy. Covers GDPR enforcement, new privacy laws, data protection authority actions, consumer privacy rights, and the regulation of data collection and tracking.",
          },
          {
            id: "11.04.03", name: "Environmental regulation",
            keywords: ["emissions standards", "environmental law", "EPA", "carbon tax", "green deal", "environmental permit", "pollution limit", "ETS", "climate regulation"],
            prompt: "Articles about environmental law and regulation. Covers emissions standards, environmental impact assessments, pollution limits, carbon pricing mechanisms, and regulatory frameworks for environmental protection.",
          },
          {
            id: "11.04.04", name: "Financial regulation",
            keywords: ["financial regulation", "SEC", "banking regulation", "Basel", "capital requirements", "systemic risk", "stress test", "prudential", "FCA", "consumer protection"],
            prompt: "Articles about financial sector regulation. Covers banking supervision, securities regulation, capital requirements, and the actions of financial regulators like the SEC, FCA, and banking supervisory authorities.",
          },
          {
            id: "11.04.05", name: "Technology regulation",
            keywords: ["AI regulation", "tech regulation", "EU AI Act", "content moderation", "digital markets", "platform accountability", "algorithmic regulation", "DSA", "DMA"],
            prompt: "Articles about the regulation of technology companies and digital platforms. Covers AI regulation, platform content moderation rules, digital market laws, and the governance of big tech companies.",
          },
        ],
      },
    ],
  },
  {
    id: "12",
    name: "Religion and belief",
    color: "#a855f7",
    keywords: ["religion", "faith", "belief", "spiritual", "church", "mosque", "temple", "prayer", "worship", "theology", "clergy"],
    prompt: "Articles about religion, faith, and religious communities. Covers religious events, institutions, theology, and the role of religion in society. Assign when religion or religious practice is the primary subject of the article.",
    children: [
      {
        id: "12.01", name: "Buddhism",
        keywords: ["Buddhism", "Buddhist", "meditation", "monk", "temple", "Dalai Lama", "dharma", "nirvana", "sangha", "Tibetan", "Zen", "monastery"],
        prompt: "Articles about Buddhism and Buddhist communities. Covers Buddhist institutions, practices, the Dalai Lama, Buddhist social issues, and news involving Buddhist communities around the world.",
      },
      {
        id: "12.02", name: "Christianity",
        keywords: ["Christianity", "church", "Pope", "Vatican", "Catholic", "Protestant", "evangelical", "faith", "diocese", "synod", "bishop", "pastor"],
        prompt: "Articles about Christianity and Christian institutions. Covers the Catholic Church, Protestant denominations, evangelical movements, the Vatican, and news involving Christian communities globally.",
      },
      {
        id: "12.03", name: "Hinduism",
        keywords: ["Hinduism", "Hindu", "temple", "festival", "caste", "Diwali", "yoga", "Sanskrit", "vedic", "mandir", "puja"],
        prompt: "Articles about Hinduism and Hindu communities. Covers Hindu religious practice, festivals, temple affairs, and news involving Hindu communities, including caste and related social issues.",
      },
      {
        id: "12.04", name: "Islam",
        keywords: ["Islam", "Muslim", "mosque", "Quran", "Ramadan", "Sharia", "imam", "hajj", "ummah", "fatwa", "halal", "Sunni", "Shia"],
        prompt: "Articles about Islam and Muslim communities. Covers Islamic institutions, religious practice, major events like Ramadan and Hajj, and news involving Muslim communities around the world.",
      },
      {
        id: "12.05", name: "Judaism",
        keywords: ["Judaism", "Jewish", "synagogue", "Torah", "rabbi", "Passover", "Shabbat", "antisemitism", "kosher", "orthodox", "Jewish community"],
        prompt: "Articles about Judaism and Jewish communities. Covers Jewish religious practice, synagogue affairs, major festivals, and news involving Jewish communities globally. For antisemitism as a political issue use Human rights and civil liberties (14.03).",
      },
      {
        id: "12.06", name: "Religious freedom and secularism",
        keywords: ["religious freedom", "secularism", "blasphemy", "church-state", "minority rights", "persecution", "apostasy", "faith school", "separation"],
        prompt: "Articles about religious freedom and the relationship between religion and the state. Covers persecution of religious minorities, blasphemy laws, church-state separation, and the rights of religious and non-religious people in public life.",
      },
    ],
  },
  {
    id: "13",
    name: "Science and technology",
    color: "#3b82f6",
    keywords: ["science", "research", "discovery", "study", "findings", "scientists", "laboratory", "experiment", "academic", "breakthrough", "technology"],
    prompt: "Articles about scientific research and technological development. Covers discoveries, research findings, and advances across all scientific disciplines. Assign when academic or research-oriented science—rather than commercial technology—is the primary subject.",
    children: [
      {
        id: "13.01",
        name: "Astronomy and space science",
        keywords: ["astronomy", "space", "telescope", "galaxy", "star", "universe", "cosmology", "exoplanet", "nebula", "black hole", "observation"],
        prompt: "Articles about astronomy and space science. Covers astronomical discoveries, observations, and missions with a scientific focus. Use subcategories for specific aspects of space science and exploration.",
        children: [
          {
            id: "13.01.01", name: "Commercial space industry",
            keywords: ["SpaceX", "Blue Origin", "Rocket Lab", "launch", "satellite", "commercial space", "reusable rocket", "Starship", "smallsat", "launch vehicle"],
            prompt: "Articles about the commercial space industry. Covers private launch companies, satellite constellations, commercial space stations, and the business of space. Assign when commercial—rather than government—space activity is the focus.",
          },
          {
            id: "13.01.02", name: "Planetary science",
            keywords: ["Mars", "Moon", "planetary", "NASA probe", "exoplanet", "solar system", "atmosphere", "surface", "geology", "rover", "orbit"],
            prompt: "Articles about planetary science and the study of planets, moons, and other solar system bodies. Covers rover findings, atmospheric studies, exoplanet characterisation, and planetary geology.",
          },
          {
            id: "13.01.03", name: "Space exploration and missions",
            keywords: ["NASA", "ESA", "mission", "astronaut", "space station", "ISS", "lunar", "Mars mission", "crew", "spacewalk", "launch"],
            prompt: "Articles about crewed and robotic space exploration missions. Covers mission planning, launches, in-flight events, and scientific returns from planetary missions. Assign when a specific space mission is the subject.",
          },
          {
            id: "13.01.04", name: "Telescopes and astronomical observation",
            keywords: ["telescope", "James Webb", "Hubble", "observation", "galaxy", "black hole", "nebula", "infrared", "radio telescope", "imaging", "spectrum"],
            prompt: "Articles about telescopes and astronomical observations. Covers new telescope capabilities, images released by observatories, and discoveries made through astronomical observation rather than space missions.",
          },
        ],
      },
      {
        id: "13.02",
        name: "Biology and life sciences",
        keywords: ["biology", "life sciences", "organism", "cell", "species", "evolutionary", "biological", "living", "flora", "fauna"],
        prompt: "Articles about biology and the life sciences. Covers research into living organisms across scales from cells to ecosystems. Use subcategories for specific biological disciplines.",
        children: [
          {
            id: "13.02.01", name: "Ecology and environmental biology",
            keywords: ["ecology", "ecosystem", "habitat", "species interaction", "food web", "biodiversity research", "population biology", "invasive species"],
            prompt: "Articles about ecology and the scientific study of ecosystems. Covers research into species interactions, population dynamics, ecosystem services, and the biological impacts of environmental change.",
          },
          {
            id: "13.02.02", name: "Evolution and palaeontology",
            keywords: ["evolution", "fossil", "palaeontology", "species", "natural selection", "Darwin", "phylogeny", "prehistoric", "dinosaur", "hominid", "ancestry"],
            prompt: "Articles about evolution and the fossil record. Covers palaeontological discoveries, evolutionary biology research, human origins, and findings about prehistoric life.",
          },
          {
            id: "13.02.03", name: "Genetics and genomics",
            keywords: ["genetics", "genomics", "DNA", "gene", "sequencing", "CRISPR", "protein", "mutation", "genome", "epigenetics", "hereditary"],
            prompt: "Articles about genetics and genomics research. Covers genome sequencing studies, genetic discovery, CRISPR research in academic settings, and the genetics of disease and evolution. For clinical gene therapy use Medical research (07.04).",
          },
          {
            id: "13.02.04", name: "Microbiology and virology",
            keywords: ["virus", "bacteria", "microbe", "pathogen", "infection", "antibiotic", "microbiology", "fungus", "antimicrobial resistance", "bacteriophage"],
            prompt: "Articles about microbiology and virology research. Covers the study of viruses, bacteria, and other microorganisms, including antimicrobial resistance research. For disease outbreaks use Epidemics and pandemics (07.01).",
          },
        ],
      },
      {
        id: "13.03", name: "Chemistry and materials science",
        keywords: ["chemistry", "materials science", "polymer", "compound", "synthesis", "catalyst", "battery chemistry", "superconductor", "alloy", "molecule"],
        prompt: "Articles about chemistry and materials science research. Covers novel compounds, materials discoveries, catalysis research, battery chemistry advances, and superconducting materials. Assign when the science of matter and materials is the primary subject.",
      },
      {
        id: "13.04",
        name: "Computer science and AI",
        keywords: ["computer science", "algorithm", "AI research", "machine learning", "neural network", "deep learning", "research paper", "benchmark", "model architecture"],
        prompt: "Articles about computer science and AI as academic disciplines. Covers research papers, algorithmic advances, and scientific progress in computation and intelligence. For commercial AI products use Artificial intelligence (04.03.01).",
        children: [
          {
            id: "13.04.01", name: "Algorithms and data science",
            keywords: ["algorithm", "machine learning", "data science", "neural network", "optimisation", "computational complexity", "data analysis", "model training"],
            prompt: "Articles about algorithmic research and data science methods. Covers novel algorithms, machine learning methodology, statistical methods, and computational approaches to problem-solving.",
          },
          {
            id: "13.04.02", name: "Artificial intelligence research",
            keywords: ["AI research", "deep learning", "foundation model", "AI safety", "alignment", "benchmark", "model architecture", "transformer", "reinforcement learning"],
            prompt: "Articles about academic and research advances in artificial intelligence. Covers new model architectures, benchmark results, AI safety research, and scientific understanding of machine learning. For commercial AI use Artificial intelligence (04.03.01).",
          },
          {
            id: "13.04.03", name: "Natural language processing",
            keywords: ["NLP", "language model", "text generation", "speech recognition", "translation", "sentiment analysis", "language understanding", "tokenisation"],
            prompt: "Articles about natural language processing research. Covers advances in language understanding, machine translation, speech recognition, and text generation from a scientific perspective.",
          },
          {
            id: "13.04.04", name: "Quantum computing",
            keywords: ["quantum computing", "qubit", "quantum advantage", "error correction", "quantum algorithm", "decoherence", "gate fidelity", "quantum processor"],
            prompt: "Articles about quantum computing research. Covers qubit technologies, quantum error correction, demonstrations of quantum advantage, and the scientific challenges of building reliable quantum computers.",
          },
          {
            id: "13.04.05", name: "Robotics and automation",
            keywords: ["robot", "automation", "humanoid", "autonomous", "industrial robot", "ROS", "manipulator", "locomotion", "swarm robotics", "drone research"],
            prompt: "Articles about robotics and automation research. Covers robot design, autonomous systems, humanoid robot research, swarm robotics, and scientific advances in making machines that can perceive and act in the world.",
          },
        ],
      },
      {
        id: "13.05", name: "Earth and climate science",
        keywords: ["climate science", "geology", "oceanography", "atmospheric", "carbon cycle", "sea level", "glaciology", "geophysics", "earth system", "seismology"],
        prompt: "Articles about Earth science and climate research. Covers geological research, oceanographic studies, atmospheric science, and the scientific understanding of Earth's systems and climate. For climate policy use Climate change (06.01).",
      },
      {
        id: "13.06", name: "Mathematics and statistics",
        keywords: ["mathematics", "theorem", "statistics", "probability", "topology", "number theory", "proof", "conjecture", "fields medal", "mathematical", "algebra"],
        prompt: "Articles about mathematical research and statistics. Covers new proofs, mathematical conjectures solved or open, fields medal awards, and advances in pure and applied mathematics and statistical methods.",
      },
      {
        id: "13.07", name: "Medicine and biomedical research",
        keywords: ["biomedical", "clinical research", "drug discovery", "pathology", "pharmacology", "physiology", "translational", "preclinical", "mechanism", "biomarker"],
        prompt: "Articles about biomedical research that bridges basic science and clinical medicine. Covers drug discovery science, disease mechanisms, preclinical research, and scientific findings not yet in clinical trials. For clinical trials use Medical research (07.04).",
      },
      {
        id: "13.08",
        name: "Physics",
        keywords: ["physics", "theory", "experiment", "measurement", "force", "energy", "matter", "observation", "theoretical", "condensed matter"],
        prompt: "Articles about physics research. Covers experimental and theoretical advances across physics disciplines. Use subcategories for specific areas of physics.",
        children: [
          {
            id: "13.08.01", name: "Nuclear physics and fusion energy",
            keywords: ["fusion", "nuclear reaction", "ITER", "plasma", "tokamak", "fission", "nuclear energy research", "inertial confinement", "deuterium", "tritium"],
            prompt: "Articles about nuclear physics and fusion energy research. Covers nuclear reactions, plasma physics, fusion milestone achievements, and scientific progress at facilities like ITER and NIF. For nuclear power plants use Nuclear energy (04.05.02).",
          },
          {
            id: "13.08.02", name: "Particle physics and high-energy physics",
            keywords: ["particle physics", "CERN", "Higgs boson", "collider", "quarks", "LHC", "standard model", "dark matter", "boson", "lepton", "detector"],
            prompt: "Articles about particle physics and high-energy experiments. Covers results from particle colliders, discoveries of new particles or forces, and advances in our understanding of the fundamental constituents of matter.",
          },
          {
            id: "13.08.03", name: "Quantum physics",
            keywords: ["quantum mechanics", "entanglement", "superposition", "wave function", "quantum field theory", "quantum optics", "Bose-Einstein", "decoherence"],
            prompt: "Articles about quantum physics research. Covers experimental tests of quantum mechanics, quantum entanglement demonstrations, quantum field theory advances, and foundational questions in quantum physics.",
          },
        ],
      },
      {
        id: "13.09", name: "Research policy and funding",
        keywords: ["research funding", "grant", "NSF", "peer review", "open access", "academic publishing", "research policy", "science budget", "citation", "preprint"],
        prompt: "Articles about science policy, research funding, and academic publishing. Covers government science budgets, grant agency decisions, open access debates, peer review integrity, and the institutional structures of research.",
      },
    ],
  },
  {
    id: "14",
    name: "Society",
    color: "#64748b",
    keywords: ["society", "social", "community", "culture", "people", "demographic", "inequality", "rights", "urban", "population", "trend"],
    prompt: "Articles about social issues, demographic trends, and the organisation of society. Covers human rights, social movements, inequality, and cultural and demographic change. Assign when the primary subject is a social condition or trend affecting communities.",
    children: [
      {
        id: "14.01", name: "Demographics and population",
        keywords: ["population", "birth rate", "aging", "demographics", "census", "migration", "fertility", "urbanisation", "mortality", "life expectancy", "population growth"],
        prompt: "Articles about demographic trends and population data. Covers birth rates, aging populations, migration patterns, census findings, and long-term demographic shifts and their societal implications.",
      },
      {
        id: "14.02", name: "Family and relationships",
        keywords: ["family", "marriage", "divorce", "parenting", "childcare", "domestic", "household", "single parent", "fertility", "adoption", "cohabitation"],
        prompt: "Articles about family structures and personal relationships. Covers marriage, divorce, parenting trends, childcare, and changing family forms. Assign when family life and personal relationships are the primary sociological subject.",
      },
      {
        id: "14.03", name: "Human rights and civil liberties",
        keywords: ["human rights", "civil rights", "freedom", "discrimination", "LGBTQ+", "racism", "rights", "liberty", "ACLU", "Amnesty", "UN rights body"],
        prompt: "Articles about human rights and civil liberties. Covers rights abuses, discrimination, LGBTQ+ rights, racial justice, and the work of human rights organisations. Assign when the protection or violation of fundamental rights is the primary subject.",
      },
      {
        id: "14.04", name: "Immigration and refugees",
        keywords: ["immigration", "refugee", "asylum", "border", "migration", "deportation", "visa", "undocumented", "displacement", "migrant", "UNHCR"],
        prompt: "Articles about immigration and refugee issues. Covers migration flows, asylum processes, border crossings, refugee crises, and immigration policy debates. Assign when the movement of people across borders—rather than trade or diplomatic policy—is the subject.",
      },
      {
        id: "14.05", name: "Inequality and poverty",
        keywords: ["inequality", "poverty", "wealth gap", "homelessness", "food insecurity", "social mobility", "Gini coefficient", "working poor", "deprivation", "redistribution"],
        prompt: "Articles about economic inequality and poverty. Covers income and wealth gaps, poverty rates, food insecurity, homelessness, and policies aimed at reducing inequality. Assign when socioeconomic inequality or material deprivation is the primary subject.",
      },
      {
        id: "14.06", name: "Internet culture and digital society",
        keywords: ["internet culture", "meme", "viral", "online community", "digital society", "platform culture", "misinformation", "online harassment", "cancel culture"],
        prompt: "Articles about the cultural and social dimensions of the internet. Covers online communities, viral phenomena, digital culture trends, misinformation spread, and the ways the internet shapes social norms and behaviour.",
      },
      {
        id: "14.07", name: "Social movements and activism",
        keywords: ["protest", "activism", "social movement", "advocacy", "rights", "demonstration", "campaign", "grassroots", "civil disobedience", "petition"],
        prompt: "Articles about social movements and organised activism. Covers protest events, activist campaigns, social movement dynamics, and advocacy efforts for political or social change. Assign when the movement or activism itself—rather than the underlying policy—is the primary subject.",
      },
      {
        id: "14.08", name: "Urbanization and cities",
        keywords: ["city", "urban", "smart city", "infrastructure", "housing", "transit", "gentrification", "urban planning", "metropolitan", "sprawl", "public space"],
        prompt: "Articles about cities and urban development. Covers urban planning, housing in cities, public transport, gentrification, and the challenges and opportunities of dense urban living. Assign when the city as a place and urban life are the primary subject.",
      },
    ],
  },
  {
    id: "15",
    name: "Sport",
    color: "#0ea5e9",
    keywords: ["sport", "athlete", "team", "match", "game", "competition", "championship", "league", "coach", "performance", "victory", "defeat"],
    prompt: "Articles about professional and competitive sport. Covers matches, tournaments, athlete news, and the sports industry. Assign when a sporting event, athlete, or sports competition is the primary subject.",
    children: [
      {
        id: "15.01", name: "American football",
        keywords: ["NFL", "football", "Super Bowl", "quarterback", "touchdown", "draft", "playoff", "college football", "linebacker", "receiver", "season"],
        prompt: "Articles about American football. Covers the NFL, college football, Super Bowl, player news, team performance, and the business of American football.",
      },
      {
        id: "15.02", name: "Athletics and track & field",
        keywords: ["athletics", "sprint", "marathon", "track", "field", "long jump", "world record", "100m", "hurdles", "javelin", "decathlon", "Diamond League"],
        prompt: "Articles about athletics and track and field events. Covers sprinting, middle and long distance running, field events, world records, and major athletics competitions including World Championships.",
      },
      {
        id: "15.03", name: "Baseball and softball",
        keywords: ["MLB", "baseball", "pitcher", "home run", "World Series", "batting average", "inning", "shortstop", "softball", "roster", "trade deadline"],
        prompt: "Articles about baseball and softball. Covers MLB, minor league baseball, college baseball, player trades, game results, and the business of professional baseball.",
      },
      {
        id: "15.04", name: "Basketball",
        keywords: ["NBA", "basketball", "three-pointer", "playoffs", "MVP", "draft", "WNBA", "point guard", "finals", "trade", "LeBron", "free agency"],
        prompt: "Articles about basketball. Covers the NBA, WNBA, college basketball, player news, game results, trades, and the business of professional basketball globally.",
      },
      {
        id: "15.05", name: "Boxing and combat sports",
        keywords: ["boxing", "UFC", "MMA", "knockout", "champion", "welterweight", "wrestling", "judo", "belt", "fight", "bout", "heavyweight"],
        prompt: "Articles about boxing and combat sports. Covers professional boxing, UFC and mixed martial arts, wrestling, and other competitive combat disciplines including results, fighter news, and title bouts.",
      },
      {
        id: "15.06", name: "Cricket",
        keywords: ["cricket", "Test match", "IPL", "batsman", "wicket", "Ashes", "ODI", "T20", "bowler", "century", "spinner", "England", "India", "Australia"],
        prompt: "Articles about cricket. Covers Test matches, ODIs, T20 leagues including the IPL and Big Bash, player news, team rankings, and the business of professional cricket.",
      },
      {
        id: "15.07", name: "Cycling",
        keywords: ["cycling", "Tour de France", "Giro", "Vuelta", "stage", "peloton", "time trial", "doping", "sprinter", "climber", "Classics", "velodrome"],
        prompt: "Articles about competitive cycling. Covers road cycling Grand Tours, one-day Classics, track cycling, mountain biking, doping cases, and team and rider news.",
      },
      {
        id: "15.08", name: "Football / Soccer",
        keywords: ["football", "soccer", "Premier League", "Champions League", "FIFA", "goal", "transfer", "World Cup", "La Liga", "Bundesliga", "Serie A"],
        prompt: "Articles about association football (soccer). Covers domestic leagues, international competitions, player transfers, FIFA, club and national team news, and the global football industry.",
      },
      {
        id: "15.09", name: "Formula 1 and motorsport",
        keywords: ["Formula 1", "F1", "Grand Prix", "Hamilton", "Verstappen", "constructor", "pit stop", "lap record", "NASCAR", "Le Mans", "WEC", "IndyCar"],
        prompt: "Articles about Formula 1 and other motorsport. Covers F1 race results, driver and constructor standings, technical regulations, NASCAR, endurance racing, and the business of motorsport.",
      },
      {
        id: "15.10", name: "Golf",
        keywords: ["golf", "PGA Tour", "Masters", "Open Championship", "par", "birdie", "leaderboard", "LIV Golf", "Ryder Cup", "green", "handicap", "major"],
        prompt: "Articles about golf. Covers the PGA Tour, LIV Golf, major championships, Ryder Cup, player rankings, and the business and culture of professional and amateur golf.",
      },
      {
        id: "15.11", name: "Ice hockey",
        keywords: ["NHL", "hockey", "Stanley Cup", "goalkeeper", "power play", "penalty", "period", "goal", "overtime", "trade deadline", "puck", "roster"],
        prompt: "Articles about ice hockey. Covers the NHL, European leagues, international ice hockey, Stanley Cup playoffs, player trades, and team news.",
      },
      {
        id: "15.12", name: "Olympics and multi-sport events",
        keywords: ["Olympics", "Games", "medal", "podium", "athlete", "host city", "IOC", "gold", "Commonwealth Games", "Asian Games", "torch relay", "doping"],
        prompt: "Articles about the Olympic Games and other multi-sport events. Covers athlete preparation, competition results, medal tables, IOC decisions, host city issues, and anti-doping matters in an Olympic context.",
      },
      {
        id: "15.13", name: "Rugby",
        keywords: ["rugby", "Six Nations", "World Cup", "tackle", "scrum", "try", "union", "league", "Lions", "Super Rugby", "Premiership", "conversion"],
        prompt: "Articles about rugby union and rugby league. Covers international tournaments including the Six Nations and World Cup, domestic leagues, club news, and the distinctive culture and business of rugby.",
      },
      {
        id: "15.14", name: "Swimming and aquatics",
        keywords: ["swimming", "pool", "stroke", "relay", "world record", "diving", "water polo", "open water", "freestyle", "butterfly", "Paralympic swimming"],
        prompt: "Articles about competitive swimming and aquatic sports. Covers pool and open-water swimming, diving, water polo, world records, and major swimming competitions including World Championships.",
      },
      {
        id: "15.15", name: "Tennis",
        keywords: ["tennis", "Grand Slam", "Wimbledon", "US Open", "serve", "ranking", "ATP", "WTA", "set", "tie-break", "Roland Garros", "Australian Open"],
        prompt: "Articles about professional tennis. Covers Grand Slam tournaments, ATP and WTA tour events, player rankings, match results, retirements, and the business of professional tennis.",
      },
      {
        id: "15.16", name: "Winter sports",
        keywords: ["skiing", "snowboarding", "Winter Olympics", "alpine", "biathlon", "figure skating", "ice", "slalom", "freestyle", "luge", "bobsled"],
        prompt: "Articles about winter sports. Covers alpine and cross-country skiing, snowboarding, biathlon, figure skating, speed skating, and other snow and ice sports outside of ice hockey.",
      },
    ],
  },
  {
    id: "16",
    name: "Conflict, war and peace",
    color: "#dc2626",
    keywords: ["war", "conflict", "military", "troops", "battle", "ceasefire", "casualties", "frontline", "offensive", "defence", "fighting"],
    prompt: "Articles about armed conflicts, warfare, and peace processes. Covers active military operations, peace negotiations, and war-related events. Assign when armed conflict or its direct resolution is the primary subject.",
    children: [
      {
        id: "16.01",
        name: "Armed conflict and warfare",
        keywords: ["armed conflict", "war", "military operation", "casualties", "front line", "offensive", "troops", "military advance", "combat", "battle"],
        prompt: "Articles about active armed conflict and military operations. Covers battles, military advances, casualty reports, and the conduct of war. Use subcategories for specific types of military operations.",
        children: [
          {
            id: "16.01.01", name: "Air warfare",
            keywords: ["air strike", "bombing", "fighter jet", "air force", "aerial", "sortie", "drone strike", "air campaign", "intercept", "air defence"],
            prompt: "Articles about military air operations. Covers air strikes, bombing campaigns, fighter jet engagements, drone strikes, and air defence operations in the context of active armed conflict.",
          },
          {
            id: "16.01.02", name: "Cyberwarfare",
            keywords: ["cyberattack", "cyberwarfare", "state-sponsored hacking", "infrastructure attack", "digital warfare", "military cyber", "offensive cyber", "CISA"],
            prompt: "Articles about state-level cyberwarfare. Covers state-sponsored cyberattacks on critical infrastructure, military cyber operations, and offensive cyber activities attributed to governments. For criminal hacking use Cybercrime (02.02.01).",
          },
          {
            id: "16.01.03", name: "Ground operations",
            keywords: ["ground offensive", "troops", "infantry", "military advance", "occupation", "retreat", "front line", "armour", "artillery", "siege"],
            prompt: "Articles about ground military operations. Covers ground offensives, infantry engagements, territorial advances or retreats, armoured operations, and urban warfare in the context of active armed conflict.",
          },
          {
            id: "16.01.04", name: "Naval operations",
            keywords: ["naval", "warship", "carrier", "blockade", "maritime", "submarine", "fleet", "destroyer", "navy", "sea lane", "port blockade"],
            prompt: "Articles about naval and maritime military operations. Covers warship movements, naval blockades, submarine operations, sea lane security, and naval engagements in active conflicts.",
          },
        ],
      },
      {
        id: "16.02", name: "Arms trade and weapons proliferation",
        keywords: ["arms sales", "weapons export", "proliferation", "illegal arms", "arms embargo", "arms dealer", "small arms", "WMD", "treaty", "defence export"],
        prompt: "Articles about the international arms trade and weapons proliferation. Covers state weapons sales, illegal arms flows, non-proliferation treaties, and concerns over weapons spreading to conflict zones or rogue actors.",
      },
      {
        id: "16.03", name: "Peace negotiations and ceasefires",
        keywords: ["ceasefire", "peace talks", "negotiations", "truce", "mediation", "peace agreement", "diplomatic solution", "hostage deal", "prisoner exchange"],
        prompt: "Articles about efforts to end armed conflicts. Covers ceasefire negotiations, peace talks, mediation processes, and peace agreements. Assign when diplomatic efforts to resolve a conflict—rather than the conflict itself—are the primary subject.",
      },
      {
        id: "16.04", name: "Terrorism and insurgency",
        keywords: ["terrorism", "insurgency", "attack", "bomb", "extremism", "militia", "IED", "counter-terrorism", "radicalism", "jihad", "separatist", "guerrilla"],
        prompt: "Articles about terrorism and armed insurgencies. Covers attacks by non-state armed groups, counter-insurgency operations, and the dynamics of armed movements challenging state authority. For criminally motivated violence use Terrorism (02.02.05).",
      },
      {
        id: "16.05", name: "War crimes and atrocities",
        keywords: ["war crimes", "atrocities", "genocide", "ICC", "humanitarian law", "civilian casualties", "tribunal", "massacre", "ethnic cleansing", "investigation"],
        prompt: "Articles about war crimes and mass atrocities. Covers alleged or confirmed violations of international humanitarian law, ICC investigations, massacre reports, and accountability efforts for atrocities committed during armed conflict.",
      },
    ],
  },
  {
    id: "17",
    name: "Weather",
    color: "#0891b2",
    keywords: ["weather", "temperature", "storm", "forecast", "climate", "rain", "snow", "wind", "heatwave", "cold", "meteorology"],
    prompt: "Articles about weather conditions and meteorology. Covers weather events, forecasts, and seasonal conditions. Assign when the weather itself—rather than its cause or long-term climate implications—is the primary subject.",
    children: [
      {
        id: "17.01", name: "Extreme weather events",
        keywords: ["heatwave", "blizzard", "tornado", "derecho", "extreme weather", "record temperature", "cold snap", "ice storm", "heat dome", "polar vortex"],
        prompt: "Articles about extreme weather events that fall short of a named natural disaster. Covers record temperatures, severe storms, blizzards, and tornado outbreaks. For events causing significant casualties or damage use Natural disaster (03.04).",
      },
      {
        id: "17.02", name: "Meteorology and forecasting",
        keywords: ["weather forecast", "temperature", "precipitation", "climate model", "meteorology", "met office", "NOAA", "forecast", "radar", "jet stream"],
        prompt: "Articles about meteorology and weather forecasting. Covers forecast updates, advances in weather prediction, meteorological services, and the science of atmospheric observation and modelling.",
      },
      {
        id: "17.03", name: "Seasonal weather",
        keywords: ["winter", "summer", "monsoon", "drought season", "seasonal outlook", "spring", "autumn", "El Niño", "La Niña", "seasonal forecast"],
        prompt: "Articles about seasonal weather patterns and outlooks. Covers seasonal forecasts, monsoon patterns, El Niño and La Niña effects, and the expected character of a forthcoming season.",
      },
    ],
  },
];

export function getNodeColor(nodeId: string): string {
  const topId = nodeId.split(".")[0];
  const topNode = IPTC_TAXONOMY.find((n) => n.id === topId);
  return topNode?.color ?? "#6366f1";
}

function _flattenNode(node: TaxonomyNode, result: TaxonomyNode[]): void {
  result.push(node);
  if (node.children) node.children.forEach((c) => _flattenNode(c, result));
}

export function flattenTaxonomy(): TaxonomyNode[] {
  const result: TaxonomyNode[] = [];
  IPTC_TAXONOMY.forEach((n) => _flattenNode(n, result));
  return result;
}

export function findNode(id: string): TaxonomyNode | undefined {
  return flattenTaxonomy().find((n) => n.id === id);
}
