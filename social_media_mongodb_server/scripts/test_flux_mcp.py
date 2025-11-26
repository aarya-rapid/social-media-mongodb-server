import asyncio

from ..services.imagegen_service import generate_image_with_fallbacks


async def test_all(prompt: str):
    print("\n=== Test: normal chain (Flux -> Pollinations -> Local) ===")
    url, provider = await generate_image_with_fallbacks(prompt)
    print(f"Provider: {provider}")
    print(f"URL     : {url}")


async def test_force_pollinations(prompt: str):
    print("\n=== Test: Pollinations only (Flux disabled) ===")
    url, provider = await generate_image_with_fallbacks(
        prompt,
        allow_flux=False,
        allow_pollinations=True,
        allow_local=False,
    )
    print(f"Provider: {provider}")
    print(f"URL     : {url}")


async def test_force_local(prompt: str):
    print("\n=== Test: Local fallback only (Flux + Pollinations disabled) ===")
    url, provider = await generate_image_with_fallbacks(
        prompt,
        allow_flux=False,
        allow_pollinations=False,
        allow_local=True,
    )
    print(f"Provider: {provider}")
    print(f"URL     : {url}")


async def main():
    prompt = "A cute robot reading a book"

    await test_all(prompt)
    await test_force_pollinations(prompt)
    await test_force_local(prompt)


if __name__ == "__main__":
    asyncio.run(main())
