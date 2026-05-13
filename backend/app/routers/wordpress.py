from fastapi import APIRouter, HTTPException

from app.services.wordpress_service import wordpress_service

router = APIRouter(prefix="/wordpress", tags=["wordpress"])


@router.get("/categories")
async def get_wp_categories():
    try:
        categories = await wordpress_service.get_categories()
        return {
            "success": True,
            "data": [{"id": c["id"], "name": c["name"], "slug": c["slug"], "count": c.get("count", 0)} for c in categories],
        }
    except Exception as e:
        raise HTTPException(502, detail=f"Failed to fetch WP categories: {str(e)}")


@router.get("/tags")
async def get_wp_tags():
    try:
        tags = await wordpress_service.get_tags()
        return {
            "success": True,
            "data": [{"id": t["id"], "name": t["name"], "slug": t["slug"], "count": t.get("count", 0)} for t in tags],
        }
    except Exception as e:
        raise HTTPException(502, detail=f"Failed to fetch WP tags: {str(e)}")
