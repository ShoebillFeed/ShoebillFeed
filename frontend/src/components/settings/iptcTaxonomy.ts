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
    prompt: "Assign this category to articles about arts, culture, entertainment, and the media industry. Include film, music, television, visual arts, gaming, fashion, and media organizations. Use the most specific subcategory available.",
    children: [
      {
        id: "01.01", name: "Cinema and film",
        keywords: ["film", "movie", "cinema", "director", "box office", "Hollywood", "Oscar", "Cannes", "release", "screenplay", "studio", "actor"],
        prompt: "Assign this category to articles about cinema and the film industry. Include new releases, box office, filmmakers, awards season, film festivals, and studio business. Exclude streaming-only content (use Television and streaming).",
      },
      {
        id: "01.02", name: "Dance",
        keywords: ["dance", "ballet", "choreography", "performance", "dance company", "contemporary dance", "hip-hop", "ballroom", "touring", "dancer"],
        prompt: "Assign this category to articles about dance as a performing art. Include ballet, contemporary, hip-hop, and ballroom dance, choreographers, and dance companies.",
      },
      {
        id: "01.03", name: "Fashion and beauty",
        keywords: ["fashion", "designer", "runway", "collection", "couture", "style", "beauty", "cosmetics", "trend", "luxury", "fashion week", "LVMH"],
        prompt: "Assign this category to articles about the fashion and beauty industries. Include runway shows, designer collections, fashion weeks, beauty products, and luxury goods. Exclude fashion as retail business (use Retail and consumer goods).",
      },
      {
        id: "01.04", name: "Gaming and video games",
        keywords: ["video game", "gaming", "PlayStation", "Xbox", "Nintendo", "PC gaming", "esports", "game release", "developer", "Steam", "Valve", "indie game"],
        prompt: "Assign this category to articles about video games and the gaming industry. Include game releases, studios, esports, gaming hardware, and gaming culture.",
      },
      {
        id: "01.05", name: "Literature and poetry",
        keywords: ["book", "novel", "author", "literature", "fiction", "nonfiction", "poetry", "publisher", "bestseller", "Booker Prize", "literary award"],
        prompt: "Assign this category to articles about books, literature, and poetry. Include new publications, author profiles, literary prizes, and the publishing industry.",
      },
      {
        id: "01.06", name: "Music",
        keywords: ["music", "album", "artist", "concert", "tour", "Grammy", "chart", "band", "singer", "record label", "Spotify", "festival", "streaming"],
        prompt: "Assign this category to articles about music and the music industry. Include album releases, concert tours, streaming performance, artist news, music awards, and record label business.",
      },
      {
        id: "01.07", name: "Photography",
        keywords: ["photography", "photographer", "exhibition", "camera", "portrait", "photojournalism", "lens", "photo award", "gallery", "Magnum", "image"],
        prompt: "Assign this category to articles about photography as an art form or profession. Include photographers, exhibitions, photojournalism, and camera technology. Exclude photos that merely illustrate another story.",
      },
      {
        id: "01.08", name: "Radio",
        keywords: ["radio", "broadcast", "station", "listener", "FM", "AM", "BBC Radio", "terrestrial radio", "digital radio", "DAB", "audio"],
        prompt: "Assign this category to articles about radio broadcasting and audio media. Include radio stations, presenters, listener ratings, and the radio industry. Exclude podcast platforms (use Online media and publishing).",
      },
      {
        id: "01.09", name: "Television and streaming",
        keywords: ["TV", "television", "streaming", "Netflix", "HBO", "Disney+", "series", "episode", "ratings", "showrunner", "commission", "broadcast"],
        prompt: "Assign this category to articles about television and video streaming services. Include TV shows, streaming platform performance, commissioning decisions, and viewership data.",
      },
      {
        id: "01.10", name: "Theatre and performing arts",
        keywords: ["theatre", "play", "Broadway", "West End", "musical", "stage", "opera", "performance", "production", "Tony Awards", "casting", "touring"],
        prompt: "Assign this category to articles about theatre and live performing arts. Include stage plays, musicals, opera, Broadway, West End, and touring productions. Exclude dance (use Dance).",
      },
      {
        id: "01.11", name: "Visual arts",
        keywords: ["art", "painting", "sculpture", "gallery", "museum", "exhibition", "artist", "auction", "contemporary art", "installation", "Christie's", "Sotheby's"],
        prompt: "Assign this category to articles about the visual arts. Include painting, sculpture, contemporary art, gallery exhibitions, auction results, and the art market. Exclude photography (use Photography).",
      },
      {
        id: "01.12", name: "Entertainment",
        keywords: ["celebrity", "entertainment", "awards", "red carpet", "premiere", "pop culture", "fame", "gossip", "public figure", "entertainment industry"],
        prompt: "Assign this category to articles about celebrity culture, award shows, and pop culture spanning film, music, and TV. Exclude articles where the professional work—rather than personal celebrity—is the subject.",
      },
      {
        id: "01.13",
        name: "Media",
        keywords: ["media", "journalism", "press", "publisher", "news industry", "media ownership", "press freedom", "newsroom", "editorial", "media company"],
        prompt: "Assign this category to articles about the media industry as a business or institution. Include media ownership, press freedom, journalism practices, and content distribution trends. Exclude specific media content — assign to the content type instead (Film, Music, TV, etc.).",
        children: [
          {
            id: "01.13.01", name: "Broadcasting",
            keywords: ["broadcaster", "network", "ratings", "FCC", "Ofcom", "terrestrial", "satellite", "cable", "broadcast rights", "viewership", "transmission"],
            prompt: "Assign this category to articles about broadcast media networks and their business. Include TV and radio networks, regulatory environment, programming strategy, and broadcast rights. Exclude coverage of specific programmes (use Television and streaming or Radio).",
          },
          {
            id: "01.13.02", name: "Journalism and news",
            keywords: ["journalism", "reporter", "press freedom", "investigative", "editorial", "newsroom", "journalist safety", "media ethics", "Pulitzer", "fact-checking"],
            prompt: "Assign this category to articles about journalism as a practice and profession. Include press freedom, investigative reporting, newsroom management, journalist safety, and media ethics. Exclude a specific story's content — assign to its topic instead.",
          },
          {
            id: "01.13.03", name: "Online media and publishing",
            keywords: ["digital media", "online news", "publisher", "newsletter", "Substack", "paywall", "digital advertising", "content monetisation", "audience growth"],
            prompt: "Assign this category to articles about digital publishing and online news. Include paywalls, newsletter platforms, digital advertising, and the economics of online journalism and content creation.",
          },
          {
            id: "01.13.04", name: "Social media and influencers",
            keywords: ["social media", "influencer", "TikTok", "Instagram", "YouTube", "viral", "content creator", "algorithm", "platform policy", "X", "creator economy"],
            prompt: "Assign this category to articles about social media platforms and content creators. Include platform policies, algorithm changes, influencer marketing, viral trends, and the creator economy. Exclude criminal activity on social media (use Cybercrime).",
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
    prompt: "Assign this category to articles about crime, the legal system, and justice. Include criminal cases, court proceedings, law enforcement, and incarceration. Use the most specific subcategory available.",
    children: [
      {
        id: "02.01", name: "Courts and judiciary",
        keywords: ["court", "judge", "verdict", "trial", "ruling", "appeal", "Supreme Court", "lawsuit", "sentence", "hearing", "justice", "litigation"],
        prompt: "Assign this category to articles about court cases and judicial proceedings. Include verdicts, rulings, appeals, and Supreme Court decisions. Exclude legislation (use Legislation and lawmaking).",
      },
      {
        id: "02.02",
        name: "Crime",
        keywords: ["crime", "criminal", "offender", "victim", "investigation", "murder", "robbery", "theft", "assault", "perpetrator"],
        prompt: "Assign this category to articles about criminal activity, investigations, and criminal networks. Exclude court proceedings (use Courts and judiciary) and law enforcement as an institution (use Law enforcement and policing).",
        children: [
          {
            id: "02.02.01", name: "Cybercrime and hacking",
            keywords: ["hacking", "data breach", "malware", "ransomware", "phishing", "cybercrime", "dark web", "exploit", "botnet", "identity theft"],
            prompt: "Assign this category to articles about cybercrime and malicious hacking. Include data breaches, ransomware attacks, phishing, criminal hacking groups, and digital fraud. Exclude state-sponsored cyber operations (use Cyberwarfare).",
          },
          {
            id: "02.02.02", name: "Drug trafficking",
            keywords: ["drug trafficking", "narcotics", "cartel", "fentanyl", "smuggling", "DEA", "seizure", "cocaine", "heroin", "drug bust"],
            prompt: "Assign this category to articles about the illegal drug trade. Include trafficking networks, cartels, major seizures, and anti-narcotics operations. Exclude drug policy debates (use Legislation and lawmaking).",
          },
          {
            id: "02.02.03", name: "Financial crime and fraud",
            keywords: ["fraud", "money laundering", "Ponzi scheme", "embezzlement", "financial crime", "SEC enforcement", "insider trading", "scam", "corruption"],
            prompt: "Assign this category to articles about financial crime. Include fraud, money laundering, embezzlement, Ponzi schemes, and insider trading. Exclude civil regulatory enforcement without criminal charges (use Financial regulation).",
          },
          {
            id: "02.02.04", name: "Organized crime",
            keywords: ["organized crime", "mafia", "cartel", "gang", "criminal network", "mob", "extortion", "protection racket", "racketeering", "syndicate"],
            prompt: "Assign this category to articles about organised criminal networks. Include mafia organisations, gangs, cartels, extortion, and racketeering.",
          },
          {
            id: "02.02.05", name: "Terrorism",
            keywords: ["terrorism", "attack", "bomb", "ISIS", "al-Qaeda", "extremism", "counter-terrorism", "threat", "radicalisation", "suicide bomber"],
            prompt: "Assign this category to articles about terrorist acts and organisations. Include attacks, plots, radicalisation, and counter-terrorism measures. Exclude ongoing armed insurgencies in conflict zones (use Terrorism and insurgency).",
          },
          {
            id: "02.02.06", name: "Violent crime",
            keywords: ["murder", "shooting", "violence", "assault", "homicide", "armed robbery", "stabbing", "gun violence", "mass shooting", "manslaughter"],
            prompt: "Assign this category to articles about violent crimes against persons. Include murder, assault, armed robbery, gun violence, and mass shootings. Exclude violence in conflict or terrorism contexts (use Armed conflict or Terrorism).",
          },
        ],
      },
      {
        id: "02.03", name: "Law enforcement and policing",
        keywords: ["police", "arrest", "FBI", "investigation", "officer", "law enforcement", "search warrant", "SWAT", "patrol", "detective", "misconduct"],
        prompt: "Assign this category to articles about law enforcement agencies and policing. Include police operations, arrests, reform, misconduct, and community relations. Exclude specific criminal cases (use Crime subcategories).",
      },
      {
        id: "02.04", name: "Legislation and legal proceedings",
        keywords: ["law", "legislation", "statute", "bill", "amendment", "legal proceedings", "lawmaker", "legal reform", "act", "ordinance", "code"],
        prompt: "Assign this category to articles about the creation and application of law outside criminal cases. Include new legislation, legal reform, and civil legal proceedings. Exclude criminal court cases (use Courts and judiciary).",
      },
      {
        id: "02.05", name: "Prisons and incarceration",
        keywords: ["prison", "jail", "sentencing", "parole", "incarceration", "inmate", "correctional", "death penalty", "solitary confinement", "prison reform"],
        prompt: "Assign this category to articles about prisons, detention, and incarceration. Include prison conditions, sentencing policy, parole, and prison reform. Exclude the crimes that led to incarceration (use Crime subcategories).",
      },
    ],
  },
  {
    id: "03",
    name: "Disaster, accident and emergency",
    color: "#f97316",
    keywords: ["disaster", "accident", "emergency", "casualties", "rescue", "evacuation", "fatalities", "relief", "crisis", "damage"],
    prompt: "Assign this category to articles about disasters, accidents, and emergencies. Include natural disasters, industrial accidents, transport crashes, and emergency response. Use the most specific subcategory available.",
    children: [
      {
        id: "03.01", name: "Aviation accident",
        keywords: ["plane crash", "aviation accident", "airline", "flight", "passengers", "NTSB", "FAA", "investigation", "crash landing", "mid-air collision"],
        prompt: "Assign this category to articles about aviation accidents and incidents. Include aircraft crashes, emergency landings, mid-air collisions, and aviation safety investigations.",
      },
      {
        id: "03.02", name: "Fire and explosion",
        keywords: ["fire", "explosion", "blaze", "arson", "firefighter", "evacuation", "inferno", "detonation", "gas leak", "building fire"],
        prompt: "Assign this category to articles about fires and explosions causing harm or damage. Include structural fires, industrial explosions, arson, and firefighting. Exclude uncontrolled wildfires (use Wildfire).",
      },
      {
        id: "03.03", name: "Industrial and nuclear accident",
        keywords: ["industrial accident", "chemical spill", "nuclear accident", "radiation", "plant explosion", "contamination", "toxic leak", "oil spill", "refinery"],
        prompt: "Assign this category to articles about accidents at industrial or nuclear facilities. Include chemical spills, refinery explosions, nuclear plant incidents, and hazardous material releases.",
      },
      {
        id: "03.04",
        name: "Natural disaster",
        keywords: ["natural disaster", "disaster relief", "casualties", "evacuation", "emergency response", "FEMA", "aid", "affected", "damage"],
        prompt: "Assign this category to articles about natural disasters, casualties, emergency response, and relief efforts. Use the most specific subcategory; assign the parent only for multi-type or preparedness coverage.",
        children: [
          {
            id: "03.04.01", name: "Drought",
            keywords: ["drought", "water shortage", "crop failure", "arid", "rainfall deficit", "groundwater", "water crisis", "dry season", "famine risk"],
            prompt: "Assign this category to articles about droughts and water scarcity from prolonged dry conditions. Include agricultural impacts, water supply crises, and affected communities.",
          },
          {
            id: "03.04.02", name: "Earthquake and tsunami",
            keywords: ["earthquake", "tsunami", "seismic", "magnitude", "tremor", "fault line", "aftershock", "richter", "tectonic", "epicentre"],
            prompt: "Assign this category to articles about earthquakes and tsunamis. Include seismic events, magnitude reports, casualties, structural damage, and triggered tsunamis.",
          },
          {
            id: "03.04.03", name: "Flood",
            keywords: ["flood", "flooding", "storm surge", "river burst", "dam failure", "inundation", "displacement", "flash flood", "levee"],
            prompt: "Assign this category to articles about flooding. Include river flooding, storm surges, flash floods, dam failures, and displacement of populations.",
          },
          {
            id: "03.04.04", name: "Hurricane and tropical storm",
            keywords: ["hurricane", "typhoon", "cyclone", "tropical storm", "Category 5", "landfall", "storm surge", "evacuation", "wind speed", "NHC"],
            prompt: "Assign this category to articles about tropical storms, hurricanes, and typhoons. Include storm development, landfall, wind and surge damage, and evacuations.",
          },
          {
            id: "03.04.05", name: "Wildfire",
            keywords: ["wildfire", "forest fire", "bushfire", "blaze", "containment", "evacuation", "acres burned", "firefighter", "air quality", "fire season"],
            prompt: "Assign this category to articles about uncontrolled fires in wildland areas. Include spread, containment, evacuations, and smoke impacts. Exclude structure fires (use Fire and explosion).",
          },
          {
            id: "03.04.06", name: "Volcanic eruption",
            keywords: ["volcano", "eruption", "lava", "ash cloud", "pyroclastic", "seismic activity", "magma", "evacuation", "crater", "caldera"],
            prompt: "Assign this category to articles about volcanic eruptions. Include lava flows, ash dispersal, air travel disruptions, and evacuations.",
          },
        ],
      },
      {
        id: "03.05", name: "Transport accident",
        keywords: ["crash", "collision", "road accident", "train derailment", "ship sinking", "fatalities", "road safety", "pile-up", "motorway", "bridge collapse"],
        prompt: "Assign this category to articles about road, rail, and maritime transport accidents. Include vehicle crashes, train derailments, ship collisions, and casualties. Exclude aviation accidents (use Aviation accident).",
      },
    ],
  },
  {
    id: "04",
    name: "Economy, business and finance",
    color: "#f59e0b",
    keywords: ["economy", "business", "finance", "market", "company", "investment", "profit", "earnings", "GDP", "growth", "industry", "trade"],
    prompt: "Assign this category to articles about economics, business, and financial markets. Include corporate news, economic indicators, industry sectors, and business strategy. Use the most specific subcategory available.",
    children: [
      {
        id: "04.01", name: "Agriculture and food industry",
        keywords: ["agriculture", "farming", "crop", "harvest", "food supply", "commodity prices", "livestock", "irrigation", "agribusiness", "food production"],
        prompt: "Assign this category to articles about agriculture, farming, and the commercial food supply chain. Include crop yields, commodity prices, farm policy, and agribusiness. Exclude food as culture (use Food and drink) and food safety as public health (use Public health).",
      },
      {
        id: "04.02",
        name: "Banking and financial services",
        keywords: ["bank", "banking", "financial services", "lending", "deposit", "interest rate", "credit", "liquidity", "balance sheet", "financial institution"],
        prompt: "Assign this category to articles about banks and financial services firms as businesses. Include bank earnings, lending activity, and financial stability. Exclude investment products and crypto (use Financial markets or Cryptocurrency) and monetary policy (use Central banking and monetary policy).",
        children: [
          {
            id: "04.02.01", name: "Central banking and monetary policy",
            keywords: ["central bank", "interest rates", "Fed", "ECB", "inflation", "monetary policy", "rate hike", "quantitative easing", "reserve", "Federal Reserve"],
            prompt: "Assign this category to articles about central banks and monetary policy. Include interest rate decisions by the Fed, ECB, and other central banks, inflation targeting, and quantitative easing.",
          },
          {
            id: "04.02.02", name: "Consumer finance and lending",
            keywords: ["mortgage", "loan", "credit card", "personal finance", "lending", "consumer debt", "auto loan", "student loan", "CFPB", "credit score"],
            prompt: "Assign this category to articles about consumer financial products and household debt. Include mortgages, personal loans, credit cards, and student debt. Exclude institutional and corporate finance (use Investment banking or Banking).",
          },
          {
            id: "04.02.03", name: "Investment banking",
            keywords: ["IPO", "underwriting", "Goldman Sachs", "Morgan Stanley", "M&A advisory", "securities", "deal", "capital markets", "bond issuance", "investment bank"],
            prompt: "Assign this category to articles about investment banking. Include IPO underwriting, M&A advisory, and capital markets activity. Exclude retail banking (use Banking and financial services).",
          },
        ],
      },
      {
        id: "04.03",
        name: "Computing and information technology",
        keywords: ["technology", "software", "hardware", "IT", "tech company", "platform", "digital", "Silicon Valley", "startup", "cloud", "data"],
        prompt: "Assign this category to articles about the computing and IT industry as a business sector. Include technology companies, product launches, and industry competition. Exclude AI (use Artificial intelligence), cybersecurity incidents (use Cybersecurity), semiconductors (use Hardware and semiconductors), and e-commerce (use Internet and e-commerce).",
        children: [
          {
            id: "04.03.01", name: "Artificial intelligence",
            keywords: ["AI", "machine learning", "LLM", "ChatGPT", "OpenAI", "Anthropic", "neural network", "model", "generative AI", "foundation model", "inference", "GPU"],
            prompt: "Assign this category to articles about AI as a commercial and industrial force. Include AI product launches, company competition, enterprise adoption, and AI investment. Exclude academic AI research (use Artificial intelligence research) and robotics hardware (use Robotics and automation).",
          },
          {
            id: "04.03.02", name: "Cloud computing and infrastructure",
            keywords: ["cloud", "AWS", "Azure", "Google Cloud", "data centre", "servers", "SaaS", "IaaS", "PaaS", "colocation", "hyperscaler", "cloud revenue"],
            prompt: "Assign this category to articles about cloud computing services and digital infrastructure. Include cloud provider competition, data centre investment, and enterprise cloud adoption by AWS, Azure, and Google Cloud.",
          },
          {
            id: "04.03.03", name: "Cybersecurity",
            keywords: ["cybersecurity", "hack", "vulnerability", "breach", "ransomware", "CVE", "zero-day", "CISA", "cyber defence", "infosec", "patch", "threat actor"],
            prompt: "Assign this category to articles about cybersecurity threats, incidents, and defences. Include disclosed vulnerabilities, ransomware attacks, data breaches, and the cybersecurity industry. Exclude state-level cyber conflict (use Cyberwarfare) and criminal hacking prosecutions (use Cybercrime).",
          },
          {
            id: "04.03.04", name: "Hardware and semiconductors",
            keywords: ["chip", "semiconductor", "NVIDIA", "Intel", "AMD", "TSMC", "processor", "GPU", "silicon", "wafer", "fab", "supply chain", "HBM"],
            prompt: "Assign this category to articles about computer hardware and the semiconductor industry. Include chip design, manufacturing, fab capacity, processor architectures, and competition among companies like NVIDIA, Intel, AMD, and TSMC.",
          },
          {
            id: "04.03.05", name: "Internet and e-commerce",
            keywords: ["e-commerce", "Amazon", "Shopify", "online retail", "marketplace", "digital commerce", "website", "platform", "internet business", "online sales"],
            prompt: "Assign this category to articles about internet businesses and e-commerce. Include online retail, digital marketplaces, and platform economics. Exclude software-as-a-service businesses (use Software and apps).",
          },
          {
            id: "04.03.06", name: "Software and apps",
            keywords: ["software", "app", "SaaS", "developer tools", "update", "release", "platform", "open source", "SDK", "API", "enterprise software", "productivity"],
            prompt: "Assign this category to articles about the software industry and application development. Include enterprise software, productivity apps, developer tools, SaaS businesses, and software company earnings.",
          },
        ],
      },
      {
        id: "04.04", name: "Cryptocurrency and digital assets",
        keywords: ["Bitcoin", "Ethereum", "crypto", "blockchain", "DeFi", "NFT", "stablecoin", "token", "exchange", "wallet", "Layer 2", "Web3", "on-chain"],
        prompt: "Assign this category to articles about cryptocurrency and digital assets. Include Bitcoin and Ethereum markets, crypto exchanges, DeFi, stablecoins, NFTs, and regulatory actions against crypto.",
      },
      {
        id: "04.05",
        name: "Energy and resources",
        keywords: ["energy", "oil", "gas", "OPEC", "renewable", "power", "grid", "electricity", "pipeline", "refinery", "fuel", "energy market"],
        prompt: "Assign this category to articles about the energy sector and natural resources. Use a specific subcategory for fossil fuels, nuclear, or renewables; assign the parent for cross-energy or general energy market coverage.",
        children: [
          {
            id: "04.05.01", name: "Fossil fuels",
            keywords: ["oil", "gas", "OPEC", "crude oil", "natural gas", "petroleum", "pipeline", "LNG", "refinery", "carbon", "coal", "drilling"],
            prompt: "Assign this category to articles about the fossil fuel industry. Include oil and gas production, OPEC decisions, pipeline projects, LNG trade, and coal. Exclude climate aspects (use Climate change).",
          },
          {
            id: "04.05.02", name: "Nuclear energy",
            keywords: ["nuclear", "reactor", "uranium", "fission", "power plant", "NRC", "SMR", "nuclear waste", "decommission", "plant life extension"],
            prompt: "Assign this category to articles about nuclear power as an energy source. Include reactor construction, uranium supply, SMRs, and waste management. Exclude nuclear weapons (use Arms and weapons programmes).",
          },
          {
            id: "04.05.03", name: "Renewable energy",
            keywords: ["solar", "wind", "renewable", "clean energy", "grid", "battery storage", "EV", "offshore wind", "photovoltaic", "turbine", "green hydrogen"],
            prompt: "Assign this category to articles about the renewable energy industry. Include solar and wind projects, grid-scale storage, offshore wind, and clean energy investment. Exclude environmental policy aspects (use Environmental regulation).",
          },
        ],
      },
      {
        id: "04.06",
        name: "Financial markets",
        keywords: ["financial markets", "trading", "investor", "market", "assets", "portfolio", "volatility", "returns", "capital", "exchange"],
        prompt: "Assign this category to articles about financial markets and investing. Use a specific subcategory for stocks, bonds, currencies, commodities, or private equity; assign the parent for broad multi-asset coverage.",
        children: [
          {
            id: "04.06.01", name: "Bonds and fixed income",
            keywords: ["bond", "yield", "Treasury", "sovereign debt", "credit rating", "fixed income", "bond market", "spreads", "Moody's", "gilts", "coupon"],
            prompt: "Assign this category to articles about bond markets and fixed income. Include government and corporate bond yields, credit ratings, and debt issuance.",
          },
          {
            id: "04.06.02", name: "Commodities",
            keywords: ["commodity", "gold", "oil prices", "copper", "agricultural futures", "commodity market", "spot price", "futures", "lithium", "wheat", "silver"],
            prompt: "Assign this category to articles about commodity markets. Include prices and trading of metals, energy commodities, and agricultural futures.",
          },
          {
            id: "04.06.03", name: "Currencies and forex",
            keywords: ["currency", "forex", "dollar", "euro", "yuan", "exchange rate", "FX", "yen", "sterling", "devaluation", "reserve currency", "DXY"],
            prompt: "Assign this category to articles about currency markets and exchange rates. Include foreign exchange trading, currency moves, and central bank FX intervention.",
          },
          {
            id: "04.06.04", name: "Equities and stock markets",
            keywords: ["stock", "shares", "S&P 500", "earnings", "market cap", "valuation", "Nasdaq", "FTSE", "index", "dividends", "analyst", "equity market"],
            prompt: "Assign this category to articles about equity markets and stocks. Include market performance, company earnings, valuations, and analyst ratings.",
          },
          {
            id: "04.06.05", name: "Private equity and venture capital",
            keywords: ["venture capital", "private equity", "funding round", "seed", "Series A", "LBO", "buyout", "portfolio company", "exit", "fund raising", "LP"],
            prompt: "Assign this category to articles about private equity and venture capital. Include fund raising, buyouts, VC funding rounds, and portfolio company performance. Exclude early-stage startup stories (use Startups and entrepreneurship).",
          },
        ],
      },
      {
        id: "04.07", name: "Healthcare industry",
        keywords: ["hospital", "health insurance", "Medicare", "Medicaid", "healthcare costs", "medical device", "health system", "payer", "provider", "HMO"],
        prompt: "Assign this category to articles about healthcare as a business sector. Include hospital networks, health insurance companies, medical device manufacturers, and healthcare costs. Exclude clinical or scientific health news (use Health).",
      },
      {
        id: "04.08", name: "Housing and real estate",
        keywords: ["housing market", "real estate", "mortgage rates", "home prices", "construction", "property", "rent", "landlord", "developer", "commercial real estate"],
        prompt: "Assign this category to articles about housing and real estate markets. Include home prices, mortgage rates, residential construction, commercial property, and rental markets. Exclude home design and renovation (use Home and living).",
      },
      {
        id: "04.09", name: "Manufacturing and industry",
        keywords: ["manufacturing", "factory", "supply chain", "industrial output", "production", "automation", "reshoring", "plant", "assembly", "workforce"],
        prompt: "Assign this category to articles about manufacturing and industrial production. Include factory output, supply chain management, industrial capacity, and reshoring trends.",
      },
      {
        id: "04.10", name: "Media and entertainment industry",
        keywords: ["media company", "streaming revenue", "advertising", "content", "studio", "rights", "merger", "media business", "subscriptions", "distribution"],
        prompt: "Assign this category to articles about the media and entertainment industry as a business. Include streaming revenue, advertising markets, content rights deals, and studio strategy. Exclude the content itself (use Arts, entertainment and media).",
      },
      {
        id: "04.11", name: "Mergers and acquisitions",
        keywords: ["acquisition", "merger", "takeover", "deal", "acquisition price", "antitrust", "buyout", "bid", "hostile takeover", "due diligence", "synergies"],
        prompt: "Assign this category to articles about corporate mergers and acquisitions. Include announced deals, hostile takeovers, regulatory approval or blockage, and deal terms.",
      },
      {
        id: "04.12", name: "Pharmaceutical industry",
        keywords: ["pharma", "drug", "FDA approval", "clinical trial", "biotech", "pipeline", "patent", "generic", "blockbuster", "GLP-1", "oncology drug"],
        prompt: "Assign this category to articles about the pharmaceutical and biotech industries as businesses. Include drug pipelines, FDA approvals from a commercial perspective, patent cliffs, and pharma M&A. Exclude clinical research (use Medical research).",
      },
      {
        id: "04.13", name: "Retail and consumer goods",
        keywords: ["retail", "consumer spending", "sales", "store", "brand", "e-commerce", "consumer", "FMCG", "grocery", "department store", "outlet", "fashion retail"],
        prompt: "Assign this category to articles about retail businesses and consumer goods. Include retail sales, brand performance, store openings and closures, and consumer spending trends. Exclude fashion as culture (use Fashion and beauty).",
      },
      {
        id: "04.14", name: "Startups and entrepreneurship",
        keywords: ["startup", "founder", "funding", "venture capital", "unicorn", "accelerator", "pitch", "growth stage", "Y Combinator", "entrepreneur", "scale-up"],
        prompt: "Assign this category to articles about startups and the entrepreneurship ecosystem. Include early-stage companies, founder stories, fundraising rounds, accelerators, and unicorn valuations. Exclude later-stage private equity (use Private equity and venture capital).",
      },
      {
        id: "04.15", name: "Trade and tariffs",
        keywords: ["tariff", "trade", "import", "export", "trade war", "WTO", "trade deficit", "customs", "trade deal", "free trade", "protectionism", "supply chain"],
        prompt: "Assign this category to articles about international trade and tariff policy. Include trade agreements, tariff impositions, trade deficits, and WTO disputes.",
      },
      {
        id: "04.16", name: "Transport and logistics",
        keywords: ["shipping", "logistics", "supply chain", "freight", "port", "container", "airline", "trucking", "rail freight", "warehouse", "last mile"],
        prompt: "Assign this category to articles about the commercial transport and logistics sector. Include shipping rates, port congestion, logistics companies, and freight markets. Exclude passenger transport news (use the relevant sport or disaster subcategory).",
      },
    ],
  },
  {
    id: "05",
    name: "Education",
    color: "#84cc16",
    keywords: ["education", "school", "university", "students", "learning", "curriculum", "teacher", "campus", "degree", "academic", "teaching"],
    prompt: "Assign this category to articles about education at all levels. Include schools, universities, educational policy, and the education sector. Use the most specific subcategory available.",
    children: [
      {
        id: "05.01", name: "Higher education and universities",
        keywords: ["university", "college", "tuition", "degree", "enrollment", "campus", "research university", "student loans", "graduation", "faculty", "academic"],
        prompt: "Assign this category to articles about universities, colleges, and higher education. Include admissions, tuition costs, campus life, university research, and funding.",
      },
      {
        id: "05.02", name: "Online and digital learning",
        keywords: ["online learning", "MOOC", "EdTech", "Coursera", "e-learning", "digital education", "virtual classroom", "remote learning", "skills platform"],
        prompt: "Assign this category to articles about online and technology-enabled education. Include MOOC platforms, EdTech companies, and virtual learning environments.",
      },
      {
        id: "05.03", name: "School education",
        keywords: ["school", "K-12", "curriculum", "students", "teachers", "standardised testing", "charter school", "public school", "school funding", "classroom"],
        prompt: "Assign this category to articles about primary and secondary (K-12) school education. Include curricula, school funding, standardised testing, school choice, and teacher recruitment.",
      },
      {
        id: "05.04", name: "Teaching and pedagogy",
        keywords: ["teaching", "pedagogy", "classroom", "educational methods", "teacher training", "curriculum design", "assessment", "learning outcomes", "STEM"],
        prompt: "Assign this category to articles about teaching methods and educational practice. Include pedagogical approaches, teacher development, curriculum design, and learning outcomes research.",
      },
      {
        id: "05.05", name: "Vocational training",
        keywords: ["vocational", "apprenticeship", "trade school", "skills training", "workforce development", "certification", "technical education", "trades", "TVET"],
        prompt: "Assign this category to articles about vocational and technical education. Include apprenticeships, trade schools, skills training, and workforce development initiatives.",
      },
    ],
  },
  {
    id: "06",
    name: "Environment",
    color: "#22c55e",
    keywords: ["environment", "climate", "ecology", "nature", "conservation", "emissions", "pollution", "sustainability", "ecosystem", "biodiversity"],
    prompt: "Assign this category to articles about the natural environment and environmental issues. Include climate change, conservation, pollution, and ecosystem health. Use the most specific subcategory available.",
    children: [
      {
        id: "06.01", name: "Climate change",
        keywords: ["climate change", "global warming", "CO2", "emissions", "IPCC", "Paris Agreement", "temperature rise", "carbon budget", "net zero", "fossil fuels", "sea level"],
        prompt: "Assign this category to articles about climate change science, impacts, and policy. Include IPCC reports, emissions trajectories, climate negotiations, and adaptation. Exclude specific natural disasters (use Disaster subcategories) and energy industry news (use Energy subcategories).",
      },
      {
        id: "06.02", name: "Conservation and biodiversity",
        keywords: ["conservation", "biodiversity", "habitat", "species", "protected area", "WWF", "deforestation", "rewilding", "national park", "endangered", "wildlife corridor"],
        prompt: "Assign this category to articles about conservation and biodiversity. Include species protection, habitat preservation, rewilding, and protected area policy. Exclude general wildlife stories (use Wildlife and ecosystems).",
      },
      {
        id: "06.03", name: "Natural resources",
        keywords: ["natural resources", "water", "forests", "minerals", "land use", "deforestation", "mining", "groundwater", "fisheries", "timber"],
        prompt: "Assign this category to articles about the use and management of natural resources. Include water supply, forest management, mineral extraction, and sustainable resource policy.",
      },
      {
        id: "06.04",
        name: "Pollution",
        keywords: ["pollution", "contamination", "toxic", "waste", "discharge", "environmental damage", "clean-up", "health impact", "regulatory fine"],
        prompt: "Assign this category to articles about pollution and environmental contamination. Use a specific subcategory for air, water, or plastic pollution; assign the parent for multi-type or general pollution coverage.",
        children: [
          {
            id: "06.04.01", name: "Air quality and air pollution",
            keywords: ["air quality", "smog", "particulate matter", "PM2.5", "emissions", "WHO limits", "ozone", "NOx", "indoor air quality", "clean air"],
            prompt: "Assign this category to articles about air pollution and air quality. Include particulate matter, smog events, emissions standards, and health impacts. Exclude climate aspects of emissions (use Climate change).",
          },
          {
            id: "06.04.02", name: "Plastic and waste pollution",
            keywords: ["plastic", "waste", "recycling", "microplastics", "landfill", "ocean plastic", "single-use", "packaging", "circular economy", "e-waste"],
            prompt: "Assign this category to articles about plastic and solid waste pollution. Include ocean plastic, microplastic contamination, recycling failures, and policies to reduce single-use plastic.",
          },
          {
            id: "06.04.03", name: "Water pollution",
            keywords: ["water quality", "contamination", "runoff", "wastewater", "ocean pollution", "PFAS", "toxic spill", "drinking water", "algal bloom", "sewage"],
            prompt: "Assign this category to articles about water pollution and contamination. Include polluted waterways, drinking water safety, PFAS contamination, and wastewater management.",
          },
        ],
      },
      {
        id: "06.05", name: "Renewable energy and clean tech",
        keywords: ["solar", "wind", "renewable", "clean tech", "green energy", "transition", "battery", "EV", "electrification", "decarbonisation", "clean power"],
        prompt: "Assign this category to articles about renewable energy and clean technology from an environmental perspective. Include clean energy as a climate solution and the energy transition. Exclude industry business news (use Renewable energy under Economy).",
      },
      {
        id: "06.06", name: "Wildlife and ecosystems",
        keywords: ["wildlife", "species", "habitat", "coral reef", "biodiversity", "extinction", "animal", "ecosystem", "marine life", "migration", "poaching"],
        prompt: "Assign this category to articles about wildlife and natural ecosystems. Include animal populations, species decline, coral reef bleaching, and poaching. Exclude conservation policy (use Conservation and biodiversity).",
      },
    ],
  },
  {
    id: "07",
    name: "Health",
    color: "#06b6d4",
    keywords: ["health", "medicine", "disease", "treatment", "patient", "hospital", "doctor", "medical", "clinical", "public health", "healthcare"],
    prompt: "Assign this category to articles about human health, medicine, and healthcare. Include diseases, treatments, public health, and medical research. Use the most specific subcategory available.",
    children: [
      {
        id: "07.01", name: "Epidemics and pandemics",
        keywords: ["pandemic", "outbreak", "virus", "WHO", "epidemic", "infection", "transmission", "mortality", "quarantine", "contagion", "contact tracing"],
        prompt: "Assign this category to articles about infectious disease outbreaks and pandemics. Include disease spread, containment measures, pandemic preparedness, and the global health response.",
      },
      {
        id: "07.02", name: "Healthcare policy and access",
        keywords: ["healthcare reform", "health insurance", "universal healthcare", "NHS", "ACA", "Medicaid", "Medicare", "health spending", "coverage", "co-pay"],
        prompt: "Assign this category to articles about healthcare policy and access to care. Include health system reform, insurance coverage, healthcare costs, and universal health programmes. Exclude clinical medicine and research (use Medical research subcategories).",
      },
      {
        id: "07.03", name: "Healthcare technology and digital health",
        keywords: ["telehealth", "digital health", "wearables", "EHR", "health app", "AI diagnostics", "remote monitoring", "medical AI", "health tech", "FDA software"],
        prompt: "Assign this category to articles about technology applied to healthcare delivery. Include telemedicine, digital health apps, AI diagnostics, electronic health records, and wearable health devices.",
      },
      {
        id: "07.04",
        name: "Medical research",
        keywords: ["medical research", "study", "findings", "journal", "researcher", "breakthrough", "discovery", "clinical", "trial", "peer-reviewed"],
        prompt: "Assign this category to articles about medical and biomedical research. Include research findings and scientific advances in medicine. Use a specific subcategory where available. Exclude pharmaceutical business news (use Pharmaceutical industry).",
        children: [
          {
            id: "07.04.01", name: "Cancer research",
            keywords: ["cancer", "tumour", "oncology", "immunotherapy", "chemotherapy", "trials", "remission", "metastatic", "carcinoma", "targeted therapy"],
            prompt: "Assign this category to articles about cancer research and oncology. Include cancer biology findings, immunotherapy breakthroughs, and clinical trial results for cancer treatments.",
          },
          {
            id: "07.04.02", name: "Drug development and clinical trials",
            keywords: ["clinical trial", "FDA", "phase 3", "drug approval", "efficacy", "placebo", "double-blind", "EMA", "regulatory approval", "primary endpoint"],
            prompt: "Assign this category to articles about clinical drug development and testing. Include trial results, regulatory approval processes, and efficacy data. Exclude commercial pharma news (use Pharmaceutical industry).",
          },
          {
            id: "07.04.03", name: "Genetics and genomics",
            keywords: ["CRISPR", "gene therapy", "genomics", "DNA", "sequencing", "genetic disorder", "gene editing", "RNA", "mutation", "epigenetics"],
            prompt: "Assign this category to articles about genetics and genomic medicine. Include gene editing research, sequencing studies, and genetic disease research.",
          },
          {
            id: "07.04.04", name: "Medical devices and diagnostics",
            keywords: ["medical device", "diagnostic", "imaging", "MRI", "ultrasound", "biomarker", "wearable", "implant", "prosthetic", "FDA clearance"],
            prompt: "Assign this category to articles about medical devices and diagnostic tools. Include diagnostic technologies, device approvals, imaging advances, and surgical tools.",
          },
          {
            id: "07.04.05", name: "Neuroscience and brain research",
            keywords: ["neuroscience", "brain", "Alzheimer's", "Parkinson's", "neural", "cognitive", "synapse", "neurodegeneration", "brain imaging", "dementia"],
            prompt: "Assign this category to articles about neuroscience and brain health research. Include brain biology discoveries, neurological disease research, and cognitive science findings.",
          },
        ],
      },
      {
        id: "07.05", name: "Mental health and psychiatry",
        keywords: ["mental health", "depression", "anxiety", "psychiatry", "therapy", "suicide prevention", "wellbeing", "burnout", "trauma", "PTSD", "mental illness"],
        prompt: "Assign this category to articles about mental health, psychiatric conditions, and psychological wellbeing. Include mental illness prevalence, treatment approaches, and mental health policy.",
      },
      {
        id: "07.06", name: "Nutrition and fitness",
        keywords: ["nutrition", "diet", "obesity", "exercise", "fitness", "public health", "food safety", "calorie", "metabolic", "weight", "physical activity"],
        prompt: "Assign this category to articles about nutrition, diet, and physical fitness. Include dietary research, obesity trends, fitness culture, and food safety guidance. Exclude food as culture (use Food and drink).",
      },
      {
        id: "07.07", name: "Pharmaceutical drugs",
        keywords: ["drug", "medication", "FDA approval", "generic", "patent", "side effects", "pharmacology", "dosage", "prescription", "OTC", "drug safety"],
        prompt: "Assign this category to articles about specific pharmaceutical drugs as medical interventions. Include drug approvals, safety signals, side effects, and access to medications. Exclude pharma company business (use Pharmaceutical industry).",
      },
      {
        id: "07.08", name: "Public health",
        keywords: ["public health", "prevention", "vaccination", "epidemiology", "disease control", "CDC", "screening", "health promotion", "immunisation", "health disparity"],
        prompt: "Assign this category to articles about public health measures and population health. Include vaccination programmes, disease surveillance, health promotion campaigns, and public health infrastructure.",
      },
    ],
  },
  {
    id: "08",
    name: "Human interest",
    color: "#fb923c",
    keywords: ["human interest", "personal story", "community", "inspiring", "unusual", "heartwarming", "social", "profile", "people"],
    prompt: "Assign this category to articles whose primary appeal is a human subject or story rather than a news event. Include personal profiles, community stories, and heartwarming or unusual accounts.",
    children: [
      {
        id: "08.01", name: "Animals",
        keywords: ["animal", "pet", "wildlife rescue", "zoo", "veterinary", "animal welfare", "dog", "cat", "exotic animal", "animal sanctuary", "RSPCA"],
        prompt: "Assign this category to articles about animals in a human-interest context. Include pet stories, animal rescue, zoo animals, and animal welfare. Exclude conservation and ecology (use Wildlife and ecosystems or Conservation and biodiversity).",
      },
      {
        id: "08.02", name: "Celebrity and public figures",
        keywords: ["celebrity", "star", "actor", "musician", "social media star", "fame", "public figure", "tabloid", "red carpet", "personal life", "gossip"],
        prompt: "Assign this category to articles about celebrities' personal lives. Include relationships, controversies, and public appearances. Exclude professional work coverage (use the relevant arts subcategory).",
      },
      {
        id: "08.03", name: "People and profiles",
        keywords: ["profile", "interview", "biography", "human story", "personal journey", "feature", "portrait", "life story", "community", "ordinary people"],
        prompt: "Assign this category to articles profiling individuals or telling human stories. Include in-depth profiles, personal journeys, and community feature stories.",
      },
      {
        id: "08.04", name: "Royalty and nobility",
        keywords: ["royal family", "monarchy", "King", "Queen", "palace", "coronation", "royal wedding", "heir", "duchess", "prince", "succession"],
        prompt: "Assign this category to articles about royal families and monarchies. Include royal events, succession, state occasions, and the institution of monarchy.",
      },
    ],
  },
  {
    id: "09",
    name: "Labour and employment",
    color: "#8b5cf6",
    keywords: ["labour", "employment", "jobs", "workers", "wages", "workforce", "hiring", "unemployment", "union", "workplace"],
    prompt: "Assign this category to articles about labour markets, employment, and worker rights. Include jobs data, wages, unions, and workplace issues. Use the most specific subcategory available.",
    children: [
      {
        id: "09.01", name: "Employment and jobs",
        keywords: ["jobs", "unemployment", "hiring", "workforce", "employment rate", "layoffs", "job market", "payroll", "labour market", "job creation", "redundancy"],
        prompt: "Assign this category to articles about the jobs market and employment conditions. Include jobs reports, unemployment rates, hiring trends, and mass layoffs.",
      },
      {
        id: "09.02", name: "Labour relations and disputes",
        keywords: ["strike", "labor dispute", "industrial action", "collective bargaining", "walkout", "lockout", "union negotiation", "contract dispute", "work-to-rule"],
        prompt: "Assign this category to articles about disputes between workers and employers. Include strikes, lockouts, and collective bargaining negotiations.",
      },
      {
        id: "09.03", name: "Trade unions",
        keywords: ["union", "AFL-CIO", "trade union", "workers' rights", "collective agreement", "union membership", "union election", "organising", "TUC"],
        prompt: "Assign this category to articles about trade unions as organisations. Include union membership, elections, organising campaigns, and unions' political role. Exclude specific labour disputes (use Labour relations and disputes).",
      },
      {
        id: "09.04", name: "Wages, benefits and pensions",
        keywords: ["wages", "salary", "minimum wage", "benefits", "pension", "retirement", "pay gap", "compensation", "bonus", "living wage", "pay rise"],
        prompt: "Assign this category to articles about worker pay, benefits, and retirement. Include minimum wage debates, pay gaps, pension performance, and executive compensation.",
      },
      {
        id: "09.05", name: "Working conditions",
        keywords: ["working conditions", "workplace safety", "remote work", "hours", "ergonomics", "burnout", "gig economy", "contractor", "four-day week", "OSHA"],
        prompt: "Assign this category to articles about working conditions. Include workplace safety, remote work, working hours, the gig economy, and worker wellbeing.",
      },
    ],
  },
  {
    id: "10",
    name: "Lifestyle and leisure",
    color: "#10b981",
    keywords: ["lifestyle", "leisure", "hobby", "travel", "food", "home", "wellness", "consumer", "trend", "culture", "recreation"],
    prompt: "Assign this category to articles about lifestyle, leisure, and consumer culture. Include food, travel, home, and hobbies. Use the most specific subcategory available.",
    children: [
      {
        id: "10.01", name: "Food and drink",
        keywords: ["food", "restaurant", "cuisine", "chef", "recipe", "dining", "beverage", "culinary trend", "Michelin", "cocktail", "wine", "food culture"],
        prompt: "Assign this category to articles about food, drink, and dining culture. Include restaurant news, chef profiles, culinary trends, and food reviews. Exclude food production economics (use Agriculture and food industry) and food safety as public health (use Public health).",
      },
      {
        id: "10.02", name: "Hobbies and crafts",
        keywords: ["hobby", "crafts", "DIY", "collecting", "gardening", "model making", "knitting", "woodworking", "amateur", "pastime", "leisure activity"],
        prompt: "Assign this category to articles about hobbies and craft activities. Include DIY, collecting communities, gardening, and specialist leisure pursuits.",
      },
      {
        id: "10.03", name: "Home and living",
        keywords: ["home", "interior design", "renovation", "decoration", "furniture", "home improvement", "architecture", "living space", "smart home"],
        prompt: "Assign this category to articles about the home as a living space. Include interior design, home renovation, decoration trends, furniture, and smart home technology. Exclude real estate investment and property markets (use Real estate (04.13)).",
      },
      {
        id: "10.04", name: "Outdoor activities",
        keywords: ["hiking", "camping", "adventure", "outdoor", "nature", "trail", "climbing", "kayaking", "cycling leisure", "birdwatching", "orienteering"],
        prompt: "Assign this category to articles about outdoor recreation and adventure activities. Include hiking, camping, rock climbing, kayaking, cycling for leisure, and birdwatching. Exclude professional and competitive sport (use Sport (15)).",
      },
      {
        id: "10.05", name: "Shopping and consumer trends",
        keywords: ["shopping", "consumer", "retail trend", "brand", "product launch", "Black Friday", "deal", "luxury goods", "consumer behaviour", "impulse buy"],
        prompt: "Assign this category to articles about consumer shopping behaviour and retail trends. Include consumer spending patterns, seasonal shopping events, brand preferences, and the lifestyle side of consumer culture. Exclude retail industry business operations (use Retail (04.14)).",
      },
      {
        id: "10.06", name: "Travel and tourism",
        keywords: ["travel", "tourism", "destination", "hotel", "flight", "passport", "tourism industry", "vacation", "backpacking", "cruise", "resort", "visa"],
        prompt: "Assign this category to articles about travel and tourism as a consumer experience. Include travel destinations, hotel and airline reviews, travel tips, visa requirements, and tourism trends. Exclude airline and transport business news (use Transportation (04.17)) and travel disruption from disasters (use Disaster, accident and emergency (03)).",
      },
    ],
  },
  {
    id: "11",
    name: "Politics",
    color: "#f43f5e",
    keywords: ["politics", "government", "policy", "election", "parliament", "congress", "minister", "legislation", "political", "power", "diplomacy"],
    prompt: "Assign this category to articles about politics, government, and public policy. Include elections, legislation, government decisions, international relations, and regulatory affairs. Assign for general political coverage; use subcategories for specific topics.",
    children: [
      {
        id: "11.01",
        name: "Defence and military policy",
        keywords: ["defence", "military", "armed forces", "defence budget", "NATO", "security", "strategy", "deterrence", "army", "navy", "air force"],
        prompt: "Assign this category to articles about defence policy and military affairs outside of active conflict. Include defence budgets, military strategy, arms procurement, and security alliances. Exclude active warfare and military operations (use Conflict, war and peace (16)).",
        children: [
          {
            id: "11.01.01", name: "Arms and weapons programmes",
            keywords: ["arms", "weapons", "missile", "nuclear weapons", "defence contract", "military spending", "arms race", "ICBM", "fighter jet", "procurement"],
            prompt: "Assign this category to articles about weapons development and arms control policy. Include nuclear weapons programmes, conventional arms procurement, missile systems, defence contracts, and arms control treaties.",
          },
          {
            id: "11.01.02", name: "Intelligence and espionage",
            keywords: ["intelligence", "CIA", "NSA", "espionage", "spy", "surveillance", "classified", "intelligence agency", "counterintelligence", "GCHQ", "signals intelligence"],
            prompt: "Assign this category to articles about intelligence services and espionage. Include intelligence agency activities, spy operations, signals intelligence, surveillance programmes, and counterintelligence. Exclude cybercrime and criminal hacking (use Cybercrime (02.02.01)).",
          },
          {
            id: "11.01.03", name: "Military technology",
            keywords: ["drone", "military tech", "stealth", "defence technology", "autonomous weapons", "satellite", "defence contractor", "AI warfare", "hypersonic"],
            prompt: "Assign this category to articles about technology developed for military applications. Include military drones, autonomous weapons systems, stealth technology, satellite surveillance, and defence technology research and procurement.",
          },
        ],
      },
      {
        id: "11.02",
        name: "Domestic politics",
        keywords: ["domestic politics", "government", "party", "politician", "poll", "cabinet", "prime minister", "president", "administration", "opposition"],
        prompt: "Assign this category to articles about politics within a single country. Include government decisions, political party affairs, and domestic political events. Exclude elections (use Elections and voting (11.02.01)), legislation (use Legislation and lawmaking (11.02.03)), and international relations (use International relations and diplomacy (11.03)).",
        children: [
          {
            id: "11.02.01", name: "Elections and voting",
            keywords: ["election", "vote", "ballot", "campaign", "polling", "candidate", "electoral", "constituency", "swing state", "primary", "turnout"],
            prompt: "Assign this category to articles about elections and the democratic process. Include electoral campaigns, polling, results, voter turnout, and debates over electoral systems.",
          },
          {
            id: "11.02.02", name: "Government and governance",
            keywords: ["government", "cabinet", "administration", "official", "minister", "policy", "decree", "governance", "accountability", "civil service"],
            prompt: "Assign this category to articles about the operation of government. Include cabinet decisions, policy announcements, government appointments, and the functioning of public institutions.",
          },
          {
            id: "11.02.03", name: "Legislation and lawmaking",
            keywords: ["legislation", "bill", "law", "Congress", "parliament", "vote", "amendment", "filibuster", "Senate", "debate", "committee", "statute"],
            prompt: "Assign this category to articles about the legislative process. Include bills moving through parliament or congress, parliamentary debates, amendments, and the passage or defeat of legislation. Exclude law enforcement (use Crime, law and justice (02)).",
          },
          {
            id: "11.02.04", name: "Political parties and movements",
            keywords: ["political party", "Democrat", "Republican", "coalition", "populism", "movement", "manifesto", "party leadership", "far right", "progressive"],
            prompt: "Assign this category to articles about political parties and ideological movements. Include party leadership contests, manifestos, intra-party dynamics, populist movements, and political ideology debates.",
          },
        ],
      },
      {
        id: "11.03",
        name: "International relations and diplomacy",
        keywords: ["international relations", "diplomacy", "foreign minister", "summit", "geopolitics", "bilateral", "multilateral", "global governance", "UN"],
        prompt: "Assign this category to articles about relations between countries and international diplomacy. Include summits, diplomatic talks, and international agreements. Exclude trade disputes (use International trade (04.04)), sanctions (use Sanctions and trade restrictions (11.03.04)), and active military conflict (use Conflict, war and peace (16)).",
        children: [
          {
            id: "11.03.01", name: "Alliances and multilateral organizations",
            keywords: ["NATO", "UN", "EU", "G7", "G20", "multilateral", "alliance", "bloc", "ASEAN", "AU", "international body", "treaty organisation"],
            prompt: "Assign this category to articles about international alliances and multilateral organisations. Include NATO, the UN, the EU, and other international bodies — their decisions, membership, and internal politics. Exclude bilateral diplomatic relations (use Bilateral diplomacy (11.03.02)).",
          },
          {
            id: "11.03.02", name: "Bilateral diplomacy",
            keywords: ["bilateral talks", "summit", "envoy", "ambassador", "diplomatic relations", "state visit", "foreign secretary", "consulate", "embassy"],
            prompt: "Assign this category to articles about diplomatic relations between two specific countries. Include state visits, bilateral summits, ambassadorial appointments, and the state of relations between two nations.",
          },
          {
            id: "11.03.03", name: "Foreign policy",
            keywords: ["foreign policy", "State Department", "foreign minister", "strategic interests", "geopolitical", "influence", "soft power", "doctrine", "national interest"],
            prompt: "Assign this category to articles about a country's foreign policy strategy. Include the foreign policy goals of major powers, shifts in strategic priorities, and the doctrinal frameworks guiding a state's international behaviour.",
          },
          {
            id: "11.03.04", name: "Sanctions and trade restrictions",
            keywords: ["sanctions", "export controls", "ban", "blacklist", "OFAC", "trade restriction", "asset freeze", "entity list", "embargo", "designation"],
            prompt: "Assign this category to articles about economic sanctions and export controls. Include sanctions imposed on countries, companies, or individuals, export control rules, and their economic and political effects.",
          },
        ],
      },
      {
        id: "11.04",
        name: "Regulation and policy",
        keywords: ["regulation", "regulator", "policy", "rule", "compliance", "enforcement", "watchdog", "agency", "framework", "directive"],
        prompt: "Assign this category to articles about government regulation across sectors. Include new rules, regulatory enforcement actions, and regulatory policy debates. Exclude environmental (use Environmental regulation (11.04.03)), financial (use Financial regulation (11.04.04)), and technology regulation (use Technology regulation (11.04.05)).",
        children: [
          {
            id: "11.04.01", name: "Antitrust and competition law",
            keywords: ["antitrust", "competition", "monopoly", "FTC", "DOJ", "cartel", "market power", "merger review", "consumer welfare", "dominant position", "CMA"],
            prompt: "Assign this category to articles about antitrust enforcement and competition policy. Include investigations into monopolistic behaviour, merger reviews by competition authorities, cartel enforcement, and debates over market power in digital markets.",
          },
          {
            id: "11.04.02", name: "Data protection and privacy",
            keywords: ["GDPR", "privacy", "data protection", "personal data", "consent", "ICO", "CCPA", "data regulator", "surveillance", "tracking", "biometric"],
            prompt: "Assign this category to articles about data privacy regulation and policy. Include GDPR enforcement, new privacy laws, data protection authority actions, and consumer privacy rights.",
          },
          {
            id: "11.04.03", name: "Environmental regulation",
            keywords: ["emissions standards", "environmental law", "EPA", "carbon tax", "green deal", "environmental permit", "pollution limit", "ETS", "climate regulation"],
            prompt: "Assign this category to articles about environmental law and regulation. Include emissions standards, environmental impact assessments, pollution limits, carbon pricing mechanisms, and regulatory frameworks for environmental protection.",
          },
          {
            id: "11.04.04", name: "Financial regulation",
            keywords: ["financial regulation", "SEC", "banking regulation", "Basel", "capital requirements", "systemic risk", "stress test", "prudential", "FCA", "consumer protection"],
            prompt: "Assign this category to articles about financial sector regulation. Include banking supervision, securities regulation, capital requirements, and the actions of financial regulators like the SEC, FCA, and banking supervisory authorities.",
          },
          {
            id: "11.04.05", name: "Technology regulation",
            keywords: ["AI regulation", "tech regulation", "EU AI Act", "content moderation", "digital markets", "platform accountability", "algorithmic regulation", "DSA", "DMA"],
            prompt: "Assign this category to articles about the regulation of technology companies and digital platforms. Include AI regulation, platform content moderation rules, digital market laws, and the governance of big tech companies.",
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
    prompt: "Assign this category to articles about religion, faith, and religious communities. Include religious events, institutions, theology, and the role of religion in public life. Assign for cross-religious coverage; use subcategories for specific faiths.",
    children: [
      {
        id: "12.01", name: "Buddhism",
        keywords: ["Buddhism", "Buddhist", "meditation", "monk", "temple", "Dalai Lama", "dharma", "nirvana", "sangha", "Tibetan", "Zen", "monastery"],
        prompt: "Assign this category to articles about Buddhism and Buddhist communities. Include Buddhist institutions, practices, the Dalai Lama, and news involving Buddhist communities around the world.",
      },
      {
        id: "12.02", name: "Christianity",
        keywords: ["Christianity", "church", "Pope", "Vatican", "Catholic", "Protestant", "evangelical", "faith", "diocese", "synod", "bishop", "pastor"],
        prompt: "Assign this category to articles about Christianity and Christian institutions. Include the Catholic Church, Protestant denominations, evangelical movements, the Vatican, and news involving Christian communities globally.",
      },
      {
        id: "12.03", name: "Hinduism",
        keywords: ["Hinduism", "Hindu", "temple", "festival", "caste", "Diwali", "yoga", "Sanskrit", "vedic", "mandir", "puja"],
        prompt: "Assign this category to articles about Hinduism and Hindu communities. Include Hindu religious practice, festivals, temple affairs, and news involving Hindu communities, including caste-related religious dimensions.",
      },
      {
        id: "12.04", name: "Islam",
        keywords: ["Islam", "Muslim", "mosque", "Quran", "Ramadan", "Sharia", "imam", "hajj", "ummah", "fatwa", "halal", "Sunni", "Shia"],
        prompt: "Assign this category to articles about Islam and Muslim communities. Include Islamic institutions, religious practice, major events like Ramadan and Hajj, and news involving Muslim communities around the world.",
      },
      {
        id: "12.05", name: "Judaism",
        keywords: ["Judaism", "Jewish", "synagogue", "Torah", "rabbi", "Passover", "Shabbat", "antisemitism", "kosher", "orthodox", "Jewish community"],
        prompt: "Assign this category to articles about Judaism and Jewish communities. Include Jewish religious practice, synagogue affairs, major festivals, and news involving Jewish communities globally. Exclude antisemitism as a political or human rights issue (use Human rights and civil liberties (14.03)).",
      },
      {
        id: "12.06", name: "Religious freedom and secularism",
        keywords: ["religious freedom", "secularism", "blasphemy", "church-state", "minority rights", "persecution", "apostasy", "faith school", "separation"],
        prompt: "Assign this category to articles about religious freedom and the relationship between religion and the state. Include persecution of religious minorities, blasphemy laws, church-state separation, and secularist debates.",
      },
    ],
  },
  {
    id: "13",
    name: "Science and technology",
    color: "#3b82f6",
    keywords: ["science", "research", "discovery", "study", "findings", "scientists", "laboratory", "experiment", "academic", "breakthrough", "technology"],
    prompt: "Assign this category to articles about scientific research and technological development. Include discoveries, research findings, and advances across all scientific disciplines. Exclude commercial technology products and companies (use Economy, business and finance (04)).",
    children: [
      {
        id: "13.01",
        name: "Astronomy and space science",
        keywords: ["astronomy", "space", "telescope", "galaxy", "star", "universe", "cosmology", "exoplanet", "nebula", "black hole", "observation"],
        prompt: "Assign this category to articles about astronomy and space science. Include astronomical discoveries and observations. Exclude commercial space companies (use Commercial space industry (13.01.01)), planetary science (use Planetary science (13.01.02)), specific missions (use Space exploration and missions (13.01.03)), and telescope findings (use Telescopes and astronomical observation (13.01.04)).",
        children: [
          {
            id: "13.01.01", name: "Commercial space industry",
            keywords: ["SpaceX", "Blue Origin", "Rocket Lab", "launch", "satellite", "commercial space", "reusable rocket", "Starship", "smallsat", "launch vehicle"],
            prompt: "Assign this category to articles about the commercial space industry. Include private launch companies, satellite constellations, commercial space stations, and the business of space. Exclude government-led space exploration (use Space exploration and missions (13.01.03)).",
          },
          {
            id: "13.01.02", name: "Planetary science",
            keywords: ["Mars", "Moon", "planetary", "NASA probe", "exoplanet", "solar system", "atmosphere", "surface", "geology", "rover", "orbit"],
            prompt: "Assign this category to articles about the scientific study of planets, moons, and other solar system bodies. Include rover findings, atmospheric studies, exoplanet characterisation, and planetary geology.",
          },
          {
            id: "13.01.03", name: "Space exploration and missions",
            keywords: ["NASA", "ESA", "mission", "astronaut", "space station", "ISS", "lunar", "Mars mission", "crew", "spacewalk", "launch"],
            prompt: "Assign this category to articles about crewed and robotic space exploration missions. Include mission planning, launches, in-flight events, and scientific returns from specific missions.",
          },
          {
            id: "13.01.04", name: "Telescopes and astronomical observation",
            keywords: ["telescope", "James Webb", "Hubble", "observation", "galaxy", "black hole", "nebula", "infrared", "radio telescope", "imaging", "spectrum"],
            prompt: "Assign this category to articles about telescopes and astronomical observations. Include new telescope capabilities, images released by observatories, and discoveries made through direct observation. Exclude discoveries from space missions (use Space exploration and missions (13.01.03)).",
          },
        ],
      },
      {
        id: "13.02",
        name: "Biology and life sciences",
        keywords: ["biology", "life sciences", "organism", "cell", "species", "evolutionary", "biological", "living", "flora", "fauna"],
        prompt: "Assign this category to articles about biology and the life sciences. Include research into living organisms across scales from cells to ecosystems. Exclude ecology (use Ecology and environmental biology (13.02.01)), evolution (use Evolution and palaeontology (13.02.02)), genetics (use Genetics and genomics (13.02.03)), and microbiology (use Microbiology and virology (13.02.04)).",
        children: [
          {
            id: "13.02.01", name: "Ecology and environmental biology",
            keywords: ["ecology", "ecosystem", "habitat", "species interaction", "food web", "biodiversity research", "population biology", "invasive species"],
            prompt: "Assign this category to articles about ecology and the scientific study of ecosystems. Include research into species interactions, population dynamics, ecosystem services, and the biological effects of environmental change.",
          },
          {
            id: "13.02.02", name: "Evolution and palaeontology",
            keywords: ["evolution", "fossil", "palaeontology", "species", "natural selection", "Darwin", "phylogeny", "prehistoric", "dinosaur", "hominid", "ancestry"],
            prompt: "Assign this category to articles about evolution and the fossil record. Include palaeontological discoveries, evolutionary biology research, human origins, and findings about prehistoric life.",
          },
          {
            id: "13.02.03", name: "Genetics and genomics",
            keywords: ["genetics", "genomics", "DNA", "gene", "sequencing", "CRISPR", "protein", "mutation", "genome", "epigenetics", "hereditary"],
            prompt: "Assign this category to articles about genetics and genomics research. Include genome sequencing studies, genetic discovery, CRISPR research, and the genetics of disease and evolution. Exclude clinical gene therapy applications (use Medical research (07.04)).",
          },
          {
            id: "13.02.04", name: "Microbiology and virology",
            keywords: ["virus", "bacteria", "microbe", "pathogen", "infection", "antibiotic", "microbiology", "fungus", "antimicrobial resistance", "bacteriophage"],
            prompt: "Assign this category to articles about microbiology and virology research. Include the study of viruses, bacteria, and other microorganisms, including antimicrobial resistance research. Exclude disease outbreaks (use Epidemics and pandemics (07.01)).",
          },
        ],
      },
      {
        id: "13.03", name: "Chemistry and materials science",
        keywords: ["chemistry", "materials science", "polymer", "compound", "synthesis", "catalyst", "battery chemistry", "superconductor", "alloy", "molecule"],
        prompt: "Assign this category to articles about chemistry and materials science research. Include novel compounds, materials discoveries, catalysis research, battery chemistry advances, and superconducting materials.",
      },
      {
        id: "13.04",
        name: "Computer science and AI",
        keywords: ["computer science", "algorithm", "AI research", "machine learning", "neural network", "deep learning", "research paper", "benchmark", "model architecture"],
        prompt: "Assign this category to articles about computer science and AI as academic disciplines. Include research papers, algorithmic advances, and scientific progress in computation and intelligence. Exclude commercial AI products and services (use Artificial intelligence (04.03.01)).",
        children: [
          {
            id: "13.04.01", name: "Algorithms and data science",
            keywords: ["algorithm", "machine learning", "data science", "neural network", "optimisation", "computational complexity", "data analysis", "model training"],
            prompt: "Assign this category to articles about algorithmic research and data science methods. Include novel algorithms, machine learning methodology, statistical methods, and computational approaches to problem-solving.",
          },
          {
            id: "13.04.02", name: "Artificial intelligence research",
            keywords: ["AI research", "deep learning", "foundation model", "AI safety", "alignment", "benchmark", "model architecture", "transformer", "reinforcement learning"],
            prompt: "Assign this category to articles about academic and research advances in artificial intelligence. Include new model architectures, benchmark results, AI safety research, and scientific understanding of machine learning. Exclude commercial AI products and deployments (use Artificial intelligence (04.03.01)).",
          },
          {
            id: "13.04.03", name: "Natural language processing",
            keywords: ["NLP", "language model", "text generation", "speech recognition", "translation", "sentiment analysis", "language understanding", "tokenisation"],
            prompt: "Assign this category to articles about natural language processing research. Include advances in language understanding, machine translation, speech recognition, and text generation from a scientific or academic perspective.",
          },
          {
            id: "13.04.04", name: "Quantum computing",
            keywords: ["quantum computing", "qubit", "quantum advantage", "error correction", "quantum algorithm", "decoherence", "gate fidelity", "quantum processor"],
            prompt: "Assign this category to articles about quantum computing research. Include qubit technologies, quantum error correction, demonstrations of quantum advantage, and the scientific challenges of building reliable quantum computers.",
          },
          {
            id: "13.04.05", name: "Robotics and automation",
            keywords: ["robot", "automation", "humanoid", "autonomous", "industrial robot", "ROS", "manipulator", "locomotion", "swarm robotics", "drone research"],
            prompt: "Assign this category to articles about robotics and automation research. Include robot design, autonomous systems, humanoid robot research, swarm robotics, and scientific advances in perception and actuation.",
          },
        ],
      },
      {
        id: "13.05", name: "Earth and climate science",
        keywords: ["climate science", "geology", "oceanography", "atmospheric", "carbon cycle", "sea level", "glaciology", "geophysics", "earth system", "seismology"],
        prompt: "Assign this category to articles about Earth science and climate research. Include geological research, oceanographic studies, atmospheric science, and the scientific understanding of Earth's systems. Exclude climate policy and environmental politics (use Climate change (06.01)).",
      },
      {
        id: "13.06", name: "Mathematics and statistics",
        keywords: ["mathematics", "theorem", "statistics", "probability", "topology", "number theory", "proof", "conjecture", "fields medal", "mathematical", "algebra"],
        prompt: "Assign this category to articles about mathematical research and statistics. Include new proofs, mathematical conjectures, Fields Medal awards, and advances in pure and applied mathematics.",
      },
      {
        id: "13.07", name: "Medicine and biomedical research",
        keywords: ["biomedical", "clinical research", "drug discovery", "pathology", "pharmacology", "physiology", "translational", "preclinical", "mechanism", "biomarker"],
        prompt: "Assign this category to articles about biomedical research bridging basic science and clinical medicine. Include drug discovery science, disease mechanisms, preclinical research, and scientific findings not yet in clinical trials. Exclude clinical trials and medical treatments (use Medical research (07.04)).",
      },
      {
        id: "13.08",
        name: "Physics",
        keywords: ["physics", "theory", "experiment", "measurement", "force", "energy", "matter", "observation", "theoretical", "condensed matter"],
        prompt: "Assign this category to articles about physics research. Include experimental and theoretical advances across physics disciplines. Exclude particle physics (use Particle physics (13.08.02)), nuclear physics and fusion (use Nuclear physics and fusion energy (13.08.01)), and quantum physics (use Quantum physics (13.08.03)).",
        children: [
          {
            id: "13.08.01", name: "Nuclear physics and fusion energy",
            keywords: ["fusion", "nuclear reaction", "ITER", "plasma", "tokamak", "fission", "nuclear energy research", "inertial confinement", "deuterium", "tritium"],
            prompt: "Assign this category to articles about nuclear physics and fusion energy research. Include nuclear reactions, plasma physics, fusion milestone achievements, and scientific progress at facilities like ITER and NIF. Exclude nuclear power plants and commercial reactors (use Nuclear energy (04.05.02)).",
          },
          {
            id: "13.08.02", name: "Particle physics and high-energy physics",
            keywords: ["particle physics", "CERN", "Higgs boson", "collider", "quarks", "LHC", "standard model", "dark matter", "boson", "lepton", "detector"],
            prompt: "Assign this category to articles about particle physics and high-energy experiments. Include results from particle colliders, discoveries of new particles or forces, and advances in understanding the fundamental constituents of matter.",
          },
          {
            id: "13.08.03", name: "Quantum physics",
            keywords: ["quantum mechanics", "entanglement", "superposition", "wave function", "quantum field theory", "quantum optics", "Bose-Einstein", "decoherence"],
            prompt: "Assign this category to articles about quantum physics research. Include experimental tests of quantum mechanics, quantum entanglement demonstrations, quantum field theory advances, and foundational questions in quantum physics.",
          },
        ],
      },
      {
        id: "13.09", name: "Research policy and funding",
        keywords: ["research funding", "grant", "NSF", "peer review", "open access", "academic publishing", "research policy", "science budget", "citation", "preprint"],
        prompt: "Assign this category to articles about science policy, research funding, and academic publishing. Include government science budgets, grant agency decisions, open access debates, peer review integrity, and the institutional structures of research.",
      },
    ],
  },
  {
    id: "14",
    name: "Society",
    color: "#64748b",
    keywords: ["society", "social", "community", "culture", "people", "demographic", "inequality", "rights", "urban", "population", "trend"],
    prompt: "Assign this category to articles about social issues, demographic trends, and the organisation of society. Include human rights, social movements, inequality, and cultural and demographic change. Assign for general social coverage; use subcategories for specific topics.",
    children: [
      {
        id: "14.01", name: "Demographics and population",
        keywords: ["population", "birth rate", "aging", "demographics", "census", "migration", "fertility", "urbanisation", "mortality", "life expectancy", "population growth"],
        prompt: "Assign this category to articles about demographic trends and population data. Include birth rates, aging populations, migration patterns, census findings, and long-term demographic shifts.",
      },
      {
        id: "14.02", name: "Family and relationships",
        keywords: ["family", "marriage", "divorce", "parenting", "childcare", "domestic", "household", "single parent", "fertility", "adoption", "cohabitation"],
        prompt: "Assign this category to articles about family structures and personal relationships. Include marriage, divorce, parenting trends, childcare, and changing family forms as social phenomena.",
      },
      {
        id: "14.03", name: "Human rights and civil liberties",
        keywords: ["human rights", "civil rights", "freedom", "discrimination", "LGBTQ+", "racism", "rights", "liberty", "ACLU", "Amnesty", "UN rights body"],
        prompt: "Assign this category to articles about human rights and civil liberties. Include rights abuses, discrimination, LGBTQ+ rights, racial justice, and the work of human rights organisations.",
      },
      {
        id: "14.04", name: "Immigration and refugees",
        keywords: ["immigration", "refugee", "asylum", "border", "migration", "deportation", "visa", "undocumented", "displacement", "migrant", "UNHCR"],
        prompt: "Assign this category to articles about immigration and refugee issues. Include migration flows, asylum processes, border crossings, refugee crises, and immigration policy debates. Exclude trade flows (use International trade (04.04)) and diplomatic policy (use International relations and diplomacy (11.03)).",
      },
      {
        id: "14.05", name: "Inequality and poverty",
        keywords: ["inequality", "poverty", "wealth gap", "homelessness", "food insecurity", "social mobility", "Gini coefficient", "working poor", "deprivation", "redistribution"],
        prompt: "Assign this category to articles about economic inequality and poverty. Include income and wealth gaps, poverty rates, food insecurity, homelessness, and policies aimed at reducing inequality.",
      },
      {
        id: "14.06", name: "Internet culture and digital society",
        keywords: ["internet culture", "meme", "viral", "online community", "digital society", "platform culture", "misinformation", "online harassment", "cancel culture"],
        prompt: "Assign this category to articles about the cultural and social dimensions of the internet. Include online communities, viral phenomena, digital culture trends, misinformation spread, and the social effects of platform culture.",
      },
      {
        id: "14.07", name: "Social movements and activism",
        keywords: ["protest", "activism", "social movement", "advocacy", "rights", "demonstration", "campaign", "grassroots", "civil disobedience", "petition"],
        prompt: "Assign this category to articles about social movements and organised activism. Include protest events, activist campaigns, social movement dynamics, and advocacy efforts for political or social change. Exclude the underlying policy debates (use the relevant policy category).",
      },
      {
        id: "14.08", name: "Urbanization and cities",
        keywords: ["city", "urban", "smart city", "infrastructure", "housing", "transit", "gentrification", "urban planning", "metropolitan", "sprawl", "public space"],
        prompt: "Assign this category to articles about cities and urban development. Include urban planning, city housing, public transport, gentrification, and the challenges of dense urban living.",
      },
    ],
  },
  {
    id: "15",
    name: "Sport",
    color: "#0ea5e9",
    keywords: ["sport", "athlete", "team", "match", "game", "competition", "championship", "league", "coach", "performance", "victory", "defeat"],
    prompt: "Assign this category to articles about professional and competitive sport. Include matches, tournaments, athlete news, and the sports industry. Assign for general sports coverage; use subcategories for specific sports.",
    children: [
      {
        id: "15.01", name: "American football",
        keywords: ["NFL", "football", "Super Bowl", "quarterback", "touchdown", "draft", "playoff", "college football", "linebacker", "receiver", "season"],
        prompt: "Assign this category to articles about American football. Include the NFL, college football, Super Bowl, player news, team performance, and the business of American football.",
      },
      {
        id: "15.02", name: "Athletics and track & field",
        keywords: ["athletics", "sprint", "marathon", "track", "field", "long jump", "world record", "100m", "hurdles", "javelin", "decathlon", "Diamond League"],
        prompt: "Assign this category to articles about athletics and track and field events. Include sprinting, distance running, field events, world records, and major competitions including the World Athletics Championships.",
      },
      {
        id: "15.03", name: "Baseball and softball",
        keywords: ["MLB", "baseball", "pitcher", "home run", "World Series", "batting average", "inning", "shortstop", "softball", "roster", "trade deadline"],
        prompt: "Assign this category to articles about baseball and softball. Include MLB, minor league baseball, college baseball, player trades, game results, and the business of professional baseball.",
      },
      {
        id: "15.04", name: "Basketball",
        keywords: ["NBA", "basketball", "three-pointer", "playoffs", "MVP", "draft", "WNBA", "point guard", "finals", "trade", "LeBron", "free agency"],
        prompt: "Assign this category to articles about basketball. Include the NBA, WNBA, college basketball, player news, game results, trades, and the business of professional basketball globally.",
      },
      {
        id: "15.05", name: "Boxing and combat sports",
        keywords: ["boxing", "UFC", "MMA", "knockout", "champion", "welterweight", "wrestling", "judo", "belt", "fight", "bout", "heavyweight"],
        prompt: "Assign this category to articles about boxing and combat sports. Include professional boxing, UFC and mixed martial arts, wrestling, and other competitive combat disciplines.",
      },
      {
        id: "15.06", name: "Cricket",
        keywords: ["cricket", "Test match", "IPL", "batsman", "wicket", "Ashes", "ODI", "T20", "bowler", "century", "spinner", "England", "India", "Australia"],
        prompt: "Assign this category to articles about cricket. Include Test matches, ODIs, T20 leagues including the IPL, player news, team rankings, and the business of professional cricket.",
      },
      {
        id: "15.07", name: "Cycling",
        keywords: ["cycling", "Tour de France", "Giro", "Vuelta", "stage", "peloton", "time trial", "doping", "sprinter", "climber", "Classics", "velodrome"],
        prompt: "Assign this category to articles about competitive cycling. Include road cycling Grand Tours, one-day Classics, track cycling, mountain biking, doping cases, and team and rider news.",
      },
      {
        id: "15.08", name: "Football / Soccer",
        keywords: ["football", "soccer", "Premier League", "Champions League", "FIFA", "goal", "transfer", "World Cup", "La Liga", "Bundesliga", "Serie A"],
        prompt: "Assign this category to articles about association football (soccer). Include domestic leagues, international competitions, player transfers, FIFA, club and national team news, and the global football industry.",
      },
      {
        id: "15.09", name: "Formula 1 and motorsport",
        keywords: ["Formula 1", "F1", "Grand Prix", "Hamilton", "Verstappen", "constructor", "pit stop", "lap record", "NASCAR", "Le Mans", "WEC", "IndyCar"],
        prompt: "Assign this category to articles about Formula 1 and other motorsport. Include F1 race results, driver and constructor standings, technical regulations, NASCAR, endurance racing, and the business of motorsport.",
      },
      {
        id: "15.10", name: "Golf",
        keywords: ["golf", "PGA Tour", "Masters", "Open Championship", "par", "birdie", "leaderboard", "LIV Golf", "Ryder Cup", "green", "handicap", "major"],
        prompt: "Assign this category to articles about golf. Include the PGA Tour, LIV Golf, major championships, Ryder Cup, player rankings, and the business and culture of professional golf.",
      },
      {
        id: "15.11", name: "Ice hockey",
        keywords: ["NHL", "hockey", "Stanley Cup", "goalkeeper", "power play", "penalty", "period", "goal", "overtime", "trade deadline", "puck", "roster"],
        prompt: "Assign this category to articles about ice hockey. Include the NHL, European leagues, international ice hockey, Stanley Cup playoffs, player trades, and team news.",
      },
      {
        id: "15.12", name: "Olympics and multi-sport events",
        keywords: ["Olympics", "Games", "medal", "podium", "athlete", "host city", "IOC", "gold", "Commonwealth Games", "Asian Games", "torch relay", "doping"],
        prompt: "Assign this category to articles about the Olympic Games and other multi-sport events. Include athlete preparation, competition results, medal tables, IOC decisions, host city issues, and anti-doping in an Olympic context.",
      },
      {
        id: "15.13", name: "Rugby",
        keywords: ["rugby", "Six Nations", "World Cup", "tackle", "scrum", "try", "union", "league", "Lions", "Super Rugby", "Premiership", "conversion"],
        prompt: "Assign this category to articles about rugby union and rugby league. Include international tournaments including the Six Nations and World Cup, domestic leagues, and club and player news.",
      },
      {
        id: "15.14", name: "Swimming and aquatics",
        keywords: ["swimming", "pool", "stroke", "relay", "world record", "diving", "water polo", "open water", "freestyle", "butterfly", "Paralympic swimming"],
        prompt: "Assign this category to articles about competitive swimming and aquatic sports. Include pool and open-water swimming, diving, water polo, world records, and major competitions including World Championships.",
      },
      {
        id: "15.15", name: "Tennis",
        keywords: ["tennis", "Grand Slam", "Wimbledon", "US Open", "serve", "ranking", "ATP", "WTA", "set", "tie-break", "Roland Garros", "Australian Open"],
        prompt: "Assign this category to articles about professional tennis. Include Grand Slam tournaments, ATP and WTA tour events, player rankings, match results, and the business of professional tennis.",
      },
      {
        id: "15.16", name: "Winter sports",
        keywords: ["skiing", "snowboarding", "Winter Olympics", "alpine", "biathlon", "figure skating", "ice", "slalom", "freestyle", "luge", "bobsled"],
        prompt: "Assign this category to articles about winter sports. Include alpine and cross-country skiing, snowboarding, biathlon, figure skating, and speed skating. Exclude ice hockey (use Ice hockey (15.11)).",
      },
    ],
  },
  {
    id: "16",
    name: "Conflict, war and peace",
    color: "#dc2626",
    keywords: ["war", "conflict", "military", "troops", "battle", "ceasefire", "casualties", "frontline", "offensive", "defence", "fighting"],
    prompt: "Assign this category to articles about armed conflicts, warfare, and peace processes. Include active military operations, peace negotiations, and war-related events. Assign for general conflict coverage; use subcategories for specific conflict types.",
    children: [
      {
        id: "16.01",
        name: "Armed conflict and warfare",
        keywords: ["armed conflict", "war", "military operation", "casualties", "front line", "offensive", "troops", "military advance", "combat", "battle"],
        prompt: "Assign this category to articles about active armed conflict and military operations. Include battles, military advances, and casualty reports. Exclude specific operation types — use Air warfare (16.01.01), Ground operations (16.01.03), or Naval operations (16.01.04).",
        children: [
          {
            id: "16.01.01", name: "Air warfare",
            keywords: ["air strike", "bombing", "fighter jet", "air force", "aerial", "sortie", "drone strike", "air campaign", "intercept", "air defence"],
            prompt: "Assign this category to articles about military air operations in active conflict. Include air strikes, bombing campaigns, fighter jet engagements, drone strikes, and air defence operations.",
          },
          {
            id: "16.01.02", name: "Cyberwarfare",
            keywords: ["cyberattack", "cyberwarfare", "state-sponsored hacking", "infrastructure attack", "digital warfare", "military cyber", "offensive cyber", "CISA"],
            prompt: "Assign this category to articles about state-level cyberwarfare. Include state-sponsored cyberattacks on critical infrastructure, military cyber operations, and offensive cyber activities attributed to governments. Exclude criminal hacking (use Cybercrime (02.02.01)).",
          },
          {
            id: "16.01.03", name: "Ground operations",
            keywords: ["ground offensive", "troops", "infantry", "military advance", "occupation", "retreat", "front line", "armour", "artillery", "siege"],
            prompt: "Assign this category to articles about ground military operations in active conflict. Include ground offensives, infantry engagements, territorial advances or retreats, armoured operations, and urban warfare.",
          },
          {
            id: "16.01.04", name: "Naval operations",
            keywords: ["naval", "warship", "carrier", "blockade", "maritime", "submarine", "fleet", "destroyer", "navy", "sea lane", "port blockade"],
            prompt: "Assign this category to articles about naval and maritime military operations. Include warship movements, naval blockades, submarine operations, sea lane security, and naval engagements in active conflicts.",
          },
        ],
      },
      {
        id: "16.02", name: "Arms trade and weapons proliferation",
        keywords: ["arms sales", "weapons export", "proliferation", "illegal arms", "arms embargo", "arms dealer", "small arms", "WMD", "treaty", "defence export"],
        prompt: "Assign this category to articles about the international arms trade and weapons proliferation. Include state weapons sales, illegal arms flows, non-proliferation treaties, and concerns over weapons spreading to conflict zones.",
      },
      {
        id: "16.03", name: "Peace negotiations and ceasefires",
        keywords: ["ceasefire", "peace talks", "negotiations", "truce", "mediation", "peace agreement", "diplomatic solution", "hostage deal", "prisoner exchange"],
        prompt: "Assign this category to articles about efforts to end armed conflicts. Include ceasefire negotiations, peace talks, mediation processes, and peace agreements. Exclude the conflict itself (use Armed conflict and warfare (16.01)).",
      },
      {
        id: "16.04", name: "Terrorism and insurgency",
        keywords: ["terrorism", "insurgency", "attack", "bomb", "extremism", "militia", "IED", "counter-terrorism", "radicalism", "jihad", "separatist", "guerrilla"],
        prompt: "Assign this category to articles about terrorism and armed insurgencies. Include attacks by non-state armed groups, counter-insurgency operations, and the dynamics of armed movements challenging state authority. Exclude criminally motivated violence without political aims (use Crime, law and justice (02)).",
      },
      {
        id: "16.05", name: "War crimes and atrocities",
        keywords: ["war crimes", "atrocities", "genocide", "ICC", "humanitarian law", "civilian casualties", "tribunal", "massacre", "ethnic cleansing", "investigation"],
        prompt: "Assign this category to articles about war crimes and mass atrocities. Include alleged or confirmed violations of international humanitarian law, ICC investigations, massacre reports, and accountability efforts for atrocities during armed conflict.",
      },
    ],
  },
  {
    id: "17",
    name: "Weather",
    color: "#0891b2",
    keywords: ["weather", "temperature", "storm", "forecast", "climate", "rain", "snow", "wind", "heatwave", "cold", "meteorology"],
    prompt: "Assign this category to articles about weather conditions and meteorology. Include weather events, forecasts, and seasonal conditions. Exclude long-term climate change (use Climate change (06.01)) and weather-caused disasters (use Natural disaster (03.04)).",
    children: [
      {
        id: "17.01", name: "Extreme weather events",
        keywords: ["heatwave", "blizzard", "tornado", "derecho", "extreme weather", "record temperature", "cold snap", "ice storm", "heat dome", "polar vortex"],
        prompt: "Assign this category to articles about extreme weather events that fall short of a named natural disaster. Include record temperatures, severe storms, blizzards, and tornado outbreaks. Exclude events causing significant casualties or damage (use Natural disaster (03.04)).",
      },
      {
        id: "17.02", name: "Meteorology and forecasting",
        keywords: ["weather forecast", "temperature", "precipitation", "climate model", "meteorology", "met office", "NOAA", "forecast", "radar", "jet stream"],
        prompt: "Assign this category to articles about meteorology and weather forecasting. Include forecast updates, advances in weather prediction, meteorological services, and the science of atmospheric observation and modelling.",
      },
      {
        id: "17.03", name: "Seasonal weather",
        keywords: ["winter", "summer", "monsoon", "drought season", "seasonal outlook", "spring", "autumn", "El Niño", "La Niña", "seasonal forecast"],
        prompt: "Assign this category to articles about seasonal weather patterns and outlooks. Include seasonal forecasts, monsoon patterns, El Niño and La Niña effects, and the expected character of a forthcoming season.",
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
