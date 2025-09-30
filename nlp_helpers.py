import dateparser
import re

def extract_datetime(text, ref_date=None):
    """
    Tries to parse a datetime from Vietnamese text using dateparser.
    Returns a datetime object or None.
    """
    settings = {'PREFER_DATES_FROM': 'future', 'RETURN_AS_TIMEZONE_AWARE': False}
    if ref_date:
        settings['RELATIVE_BASE'] = ref_date
    try:
        dt = dateparser.parse(text, settings=settings, languages=['vi'])
        return dt
    except Exception:
        return None

def extract_title(text):
    t = text.strip().split('\n')[0]
    if len(t) > 120:
        t = t[:120] + '...'
    return t

def extract_location(text):
    m = re.search(r'(Địa điểm|Tại|địa chỉ|tại)\s*[:\-]?\s*(.+)', text, flags=re.I)
    if m:
        return m.group(2).strip().split('\n')[0]
    return None
