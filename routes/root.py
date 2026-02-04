"""
Root API endpoint.

Returns HSDS API metadata as required by the specification.
"""
from fastapi import APIRouter
from models.hsds import ApiInfo
from config import get_settings

router = APIRouter()


@router.get("/", response_model=ApiInfo, tags=["metadata"])
async def get_api_info():
    """
    Get API metadata.
    
    REQUIRED endpoint per HSDS specification.
    Returns version, profile URI, and OpenAPI URL.
    """
    settings = get_settings()
    return ApiInfo(
        version=settings.api_version,
        profile=settings.api_profile,
        openapi_url="/openapi.json"
    )
