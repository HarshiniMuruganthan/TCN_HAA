"""
sniff_aqi_in.py — Use Playwright to intercept all network requests made by
aqi.in so we can discover hidden JSON API endpoints.

Run: python backend/scripts/sniff_aqi_in.py
"""

import asyncio
import json
import re
from playwright.async_api import async_playwright

CITIES = [
    ("chennai",    "https://www.aqi.in/dashboard/india/tamil-nadu/chennai"),
    ("delhi",      "https://www.aqi.in/dashboard/india/delhi/delhi"),
    ("mumbai",     "https://www.aqi.in/dashboard/india/maharashtra/mumbai"),
]


async def sniff(city: str, url: str, page, results: list):
    """Navigate to a city page and record all XHR/fetch requests."""
    print(f"\n{'='*60}")
    print(f"  Navigating to {city}: {url}")
    print(f"{'='*60}")

    captured = []

    def on_request(request):
        rtype = request.resource_type
        rurl  = request.url
        # Only interested in XHR/fetch and data-looking URLs
        if rtype in ("xhr", "fetch", "script") or re.search(
            r"(api|json|data|aqi|station|pollut|city|measure)", rurl, re.I
        ):
            captured.append({"url": rurl, "type": rtype, "method": request.method})

    async def on_response(response):
        rurl = response.url
        if response.status != 200:
            return
        ctype = response.headers.get("content-type", "")
        if "json" not in ctype:
            return
        try:
            body = await response.json()
            snippet = json.dumps(body)[:800]
            print(f"\n  ✓ JSON response from:\n    {rurl}")
            print(f"    Content-Type: {ctype}")
            print(f"    Body snippet: {snippet[:400]}")
            results.append({"city": city, "url": rurl, "body": body})
        except Exception:
            pass

    page.on("request", on_request)
    page.on("response", on_response)

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)  # let lazy-loaded JS fire
        print(f"\n  All requests captured ({len(captured)}):")
        for r in captured[:30]:
            print(f"    [{r['type']:6}] {r['url'][:120]}")
    except Exception as exc:
        print(f"  ERROR: {exc}")

    page.remove_listener("request", on_request)
    page.remove_listener("response", on_response)


async def main():
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        for city, url in CITIES:
            await sniff(city, url, page, results)

        await browser.close()

    print("\n\n" + "="*60)
    print("SUMMARY — JSON APIs discovered:")
    print("="*60)
    seen = set()
    for r in results:
        key = r["url"]
        if key not in seen:
            seen.add(key)
            print(f"\n  City: {r['city']}")
            print(f"  URL:  {r['url']}")
            sample = json.dumps(r["body"])[:300]
            print(f"  Body: {sample}")

    # Save results
    with open("backend/scripts/aqi_in_api_discovery.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("\n\nFull results saved to: backend/scripts/aqi_in_api_discovery.json")


if __name__ == "__main__":
    asyncio.run(main())
