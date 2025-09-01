# src/preprocessing/regex_pass.py
import regex as re
from typing import List, Dict, Any, Optional

# ----------------------------
# Core requirement modality (kept)
# ----------------------------
MODALITY_RX = re.compile(
    r"\b(SHALL|MUST|SHOULD|MAY|WILL|REQUIRED?|PROHIBITED?|MUST\s+NOT|SHALL\s+NOT)\b[^.!?]*",
    re.I
)

# Time/deadline requirements like "within 10 business days"
TIME_REQUIREMENT_RX = re.compile(
    r"\b(?:within|no\s+later\s+than|not\s+later\s+than|NLT|prior\s+to|before|after)\s+"
    r"(\d+)\s*(?:calendar|business|working)?\s*(?:days?|months?|years?|hours?)",
    re.I
)

# Performance percentages (kept)
PERFORMANCE_RX = re.compile(
    r"\b(\d+)\s*(?:%|percent)\s+(?:accuracy|completion|standard|requirement|or\s+(?:higher|greater|more|less))",
    re.I
)

# Government forms and documents (kept)
GOV_FORM_RX = re.compile(
    r"\b(?:DHS|CBP|OPM|GSA|NIST|FIPS|OMB)\s*(?:Form|Publication|Directive|Handbook|MD|M-|SP)?\s*[\d\-A-Z]+",
    re.I
)

# Security standards and certifications (kept/expanded slightly)
SECURITY_STD_RX = re.compile(
    r"\b(?:FISMA|FIPS\s*\d+|NIST(?:\s*SP)?\s*\d+|Section\s*508|HSPD-12|PIV|"
    r"ISO\s*\d{3,5}|AS9100|CMMI|FedRAMP|SOC\s*\d|SSBI|"
    r"AES\s*\d+|SHA-\d+|TLS\s*\d+\.?\d*)\b",
    re.I
)

# Federal systems and programs (kept)
FED_SYSTEM_RX = re.compile(
    r"\b(?:CSRS|FERS|TSP|FEHB|FEGLI|COPRA|LEO|CBPO|OPM|GSA|FTR|"
    r"Federal\s+Travel\s+Regulations?|Thrift\s+Savings\s+Plan|"
    r"Federal\s+Employees?.{0,20}(?:Retirement|Health|Insurance))\b",
    re.I
)

# Labor categories and FTEs (kept)
LABOR_RX = re.compile(
    r"\b(?:FTE|Full[- ]Time\s+Equivalent|labor\s+categor(?:y|ies)|"
    r"(?:Senior|Junior|Journeyman)\s+(?:HCATS|position)|"
    r"\d+\s*(?:FTEs?|positions?|personnel|employees?))\b",
    re.I
)

# Deliverable references (kept)
DELIVERABLE_RX = re.compile(
    r"\b(?:deliverable|monthly\s+status\s+report|MSR|QCP|Quality\s+Control\s+Plan|"
    r"Transition[- ](?:In|Out)\s+Plan|Non-?Disclosure\s+Agreement|NDA)\b",
    re.I
)

# Dollar amounts and rates (kept)
COST_RX = re.compile(
    r"\$[\d,]+(?:\.\d{2})?|\b\d+\s*(?:hours?/FTE|hours?\s+per|hourly\s+rate)\b",
    re.I
)

# Section references (kept)
SECTION_REF_RX = re.compile(
    r"\b(?:Section|Sec\.?|§)\s*\d+(?:\.\d+)*",
    re.I
)

