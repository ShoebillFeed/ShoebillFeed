"""arXiv subject-category codes → human-readable labels.

arXiv tags every paper with its own curated taxonomy (`cs.LG`, `quant-ph`,
...), which is far better clustering signal than generated keywords: two
papers both tagged `cs.CL` + `cs.LG` are reliably related, where two LLM
keyword sets describing the same idea can disagree on wording.

The codes are mapped to readable names rather than stored verbatim for two
reasons. `normalize_keyword()` strips punctuation, so a raw `cs.LG` becomes
the token `"cs lg"` -- opaque in the Trends tab and keyword-cluster map, and
guaranteed never to overlap with an LLM keyword. A label like
"machine learning" both reads correctly and actually merges with what the
model already produces, which is the whole point of carrying these through.

Coverage is exact for the archives with small, stable subcategory lists
(cs, stat, eess, econ, q-bio, q-fin). Everything else falls back to its
archive name via `_ARCHIVE_NAMES` (`math.AT` -> "mathematics"), and an
unknown code falls back to itself -- deliberately no silent drop, since a
new arXiv category should still cluster papers together even before this
catalog knows its name.
"""

_CATEGORY_NAMES: dict[str, str] = {
    # cs.*
    "cs.AI": "artificial intelligence",
    "cs.AR": "hardware architecture",
    "cs.CC": "computational complexity",
    "cs.CE": "computational engineering",
    "cs.CG": "computational geometry",
    "cs.CL": "computation and language",
    "cs.CR": "cryptography and security",
    "cs.CV": "computer vision",
    "cs.CY": "computers and society",
    "cs.DB": "databases",
    "cs.DC": "distributed and parallel computing",
    "cs.DL": "digital libraries",
    "cs.DM": "discrete mathematics",
    "cs.DS": "data structures and algorithms",
    "cs.ET": "emerging technologies",
    "cs.FL": "formal languages and automata theory",
    "cs.GL": "general literature",
    "cs.GR": "graphics",
    "cs.GT": "computer science and game theory",
    "cs.HC": "human-computer interaction",
    "cs.IR": "information retrieval",
    "cs.IT": "information theory",
    "cs.LG": "machine learning",
    "cs.LO": "logic in computer science",
    "cs.MA": "multiagent systems",
    "cs.MM": "multimedia",
    "cs.MS": "mathematical software",
    "cs.NA": "numerical analysis",
    "cs.NE": "neural and evolutionary computing",
    "cs.NI": "networking and internet architecture",
    "cs.OH": "other computer science",
    "cs.OS": "operating systems",
    "cs.PF": "performance",
    "cs.PL": "programming languages",
    "cs.RO": "robotics",
    "cs.SC": "symbolic computation",
    "cs.SD": "sound",
    "cs.SE": "software engineering",
    "cs.SI": "social and information networks",
    "cs.SY": "systems and control",
    # stat.*
    "stat.AP": "statistics applications",
    "stat.CO": "statistical computation",
    "stat.ME": "statistics methodology",
    "stat.ML": "machine learning",
    "stat.OT": "other statistics",
    "stat.TH": "statistics theory",
    # eess.*
    "eess.AS": "audio and speech processing",
    "eess.IV": "image and video processing",
    "eess.SP": "signal processing",
    "eess.SY": "systems and control",
    # econ.*
    "econ.EM": "econometrics",
    "econ.GN": "general economics",
    "econ.TH": "theoretical economics",
    # q-bio.*
    "q-bio.BM": "biomolecules",
    "q-bio.CB": "cell behavior",
    "q-bio.GN": "genomics",
    "q-bio.MN": "molecular networks",
    "q-bio.NC": "neurons and cognition",
    "q-bio.OT": "other quantitative biology",
    "q-bio.PE": "populations and evolution",
    "q-bio.QM": "quantitative methods",
    "q-bio.SC": "subcellular processes",
    "q-bio.TO": "tissues and organs",
    # q-fin.*
    "q-fin.CP": "computational finance",
    "q-fin.EC": "economics",
    "q-fin.GN": "general finance",
    "q-fin.MF": "mathematical finance",
    "q-fin.PM": "portfolio management",
    "q-fin.PR": "pricing of securities",
    "q-fin.RM": "risk management",
    "q-fin.ST": "statistical finance",
    "q-fin.TR": "trading and market microstructure",
    # Archives with no subcategories.
    "gr-qc": "general relativity and quantum cosmology",
    "hep-ex": "high energy physics - experiment",
    "hep-lat": "high energy physics - lattice",
    "hep-ph": "high energy physics - phenomenology",
    "hep-th": "high energy physics - theory",
    "math-ph": "mathematical physics",
    "nucl-ex": "nuclear experiment",
    "nucl-th": "nuclear theory",
    "quant-ph": "quantum physics",
}

# Fallback for archives whose subcategory lists are large and change more
# often than it's worth tracking here -- the archive name is still a useful,
# consistent clustering term.
_ARCHIVE_NAMES: dict[str, str] = {
    "astro-ph": "astrophysics",
    "cond-mat": "condensed matter",
    "cs": "computer science",
    "econ": "economics",
    "eess": "electrical engineering and systems science",
    "math": "mathematics",
    "nlin": "nonlinear sciences",
    "physics": "physics",
    "q-bio": "quantitative biology",
    "q-fin": "quantitative finance",
    "stat": "statistics",
}


def category_label(term: str) -> str | None:
    """Readable label for an arXiv category code, or None for empty input.

    Falls back to the archive name, then to the code itself -- never drops a
    term, so an unrecognized category still groups its papers together.
    """
    term = (term or "").strip()
    if not term:
        return None
    exact = _CATEGORY_NAMES.get(term)
    if exact:
        return exact
    archive = _ARCHIVE_NAMES.get(term.split(".", 1)[0])
    if archive:
        return archive
    return term.lower()
