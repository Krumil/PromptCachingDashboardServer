from fastapi import APIRouter, BackgroundTasks
from ..services.scheduler import scheduler_service
from ..services.blockchain import blockchain_service
import json

router = APIRouter()

@router.post("/update_addresses")
async def trigger_update_addresses(background_tasks: BackgroundTasks):
    background_tasks.add_task(scheduler_service.update_interacting_addresses)
    return {"message": "Address update initiated"}

@router.get("/update_ens")
async def trigger_update_ens(background_tasks: BackgroundTasks):
    background_tasks.add_task(blockchain_service.update_ens_names)
    return {"message": "ENS update initiated"}


@router.post("/recalculate_percentages")
async def recalculate_percentages():
    try:
        # Load current data
        with open("interacting_addresses.json", "r") as f:
            data = json.load(f)
        
        # Recalculate percentages and sort
        sorted_data = blockchain_service.calculate_and_sort_addresses(data)
        
        # Save updated data
        with open("interacting_addresses.json", "w") as f:
            json.dump(sorted_data, f, indent=4)
        
        return {"message": "Successfully recalculated percentages"}
    except Exception as e:
        return {"error": str(e)}


