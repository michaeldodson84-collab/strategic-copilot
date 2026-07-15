from datetime import datetime, timedelta

# Default keywords for description-level pre-filter (broad search only)
_DEFAULT_AI_SIGNALS = [
    'ai', 'artificial intelligence', 'automation', 'agentic', 'machine learning',
    'llm', 'generative ai', 'ai-enabled', 'ai-driven', 'ai strategy',
]
_DEFAULT_DOMAIN_SIGNALS = [
    'gtm', 'go-to-market', 'revenue operations', 'revops', 'sales operations',
    'sales strategy', 'commercial operations', 'field operations',
]

# Known non-US location keywords — used when Location = "US only"
_NON_US = [
    'united kingdom', 'london', 'england', 'scotland', 'ireland', 'edinburgh', 'manchester',
    'germany', 'berlin', 'munich', 'frankfurt', 'hamburg',
    'france', 'paris', 'lyon',
    'netherlands', 'amsterdam', 'sweden', 'stockholm',
    'spain', 'madrid', 'barcelona', 'italy', 'milan', 'rome',
    'switzerland', 'zurich', 'geneva',
    'india', 'bangalore', 'bengaluru', 'mumbai', 'delhi', 'hyderabad', 'pune', 'chennai', 'gurgaon',
    'singapore', 'hong kong', 'australia', 'sydney', 'melbourne',
    'japan', 'tokyo', 'china', 'beijing', 'shanghai',
    'canada', 'toronto', 'vancouver', 'montreal',
    'israel', 'tel aviv', 'poland', 'warsaw', 'krakow',
    'brazil', 'sao paulo', 'mexico city',
    'emea', 'apac', 'latam', 'europe', 'asia pacific', 'asia-pacific', ', uk', '- uk',
]

# Fallback defaults used when profile fields are blank
_DEFAULT_SENIORITY = [
    'head of', 'vp ', 'vp,', 'vice president', 'director', 'chief',
    'principal', 'managing director', 'general manager',
]
_DEFAULT_TARGET = [
    'gtm', 'go-to-market', 'go to market', 'sales', 'revenue', 'commercial',
    'product ops', 'product operations', 'product strategy', 'business ops',
    'business operations', 'operations', ' ops', 'strategy', 'strategic',
    'transformation', 'enablement', 'customer success', 'customer experience',
    'partnerships', 'alliances', 'biz dev', 'ai strategy', 'ai lead', 'enterprise',
    'growth', 'chief of staff', 'value', 'market', 'field ',
]
_DEFAULT_EXCLUDE = [
    'engineer', 'devops', 'backend', 'frontend', 'fullstack', 'full-stack', 'qa ', 'sre ',
    'design', 'scientist', 'researcher', ' research', ' legal', 'counsel', 'attorney',
    'compliance', 'governance', 'regulatory', 'finance', 'financial', 'treasury',
    'accounting', 'controllership', 'procurement', 'tax ', 'compensation', 'benefits',
    'recruiter', 'recruiting', 'talent acquisition', 'brand ', 'content director',
    'creative director', 'communications', 'public relation', 'cybersecurity',
    'information security', 'security operation', 'supply chain', 'logistics',
    'facilities', 'real estate', 'data science', 'machine learning', 'clinical', 'medical',
]


def _parse_list(value: str) -> list:
    """Parse a comma-separated or pipe-separated string into a list of lowercase strings."""
    if not value or not value.strip():
        return []
    sep = '|' if '|' in value else ','
    return [item.strip().lower() for item in value.split(sep) if item.strip()]


def _build_filter_lists(profile: dict) -> tuple:
    """Return (location_mode, seniority, target, exclude) from profile, with defaults."""
    location = (profile.get('location') or '').strip().lower() or 'us only'
    seniority = _parse_list(profile.get('seniority_keywords', '')) or _DEFAULT_SENIORITY
    target    = _parse_list(profile.get('target_functions', ''))   or _DEFAULT_TARGET
    exclude   = _parse_list(profile.get('exclude_functions', ''))  or _DEFAULT_EXCLUDE
    return location, seniority, target, exclude


def is_too_old(job: dict, days: int = 30) -> bool:
    date_str = (job.get('date_posted') or '')[:10]
    if not date_str:
        return False
    try:
        return datetime.strptime(date_str, '%Y-%m-%d') < datetime.utcnow() - timedelta(days=days)
    except ValueError:
        return False


def _location_ok(loc: str, mode: str) -> bool:
    if not loc:
        return True
    loc = loc.strip().lower()

    if mode == 'remote only':
        return 'remote' in loc

    if mode == 'us only':
        if 'remote' in loc:
            return True
        return not any(k in loc for k in _NON_US)

    # "any" or anything else — no filtering
    return True


def passes_description_filter(job: dict, profile: dict = None) -> bool:
    """Require AI signal + GTM/domain signal both present in description. Used for broad search only."""
    profile = profile or {}
    desc = (job.get('description') or '').lower()
    if not desc:
        return True  # no description available — let title filter and scorer decide

    ai_signals     = _parse_list(profile.get('description_ai_signals', ''))     or _DEFAULT_AI_SIGNALS
    domain_signals = _parse_list(profile.get('description_domain_signals', '')) or _DEFAULT_DOMAIN_SIGNALS

    return any(s in desc for s in ai_signals) and any(s in desc for s in domain_signals)


def passes_title_filter(job: dict, profile: dict = None) -> bool:
    profile  = profile or {}
    location, seniority, target, exclude = _build_filter_lists(profile)

    title = (job.get('job_title') or '').lower()
    loc   = (job.get('location_raw') or '').strip()

    if not _location_ok(loc, location):
        return False

    has_seniority = any(s in title for s in seniority)
    has_exclude   = any(s in title for s in exclude)
    has_target    = any(f in title for f in target)

    return has_seniority and not has_exclude and has_target
