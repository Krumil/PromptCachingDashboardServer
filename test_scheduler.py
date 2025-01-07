import asyncio
from app.services.scheduler import schedule_hourly_update, update_interacting_addresses

async def test_scheduler():
    print("Starting scheduler test...")
    
    # Run initial update
    print("Running initial update...")
    await update_interacting_addresses()
    
    # Start scheduler
    print("Starting scheduler...")
    schedule_hourly_update()
    
    # Keep the script running to observe scheduled updates
    print("Scheduler is running. Press Ctrl+C to stop.")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nTest ended by user.")

if __name__ == "__main__":
    asyncio.run(test_scheduler()) 