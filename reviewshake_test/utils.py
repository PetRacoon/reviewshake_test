from urllib.parse import urlparse, urlencode, urlunparse, parse_qs


def update_querystring(url, query):
    """Takes url and dict-like query and replase query in url.
    """
    parsed_url = list(urlparse(url))
    _query = extract_querystring(url)
    _query.update(query)
    query = _query
    parsed_url[4] = urlencode(query, True)
    return urlunparse(parsed_url)


def change_query_parameter(url, name, value):
    """Update single query parameter only if it exists in original URL

    :param url: original URL
    :param name: name of parameter to be changed
    :param value: new value
    :return: updated URL
    :raises: KeyError if parameter wasn't found in original URL query

    """
    query = extract_querystring(url)
    if name not in query:
        raise KeyError(u'parameter {} is not present in query'.format(name))
    return update_querystring(url, {name: value})


def extract_querystring(url):
    parsed_url = urlparse(url)
    return {k: v[0] for k, v in parse_qs(parsed_url.query).items()}
