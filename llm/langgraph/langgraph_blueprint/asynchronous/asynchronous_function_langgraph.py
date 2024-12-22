import asyncio

async def fetch_data_from_node(node_id, api_url):
    print(f"Node {node_id}: Fetching data from {api_url}...")
    await asyncio.sleep(2)  # simulate a network delay
    print(f"Node {node_id}: Completed data fetch from {api_url}")
    return f"Data from {api_url}"

async def main():
    # URLs for data fetching in different codes
    nodes = {
        "Node 1": "https://api.example.com/data1",
        "Node 2": "https://api.example.com/data2",
        "Node 3": "https://api.example.com/data3"
    }
    # Concurrently fetch data for all nodes
    results = await asyncio.gather(
        *(fetch_data_from_node(node_id, url) for node_id, url in nodes.items())
    )
    print("All data fetched: ", results)

asyncio.run(main())