# ----------------------------
# New admin/Section L helpers
# ----------------------------
MONTH_RX = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
NUM_DATE_RX = r"(?P<numdate>\b\d{1,4}[/-]\d{1,2}[/-]\d{2,4}\b)"   # 08/31/2025, 31/8/2025, 2025-08-31 (with '/')
TEXT_DATE_RX1 = rf"(?P<textdate1>\b{MONTH_RX}\s+\d{{1,2}}(?:st|nd|rd|th)?(?:,)?\s+\d{{4}}\b)"  # August 31, 2025
TEXT_DATE_RX2 = rf"(?P<textdate2>\b\d{{1,2}}(?:st|nd|rd|th)?\s+{MONTH_RX}(?:,)?\s+\d{{4}}\b)"  # 31 Aug 2025
DATE_RX = rf"(?:{NUM_DATE_RX}|{TEXT_DATE_RX1}|{TEXT_DATE_RX2})"
TIME_RX = r"(?P<time>\b\d{1,2}:\d{2}\s?(?:am|pm|a\.m\.|p\.m\.)\b|\bEOD\b|\bCOB\b)"
TZ_RX = r"(?P<tz>\b[A-Z]{2,4}\b|Eastern\s+(?:Time|Standard|Daylight)\s*Time|Central\s+Time|Mountain\s+Time|Pacific\s+Time)"
NLT_WORDS = r"(?:no\s+later\s+than|not\s+later\s+than|nlt|by|before|due|deadline|submit(?:ted)?)"

def _norm_date(s: str) -> str:
    return (s or "").strip().rstrip(".,;")

def _value(groupdict: Dict[str, Any], *names: str) -> Optional[str]:
    for n in names:
        v = groupdict.get(n)
        if v:
            return v.strip()
    return None

# Deadlines (submission)
DEADLINE_RX = re.compile(
    rf"\b(?:due|submit(?:ted)?|deadline|{NLT_WORDS})\b.*?"
    rf"(?P<date>{DATE_RX})(?:\s*(?:at|by)\s*{TIME_RX})?(?:\s*(?:{TZ_RX}))?",
    re.I | re.S
)

# Questions due
QUESTIONS_RX = re.compile(
    rf"\b(questions?|clarification[s]?)\b.*?(?:{NLT_WORDS})\s*(?P<date>{DATE_RX})(?:\s*(?:at|by)\s*{TIME_RX})?(?:\s*(?:{TZ_RX}))?",
    re.I | re.S
)

# Page/slide limits and formatting
PAGE_LIMIT_RX = re.compile(
    r"\b(?:page(?:\s+count)?\s*(?:limit|maximum)|(?:shall\s+)?not\s+exceed|no\s+more\s+than)\s*"
    r"(?P<pages>\d{1,4})\s*(?:page|pages|pgs?|slides?)\b", re.I
)
LINE_SPACING_RX = re.compile(r"\b(?P<spacing>single[- ]?spaced|double[- ]?spaced|1\.5[- ]?spaced)\b", re.I)
FONT_RX = re.compile(
    r"\b(?:(?P<family>Times\s+New\s+Roman|Arial|Calibri)[^.\n]{0,40}?\b(?P<size>\d{1,2})\s*(?:pt|point)s?\b"
    r"|\bfont\s+size\s*(?P<size2>\d{1,2})\s*(?:pt|point)s?\b)", re.I)
MARGIN_RX = re.compile(r"\bmargin[s]?\s*(?:of|:)?\s*(?P<marg>0?\.\d+|\d(?:\.\d+)?)\s*(?:in|inch|in\.)s?\b", re.I)
FORMAT_RX = re.compile(r"\b(?P<fmt>PDF|MS\s*Word|Word|Excel|PowerPoint|PPTX|native\s+format|searchable\s+PDF)\b", re.I)

# File size limit and ZIP prohibition
EMAIL_SIZE_RX = re.compile(r"\b(?:email|attachment)\s+(?:size|limit)\s+(?:is|shall\s+be|must\s+be|may\s+not\s+exceed)\s+(?P<mb>\d{1,3})\s*MB\b", re.I)
ZIP_PROHIBITED_RX = re.compile(r"\b(?:ZIP|\.zip)\s+(?:files?\s+)?(?:are\s+)?(?:not\s+permitted|prohibited|disallowed)\b", re.I)

# File naming / labeling
LABELING_RX = re.compile(r"\b(?:label(?:ed|ling)?|file\s*name|file\s*naming|subject\s*line)\b[^.\n]{0,160}", re.I)

