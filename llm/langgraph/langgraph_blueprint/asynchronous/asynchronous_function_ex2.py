import asyncio

async def task1():
    await asyncio.sleep(1)
    print("Task 1 completed")
async def task2():
    await asyncio.sleep(2)
    print("Task 2 completed")
async def main():
    await task1()
    await task2()
asyncio.run(main())