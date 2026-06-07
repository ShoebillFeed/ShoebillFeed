import { useState, useRef } from "react";
import { Plus, Trash2, Pencil, RotateCcw, Download, Upload, Search, Check } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useCategories, useDeleteCategory, useResetWeights, useSetManualWeight, useImportCategories, useUpdateCategory, useCreateCategory } from "../../hooks/useCategories";
import { categoriesApi } from "../../api/categories";
import CategoryForm from "./CategoryForm";
import type { Category, CategoryCreate } from "../../types/category";

type Preset = CategoryCreate & { label: string };

const CATEGORY_PRESETS: Preset[] = [
  // Technology
  { label: "AI & Machine Learning", name: "AI & Machine Learning", color: "#6366f1", keywords: ["AI", "LLM", "machine learning", "deep learning", "neural network", "ChatGPT", "GPT", "Claude", "Gemini", "OpenAI", "Anthropic", "transformer", "fine-tuning", "inference"], prompt: "Articles about artificial intelligence and machine learning. Covers large language model research and releases, AI safety and alignment, new model benchmarks, AI applications across industries, and updates from major AI labs such as OpenAI, Anthropic, Google DeepMind, and Meta AI." },
  { label: "Cybersecurity", name: "Cybersecurity", color: "#ef4444", keywords: ["vulnerability", "CVE", "exploit", "data breach", "ransomware", "malware", "zero-day", "phishing", "hacking", "CISA", "patch", "infosec", "threat actor"], prompt: "Articles about cybersecurity threats, incidents, and defences. Covers newly disclosed vulnerabilities and CVEs, ransomware and malware campaigns, data breaches, nation-state attacks, security research, and defensive tooling and best practices." },
  { label: "Open Source & Dev Tools", name: "Open Source & Dev Tools", color: "#14b8a6", keywords: ["open source", "GitHub", "release", "framework", "library", "SDK", "API", "DevOps", "CI/CD", "Docker", "Kubernetes", "Linux", "kernel", "self-hosted"], prompt: "Articles about open source projects, developer tooling, and software infrastructure. Covers major version releases of popular frameworks and libraries, Linux kernel updates, notable GitHub repositories, cloud-native tooling, and open source community and governance news." },
  { label: "Hardware & Chips", name: "Hardware & Chips", color: "#3b82f6", keywords: ["CPU", "GPU", "semiconductor", "NVIDIA", "Intel", "AMD", "TSMC", "chip", "processor", "silicon", "data centre", "HBM", "wafer"], prompt: "Articles about computer hardware, semiconductors, and chip manufacturing. Covers new processor and GPU architectures, semiconductor supply chain and geopolitics, fab capacity from TSMC and Intel Foundry, AI accelerator developments, and hardware benchmark results." },
  // Business & Finance
  { label: "Financial Markets", name: "Financial Markets", color: "#f59e0b", keywords: ["stock market", "S&P 500", "interest rate", "Fed", "inflation", "recession", "bond", "yield", "GDP", "earnings", "IPO", "index", "ECB", "monetary policy"], prompt: "Articles about financial markets, macroeconomics, and investing. Covers equity and bond market movements, central bank decisions and interest rates, inflation and GDP data, corporate earnings, IPOs, and broader macroeconomic trends." },
  { label: "Startups & Venture Capital", name: "Startups & VC", color: "#ec4899", keywords: ["startup", "funding", "venture capital", "seed", "Series A", "Series B", "Series C", "unicorn", "Y Combinator", "founder", "valuation", "angel", "pitch"], prompt: "Articles about the startup ecosystem and venture capital activity. Covers funding rounds from seed to late stage, new company launches, notable founders, unicorn valuations, accelerator cohorts, and the investment theses driving capital in emerging sectors." },
  { label: "Crypto & Web3", name: "Crypto & Web3", color: "#8b5cf6", keywords: ["Bitcoin", "Ethereum", "crypto", "blockchain", "DeFi", "NFT", "Web3", "stablecoin", "Layer 2", "wallet", "exchange", "SEC", "token", "on-chain"], prompt: "Articles about cryptocurrency, blockchain technology, and decentralised finance. Covers Bitcoin and Ethereum price action and network developments, DeFi protocols, regulatory actions from the SEC and other bodies, exchange news, and emerging Layer 2 and scaling solutions." },
  { label: "Mergers & Acquisitions", name: "Mergers & Acquisitions", color: "#84cc16", keywords: ["acquisition", "merger", "deal", "buyout", "takeover", "acquired", "purchase", "divestiture", "strategic deal", "antitrust approval"], prompt: "Articles about corporate mergers, acquisitions, and major business deals. Covers announced and completed transactions, hostile takeover attempts, regulatory approvals or blocks from competition authorities, and the strategic rationale and financial terms behind significant deals." },
  { label: "Advertising & Marketing", name: "Advertising & Marketing", color: "#f97316", keywords: ["advertising", "ad spend", "programmatic", "Google Ads", "Meta Ads", "marketing", "brand", "campaign", "agency", "adtech", "CPM", "targeting", "cookie"], prompt: "Articles about the advertising and marketing industry. Covers digital ad market trends and spend data, programmatic and adtech developments, major campaign launches, agency news and consolidation, changes to ad targeting and privacy (such as cookie deprecation), and platform advertising policies at Google and Meta." },
  // Politics & Society
  { label: "Domestic Politics", name: "Domestic Politics", color: "#f43f5e", keywords: ["election", "parliament", "congress", "senate", "president", "prime minister", "legislation", "bill", "vote", "party", "policy", "government", "coalition"], prompt: "Articles about domestic politics and government. Covers elections, legislative activity, government appointments and decisions, party politics, and policy changes. Focuses on factual reporting of political events and their direct consequences for citizens and institutions." },
  { label: "Geopolitics & Conflicts", name: "Geopolitics & Conflicts", color: "#64748b", keywords: ["NATO", "sanctions", "war", "conflict", "diplomacy", "treaty", "UN", "military", "foreign policy", "bilateral", "alliance", "embargo", "ceasefire"], prompt: "Articles about international relations, geopolitical tensions, and armed conflicts. Covers military conflicts and ceasefires, diplomatic negotiations, international sanctions, NATO and UN activity, bilateral trade and security disputes, and the foreign policy positions of major powers." },
  { label: "Privacy & Regulation", name: "Privacy & Regulation", color: "#a855f7", keywords: ["GDPR", "privacy", "data protection", "antitrust", "FTC", "EU AI Act", "DSA", "DMA", "compliance", "lawsuit", "fine", "court ruling", "regulator"], prompt: "Articles about technology regulation, data privacy, and antitrust enforcement. Covers GDPR and data protection enforcement actions, EU legislation such as the AI Act, DSA, and DMA, FTC and DOJ investigations, court rulings affecting the tech industry, and corporate compliance and lobbying activity." },
  { label: "Climate & Environment", name: "Climate & Environment", color: "#22c55e", keywords: ["climate change", "CO2", "emissions", "renewable energy", "solar", "wind", "carbon", "IPCC", "COP", "sustainability", "fossil fuel", "deforestation", "net zero"], prompt: "Articles about climate change, environmental policy, and the energy transition. Covers new climate science findings, renewable energy deployment and costs, fossil fuel industry developments, international agreements and COP summits, carbon markets, and extreme weather events attributed to climate change." },
  // Science & Academia
  { label: "Space & Astronomy", name: "Space & Astronomy", color: "#0ea5e9", keywords: ["NASA", "SpaceX", "ESA", "rocket", "launch", "satellite", "ISS", "Mars", "Moon", "telescope", "asteroid", "orbit", "exoplanet", "James Webb"], prompt: "Articles about space exploration, astronomy, and the commercial space industry. Covers rocket launches and mission updates from NASA and ESA, commercial spaceflight from SpaceX, Blue Origin, and Rocket Lab, telescope observations and astronomical discoveries, and planetary science findings." },
  { label: "Health & Medicine", name: "Health & Medicine", color: "#06b6d4", keywords: ["FDA", "drug approval", "vaccine", "clinical trial", "cancer", "disease", "therapy", "WHO", "pharmaceutical", "treatment", "pandemic", "antibiotic", "GLP-1"], prompt: "Articles about medicine, public health, and the pharmaceutical industry. Covers drug and device approvals, clinical trial results, disease outbreaks and pandemic preparedness, breakthrough therapies, healthcare policy and access, and medical research published in leading journals." },
  { label: "Physics & Engineering", name: "Physics & Engineering", color: "#10b981", keywords: ["quantum computing", "fusion energy", "particle physics", "CERN", "materials science", "superconductor", "photonics", "robotics", "nanotechnology", "research"], prompt: "Articles about physics research and engineering breakthroughs. Covers quantum computing hardware and algorithms, nuclear fusion progress, particle physics discoveries at CERN, new materials and superconductors, robotics advances, and fundamental physics findings from universities and research institutions." },
  { label: "Biology & Genetics", name: "Biology & Genetics", color: "#4ade80", keywords: ["CRISPR", "gene editing", "genomics", "DNA", "protein", "AlphaFold", "evolution", "microbiome", "ecology", "species", "cell", "RNA", "sequencing"], prompt: "Articles about biology, genetics, and life sciences research. Covers gene editing and CRISPR developments, genomics and proteomics discoveries, evolutionary biology, ecology and biodiversity, microbiome research, and computational biology tools such as AlphaFold." },
  { label: "Sponsored & Ads", name: "Sponsored & Ads", color: "#9ca3af", keywords: ["sponsored", "advertisement", "advertorial", "promoted", "paid content", "press release", "native ad", "brand content", "affiliate"], prompt: "Articles that are advertisements, sponsored content, or promotional material rather than independent editorial reporting. Assign this category to press releases presented as news, native advertising, advertorials, paid partnerships, and any content that primarily exists to promote a product, service, or company rather than to inform." },
  { label: "Social Science & Psychology", name: "Social Science & Psychology", color: "#fb923c", keywords: ["psychology", "behaviour", "study", "survey", "society", "mental health", "cognitive", "social media", "inequality", "demographics", "economics research", "experiment"], prompt: "Articles about social science research and psychology. Covers findings from psychology and behavioural studies, sociological research on inequality and demographics, mental health trends, the societal effects of technology and social media, and economics research that focuses on human behaviour rather than markets." },
];

