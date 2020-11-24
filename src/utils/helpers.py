def getKeyOrDefault(attrdict, key, default=None):
    if attrdict is None:
        return default
    return attrdict[key] if key in attrdict else default
