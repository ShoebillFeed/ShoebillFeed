export interface TaxonomyNode {
  id: string;
  name: string;
  color?: string;
  children?: TaxonomyNode[];
}

export const IPTC_TAXONOMY: TaxonomyNode[] = [
  {
    id: "01",
    name: "Arts, entertainment and media",
    color: "#ec4899",
    children: [
      { id: "01.01", name: "Cinema and film" },
      { id: "01.02", name: "Dance" },
      { id: "01.03", name: "Fashion and beauty" },
      { id: "01.04", name: "Gaming and video games" },
      { id: "01.05", name: "Literature and poetry" },
      { id: "01.06", name: "Music" },
      { id: "01.07", name: "Photography" },
      { id: "01.08", name: "Radio" },
      { id: "01.09", name: "Television and streaming" },
      { id: "01.10", name: "Theatre and performing arts" },
      { id: "01.11", name: "Visual arts" },
      { id: "01.12", name: "Entertainment" },
      {
        id: "01.13",
        name: "Media",
        children: [
          { id: "01.13.01", name: "Broadcasting" },
          { id: "01.13.02", name: "Journalism and news" },
          { id: "01.13.03", name: "Online media and publishing" },
          { id: "01.13.04", name: "Social media and influencers" },
        ],
      },
    ],
  },
  {
    id: "02",
    name: "Crime, law and justice",
    color: "#ef4444",
    children: [
      { id: "02.01", name: "Courts and judiciary" },
      {
        id: "02.02",
        name: "Crime",
        children: [
          { id: "02.02.01", name: "Cybercrime and hacking" },
          { id: "02.02.02", name: "Drug trafficking" },
          { id: "02.02.03", name: "Financial crime and fraud" },
          { id: "02.02.04", name: "Organized crime" },
          { id: "02.02.05", name: "Terrorism" },
          { id: "02.02.06", name: "Violent crime" },
        ],
      },
      { id: "02.03", name: "Law enforcement and policing" },
      { id: "02.04", name: "Legislation and legal proceedings" },
      { id: "02.05", name: "Prisons and incarceration" },
    ],
  },
  {
    id: "03",
    name: "Disaster, accident and emergency",
    color: "#f97316",
    children: [
      { id: "03.01", name: "Aviation accident" },
      { id: "03.02", name: "Fire and explosion" },
      { id: "03.03", name: "Industrial and nuclear accident" },
      {
        id: "03.04",
        name: "Natural disaster",
        children: [
          { id: "03.04.01", name: "Drought" },
          { id: "03.04.02", name: "Earthquake and tsunami" },
          { id: "03.04.03", name: "Flood" },
          { id: "03.04.04", name: "Hurricane and tropical storm" },
          { id: "03.04.05", name: "Wildfire" },
          { id: "03.04.06", name: "Volcanic eruption" },
        ],
      },
      { id: "03.05", name: "Transport accident" },
    ],
  },
  {
    id: "04",
    name: "Economy, business and finance",
    color: "#f59e0b",
    children: [
      { id: "04.01", name: "Agriculture and food industry" },
      {
        id: "04.02",
        name: "Banking and financial services",
        children: [
          { id: "04.02.01", name: "Central banking and monetary policy" },
          { id: "04.02.02", name: "Consumer finance and lending" },
          { id: "04.02.03", name: "Investment banking" },
        ],
      },
      {
        id: "04.03",
        name: "Computing and information technology",
        children: [
          { id: "04.03.01", name: "Artificial intelligence" },
          { id: "04.03.02", name: "Cloud computing and infrastructure" },
          { id: "04.03.03", name: "Cybersecurity" },
          { id: "04.03.04", name: "Hardware and semiconductors" },
          { id: "04.03.05", name: "Internet and e-commerce" },
          { id: "04.03.06", name: "Software and apps" },
        ],
      },
      { id: "04.04", name: "Cryptocurrency and digital assets" },
      {
        id: "04.05",
        name: "Energy and resources",
        children: [
          { id: "04.05.01", name: "Fossil fuels" },
          { id: "04.05.02", name: "Nuclear energy" },
          { id: "04.05.03", name: "Renewable energy" },
        ],
      },
      {
        id: "04.06",
        name: "Financial markets",
        children: [
          { id: "04.06.01", name: "Bonds and fixed income" },
          { id: "04.06.02", name: "Commodities" },
          { id: "04.06.03", name: "Currencies and forex" },
          { id: "04.06.04", name: "Equities and stock markets" },
          { id: "04.06.05", name: "Private equity and venture capital" },
        ],
      },
      { id: "04.07", name: "Healthcare industry" },
      { id: "04.08", name: "Housing and real estate" },
      { id: "04.09", name: "Manufacturing and industry" },
      { id: "04.10", name: "Media and entertainment industry" },
      { id: "04.11", name: "Mergers and acquisitions" },
      { id: "04.12", name: "Pharmaceutical industry" },
      { id: "04.13", name: "Retail and consumer goods" },
      { id: "04.14", name: "Startups and entrepreneurship" },
      { id: "04.15", name: "Trade and tariffs" },
      { id: "04.16", name: "Transport and logistics" },
    ],
  },
  {
    id: "05",
    name: "Education",
    color: "#84cc16",
    children: [
      { id: "05.01", name: "Higher education and universities" },
      { id: "05.02", name: "Online and digital learning" },
      { id: "05.03", name: "School education" },
      { id: "05.04", name: "Teaching and pedagogy" },
      { id: "05.05", name: "Vocational training" },
    ],
  },
  {
    id: "06",
    name: "Environment",
    color: "#22c55e",
    children: [
      { id: "06.01", name: "Climate change" },
      { id: "06.02", name: "Conservation and biodiversity" },
      { id: "06.03", name: "Natural resources" },
      {
        id: "06.04",
        name: "Pollution",
        children: [
          { id: "06.04.01", name: "Air quality and air pollution" },
          { id: "06.04.02", name: "Plastic and waste pollution" },
          { id: "06.04.03", name: "Water pollution" },
        ],
      },
      { id: "06.05", name: "Renewable energy and clean tech" },
      { id: "06.06", name: "Wildlife and ecosystems" },
    ],
  },
  {
    id: "07",
    name: "Health",
    color: "#06b6d4",
    children: [
      { id: "07.01", name: "Epidemics and pandemics" },
      { id: "07.02", name: "Healthcare policy and access" },
      { id: "07.03", name: "Healthcare technology and digital health" },
      {
        id: "07.04",
        name: "Medical research",
        children: [
          { id: "07.04.01", name: "Cancer research" },
          { id: "07.04.02", name: "Drug development and clinical trials" },
          { id: "07.04.03", name: "Genetics and genomics" },
          { id: "07.04.04", name: "Medical devices and diagnostics" },
          { id: "07.04.05", name: "Neuroscience and brain research" },
        ],
      },
      { id: "07.05", name: "Mental health and psychiatry" },
      { id: "07.06", name: "Nutrition and fitness" },
      { id: "07.07", name: "Pharmaceutical drugs" },
      { id: "07.08", name: "Public health" },
    ],
  },
  {
    id: "08",
    name: "Human interest",
    color: "#fb923c",
    children: [
      { id: "08.01", name: "Animals" },
      { id: "08.02", name: "Celebrity and public figures" },
      { id: "08.03", name: "People and profiles" },
      { id: "08.04", name: "Royalty and nobility" },
    ],
  },
  {
    id: "09",
    name: "Labour and employment",
    color: "#8b5cf6",
    children: [
      { id: "09.01", name: "Employment and jobs" },
      { id: "09.02", name: "Labour relations and disputes" },
      { id: "09.03", name: "Trade unions" },
      { id: "09.04", name: "Wages, benefits and pensions" },
      { id: "09.05", name: "Working conditions" },
    ],
  },
  {
    id: "10",
    name: "Lifestyle and leisure",
    color: "#10b981",
    children: [
      { id: "10.01", name: "Food and drink" },
      { id: "10.02", name: "Hobbies and crafts" },
      { id: "10.03", name: "Home and living" },
      { id: "10.04", name: "Outdoor activities" },
      { id: "10.05", name: "Shopping and consumer trends" },
      { id: "10.06", name: "Travel and tourism" },
    ],
  },
  {
    id: "11",
    name: "Politics",
    color: "#f43f5e",
    children: [
      {
        id: "11.01",
        name: "Defence and military policy",
        children: [
          { id: "11.01.01", name: "Arms and weapons programmes" },
          { id: "11.01.02", name: "Intelligence and espionage" },
          { id: "11.01.03", name: "Military technology" },
        ],
      },
      {
        id: "11.02",
        name: "Domestic politics",
        children: [
          { id: "11.02.01", name: "Elections and voting" },
          { id: "11.02.02", name: "Government and governance" },
          { id: "11.02.03", name: "Legislation and lawmaking" },
          { id: "11.02.04", name: "Political parties and movements" },
        ],
      },
      {
        id: "11.03",
        name: "International relations and diplomacy",
        children: [
          { id: "11.03.01", name: "Alliances and multilateral organizations" },
          { id: "11.03.02", name: "Bilateral diplomacy" },
          { id: "11.03.03", name: "Foreign policy" },
          { id: "11.03.04", name: "Sanctions and trade restrictions" },
        ],
      },
      {
        id: "11.04",
        name: "Regulation and policy",
        children: [
          { id: "11.04.01", name: "Antitrust and competition law" },
          { id: "11.04.02", name: "Data protection and privacy" },
          { id: "11.04.03", name: "Environmental regulation" },
          { id: "11.04.04", name: "Financial regulation" },
          { id: "11.04.05", name: "Technology regulation" },
        ],
      },
    ],
  },
  {
    id: "12",
    name: "Religion and belief",
    color: "#a855f7",
    children: [
      { id: "12.01", name: "Buddhism" },
      { id: "12.02", name: "Christianity" },
      { id: "12.03", name: "Hinduism" },
      { id: "12.04", name: "Islam" },
      { id: "12.05", name: "Judaism" },
      { id: "12.06", name: "Religious freedom and secularism" },
    ],
  },
  {
    id: "13",
    name: "Science and technology",
    color: "#3b82f6",
    children: [
      {
        id: "13.01",
        name: "Astronomy and space science",
        children: [
          { id: "13.01.01", name: "Commercial space industry" },
          { id: "13.01.02", name: "Planetary science" },
          { id: "13.01.03", name: "Space exploration and missions" },
          { id: "13.01.04", name: "Telescopes and astronomical observation" },
        ],
      },
      {
        id: "13.02",
        name: "Biology and life sciences",
        children: [
          { id: "13.02.01", name: "Ecology and environmental biology" },
          { id: "13.02.02", name: "Evolution and palaeontology" },
          { id: "13.02.03", name: "Genetics and genomics" },
          { id: "13.02.04", name: "Microbiology and virology" },
        ],
      },
      { id: "13.03", name: "Chemistry and materials science" },
      {
        id: "13.04",
        name: "Computer science and AI",
        children: [
          { id: "13.04.01", name: "Algorithms and data science" },
          { id: "13.04.02", name: "Artificial intelligence research" },
          { id: "13.04.03", name: "Natural language processing" },
          { id: "13.04.04", name: "Quantum computing" },
          { id: "13.04.05", name: "Robotics and automation" },
        ],
      },
      { id: "13.05", name: "Earth and climate science" },
      { id: "13.06", name: "Mathematics and statistics" },
      { id: "13.07", name: "Medicine and biomedical research" },
      {
        id: "13.08",
        name: "Physics",
        children: [
          { id: "13.08.01", name: "Nuclear physics and fusion energy" },
          { id: "13.08.02", name: "Particle physics and high-energy physics" },
          { id: "13.08.03", name: "Quantum physics" },
        ],
      },
      { id: "13.09", name: "Research policy and funding" },
    ],
  },
  {
    id: "14",
    name: "Society",
    color: "#64748b",
    children: [
      { id: "14.01", name: "Demographics and population" },
      { id: "14.02", name: "Family and relationships" },
      { id: "14.03", name: "Human rights and civil liberties" },
      { id: "14.04", name: "Immigration and refugees" },
      { id: "14.05", name: "Inequality and poverty" },
      { id: "14.06", name: "Internet culture and digital society" },
      { id: "14.07", name: "Social movements and activism" },
      { id: "14.08", name: "Urbanization and cities" },
    ],
  },
  {
    id: "15",
    name: "Sport",
    color: "#0ea5e9",
    children: [
      { id: "15.01", name: "American football" },
      { id: "15.02", name: "Athletics and track & field" },
      { id: "15.03", name: "Baseball and softball" },
      { id: "15.04", name: "Basketball" },
      { id: "15.05", name: "Boxing and combat sports" },
      { id: "15.06", name: "Cricket" },
      { id: "15.07", name: "Cycling" },
      { id: "15.08", name: "Football / Soccer" },
      { id: "15.09", name: "Formula 1 and motorsport" },
      { id: "15.10", name: "Golf" },
      { id: "15.11", name: "Ice hockey" },
      { id: "15.12", name: "Olympics and multi-sport events" },
      { id: "15.13", name: "Rugby" },
      { id: "15.14", name: "Swimming and aquatics" },
      { id: "15.15", name: "Tennis" },
      { id: "15.16", name: "Winter sports" },
    ],
  },
  {
    id: "16",
    name: "Conflict, war and peace",
    color: "#dc2626",
    children: [
      {
        id: "16.01",
        name: "Armed conflict and warfare",
        children: [
          { id: "16.01.01", name: "Air warfare" },
          { id: "16.01.02", name: "Cyberwarfare" },
          { id: "16.01.03", name: "Ground operations" },
          { id: "16.01.04", name: "Naval operations" },
        ],
      },
      { id: "16.02", name: "Arms trade and weapons proliferation" },
      { id: "16.03", name: "Peace negotiations and ceasefires" },
      { id: "16.04", name: "Terrorism and insurgency" },
      { id: "16.05", name: "War crimes and atrocities" },
    ],
  },
  {
    id: "17",
    name: "Weather",
    color: "#0891b2",
    children: [
      { id: "17.01", name: "Extreme weather events" },
      { id: "17.02", name: "Meteorology and forecasting" },
      { id: "17.03", name: "Seasonal weather" },
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
