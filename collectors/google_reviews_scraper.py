# ============================================================
# FICHIER : collectors/google_reviews_scraper.py
# VERSION : 2.0 — Extraction robuste + debug
# ============================================================

import asyncio
from playwright.async_api import async_playwright
import random
import re

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]


async def scraper_avis_google_auto(mot_cle, limit=10):
    """Scraper les avis Google Maps avec extraction robuste"""
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

            # Nettoyer la requête (enlever virgules)
            query = mot_cle.replace(' ', '+').replace(',', '')
            search_url = f"https://www.google.com/maps/search/{query}"
            print(f"[Scraper] 🔍 Recherche : {search_url}", flush=True)

            await page.goto(search_url, timeout=120000, wait_until="domcontentloaded")
            await page.wait_for_timeout(5000)

            try:
                await page.wait_for_selector('a[href*="/place/"]', timeout=20000)
                print("[Scraper] ✅ Résultats détectés", flush=True)
            except:
                print("[Scraper] ⚠️ Aucun résultat détecté", flush=True)

            # ============================================================
            # SÉLECTION DU COMMERCE
            # ============================================================
            commerce_trouve = False
            try:
                await page.click('a[href*="/place/"]', timeout=10000)
                await page.wait_for_timeout(3000)
                print("[Scraper] ✅ Commerce sélectionné via lien place", flush=True)
                commerce_trouve = True
            except:
                pass

            if not commerce_trouve:
                try:
                    await page.click('div[role="article"]:first-child', timeout=10000)
                    await page.wait_for_timeout(3000)
                    print("[Scraper] ✅ Commerce sélectionné via article", flush=True)
                    commerce_trouve = True
                except:
                    print("[Scraper] ❌ Aucun commerce trouvé", flush=True)
                    await browser.close()
                    return avis_collectes

            # ============================================================
            # OUVERTURE DE L'ONGLET AVIS
            # ============================================================
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
                    print(f"[Scraper] ✅ Onglet Avis ouvert avec {sel}", flush=True)
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

                    print(f"[Scraper] 🔗 Tentative URL avis : {avis_url}", flush=True)
                    await page.goto(avis_url, timeout=15000, wait_until="domcontentloaded")
                    await page.wait_for_timeout(4000)

                    try:
                        await page.click('button:has-text("Avis")', timeout=3000)
                        await page.wait_for_timeout(2000)
                        avis_ouvert = True
                        print("[Scraper] ✅ Onglet Avis ouvert via URL", flush=True)
                    except:
                        pass
                except Exception as e:
                    print(f"[Scraper] ❌ Échec méthode URL : {e}", flush=True)

            if not avis_ouvert:
                print("[Scraper] ℹ️ Aucun onglet Avis (établissement sans avis)", flush=True)
                await browser.close()
                return avis_collectes

            # ============================================================
            # SCROLL POUR CHARGER LES AVIS (6 fois au lieu de 4)
            # ============================================================
            for i in range(6):
                await page.mouse.wheel(0, 1500)
                await page.wait_for_timeout(2500)
                print(f"[Scraper] Défilement {i+1}/6", flush=True)

            # ============================================================
            # TROUVER LES CONTENEURS D'AVIS (5 sélecteurs)
            # ============================================================
            avis_elements = []
            selecteurs_elements = [
                'div.jftiEf',
                'div[data-review-id]',
                'div[role="article"]',
                'div.section-review-content',
                'div[jsaction*="review"]'
            ]
            for sel in selecteurs_elements:
                elements = await page.query_selector_all(sel)
                if elements:
                    avis_elements = elements
                    print(f"[Scraper] {len(avis_elements)} avis trouvés avec {sel}", flush=True)
                    break

            if not avis_elements:
                print("[Scraper] Aucun élément d'avis trouvé", flush=True)
                await browser.close()
                return avis_collectes

            # ============================================================
            # EXTRACTION ROBUSTE DE CHAQUE AVIS
            # ============================================================
            for idx, element in enumerate(avis_elements[:limit]):
                try:
                    # --- TEXTE : 7 sélecteurs + 2 fallbacks ---
                    text = ""

                    selecteurs_texte = [
                        'span.wiI7pd',
                        'span.review-text',
                        'span.MyEned',
                        'div.MyEned',
                        'span[jsaction*="review"]',
                        '.review-full-text',
                        'div[data-review-id] span'
                    ]
                    for sel in selecteurs_texte:
                        try:
                            sub = await element.query_selector(sel)
                            if sub:
                                t = await sub.text_content()
                                if t and len(t.strip()) > 5:
                                    text = t.strip()
                                    break
                        except:
                            continue

                    # Fallback 1 : texte complet de l'élément
                    if not text:
                        try:
                            full_text = await element.text_content()
                            if full_text:
                                lines = [l.strip() for l in full_text.split('\n') if len(l.strip()) > 10]
                                if lines:
                                    text = max(lines, key=len)
                        except:
                            pass

                    # Fallback 2 : innerText via JS
                    if not text:
                        try:
                            text = await element.evaluate("el => el.innerText || el.textContent || ''")
                            text = text.strip()
                        except:
                            pass

                    # --- ÉTOILES : 5 sélecteurs ---
                    stars = "0"
                    selecteurs_stars = [
                        'span.kvMYJc',
                        'span[aria-label*="étoiles"]',
                        'span[aria-label*="stars"]',
                        '[role="img"][aria-label*="étoile"]',
                        '[role="img"][aria-label*="star"]'
                    ]
                    for sel in selecteurs_stars:
                        try:
                            sub = await element.query_selector(sel)
                            if sub:
                                stars = await sub.get_attribute('aria-label') or await sub.text_content()
                                if stars:
                                    break
                        except:
                            continue

                    # --- AUTEUR : 5 sélecteurs ---
                    author = "Anonyme"
                    selecteurs_author = [
                        'div.d4r55',
                        'div[role="link"]',
                        'span.author-name',
                        '.d4r55',
                        '[data-review-id] button'
                    ]
                    for sel in selecteurs_author:
                        try:
                            sub = await element.query_selector(sel)
                            if sub:
                                a = await sub.text_content()
                                if a and len(a.strip()) > 1:
                                    author = a.strip()
                                    break
                        except:
                            continue

                    # --- LOG DE DEBUG ---
                    preview = text[:60] if text else "(vide)"
                    print(f"[Scraper] 📝 Avis #{idx+1} — text='{preview}...' | stars='{stars}' | author='{author}'", flush=True)

                    # --- AJOUTER SI VALIDE (seuil 5 au lieu de 10) ---
                    if text and len(text.strip()) >= 5:
                        text = re.sub(r'\s+', ' ', text.strip())

                        # Nettoyer les étoiles
                        stars_clean = "0"
                        if stars:
                            match = re.search(r'(\d+)', str(stars))
                            if match:
                                stars_clean = match.group(1)

                        avis_collectes.append({
                            "texte": text,
                            "note": stars_clean,
                            "auteur": author,
                            "source": "Google Maps"
                        })
                        print(f"[Scraper] ✅ Avis #{idx+1} ajouté", flush=True)
                    else:
                        print(f"[Scraper] ⚠️ Avis #{idx+1} ignoré (texte trop court: {len(text) if text else 0} chars)", flush=True)

                except Exception as e:
                    print(f"[Scraper] ❌ Erreur extraction avis #{idx+1}: {e}", flush=True)
                    continue

            await browser.close()

    except Exception as e:
        print(f"[Scraper] ❌ Erreur générale : {e}", flush=True)

    print(f"[Scraper] Total : {len(avis_collectes)} avis collectés", flush=True)
    return avis_collectes


def collecter_avis_google_auto_sync(mot_cle, limit=5):
    return asyncio.run(scraper_avis_google_auto(mot_cle, limit))