# Submission method: portal or email
SUBMIT_PORTAL_RX = re.compile(
    r"\b(?:submit|upload)\s+(?:via|through|to)\s+(?P<portal>(?:SAM\.gov|PIEE|WAWF|e[- ]?Buy|Grants\.gov|FedConnect|Seaport[- ]?NxG|DoD\s*SAFE|SharePoint|portal))\b",
    re.I
)
EMAIL_ADDR_RX = re.compile(r"(?P<email>\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b)")
SUBMIT_EMAIL_RX = re.compile(rf"(?:{NLT_WORDS}).{{0,120}}?{EMAIL_ADDR_RX.pattern}", re.I | re.S)

# Volumes / Tabs
ROMAN = r"(?:[IVXLCM]+)"
VOLUME_RX = re.compile(rf"\bVol(?:ume)?\s*(?P<volnum>\d+|{ROMAN})\b|\bVolume\s*(?P<volword>I|II|III|IV|V|VI|VII)\b", re.I)
TAB_RX = re.compile(r"\bTab\s*(?P<tab>[A-Z]|\d+)\b", re.I)

# Orals logistics
ORALS_PLATFORM_RX = re.compile(r"\b(?:Microsoft\s*Teams|Webex|Zoom|in[- ]?person)\b", re.I)
ORALS_DURATION_RX = re.compile(r"\b(?P<num>\d{1,3})\s*(?:minutes?|mins?)\b", re.I)
ORALS_HEADCOUNT_RX = re.compile(r"\b(?:max(?:imum)?\s*)?(?:presenters?|participants?|attendees?)\s*(?:is|are|shall\s+be|limited\s+to)?\s*(?P<n>\d+)\b", re.I)
ORALS_PROHIBITIONS_RX = re.compile(r"\b(?:no\s+recording|recording\s+is\s+prohibited|price\s+content\s+prohibited)\b", re.I)

# Evaluation criteria / weights (extend yours)
EVAL_CRITERIA_RX = re.compile(
    r"\b(?:evaluation|scoring|weight(?:ed|ing)|rated?|technical\s+(?:factor|criteria)|factor[s]?\s+(?:are|is))\b.*?"
    r"(?P<weight>\d+\s*(?:points?|%|percent))",
    re.I | re.S
)

# Deliverables / CDRLs / DI numbers
CDRL_RX = re.compile(r"\bCDRLs?\b|\bContract\s+Data\s+Requirements\s+List\b", re.I)
DI_RX = re.compile(r"\bDI-[A-Z]{2,4}-\d{3,6}\b", re.I)

# Reviews / Meetings
REVIEW_RX = re.compile(r"\b(?:SRR|PDR|CDR|PMR|IBR|TIM|FRR|KDP|kick[- ]?off|status\s+review|design\s+review)\b", re.I)

# Clauses / Contract type / Codes
CLAUSE_RX = re.compile(r"\b(?:FAR|DFARS)\s*(?:52\.\d{3}-\d{1,3}|\d{2}\.\d{3}(?:-\d{1,3})?)\b", re.I)
CONTRACT_TYPE_RX = re.compile(r"\b(?:FFP|Firm[-\s]?Fixed[-\s]?Price|T&M|Time[-\s]?and[-\s]?Materials|CPFF|Cost[-\s]?Plus[-\s]?Fixed[-\s]?Fee|IDIQ|BPA|BOA)\b", re.I)
NAICS_RX = re.compile(r"\bNAICS\b[^0-9]{0,10}(?P<naics>\d{6})\b", re.I)
PSC_RX = re.compile(r"\bPSC\b[^A-Z0-9]{0,10}(?P<psc>[A-Z]\d{3})\b", re.I)

# Place / Period of Performance
PLACE_RX = re.compile(r"\b(?:Place\s+of\s+Performance|PoP\s+Location|performance\s+will\s+be\s+at)\b[^.\n]{0,200}", re.I)
PERIOD_RX = re.compile(
    rf"\b(?:Period\s+of\s+Performance|PoP)\b[^.\n]{{0,80}}"
    rf"(?:(?:from|:\s*)\s*(?P<start>{DATE_RX}))?(?:[^.\n]{{0,40}}?(?:to|thru|-)\s*(?P<end>{DATE_RX}))?",
    re.I
)

