"""Search and browse available datasets using the Catalog API."""

from kpubdata import Client

client = Client.from_env()

# List all datasets from a specific provider
for ds in client.datasets.list(provider="bok"):
    print(ds.id, ds.name)

# Fuzzy search across name, description, tags, and id
results = client.datasets.search("예보")
for ds in results:
    print(ds.id, ds.name, ds.tags)

# Strict search with higher threshold
strict = client.datasets.search("금리", threshold=0.8)
for ds in strict:
    print(ds.id, ds.name)
