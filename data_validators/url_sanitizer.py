endpoint = "http://geco.deib.polimi.it/cov2k/api/variants/"
args = {
    "nextsrain-id": "20A/S:98F",
    "pangolin-id": "21C (Epsilon)"
}

if __name__ == '__main__':
    from urllib.parse import urljoin, urlencode

    url = urljoin(endpoint, urlencode(args, doseq=True))
    print(url, type(url))

# encodes array as of type:form explode:True
