import asyncio
from ..services.imagegen_service import generate_image_via_mcp

async def main():
    url = await generate_image_via_mcp("A cute robot reading a book")
    print("Generated image URL:", url)

if __name__ == "__main__":
    asyncio.run(main())
