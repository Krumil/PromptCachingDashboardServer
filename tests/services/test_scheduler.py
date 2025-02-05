"""
Tests for the scheduler service.

This module contains tests for the scheduler functionality, including:
- Scheduled updates
- Interval timing
- Error handling
- Status monitoring
"""
import json
import asyncio
import time
import pytest
from app.services.scheduler import scheduler_service
from app.services.blockchain import blockchain_service
from app.services.logging_service import logging_service

@pytest.mark.asyncio
async def test_ens_update():
    """Test only the ENS names update functionality"""
    try:
        print("\nTesting ENS names update...")
        task_name = "test_ens_update"
        logging_service.start_timer(task_name)
        
        await logging_service.log("\nStarting ENS names update...")
        # read data from interacting_addresses.json
        with open("interacting_addresses.json", "r") as f:
            sample_data = json.load(f)
        await blockchain_service.update_ens_names(sample_data)
        

        duration = logging_service.end_timer(task_name)
        print(f"ENS update test completed in {duration:.2f} seconds!")
    except Exception as e:
        print(f"Error during ENS update test: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_single_update():
    """Test a single update execution"""
    try:
        print("\nTesting single update execution...")
        await scheduler_service.update_interacting_addresses()
        print("Single update test completed successfully!")
    except Exception as e:
        print(f"Error during single update test: {str(e)}")
        raise

@pytest.mark.asyncio
async def test_scheduled_updates(interval_seconds=120, monitoring_time=600):
    """
    Test scheduled updates with monitoring.
    
    Args:
        interval_seconds (int): Seconds between updates (default: 120)
        monitoring_time (int): Total monitoring time in seconds (default: 600)
    """
    try:
        print(f"\nStarting scheduler test with {interval_seconds}s interval...")
        print(f"Will monitor for {monitoring_time} seconds...")
        
        # Start the scheduler (don't await it as it's not a coroutine)
        scheduler_service.schedule_test_update(interval_seconds=interval_seconds)
        start_time = time.time()
        
        # Monitor the scheduler
        while time.time() - start_time < monitoring_time:
            status = scheduler_service.get_scheduler_status()
            print("\nScheduler Status:")
            print(f"Running: {status['running']}")
            print(f"Number of jobs: {status['job_count']}")
            
            for job in status['jobs']:
                print(f"Job ID: {job['id']}")
                print(f"Next run: {job['next_run']}")
                print(f"Interval: {job['interval']}")
            
            await asyncio.sleep(30)  # Check status every 30 seconds
            
        print("\nScheduled test completed successfully!")
    
    except Exception as e:
        print(f"Error during scheduled test: {str(e)}")
        raise
    finally:
        try:
            print("Stopping scheduler...")
            scheduler_service.stop_scheduler()
        except Exception as e:
            print(f"Warning: Error while stopping scheduler: {str(e)}")

async def main():
    """Main test runner"""
    try:
        # # # Test ENS update only
        # await test_ens_update()
        
        # Test single update
        await test_single_update()
        
        # # Test scheduled updates
        # await test_scheduled_updates(
        #     interval_seconds=60,  # 1 minute intervals
        #     monitoring_time=300   # 5 minutes total
        # )
        
    except KeyboardInterrupt:
        print("\nTests interrupted by user.")
        try:
            scheduler_service.stop_scheduler()
        except Exception as e:
            print(f"Warning: Error while stopping scheduler: {str(e)}")
    except Exception as e:
        print(f"Test suite failed: {str(e)}")
        try:
            scheduler_service.stop_scheduler()
        except Exception as e:
            print(f"Warning: Error while stopping scheduler: {str(e)}")
        raise

if __name__ == "__main__":
    # Run the test suite
    asyncio.run(main()) 