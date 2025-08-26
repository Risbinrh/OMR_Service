from fastapi import APIRouter
from datetime import datetime
import psutil
import os

from app.core.models import HealthCheck
from app import __version__

router = APIRouter()


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint to verify service status"""
    from app.main import get_app_uptime
    
    return HealthCheck(
        status="healthy",
        version=__version__,
        uptime=get_app_uptime(),
        timestamp=datetime.utcnow()
    )


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with system metrics"""
    from app.main import get_app_uptime
    
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "status": "healthy",
        "version": __version__,
        "uptime": get_app_uptime(),
        "timestamp": datetime.utcnow(),
        "system": {
            "cpu": {
                "percent": cpu_percent,
                "cores": os.cpu_count()
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            "disk": {
                "total": disk.total,
                "free": disk.free,
                "percent": disk.percent
            }
        },
        "python_version": os.sys.version,
        "platform": os.sys.platform
    }