import asyncio

async def fecthc_data():
    await asyncio.sleep(1)      # Simulates a non blocking wait
    return "Data Fectched!"

# Run the asynchronous function
result = asyncio.run(fecthc_data())
print(result) 