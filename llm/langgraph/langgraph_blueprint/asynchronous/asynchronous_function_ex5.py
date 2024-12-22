import asyncio

async def task1():
    raise ValueError("Error in Task 1")

async def task2():
    await asyncio.sleep(1)
    return "Task 2 completed successfully"

async def main():
    results = await asyncio.gather(task1(), task2(), return_exceptions=True)
    for result in results:
        if isinstance(result, Exception):
            print(f"Handled exception: {result}")
        else:
            print(result)

asyncio.run(main())