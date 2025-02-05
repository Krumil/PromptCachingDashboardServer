from .blockchain import blockchain_service
from .cache import cache_service
from .logging_service import logging_service
from .dune import dune_service
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import json
import datetime

load_dotenv()

class SchedulerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.ETH_NETWORK = "eth-mainnet"
        self.BASE_NETWORK = "base-mainnet"

    async def update_interacting_addresses(self):
        """
        1) Fetch interacting addresses from Dune.
        2) Fetch cache data for the addresses.
        3) Add avatar count to the data.
        4) Save to JSON.
        5) Recalculate percentages and sort
        6) Update ENS names
        """
        task_name = "update_interacting_addresses"
        logging_service.start_timer(task_name)
        
        start_time = datetime.datetime.now()
        await logging_service.log(f"🕒 Starting update at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        await logging_service.log("Step 1: Fetching interacting addresses from Dune...")

        # Fetch addresses from Dune
        merged_addresses = await dune_service.get_interacting_addresses()
            
        await logging_service.log(f"Dune returned {len(merged_addresses)} addresses.")

        # Step 3: Fetch wayfinder data for the merged addresses
        await logging_service.log("Fetching wayfinder data for addresses...")
        wayfinder_data = await cache_service.fetch_wayfinder_data(list(merged_addresses))
        valid_wayfinder_data = [item for item in wayfinder_data if item["data"] is not None]
        await logging_service.log(f"Retrieved wayfinder data for {len(valid_wayfinder_data)} addresses (non-empty data).")


        # Step 4: Add avatar count to the data
        await logging_service.log("Getting avatar count for addresses...")
        valid_wayfinder_data = await blockchain_service.get_avatar_count(valid_wayfinder_data)

        # Step 5: Recalculate percentages and sort
        valid_wayfinder_data = blockchain_service.calculate_and_sort_addresses(valid_wayfinder_data)


        # Step 6: Update ENS names and recalculate percentages
        await logging_service.log("\nStarting ENS names update...")
        wayfinder_data_with_ens = await blockchain_service.add_ens_names(valid_wayfinder_data)
        
		# Save sorted data
        with open("interacting_addresses.json", "w") as f:
            json.dump(wayfinder_data_with_ens, f, indent=4)
        
        end_time = datetime.datetime.now()
        duration = logging_service.end_timer(task_name)
        await logging_service.log(
            f"🏁 Update Summary:\n"
            f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Ended: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Duration: {duration:.2f} seconds"
        )

    def schedule_daily_update(self):
        """Schedule the update_interacting_addresses function to run once per day"""
        self.scheduler.add_job(self.update_interacting_addresses, 'interval', days=1)
        self.scheduler.start()

    def schedule_test_update(self, interval_seconds=300):
        """
        Schedule updates with a custom interval for testing purposes.
        Default is 5 minutes (300 seconds).
        """
        self.scheduler.add_job(
            self.update_interacting_addresses, 
            'interval', 
            seconds=interval_seconds,
            next_run_time=datetime.datetime.now()  # Run immediately
        )
        self.scheduler.start()
        return None

    def stop_scheduler(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        return "Scheduler stopped"

    def get_scheduler_status(self):
        """Get the current status of the scheduler"""
        jobs = self.scheduler.get_jobs()
        status = {
            "running": self.scheduler.running,
            "job_count": len(jobs),
            "jobs": [{
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else None,
                "interval": str(job.trigger),
            } for job in jobs]
        }
        return status

# Create a singleton instance
scheduler_service = SchedulerService()