import base64

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.utils.logger import logger


def _is_retryable(e: BaseException) -> bool:
    if isinstance(e, httpx.HTTPStatusError):
        code = e.response.status_code
        if code == 401:
            return False
        return code in {429, 500, 502, 503}
    return isinstance(e, (httpx.ConnectError, httpx.ReadTimeout))


class WordPressService:
    def __init__(self):
        self.api_url = settings.wp_api_url.rstrip("/")
        credentials = f"{settings.wp_username}:{settings.wp_app_password.get_secret_value()}"
        token = base64.b64encode(credentials.encode()).decode()
        self.auth_header = {"Authorization": f"Basic {token}"}

    @retry(
        retry=retry_if_exception(_is_retryable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=8),
        reraise=True,
    )
    async def _request(self, method: str, path: str, json_data: dict | None = None) -> dict:
        url = f"{self.api_url}{path}"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.request(method, url, headers=self.auth_header, json=json_data)
            if resp.status_code == 409 and json_data and "slug" in json_data:
                json_data["slug"] = f"{json_data['slug']}-2"
                resp = await client.request(method, url, headers=self.auth_header, json=json_data)
            resp.raise_for_status()
            return resp.json()

    async def get_posts(self, per_page: int = 20) -> list[dict]:
        return await self._request("GET", f"/wp/v2/posts?per_page={per_page}")

    async def create_post(
        self,
        title: str,
        content: str,
        slug: str | None = None,
        status: str = "publish",
        category_id: int | None = None,
        tag_ids: list[int] | None = None,
        featured_media_id: int | None = None,
    ) -> dict:
        data: dict = {"title": title, "content": content, "status": status}
        if slug:
            data["slug"] = slug
        if category_id:
            data["categories"] = [category_id]
        if tag_ids:
            data["tags"] = tag_ids
        if featured_media_id:
            data["featured_media"] = featured_media_id
        logger.info("WP create post: title=%s status=%s featured_media=%s", title, status, featured_media_id)
        return await self._request("POST", "/wp/v2/posts", data)

    async def upload_media(self, image_url: str, alt_text: str = "") -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            img_resp = await client.get(image_url)
            img_resp.raise_for_status()
            filename = image_url.split("/")[-1].split("?")[0] or "image.jpg"
            files = {"file": (filename, img_resp.content, "image/jpeg")}
            resp = await client.post(
                f"{self.api_url}/wp/v2/media",
                headers=self.auth_header,
                files=files,
            )
            resp.raise_for_status()
            media = resp.json()
            if alt_text:
                await client.post(
                    f"{self.api_url}/wp/v2/media/{media['id']}",
                    headers=self.auth_header,
                    json={"alt_text": alt_text},
                )
        logger.info("WP upload media: url=%s id=%s", image_url, media["id"])
        return media

    async def get_categories(self) -> list[dict]:
        return await self._request("GET", "/wp/v2/categories?per_page=100")

    async def get_tags(self) -> list[dict]:
        return await self._request("GET", "/wp/v2/tags?per_page=100")

    async def create_category(self, name: str, slug: str | None = None) -> dict:
        data = {"name": name}
        if slug:
            data["slug"] = slug
        return await self._request("POST", "/wp/v2/categories", data)

    async def create_tag(self, name: str, slug: str | None = None) -> dict:
        data = {"name": name}
        if slug:
            data["slug"] = slug
        return await self._request("POST", "/wp/v2/tags", data)

    async def get_current_user(self) -> dict:
        return await self._request("GET", "/wp/v2/users/me")

    async def check_connection(self) -> bool:
        try:
            await self._request("GET", "/wp/v2/posts?per_page=1")
            return True
        except Exception:
            return False


wordpress_service = WordPressService()
