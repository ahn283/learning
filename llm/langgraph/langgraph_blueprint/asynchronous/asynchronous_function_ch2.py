import asyncio

async def task(name):
    await asyncio.sleep(1)
    print(f"Task {name} completed")

async def main():
    await asyncio.gather(task("A"), task("B"), task("C"))
    
asyncio.run(main())