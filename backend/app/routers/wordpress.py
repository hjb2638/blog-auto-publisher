from fastapi import APIRouter, HTTPException

from app.services.wordpress_service import wordpress_service

router = APIRouter(prefix="/wordpress", tags=["wordpress"])


@router.get("/me")
async def get_current_user():
    try:
        user = await wordpress_service.get_current_user()
        return {
            "success": True,
            "data": {
                "name": user.get("name"),
                "slug": user.get("slug"),
                "avatar_urls": user.get("avatar_urls"),
                "roles": user.get("roles", []),
                "description": user.get("description", ""),
            },
        }
    except Exception as e:
        raise HTTPException(502, detail=f"Failed to fetch WP user: {str(e)}")


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


@router.get("/posts")
async def get_wp_posts(page: int = 1, per_page: int = 20, status: str | None = None):
    try:
        posts = await wordpress_service.get_posts_paginated(page, per_page, status)
        return {"success": True, "data": posts, "meta": {"page": page, "per_page": per_page}}
    except Exception as e:
        raise HTTPException(502, detail=f"Failed to fetch WP posts: {str(e)}")


@router.get("/posts/{post_id}")
async def get_wp_post(post_id: int):
    try:
        post = await wordpress_service.get_post(post_id)
        return {"success": True, "data": post}
    except Exception as e:
        raise HTTPException(502, detail=f"Failed to fetch WP post: {str(e)}")


@router.put("/posts/{post_id}")
async def update_wp_post(post_id: int, body: dict):
    try:
        updated = await wordpress_service.update_post(post_id, **body)
        return {"success": True, "data": updated}
    except Exception as e:
        raise HTTPException(502, detail=f"Failed to update WP post: {str(e)}")


@router.delete("/posts/{post_id}")
async def delete_wp_post(post_id: int, force: bool = False):
    try:
        await wordpress_service.delete_post(post_id, force=force)
        return {"success": True, "data": {"deleted": True, "id": post_id}}
    except Exception as e:
        raise HTTPException(502, detail=f"Failed to delete WP post: {str(e)}")
