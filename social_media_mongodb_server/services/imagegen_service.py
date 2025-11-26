import os
import json
import random
import httpx
from urllib.parse import quote_plus
from typing import Tuple, Optional
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client  # note: `_http`
from urllib.parse import urlencode
from dotenv import load_dotenv
from ..repositories.posts_repo import get_post_by_id, set_post_image
from ..utils.helpers import mongo_obj_to_dict

load_dotenv()  # take environment variables from .env file

FLUX_MCP_BASE_URL = "https://server.smithery.ai/@falahgs/flux-imagegen-mcp-server/mcp"

FLUX_MCP_API_KEY = os.getenv("FLUX_MCP_API_KEY")

POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt"

LOCAL_FALLBACK_IMAGES = [
    "images/fallbacks/fallback1.jpg",
    "images/fallbacks/fallback2.jpg",
    "images/fallbacks/fallback3.jpg",
    "images/fallbacks/fallback4.jpg",
    "images/fallbacks/fallback5.jpg"
]

APP_BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")

def _build_flux_server_url() -> str:
    """
    Build the Smithery server URL with api_key as query param.
    Matches the snippet from their docs.
    """
    if not FLUX_MCP_API_KEY:
        raise RuntimeError("FLUX_MCP_API_KEY is not set in environment")
    params = {"api_key": FLUX_MCP_API_KEY}
    return f"{FLUX_MCP_BASE_URL}?{urlencode(params)}"


async def generate_image_for_post_service(
    db,
    post_id: str,
    prompt: Optional[str] = None,
):
    post = await get_post_by_id(db, post_id)
    if not post:
        return None, 404, "Post not found"

    post = mongo_obj_to_dict(post)

    final_prompt = prompt or f"Social media image for post: {post.get('title','')} - {post.get('content','')[:200]}"

    try:
        image_url, provider = await generate_image_with_fallbacks(final_prompt)
    except Exception as e:
        # you can log e here
        return None, 500, f"Image generation failed: {e}"

    updated = await set_post_image(db, post_id, image_url, final_prompt, provider=provider)
    updated = mongo_obj_to_dict(updated)
    updated["author_id"] = str(updated["author_id"]) if updated.get("author_id") else None

    return updated, None, None

async def generate_image_via_mcp(
    prompt: str,
    *,
    model: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    enhance: Optional[bool] = None,
    safe: Optional[bool] = None,
) -> str:
    """
    Call the Flux ImageGen MCP server and return a single image URL.

    Uses the `generateImageUrl` tool described in the repo README.
    """
    url = _build_flux_server_url()

    # Build arguments according to the tool schema in README
    args: dict = {"prompt": prompt}
    if model is not None:
        args["model"] = model
    if width is not None:
        args["width"] = width
    if height is not None:
        args["height"] = height
    if enhance is not None:
        args["enhance"] = enhance
    if safe is not None:
        args["safe"] = safe

    # 1) Connect to the remote MCP server over streamable HTTP
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            # 2) Initialize session (handshake, capabilities, etc.)
            await session.initialize()

            # 3) Call the tool exposed by this server
            # Tool name from README: "generateImageUrl"
            result = await session.call_tool("generateImageUrl", args)

    # 4) Extract the image URL from the result
    #
    # The MCP Python SDK wraps tool output in a CallToolResult object whose
    # .content usually includes a TextContent fallback (server converts the
    # structured JSON into a text block for backwards compat). :contentReference[oaicite:2]{index=2}
    #
    # We'll handle both:
    #   - plain URL in text
    #   - JSON in text with keys like "url"/"imageUrl"/"image_url".
    #
    # (You can add logging/prints while testing to see the exact shape.)
    for item in result.content:
        # Old and new SDKs both expose text blocks with .type == "text"
        if getattr(item, "type", None) == "text":
            text = (getattr(item, "text", "") or "").strip()

            # Case 1: content is just the URL
            if text.startswith("http"):
                return text

            # Case 2: JSON blob with url field
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    for key in ("url", "imageUrl", "image_url"):
                        if key in data and isinstance(data[key], str):
                            return data[key]
            except Exception:
                # not JSON, ignore and keep trying
                pass

    # If we reach here, we couldn't find a URL in any content block
    raise RuntimeError("Flux MCP response did not contain an image URL")


async def generate_image_via_pollinations(prompt: str) -> str:
    """
    Fallback 1: call Pollinations directly by constructing an image URL.
    We also do a lightweight HEAD/GET to ensure it doesn't immediately error.
    """
    # Build URL – you can tweak style/size via query params if you want
    url = f"{POLLINATIONS_BASE_URL}/{quote_plus(prompt)}"

    # Quick validation: make sure it doesn't return an obvious error
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(url)

    content_type = resp.headers.get("content-type", "").lower()

    if resp.status_code >= 400:
        raise RuntimeError(f"Pollinations failed with status {resp.status_code}")

    if "application/json" in content_type:
        # likely an error JSON, not an image
        try:
            data = resp.json()
            msg = data.get("message") or data.get("error") or "Pollinations error"
        except Exception:
            msg = "Pollinations returned JSON instead of image"
        raise RuntimeError(msg)

    if not content_type.startswith("image/"):
        raise RuntimeError(f"Pollinations unexpected content-type: {content_type}")

    # Looks good, return the URL
    return url


def pick_local_fallback_image() -> str:
    """
    Fallback 2: pick a random local image served under /static.
    """
    if not LOCAL_FALLBACK_IMAGES:
        raise RuntimeError("No local fallback images configured")

    path = random.choice(LOCAL_FALLBACK_IMAGES)
    # Full URL e.g. http://127.0.0.1:8000/static/images/fallbacks/fallback3.jpg
    return f"{APP_BASE_URL}/static/{path}"


async def generate_image_with_fallbacks(
    prompt: str,
    *,
    allow_flux: bool = True,
    allow_pollinations: bool = True,
    allow_local: bool = True,
) -> tuple[str, str]:
    """
    Try 3 levels:
      1) Flux MCP          (if allow_flux)
      2) Pollinations      (if allow_pollinations)
      3) Local fallback    (if allow_local)

    Returns (image_url, provider_name).
    Raises RuntimeError if all enabled options fail.
    """

    # Try 1: Flux MCP
    if allow_flux:
        try:
            url = await generate_image_via_mcp(prompt)
            return url, "flux-imagegen-mcp"
        except Exception as e1:
            # log e1 if you want
            pass

    # Try 2: Pollinations direct
    if allow_pollinations:
        try:
            url = await generate_image_via_pollinations(prompt)
            return url, "pollinations-direct"
        except Exception as e2:
            # log e2 if you want
            pass

    # Try 3: local fallback
    if allow_local:
        try:
            url = pick_local_fallback_image()
            return url, "local-fallback"
        except Exception as e3:
            raise RuntimeError(f"All image fallbacks failed: {e3}")

    # If we got here, everything is disabled
    raise RuntimeError("All image providers are disabled (check flags)")

