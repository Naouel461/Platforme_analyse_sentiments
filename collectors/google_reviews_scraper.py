import asyncio
from playwright.async_api import async_playwright
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

async def scraper_avis_google_auto(mot_cle, limit=10):
    avis_collectes = []

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                slow_mo=300,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials',
                    '--disable-web-security',
                    '--disable-gpu'
                ]
            )

            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={'width': 1280, 'height': 800},
                locale='fr-FR'
            )

            page = await context.new_page()
            await page.set_extra_http_headers({
                'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8'
            })

            query = mot_cle.replace(' ', '+')
            search_url = f"https://www.google.com/maps/search/{query}"
            print(f"[Scraper] 🔍 Recherche : {search_url}")

            await page.goto(search_url, timeout=120000, wait_until="domcontentloaded")
            await page.wait_for_timeout(5000)

            try:
                await page.wait_for_selector('a[href*="/place/"]', timeout=20000)
                print("[Scraper] ✅ Résultats détectés")
            except:
                print("[Scraper] ⚠️ Aucun résultat détecté")

            commerce_trouve = False
            try:
                await page.click('a[href*="/place/"]', timeout=10000)
                await page.wait_for_timeout(3000)
                print("[Scraper] ✅ Commerce sélectionné via lien place")
                commerce_trouve = True
            except:
                pass

            if not commerce_trouve:
                try:
                    await page.click('div[role="article"]:first-child', timeout=10000)
                    await page.wait_for_timeout(3000)
                    print("[Scraper] ✅ Commerce sélectionné via article")
                    commerce_trouve = True
                except:
                    print("[Scraper] ❌ Aucun commerce trouvé")
                    await browser.close()
                    return avis_collectes

            # ============================================
            # TENTATIVE AVEC URL DES AVIS
            # ============================================
            avis_ouvert = False

            selecteurs_avis = [
                'button[aria-label*="Avis"]',
                'button[aria-label*="Reviews"]',
                'button:has-text("Avis")',
                'button:has-text("Reviews")',
                '[data-tab-index="3"]',
                'div[role="tablist"] button:nth-of-type(3)',
                'a[jsaction*="review"]',
                'button[jsaction*="review"]'
            ]

            for sel in selecteurs_avis:
                try:
                    await page.wait_for_selector(sel, timeout=5000)
                    await page.click(sel, timeout=3000)
                    await page.wait_for_timeout(2000)
                    print(f"[Scraper] ✅ Onglet Avis ouvert avec {sel}")
                    avis_ouvert = True
                    break
                except:
                    continue

            if not avis_ouvert:
                try:
                    current_url = page.url
                    if '/place/' in current_url:
                        base_url = current_url.split('?')[0]
                        avis_url = f"{base_url}/reviews?hl=fr"
                    else:
                        avis_url = current_url + '?hl=fr'

                    print(f"[Scraper] 🔗 Tentative d'ouverture de l'URL des avis : {avis_url}")
                    await page.goto(avis_url, timeout=15000, wait_until="domcontentloaded")
                    await page.wait_for_timeout(4000)

                    try:
                        await page.click('button:has-text("Avis")', timeout=3000)
                        await page.wait_for_timeout(2000)
                        avis_ouvert = True
                        print("[Scraper] ✅ Onglet Avis ouvert via URL")
                    except:
                        pass
                except Exception as e:
                    print(f"[Scraper] ❌ Échec de la méthode URL : {e}")

            if not avis_ouvert:
                print("[Scraper] ℹ️ Aucun onglet Avis (établissement sans avis)")
                await browser.close()
                return avis_collectes

            # ============================================
            # EXTRACTION DES AVIS
            # ============================================
            for i in range(4):
                await page.mouse.wheel(0, 1000)
                await page.wait_for_timeout(2000)
                print(f"[Scraper] Défilement {i+1}/4")

            avis_elements = []
            selecteurs_elements = [
                'div.jftiEf',
                'div[role="article"]',
                'div.section-review-content',
                'div[jsaction*="review"]'
            ]
            for sel in selecteurs_elements:
                elements = await page.query_selector_all(sel)
                if elements:
                    avis_elements = elements
                    print(f"[Scraper] {len(avis_elements)} avis trouvés avec {sel}")
                    break

            if not avis_elements:
                print("[Scraper] Aucun élément d'avis trouvé")
                await browser.close()
                return avis_collectes

            for element in avis_elements[:limit]:
                try:
                    text = ""
                    selecteurs_texte = ['span.wiI7pd', 'span.review-text', 'span[jsaction*="review"]']
                    for sel in selecteurs_texte:
                        sub = await element.query_selector(sel)
                        if sub:
                            text = await sub.text_content()
                            break

                    stars = "0"
                    selecteurs_stars = ['span.kvMYJc', 'span[aria-label*="étoiles"]']
                    for sel in selecteurs_stars:
                        sub = await element.query_selector(sel)
                        if sub:
                            stars = await sub.get_attribute('aria-label') or await sub.text_content()
                            break

                    author = "Anonyme"
                    selecteurs_author = ['div.d4r55', 'div[role="link"]', 'span.author-name']
                    for sel in selecteurs_author:
                        sub = await element.query_selector(sel)
                        if sub:
                            author = await sub.text_content()
                            break

                    if text and len(text.strip()) > 10:
                        avis_collectes.append({
                            "texte": text.strip(),
                            "note": stars.replace("étoiles", "").strip() if stars else "0",
                            "auteur": author.strip(),
                            "source": "Google Maps"
                        })
                except Exception as e:
                    print(f"[Scraper] Erreur extraction avis: {e}")
                    continue

            await browser.close()

    except Exception as e:
        print(f"[Scraper] ❌ Erreur générale : {e}")

    print(f"[Scraper] Total : {len(avis_collectes)} avis collectés")
    return avis_collectes

def collecter_avis_google_auto_sync(mot_cle, limit=5):
    return asyncio.run(scraper_avis_google_auto(mot_cle, limit))