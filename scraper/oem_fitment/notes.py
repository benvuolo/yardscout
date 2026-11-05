"""List-note clause classifier (CURATION_SPEC.md §5.6). Pure, no I/O.

A list row's notes ("US Built, Without Heated, Black;Without Heated, US
Built, Black") are split into segments on ";" and clauses on "," outside
parentheses. Each clause is tokenized left to right into atoms from a closed
vocabulary. Any leftover text makes the whole clause UNKNOWN, and UNKNOWN
restricts. This is an allow-list: a clause is neutral only when every atom
is NEUTRAL_SPEC (describes the part), NEUTRAL_MODEL (the cell's own catalog
model) or a YEARS span that contains the cell's year. Everything else makes
the row conditional (cover `maybe`).

Lexicon maintenance: every pattern carries a basis comment; new entries come
only by reviewed commit. curate.py counts UNKNOWN clauses in the report.
Ties between patterns of equal length go to the restricting class, so a new
pattern can never turn a restricting clause neutral by accident.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

NEUTRAL_CLASSES = frozenset({"NEUTRAL_SPEC", "NEUTRAL_MODEL"})
TRANSLATABLE = frozenset({"PLANT", "ENGINE", "FUEL", "TRANS"})
# equal-length tie-break order: restricting classes first, neutral last
PRIORITY = ["FUEL", "PLANT", "ENGINE", "TRANS", "EMISSIONS", "PRODUCTION", "BODY", "TRIM",
            "PACKAGE", "OPTION", "COLOUR", "POSITION", "MODEL_OTHER", "YEARS",
            "NEUTRAL_MODEL", "NEUTRAL_SPEC"]
ALL_CLASSES = PRIORITY + ["UNKNOWN"]

_I = re.I

# ------------------------------------------------------------------ lexicon
# (class, pattern, basis). Patterns are matched at the current position and
# must end at a word boundary.
_COLOUR_MOD = r"(?:dark|dk\.?|light|lt\.?|med(?:ium)?\.?|pale|deep|bright|super|frosted|frost|grayish|greyish|sky)"
_COLOUR_WORD = (r"(?:white|black|gray|grey|red|blue|green|silver|slver|beige|sand|titanium|magenta|"
                r"stratosphere|iris|jasper|ribbon|mirage|purple|purpl|gold|brown|tan|bronze|yellow|"
                r"orange|maroon|charcoal|graphite|pewter|champagne|burgundy|ivory|cream|copper|teal|"
                r"aqua|pearl|mica)")
_COLOUR_FIN = r"(?:pearl|mica|met\.?|metallic|m\.\s?m\.?|mc\.|cs\.|me\.|pc\.|\d)"
# longest alternatives first: Python alternation is first-match, not longest
_TRIM_WORD = (r"(?:le\s+plus|xle\s+limited|special\s+edition|sr5|xle|xse|xls|xl|le|se|ce|base|"
              r"limited|platinum|touring|sport|trd|prime|solara|spec|laredo|overland|latitude|"
              r"altitude|rubicon|sahara|trailhawk)")
_WITH = r"(?:with\s*/\s*without|with|without|w/o|w/|less|non|exc(?:ept)?\.?|excluding)"
_OPTION_PHRASE = (
    r"(?:heated|heater|heat|auto\s+dimmer|auto[\s-]+dimming|memory|signal\s+lamp|"
    r"turn\s+signal(?:\s+lamp)?|hid|high\s+intensity\s+discharge|auto\s+level(?:l?ing)?|"
    r"auto\s+high\s+beam|blind\s+spot(?:\s+monitor)?|auto\s+a/c\s+control|auto\s+a/c|"
    r"auto\s+climate(?:\s+control)?|atc|\d+(?:\.\d+)?\"\s*display|display|navigation|nav|"
    r"power\s+folding|power|manual|electric\s+remote\s+control(?:\s+mirror)?(?:\s+w/\s*heater)?|"
    r"windshield\s+deicer(?:-w/\s*wiper\s+deicer)?|wiper\s+deicer|"
    r"pre-collision\s+system(?:-with(?:out)?)?|seat\s+cover\s+material-[a-z]+|premium\s+audio|"
    r"jbl|sunroof|moonroof|fog\s+lamps?|puddle\s+lamps?|camera|homelink|compass|leather|"
    r"keyless\s+entry|smart\s+key|chrome|painted|auto\s+on/off|daytime\s+running\s+lamps?|drl|"
    r"led|halogen|projector|xenon|levell?ing)")

_STATIC: list[tuple[str, str, str]] = [
    # NEUTRAL_SPEC: the part's own rating (toyotapartsnow alternator/starter
    # list notes "12V 100A", "12V 1.7KW", "1.2 KW"; jeeppartsdeal "140 AMP").
    ("NEUTRAL_SPEC", r"\d{1,2}\s?V\s+\d{2,3}(?:\.\d+)?\s?A(?:MPS?)?", "toyotapartsnow '12V 100A' (f2652c3)"),
    ("NEUTRAL_SPEC", r"\d{1,2}\s?V\s+\d(?:\.\d+)?\s?KW", "toyotapartsnow '12V 1.7KW' (f2652c3)"),
    ("NEUTRAL_SPEC", r"\d(?:\.\d+)?\s?KW", "toyotapartsnow '1.2 KW' (f2652c3)"),
    ("NEUTRAL_SPEC", r"\d{2,3}\s?AMPS?", "jeeppartsdeal 4801477AG '140 AMP'"),
    # "New" labels the new (non-reman) row next to a reman one; it describes
    # the part, not the car (jeeppartsdeal 4801477AG "140 AMP, New").
    ("NEUTRAL_SPEC", r"new", "jeeppartsdeal 4801477AG '140 AMP, New'"),
    # YEARS: "2007-09", "1997-2001", "2016-18"; a single year.
    ("YEARS", r"(?:19|20)\d{2}\s*-\s*(?:(?:19|20)\d{2}|\d{2})", "toyotapartsnow '2007-09' (f2652c3)"),
    ("YEARS", r"(?:19|20)\d{2}", "single model year"),
    # PLANT: plant of manufacture (§1: the most common splitter).
    ("PLANT", r"(?:u\.?s\.?a?\.?|japan|canada|mexico|korea|georgia|kentucky|indiana|texas)\s+buil[dt](?:\s+only)?",
     "toyotapartsnow 'US Built', 'USA Built', 'Japan Build', 'US Built Only' (f2652c3)"),
    ("PLANT", r"(?:made|built)\s+in\s+(?:the\s+)?(?:u\.?s\.?a?\.?|japan|canada|mexico|korea)", "plant phrasing"),
    # ENGINE
    ("ENGINE", r"\d\.\d\s?l(?:\s+(?:v6|v8|v10|l4|i4|i5|i6|h4|h6|turbo|diesel))*", "toyotapartsnow '2.4L' (f2652c3)"),
    ("ENGINE", r"(?:v6|v8|v10|l4|i4|i5|i6|\d\s?cyl(?:inder)?)", "engine layout"),
    # FUEL: the model "Camry Hybrid" and the trim "Hybrid" (§5.6 table).
    ("FUEL", r"hybrid|plug-in(?:\s+hybrid)?|phev|fhev|cng|flex\s*fuel|ffv|diesel|gasoline|gas",
     "toyotapartsnow 'Camry Hybrid' (f2652c3); fuel words"),
    # TRANS
    ("TRANS", r"(?:manual|automatic|auto)\s+trans(?:mission)?|a/t|m/t|cvt|\d\s?(?:at|mt|spd|speed)",
     "toyotapartsnow 'Manual Transmission', 'Auto Transmission' (f2652c3)"),
    # EMISSIONS
    ("EMISSIONS", r"(?:california|calif\.?|federal|fed\.?|49[\s-]*states?|50[\s-]*states?|cal)\s+emissions?(?:\s+only)?",
     "toyotapartsnow 'California Emissions', 'Federal Emissions' (f2652c3)"),
    ("EMISSIONS", r"pzev|sulev|ulev|lev|zev", "emission classes"),
    # PRODUCTION dates: never translatable.
    ("PRODUCTION", r"(?:from|thru|through|after|before|to|up\s+to|till|until|prior\s+to)\s+\d{1,2}/\d{1,2}(?:/\d{2,4})?",
     "toyotapartsnow 'From 4/97' (f2652c3)"),
    ("PRODUCTION", r"\(\s*\d{1,2}/\d{2}\s*-\s*(?:\d{1,2}/\d{2})?\s*\)?", "'(mm/yy-' (§5.6)"),
    # BODY
    ("BODY", r"coupe|convertible|sedan|wagon|hatchback|liftback|(?:regular|extended|crew|double|access|king|quad|super)\s*cab|\d\s?-?doors?|[245]\s?dr",
     "toyotapartsnow 'Coupe', 'Convertible' (f2652c3)"),
    # TRIM: "With XLE", "Without SE", "LE & XLE", "CE PACKAGE ...", "Without
    # Prime", "With Solara" (§5.6 table).
    ("TRIM", rf"(?:{_WITH}\s*)?{_TRIM_WORD}(?:\s*(?:&|and|/)\s*{_TRIM_WORD})*(?:\s+(?:package|pkg|grade|models?))?",
     "toyotapartsnow 'With XLE', 'LE & SE', 'CE PACKAGE' (f2652c3)"),
    # PACKAGE / MARKET
    ("PACKAGE", r"\d+(?:st|nd|rd|th)\s+anniversary(?:\s*\([a-z]+\))?", "toyotapartsnow '20TH ANNIVERSARY(USA)'"),
    ("PACKAGE", r"(?:usa?|korea|japan|canada|europe|gcc|mexico|china|taiwan|australia)\s+spec(?:ification)?",
     "toyotapartsnow 'KOREA SPEC' (f2652c3)"),
    # (the words before "package" may not be "package": "CE PACKAGE CE
    # PACKAGE" is two TRIM atoms, the tie going to TRIM)
    ("PACKAGE", r"(?:(?!package\b|pkg\b)[a-z0-9]+\s+){0,3}(?:package|pkg)(?:-for\s+\d+\s*lbs)?",
     "toyotapartsnow 'USA VALUE PACKAGE', 'TOWING PACKAGE-FOR 3500LBS'"),
    # OPTION: "With/Without Heated", "Power With Heater", "Without Auto
    # Dimmer", "Without 11.6\" Display", "Power", "Manual" (§5.6 table).
    ("OPTION", rf"(?:power\s+)?(?:{_WITH}[\s-]*)?{_OPTION_PHRASE}", "toyotapartsnow option notes (f2652c3)"),
    # Mopar sales codes in brackets (jeeppartsdeal 4801477AA "[BAE]") and
    # PartsGiant "Fitting Vehicle Options: <codes>" both name an option.
    ("OPTION", r"\[[a-z0-9]{2,4}\]", "jeeppartsdeal '[BAE]' sales code"),
    ("OPTION", r"fitting\s+vehicle\s+options?\s*:.*", "PartsGiant list_info 'Fitting Vehicle Options: VQ35DE'"),
    # COLOUR: names with modifiers, a paint code, "Red (3P5)".
    ("COLOUR", rf"(?:{_COLOUR_MOD}\s*)*{_COLOUR_WORD}(?:\s*(?:{_COLOUR_WORD}|{_COLOUR_FIN}))*(?:\s*\(\s*[0-9][a-z0-9]{{2}}\s*\))?",
     "toyotapartsnow mirror colour notes (f2652c3)"),
    ("COLOUR", r"[0-9][a-z0-9]{2}", "Toyota paint codes '1D7', '3Q3', '040' (f2652c3)"),
    # POSITION: feeds positions.py (mount axis); restricting for notes.
    ("POSITION", r"(?:front|rear|left|right|lh|rh|l/h|r/h|upper|lower|inner|outer|center|centre|"
                 r"driver'?s?(?:\s+side)?|passenger'?s?(?:\s+side)?)(?:\s+(?:side|left|right|lh|rh))?",
     "toyotapartsnow 'Left', 'Right', 'Front' (f2652c3)"),
    ("POSITION", r"on\s+(?:body|side\s+panel|trunk\s+lid|back\s+door|lift\s*gate|tail\s*gate|deck\s*lid|quarter\s+panel|bumper|fender)",
     "toyotapartsnow 'On Body', 'On Side Panel' (f2652c3)"),
]
# Every atom must end at a word boundary: either its last character is not
# alphanumeric or the next one is not. Inside the regex, so alternation
# backtracks to an alternative that satisfies it.
_END = r"(?:(?<![A-Za-z0-9])|(?![A-Za-z0-9]))"


def _rx(p: str):
    return re.compile(rf"(?:{p}){_END}", _I)


_STATIC_RX = [(c, _rx(p), b) for c, p, b in _STATIC]


@dataclass(frozen=True)
class NoteContext:
    """year: the cell's model year. own_models: the cell's catalog model
    name(s), case-folded. ns_models: every catalog model name seen in the
    namespace, case-folded (so "Prius" on a Camry cell is MODEL_OTHER, not
    UNKNOWN)."""
    year: int | None = None
    own_models: frozenset = frozenset()
    ns_models: frozenset = frozenset()


@dataclass(frozen=True)
class Atom:
    cls: str
    text: str
    value: object = None


@dataclass(frozen=True)
class Clause:
    text: str
    cls: str
    atoms: tuple = ()
    satisfied: bool | None = None   # YEARS only: does the span contain ctx.year
    leftover: str = ""

    @property
    def neutral(self) -> bool:
        return self.cls in NEUTRAL_CLASSES or (self.cls == "YEARS" and self.satisfied is True)


@dataclass
class Verdict:
    segments: list = field(default_factory=list)    # [[Clause]]
    clean: bool = True
    classes: set = field(default_factory=set)       # restricting classes present
    unknown: list = field(default_factory=list)     # UNKNOWN clause texts
    years_unsatisfied: bool = False


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def split_clauses(segment: str) -> list[str]:
    out, depth, cur = [], 0, []
    for ch in segment:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            out.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur).strip())
    return [x for x in out if x]


def split_note(text: str) -> list[list[str]]:
    """'A, B;C' -> [['A', 'B'], ['C']]. Empty segments are dropped."""
    segs = []
    for seg in _clean(text).split(";"):
        cl = split_clauses(seg)
        if cl:
            segs.append(cl)
    return segs


def _model_rx(name: str) -> str:
    return r"\s+".join(re.escape(w) for w in name.split())


_DYN_CACHE: dict = {}


def _dynamic(ctx: NoteContext):
    key = (ctx.own_models, ctx.ns_models)
    if key not in _DYN_CACHE:
        pats = []
        for m in sorted(ctx.own_models, key=len, reverse=True):
            if m:
                pats.append(("NEUTRAL_MODEL", _rx(_model_rx(m)), "the cell's own catalog model"))
                # "<own model> Hybrid" names the hybrid (FUEL)
                pats.append(("FUEL", _rx(_model_rx(m) + r"\s+hybrid"), "'Camry Hybrid' on a Camry cell"))
        for m in sorted(ctx.ns_models - ctx.own_models, key=len, reverse=True):
            if m:
                pats.append(("MODEL_OTHER", _rx(_model_rx(m)), "another catalog model of the namespace"))
        _DYN_CACHE[key] = pats
    return _DYN_CACHE[key]


def _year_span(text: str) -> tuple[int, int] | None:
    m = re.match(r"((?:19|20)\d{2})(?:\s*-\s*(\d{2,4}))?$", text.strip())
    if not m:
        return None
    lo = int(m.group(1))
    if not m.group(2):
        return lo, lo
    e = m.group(2)
    if len(e) == 4:
        return lo, int(e)
    hi = (lo // 100) * 100 + int(e)
    if hi < lo:
        hi += 100
    return lo, hi


def tokenize(text: str, ctx: NoteContext) -> tuple[list[Atom], str]:
    """Atoms left to right; the second value is any text no atom consumed."""
    s = _clean(text)
    pats = _dynamic(ctx) + _STATIC_RX
    atoms: list[Atom] = []
    pos = 0
    n = len(s)
    while pos < n:
        while pos < n and (s[pos].isspace() or s[pos] == "&"):
            pos += 1
        if pos >= n:
            break
        best = None
        for cls, rx, _b in pats:
            m = rx.match(s, pos)
            if not m or m.end() == pos:
                continue
            end = m.end()
            if end < n and s[end].isalnum() and s[end - 1].isalnum():
                continue    # must end at a word boundary
            rank = (end - pos, -PRIORITY.index(cls))
            if best is None or rank > best[0]:
                best = (rank, cls, m)
        if best is None:
            return atoms, s[pos:]
        _, cls, m = best
        val = None
        if cls == "YEARS":
            val = _year_span(m.group(0))
        elif cls == "PLANT":
            w = m.group(0).lower().replace(".", "")
            for k, v in (("usa", "US"), ("us", "US"), ("japan", "JP"), ("canada", "CA"),
                         ("mexico", "MX"), ("korea", "KR"), ("georgia", "US"), ("kentucky", "US"),
                         ("indiana", "US"), ("texas", "US")):
                if re.search(rf"\b{k}\b", w):
                    val = v
                    break
        elif cls == "ENGINE":
            lm = re.match(r"(\d\.\d)", m.group(0))
            val = float(lm.group(1)) if lm else None
        elif cls == "FUEL":
            val = "hybrid" if re.search(r"hybrid|fhev", m.group(0), _I) else m.group(0).lower()
        elif cls == "TRANS":
            val = "manual" if re.search(r"manual|m/t|mt", m.group(0), _I) else "auto"
        atoms.append(Atom(cls, m.group(0), val))
        pos = m.end()
    return atoms, ""


def classify_clause(text: str, ctx: NoteContext) -> Clause:
    atoms, leftover = tokenize(text, ctx)
    if leftover or not atoms:
        return Clause(text, "UNKNOWN", tuple(atoms), None, leftover or text)
    years = [a for a in atoms if a.cls == "YEARS"]
    sat = None
    if years:
        sat = all(a.value is not None and ctx.year is not None and a.value[0] <= ctx.year <= a.value[1]
                  for a in years)
    restricting = [a for a in atoms if a.cls not in NEUTRAL_CLASSES and a.cls != "YEARS"]
    if restricting:
        cls = restricting[0].cls
    elif years:
        cls = "YEARS"
    else:
        cls = atoms[0].cls
    return Clause(text, cls, tuple(atoms), sat, "")


def classify(texts, ctx: NoteContext) -> Verdict:
    """Classify every note string that T's own rows print for one pn."""
    v = Verdict()
    for t in texts or []:
        for seg in split_note(t):
            row = [classify_clause(c, ctx) for c in seg]
            v.segments.append(row)
            for c in row:
                if c.neutral:
                    continue
                v.clean = False
                if c.cls == "YEARS":
                    v.years_unsatisfied = True
                    v.classes.add("YEARS")
                else:
                    v.classes.add(c.cls)
                if c.cls == "UNKNOWN":
                    v.unknown.append(c.text)
                # atoms inside a restricting clause also restrict
                for a in c.atoms:
                    if a.cls not in NEUTRAL_CLASSES and a.cls != "YEARS":
                        v.classes.add(a.cls)
    return v