# Travel / Key Personnel / Validity
TRAVEL_RX = re.compile(r"\btravel\b[^.\n]{0,120}\b(?:reimburs|in[- ]?accordance|per\s+diem|JTR|local|non[- ]?local)\b", re.I)
KEYPERS_RX = re.compile(r"\bkey\s+personnel\b[^.\n]{0,200}", re.I)
VALIDITY_RX = re.compile(r"\b(?:offer|quote|proposal)\s+(?:shall\s+remain\s+)?valid\s+for\s+(?P<days>\d{1,4})\s+days\b", re.I)

# ----------------------------
# Pattern registry
# ----------------------------
ALL_PATTERNS = [
    # your originals
    (MODALITY_RX,         "requirement"),
    (TIME_REQUIREMENT_RX, "time_requirement"),
    (PERFORMANCE_RX,      "performance"),
    (GOV_FORM_RX,         "gov_form"),
    (SECURITY_STD_RX,     "security_std"),
    (FED_SYSTEM_RX,       "fed_system"),
    (LABOR_RX,            "labor"),
    (DELIVERABLE_RX,      "deliverable"),
    (COST_RX,             "cost"),
    (SECTION_REF_RX,      "section_ref"),
    # extended / new
    (DEADLINE_RX,         "deadline"),
    (QUESTIONS_RX,        "questions_due"),
    (PAGE_LIMIT_RX,       "page_limit"),
    (LINE_SPACING_RX,     "line_spacing"),
    (FONT_RX,             "font_spec"),
    (MARGIN_RX,           "margin_spec"),
    (FORMAT_RX,           "format_spec"),
    (EMAIL_SIZE_RX,       "email_size_limit"),
    (ZIP_PROHIBITED_RX,   "zip_prohibited"),
    (LABELING_RX,         "file_labeling"),
    (SUBMIT_PORTAL_RX,    "submission_portal"),
    (SUBMIT_EMAIL_RX,     "submission_email_hint"),
    (EMAIL_ADDR_RX,       "email"),
    (VOLUME_RX,           "volume"),
    (TAB_RX,              "tab"),
    (ORALS_PLATFORM_RX,   "orals_platform"),
    (ORALS_DURATION_RX,   "orals_duration"),
    (ORALS_HEADCOUNT_RX,  "orals_headcount"),
    (ORALS_PROHIBITIONS_RX,"orals_prohibition"),
    (EVAL_CRITERIA_RX,    "eval_criteria"),
    (CDRL_RX,             "cdrl"),
    (DI_RX,               "di_number"),
    (REVIEW_RX,           "review_meeting"),
    (CLAUSE_RX,           "far_dfars"),
    (CONTRACT_TYPE_RX,    "contract_type"),
    (NAICS_RX,            "naics"),
    (PSC_RX,              "psc"),
    (PLACE_RX,            "place_of_performance"),
    (PERIOD_RX,           "period_of_performance"),
    (TRAVEL_RX,           "travel"),
    (KEYPERS_RX,          "key_personnel"),
    (VALIDITY_RX,         "quote_validity_days"),
]

