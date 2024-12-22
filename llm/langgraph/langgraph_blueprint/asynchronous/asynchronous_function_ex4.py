import asyncio

async def faulty_task():
    try:
        raise ValueError("An error occurred")
    except ValueError as e:
        print(f"Error: {e}")

asyncio.run(faulty_task())