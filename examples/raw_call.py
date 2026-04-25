"""Use call_raw to access the original provider API directly."""

from kpubdata import Client

client = Client.from_env()

ds = client.dataset("datago.air_quality")

# Call the provider's native operation with original parameter names.
raw = ds.call_raw(
    "getCtprvnRltmMesureDnsty",
    sidoName="서울",
    numOfRows="5",
)

print(raw)
