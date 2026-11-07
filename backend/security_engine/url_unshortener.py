import urllib.parse
from typing import Dict, Any, List, Optional
import httpx

KNOWN_SHORTENERS = {
    "bit.ly", "tinyurl.com", "is.gd", "t.co", "cutt.ly", "clck.ru",
    "vk.cc", "cleanuri.com", "rb.gy", "v.gd", "t.me", "linktr.ee",
    "cutt.us", "goo.gl", "ow.ly", "buff.ly", "rebrand.ly", "shorturl.at",
    "qrs.ly", "s.id", "surv.es", "telegra.ph"
}

def is_shortened_domain(domain: str) -> bool:
    """Domen taniqli havolani qisqartirish xizmatiga tegishli ekanini tekshiradi."""
    domain_clean = domain.lower()
    if domain_clean.startswith("www."):
        domain_clean = domain_clean[4:]
    return domain_clean in KNOWN_SHORTENERS

async def trace_url_redirects(initial_url: str, max_hops: int = 7) -> Dict[str, Any]:
    """Qisqartirilgan yoki yashiringan havolani oxirgi manziliga qadar kuzatib boradi."""
    result = {
        "initial_url": initial_url,
        "final_url": initial_url,
        "is_shortened": False,
        "was_redirected": False,
        "redirect_chain": [],
        "intermediate_domains": [],
        "status_code": None
    }

    parsed = urllib.parse.urlparse(initial_url)
    domain = (parsed.hostname or "").lower()
    if domain.startswith("www."):
        domain = domain[4:]

    if is_shortened_domain(domain):
        result["is_shortened"] = True

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 ShieldGuard-Radar/2.0",
        "Accept": "*/*"
    }

    current_url = initial_url
    visited = [initial_url]

    try:
        async with httpx.AsyncClient(timeout=4.0, follow_redirects=True, verify=False) as client:
            # HEAD so'rovi orqali yengil va tez yo'naltirishlarni tekshirish
            resp = await client.head(current_url, headers=headers)
            result["status_code"] = resp.status_code
            result["final_url"] = str(resp.url)

            for hist in resp.history:
                h_url = str(hist.url)
                result["redirect_chain"].append(h_url)
                p_dom = urllib.parse.urlparse(h_url).hostname or ""
                if p_dom and p_dom not in result["intermediate_domains"]:
                    result["intermediate_domains"].append(p_dom)

            if len(resp.history) > 0:
                result["was_redirected"] = True
                final_dom = urllib.parse.urlparse(str(resp.url)).hostname or ""
                if final_dom and final_dom not in result["intermediate_domains"]:
                    result["intermediate_domains"].append(final_dom)

    except Exception:
        # HEAD ishlamasa, oddiy xavfsiz qisqa GET bilan urinib ko'rish
        try:
            async with httpx.AsyncClient(timeout=4.0, follow_redirects=True, verify=False) as client:
                resp = await client.get(current_url, headers=headers)
                result["status_code"] = resp.status_code
                result["final_url"] = str(resp.url)
                if len(resp.history) > 0:
                    result["was_redirected"] = True
                    for hist in resp.history:
                        result["redirect_chain"].append(str(hist.url))
        except Exception:
            pass

    return result
