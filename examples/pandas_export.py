"""Export query results to a pandas DataFrame.

Requires: pip install kpubdata[pandas]
"""

from kpubdata import Client

client = Client.from_env()

ds = client.dataset("bok.base_rate")
result = ds.list(start_date="202401", end_date="202412")

df = result.to_pandas()
print(df.head())
print(f"\nTotal rows: {len(df)}")
