from fastapi import APIRouter

router = APIRouter()


# PUBLIC_INTERFACE
@router.get("/", tags=["health"], summary="Health Check")
def health_check():
    """Simple health check endpoint returning a static message."""
    return {"message": "Healthy"}
