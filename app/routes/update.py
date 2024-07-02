from fastapi import APIRouter, BackgroundTasks
from ..services.scheduler import update_interacting_addresses

router = APIRouter()

@router.post("/update_addresses")
async def trigger_update_addresses(background_tasks: BackgroundTasks):
    background_tasks.add_task(update_interacting_addresses)
    return {"message": "Address update initiated"}