# ----------------------------
# Extraction
# ----------------------------
def _normalize(kind: str, m: "re.Match") -> Optional[str]:
    gd = m.groupdict() if hasattr(m, "groupdict") else {}
    if kind in {"deadline", "questions_due"}:
        return " ".join(v for v in [_value(gd, "numdate","textdate1","textdate2"), _value(gd, "time"), _value(gd, "tz")] if v)
    if kind == "page_limit":
        return _value(gd, "pages")
    if kind in {"font_spec"}:
        fam = _value(gd, "family") or ""
        size = _value(gd, "size", "size2") or ""
        return f"{fam} {size}pt".strip()
    if kind == "margin_spec":
        return _value(gd, "marg")
    if kind == "format_spec":
        return (_value(gd, "fmt") or "").upper() or None
    if kind == "email_size_limit":
        return _value(gd, "mb")
    if kind == "submission_portal":
        return _value(gd, "portal")
    if kind in {"submission_email_hint", "email"}:
        return _value(gd, "email")
    if kind == "volume":
        return _value(gd, "volnum", "volword")
    if kind == "tab":
        return _value(gd, "tab")
    if kind == "orals_duration":
        return _value(gd, "num")
    if kind == "orals_headcount":
        return _value(gd, "n")
    if kind == "eval_criteria":
        return _value(gd, "weight")
    if kind == "di_number":
        return m.group(0)
    if kind in {"far_dfars", "security_std", "contract_type", "cdrl", "review_meeting",
                "place_of_performance", "orals_platform", "orals_prohibition",
                "key_personnel", "travel"}:
        return m.group(0)
    if kind == "naics":
        return _value(gd, "naics")
    if kind == "psc":
        return _value(gd, "psc")
    if kind == "period_of_performance":
        start = _value(gd, "numdate", "textdate1", "textdate2", "start")
        end   = _value(gd, "numdate", "textdate1", "textdate2", "end")
        if start or end:
            s = _norm_date(start) if start else ""
            e = _norm_date(end) if end else ""
            return f"{s} -> {e}".strip(" ->")
    if kind == "quote_validity_days":
        return _value(gd, "days")
    return None

def fast_hits(chunk: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract compliance-relevant items via regex.
    Returns a list of dicts with:
      kind, match, (optional) value, section, start_page, end_page, source
    """
    text = chunk.get("text", "") or ""
    if not text:
        return []

    matches: List[Dict[str, Any]] = []

    for rx, kind in ALL_PATTERNS:
        for m in rx.finditer(text):
            match_text = m.group(0).strip()

            # Expand the 'requirement' to sentence scope
            if kind == "requirement":
                start = max(0, text.rfind('.', 0, m.start()) + 1)
                end = text.find('.', m.end())
                if end == -1:
                    end = min(m.end() + 200, len(text))
                match_text = text[start:end].strip()

            # Skip very short & noisy matches
            if kind in {"requirement", "fed_system"} and len(match_text) < 10:
                continue

            matches.append({
                "kind": kind,
                "match": match_text[:500],
                "value": _normalize(kind, m),
                "section": chunk.get("section", "Unknown"),
                "start_page": chunk.get("start_page", 0),
                "end_page": chunk.get("end_page", 0),
                "source": "regex",
            })

    # Deduplicate (kind + value/match + page span)
    seen = set()
    uniq = []
    for hit in matches:
        key = (hit["kind"], hit.get("value") or hit["match"][:120],
               hit.get("start_page"), hit.get("end_page"))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(hit)

    return uniq

# ----------------------------
# Summary (kept, with light expansion)
# ----------------------------
def get_requirement_summary(text: str) -> dict:
    summary = {
        "total_requirements": 0,
        "shall_count": len(re.findall(r'\bSHALL\b', text, re.I)),
        "must_count": len(re.findall(r'\bMUST\b', text, re.I)),
        "should_count": len(re.findall(r'\bSHOULD\b', text, re.I)),
        "may_count": len(re.findall(r'\bMAY\b', text, re.I)),
        "deliverables": len(re.findall(r'\bdeliverable\b', text, re.I)),
        "has_security_requirements": bool(SECURITY_STD_RX.search(text)),
        "has_performance_metrics": bool(PERFORMANCE_RX.search(text)),
        "has_time_constraints": bool(TIME_REQUIREMENT_RX.search(text)),
        "has_certifications": bool(SECURITY_STD_RX.search(text)),
        "has_page_limits": bool(PAGE_LIMIT_RX.search(text)),
        "has_orals": bool(ORALS_PLATFORM_RX.search(text) or ORALS_DURATION_RX.search(text)),
        "has_section_l_formatting": any(rx.search(text) for rx in [FONT_RX, MARGIN_RX, FORMAT_RX, LINE_SPACING_RX]),
    }
    summary["total_requirements"] = (
        summary["shall_count"] + summary["must_count"] +
        summary["should_count"] + summary["may_count"]
    )
    return summary