function downloadJson(data: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function CategoriesPanel() {
  const { t } = useTranslation();
  const { data: categories, isLoading } = useCategories();
  const deleteCategory = useDeleteCategory();
  const resetWeights = useResetWeights();
  const importCategories = useImportCategories();
  const createCategory = useCreateCategory();
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Category | null>(null);
  const [presetSearch, setPresetSearch] = useState("");
  const [addedPresets, setAddedPresets] = useState<Set<string>>(new Set());

  const existingNames = new Set((categories ?? []).map((c) => c.name.toLowerCase()));

  const handleAddPreset = (preset: typeof CATEGORY_PRESETS[number]) => {
    createCategory.mutate(
      { name: preset.name, color: preset.color, keywords: preset.keywords, prompt: preset.prompt },
      { onSuccess: () => setAddedPresets((s) => new Set(s).add(preset.name)) },
    );
  };

  const handleExport = async () => {
    const data = await categoriesApi.export();
    downloadJson(data, "categories.json");
  };

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const data = JSON.parse(ev.target?.result as string);
        importCategories.mutate(data);
      } catch {
        alert(t("categories.invalidJson"));
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold text-gray-900 dark:text-gray-100">{t("categories.title")}</h2>
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={handleExport}
            title={t("categories.exportTitle")}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-gray-600 dark:text-gray-400"
          >
            <Download size={14} /> {t("common.export")}
          </button>
          <label
            title={t("categories.importTitle")}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-gray-600 dark:text-gray-400 cursor-pointer"
          >
            <Upload size={14} /> {t("common.import")}
            <input type="file" accept=".json" className="hidden" onChange={handleImport} />
          </label>
          <button
            onClick={() => {
              if (confirm(t("categories.resetWeightsConfirm")))
                resetWeights.mutate();
            }}
            title={t("categories.resetWeights")}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-gray-600 dark:text-gray-400"
          >
            <RotateCcw size={14} /> {t("categories.resetWeights")}
          </button>
          <button
            onClick={() => { setEditing(null); setShowForm(true); }}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors"
          >
            <Plus size={14} /> {t("categories.addCategory")}
          </button>
        </div>
      </div>

      {showForm && (
        <div className="mb-4 p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800/50">
          <h3 className="font-medium text-sm mb-3">{t("categories.addNewCategory")}</h3>
          <CategoryForm
            onClose={() => setShowForm(false)}
          />
        </div>
      )}

      {isLoading && <p className="text-sm text-gray-400">{t("common.loading")}</p>}

      <div className="flex flex-col gap-2">
        {categories?.map((cat) => (
          editing?.id === cat.id ? (
            <div key={cat.id} className="p-4 border border-indigo-200 dark:border-indigo-800 rounded-lg bg-gray-50 dark:bg-gray-800/50">
              <h3 className="font-medium text-sm mb-3 text-indigo-600 dark:text-indigo-400">{t("categories.editingCategory", { name: cat.name })}</h3>
              <CategoryForm
                category={cat}
                onClose={() => setEditing(null)}
              />
            </div>
          ) : (
            <CategoryRow
              key={cat.id}
              cat={cat}
              onEdit={() => { setEditing(cat); setShowForm(false); }}
              onDelete={() => {
                if (confirm(t("categories.deleteConfirm", { name: cat.name })))
                  deleteCategory.mutate(cat.id);
              }}
            />
          )
        ))}

        {categories?.length === 0 && !isLoading && (
          <p className="text-sm text-gray-400 text-center py-8">{t("categories.empty")}</p>
        )}
      </div>

      <div className="mt-8">
        <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
          <div className="flex items-center justify-between mb-1">
            <h3 className="font-medium text-sm text-gray-900 dark:text-gray-100">{t("categories.presetsTitle")}</h3>
            <span className="text-xs text-gray-400">{CATEGORY_PRESETS.length}</span>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">{t("categories.presetsDesc")}</p>
          <div className="relative mb-3">
            <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
            <input
              type="text"
              placeholder={t("categories.presetsSearch")}
              value={presetSearch}
              onChange={(e) => setPresetSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div className="flex flex-col gap-1.5 max-h-72 overflow-y-auto pr-1">
            {CATEGORY_PRESETS
              .filter((p: Preset) => p.label.toLowerCase().includes(presetSearch.toLowerCase()))
              .map((preset: Preset) => {
                const already = existingNames.has(preset.name.toLowerCase()) || addedPresets.has(preset.name);
                return (
                  <div
                    key={preset.name}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700"
                  >
                    <span
                      className="w-3 h-3 rounded-full shrink-0"
                      style={{ backgroundColor: preset.color }}
                    />
                    <span className="flex-1 text-sm text-gray-700 dark:text-gray-300 truncate">{preset.label}</span>
                    <span className="text-xs text-gray-400 dark:text-gray-500 truncate max-w-[200px] hidden sm:block">
                      {preset.keywords.slice(0, 4).join(", ")}
                    </span>
                    <button
                      title={already ? t("categories.presetsAlreadyAdded") : t("categories.addCategory")}
                      onClick={() => !already && handleAddPreset(preset)}
                      disabled={already || createCategory.isPending}
                      className="p-1 rounded transition-colors shrink-0 disabled:cursor-default text-indigo-500 hover:text-indigo-700 dark:hover:text-indigo-300 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 disabled:text-gray-300 dark:disabled:text-gray-600 disabled:hover:bg-transparent"
                    >
                      {already ? <Check size={14} /> : <Plus size={14} />}
                    </button>
                  </div>
                );
              })}
            {CATEGORY_PRESETS.filter((p: Preset) => p.label.toLowerCase().includes(presetSearch.toLowerCase())).length === 0 && (
              <p className="text-sm text-gray-400 text-center py-4">{t("categories.presetsNoMatch")}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function CategoryRow({
  cat,
  onEdit,
  onDelete,
}: {
  cat: Category;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const { t } = useTranslation();
  const setManualWeight = useSetManualWeight();
  const updateCategory = useUpdateCategory();
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [localWeight, setLocalWeight] = useState(cat.weight?.manual_weight ?? 1.0);

  const handleSliderChange = (value: number) => {
    setLocalWeight(value);
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      setManualWeight.mutate({ id: cat.id, manual_weight: value });
    }, 400);
  };

  const handleToggleActive = () => {
    updateCategory.mutate({ id: cat.id, data: { is_active: !cat.is_active } });
  };

  const learnedWeight = cat.weight?.weight ?? 1.0;
  const effectiveWeight = learnedWeight * localWeight;
  const inactive = !cat.is_active;

  return (
    <div className={`p-3 bg-white dark:bg-gray-900 border rounded-lg transition-opacity ${inactive ? "opacity-50 border-gray-100 dark:border-gray-800" : "border-gray-200 dark:border-gray-700"}`}>
      <div className="flex items-center gap-3">
        <div
          className="w-4 h-4 rounded-full shrink-0"
          style={{ backgroundColor: inactive ? "#9ca3af" : cat.color }}
        />
        <div className="flex-1 min-w-0">
          <span className={`text-sm font-medium ${inactive ? "text-gray-400 dark:text-gray-500" : ""}`}>{cat.name}</span>
          <p className="text-xs text-gray-400">
            {t("categories.articles", { count: cat.item_count })}
            {cat.weight?.total_marked ? ` · ${t("categories.starMarks", { count: cat.weight.total_marked })}` : ""}
          </p>
          {cat.keywords.length > 0 && (
            <p className="text-xs text-gray-400 truncate">{cat.keywords.join(", ")}</p>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {/* Active toggle */}
          <button
            role="switch"
            aria-checked={cat.is_active}
            title={cat.is_active ? t("categories.disable") : t("categories.enable")}
            onClick={handleToggleActive}
            className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus:outline-none ${cat.is_active ? "bg-indigo-600" : "bg-gray-300 dark:bg-gray-600"}`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${cat.is_active ? "translate-x-4" : "translate-x-0"}`}
            />
          </button>
          <button
            title={t("common.edit")}
            onClick={onEdit}
            className="p-1.5 rounded text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <Pencil size={14} />
          </button>
          <button
            title={t("common.delete")}
            onClick={onDelete}
            className="p-1.5 rounded text-gray-400 hover:text-red-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {/* Weight slider — only shown when active */}
      {cat.is_active && (
        <>
          <div className="mt-2.5 flex items-center gap-3">
            <span className="text-xs text-gray-400 w-12 shrink-0">{t("categories.weight")}</span>
            <input
              type="range"
              min={0}
              max={5}
              step={0.1}
              value={localWeight}
              onChange={(e) => handleSliderChange(parseFloat(e.target.value))}
              className="flex-1 h-1.5 accent-indigo-600 cursor-pointer"
            />
            <span className="text-xs font-mono text-gray-500 dark:text-gray-400 w-20 shrink-0 text-right">
              ×{localWeight.toFixed(1)}
              <span className="text-gray-400 dark:text-gray-600"> = {effectiveWeight.toFixed(2)}</span>
            </span>
          </div>
          <p className="text-xs text-gray-400 mt-0.5 pl-[3.25rem]">
            {t("categories.manualLearned", { weight: learnedWeight.toFixed(2) })}
          </p>
        </>
      )}
    </div>
  );
}