def cond_dnf(v: Verdict) -> list[dict] | None:
    """§5.18 Phase 2: the notes as a DNF over translatable atoms, or None when
    any segment holds an UNKNOWN or a non-translatable restricting clause.
    Each disjunct is {atom: value}. Never shipped in Phase 1."""
    if not v.segments:
        return [{}]
    out = []
    for seg in v.segments:
        conj: dict = {}
        dead = False
        for c in seg:
            if c.cls == "UNKNOWN":
                return None
            for a in c.atoms:
                if a.cls in NEUTRAL_CLASSES:
                    continue
                if a.cls == "YEARS":
                    if c.satisfied is not True:
                        dead = True
                    continue
                if a.cls not in TRANSLATABLE or a.value is None:
                    return None
                key = a.cls.lower()
                if key in conj and conj[key] != a.value:
                    dead = True
                conj[key] = a.value
        if not dead and conj not in out:
            out.append(conj)
    return out


# ----------------------------------------------------------- name qualifiers
QUALIFIER_RE = re.compile(
    r"(?:^|[\s,;(])(w/o|w/|with(?:out)?|less|exc(?:ept)?|excl(?:uding)?|for\s+(?:models|vehicles)\s+with|"
    r"if\s+equipped)\s*([^,;)]*)", re.I)


def qualifier_phrases(text: str, content_tokens=(), cat: str = "") -> list[str]:
    """Qualifier phrases in a name that may condition the car (§5.6). Phrases
    naming only a CONTENT_TOKENS object of the category describe the assembly
    and are exempt; "with/without motor" on regulators is packaging (§5.8)."""
    out = []
    for m in QUALIFIER_RE.finditer(text or ""):
        phrase = (m.group(1) + " " + m.group(2)).strip()
        obj = m.group(2).strip().lower()
        if not obj and m.group(1).lower() != "if equipped":
            continue
        words = set(re.findall(r"[a-z]+", obj))
        if words and words <= set(t.lower() for t in content_tokens):
            continue
        if cat == "window-regulator" and re.search(r"\bmotor\b", obj):
            continue
        out.append(phrase)
    return out
