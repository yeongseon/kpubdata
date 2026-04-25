"""Quickstart: create a client and fetch base rate data from BOK."""

from kpubdata import Client

# Set KPUBDATA_BOK_API_KEY env var, or pass provider_keys directly.
client = Client.from_env()

ds = client.dataset("bok.base_rate")

result = ds.list(start_date="202401", end_date="202406")

for item in result.items:
    print(f"{item['TIME']} — {item['DATA_VALUE']}%")
