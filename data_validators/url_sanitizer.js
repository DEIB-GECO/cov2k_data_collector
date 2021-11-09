const endpoint = new URL("http://geco.deib.polimi.it/cov2k/api/variants/");
var args = new URLSearchParams({
    "nextsrain-id": "20A/S:98F",
    "pangolin-id": "21C (Epsilon)",
    "effects": [1, 2, 4]
});

args.forEach((value, key) => {
  endpoint.searchParams.append(key, value);
});
console.log(endpoint.toString())

// encodes arrays as comma separated list of values, but the comma is encoded too.