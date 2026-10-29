import re, unicodedata


def slugify(s):
    s = s.lower().replace('×', 'x').replace('–', '-').replace('’', '').replace("'", '').replace('ß', 'ss')
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s
