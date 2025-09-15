from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time, os, random, json
from typing import Optional
from .botasaurus_adapter import apply_stealth
from .proxy_manager import ProxyManager

class PlaywrightRunner:
    def __init__(self, proxy: Optional[str] = None, headless: bool = True, storage_path=None, user_agent: Optional[str] = None):
        self.proxy = proxy
        self.headless = headless
        self.storage_path = storage_path
        self.user_agent = user_agent or "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        # proxy manager (reads PROXY_LIST or PROXY_FILE)
        try:
            self.proxy_manager = ProxyManager()
        except Exception:
            self.proxy_manager = None
        # ensure worker-data dir exists
        os.makedirs('/tmp/worker-data', exist_ok=True)

    def _launch_browser(self, p):
        launch_args = {'headless': self.headless, 'args': ['--no-sandbox', '--disable-dev-shm-usage']}
        # decide proxy: explicit self.proxy or from ProxyManager
        proxy_to_use = self.proxy
        try:
            if not proxy_to_use and getattr(self,'proxy_manager',None) and self.proxy_manager.has_proxies():
                proxy_to_use = self.proxy_manager.get_round_robin()
        except Exception:
            proxy_to_use = proxy_to_use
        if proxy_to_use:
            launch_args['proxy'] = {'server': proxy_to_use}
        return p.chromium.launch(**launch_args)

    def _make_context(self, browser):
        ctx_kwargs = {'user_agent': self.user_agent, 'locale':'en-US'}
        # enable storage state if present
        if self.storage_path and os.path.exists(self.storage_path):
            ctx = browser.new_context(storage_state=self.storage_path, **ctx_kwargs)
        else:
            ctx = browser.new_context(**ctx_kwargs)
        return ctx

    def _human_delay(self, min_ms=150, max_ms=450):
        time.sleep(random.uniform(min_ms/1000.0, max_ms/1000.0))

    def _save_artifact(self, name_prefix='artifact', page=None):
        ts = int(time.time() * 1000)
        fname = f'/tmp/worker-data/{name_prefix}-{ts}.png'
        fhtml = f'/tmp/worker-data/{name_prefix}-{ts}.html'
        try:
            if page:
                page.screenshot(path=fname, full_page=True)
                with open(fhtml, 'w', encoding='utf-8') as fh:
                    fh.write(page.content())
        except Exception:
            # best-effort only
            try:
                # fallback: empty placeholder
                open(fhtml, 'w').close()
            except:
                pass
            fname = None
        return {'screenshot': fname, 'html': fhtml}

    def login(self, email: str, password: str, wait_for_selector: str = 'input#Email'):
        with sync_playwright() as p:
            browser = self._launch_browser(p)
            context = self._make_context(browser)
            page = context.new_page()
            try:
                apply_stealth(page)
                try:
                    if BOTASAURUS_AVAILABLE:
                        apply_botasaurus(page)
                except Exception:
                    pass
            except Exception:
                pass
                page.goto('https://demo.nopcommerce.com/login', timeout=60000)
                page.wait_for_selector(wait_for_selector, timeout=30000)
                self._human_delay()
                page.fill('input#Email', email, timeout=15000)
                self._human_delay()
                page.fill('input#Password', password, timeout=15000)
                self._human_delay()
                page.click('button[type=submit]')
                # wait for some post-login indicator like logout link or account page
                try:
                    page.wait_for_selector('a.ico-logout, .account', timeout=15000)
                except PlaywrightTimeoutError:
                    # not critical
                    pass
                # persist storage state if requested
                if self.storage_path:
                    os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
                    context.storage_state(path=self.storage_path)
                artifacts = self._save_artifact('login', page=page)
                browser.close()
                return {'status':'ok', 'artifacts': artifacts}
            except PlaywrightTimeoutError as e:
                artifacts = self._save_artifact('login-err', page=page)
                try:
                    browser.close()
                except:
                    pass
                return {'status':'error', 'error':'timeout', 'message': str(e), 'artifacts': artifacts}
            except Exception as e:
                artifacts = self._save_artifact('login-exc', page=page)
                try:
                    browser.close()
                except:
                    pass
                return {'status':'error', 'error':'exception', 'message': str(e), 'artifacts': artifacts}

    def search(self, query: str, take_screenshot: bool = False, retries: int = 2):
        last_err = None
        for attempt in range(retries + 1):
            with sync_playwright() as p:
                browser = self._launch_browser(p)
                context = self._make_context(browser)
                page = context.new_page()
                try:
                    apply_stealth(page)
                    try:
                        if BOTASAURUS_AVAILABLE:
                            apply_botasaurus(page)
                    except Exception:
                        pass
                    page.goto('https://demo.nopcommerce.com/', timeout=60000)
                    try:
                        page.wait_for_load_state('networkidle', timeout=45000)
                    except PlaywrightTimeoutError:
                        pass
                    # try multiple selectors
                    selectors = ['input[id="small-searchterms"]', 'input[type="search"]', 'input[placeholder*="Search"]']
                    sel = None
                    for s in selectors:
                        try:
                            page.wait_for_selector(s, timeout=8000)
                            sel = s
                            break
                        except PlaywrightTimeoutError:
                            continue
                    if not sel:
                        raise PlaywrightTimeoutError('search input not found')
                    self._human_delay()
                    page.fill(sel, query, timeout=30000)
                    self._human_delay()
                    try:
                        page.click('button[type=submit]', timeout=8000)
                    except Exception:
                        page.press(sel, 'Enter')
                    try:
                        page.wait_for_selector('.product-item', timeout=15000)
                    except PlaywrightTimeoutError:
                        # no results
                        pass
                    artifacts = None
                    if take_screenshot:
                        artifacts = self._save_artifact('search', page=page)
                    item = page.query_selector('.product-item')
                    if item:
                        title_el = item.query_selector('.product-title')
                        title = title_el.inner_text().strip() if title_el else ''
                        price_el = item.query_selector('.prices') or item.query_selector('.add-info')
                        price = price_el.inner_text().strip() if price_el else ''
                    else:
                        title = ''
                        price = ''
                    browser.close()
                    return {'title': title, 'price': price, 'artifacts': artifacts}
                except PlaywrightTimeoutError as e:
                    last_err = str(e)
                    try:
                        self._save_artifact('search-err', page=page)
                    except:
                        pass
                    try:
                        browser.close()
                    except:
                        pass
                    # small backoff before retry
                    time.sleep(1 + attempt * 1.5)
                    continue
                except Exception as e:
                    last_err = str(e)
                    try:
                        self._save_artifact('search-exc', page=page)
                    except:
                        pass
                    try:
                        browser.close()
                    except:
                        pass
                    time.sleep(1 + attempt * 1.5)
                    continue
        return {'title':'', 'price':'', 'error': 'failed', 'message': last_err}

    def add_to_cart(self, product_index: int = 0, retries: int = 1):
        last_err = None
        for attempt in range(retries + 1):
            with sync_playwright() as p:
                browser = self._launch_browser(p)
                context = self._make_context(browser)
                page = context.new_page()
                try:
                    apply_stealth(page)
                    try:
                        if BOTASAURUS_AVAILABLE:
                            apply_botasaurus(page)
                    except Exception:
                        pass
                    page.goto('https://demo.nopcommerce.com/', timeout=60000)
                    try:
                        page.wait_for_selector('.product-item', timeout=15000)
                    except PlaywrightTimeoutError:
                        pass
                    items = page.query_selector_all('.product-item')
                    if not items:
                        raise Exception('no-items')
                    target = items[product_index] if product_index < len(items) else items[0]
                    btn = target.query_selector('.product-box-add-to-cart-button')
                    if btn:
                        btn.click()
                    else:
                        link = target.query_selector('a')
                        if link:
                            link.click()
                            page.wait_for_selector('button[id^="add-to-cart-button"]', timeout=5000)
                            page.click('button[id^="add-to-cart-button"]')
                    self._human_delay()
                    artifacts = self._save_artifact('addtocart', page=page)
                    browser.close()
                    return {'status':'added', 'artifacts': artifacts}
                except PlaywrightTimeoutError as e:
                    last_err = str(e)
                    try:
                        self._save_artifact('addtocart-err', page=page)
                    except:
                        pass
                    try:
                        browser.close()
                    except:
                        pass
                    time.sleep(1 + attempt * 1.2)
                    continue
                except Exception as e:
                    last_err = str(e)
                    try:
                        self._save_artifact('addtocart-exc', page=page)
                    except:
                        pass
                    try:
                        browser.close()
                    except:
                        pass
                    time.sleep(1 + attempt * 1.2)
                    continue
        return {'status':'error', 'message': last_err}

    def checkout(self, payment_method: str = 'COD', retries: int = 1):
        # Very light skeleton for checkout flow on demo.nopcommerce.com
        for attempt in range(retries + 1):
            with sync_playwright() as p:
                browser = self._launch_browser(p)
                context = self._make_context(browser)
                page = context.new_page()
                try:
                    apply_stealth(page)
                    try:
                        if BOTASAURUS_AVAILABLE:
                            apply_botasaurus(page)
                    except Exception:
                        pass
                    page.goto('https://demo.nopcommerce.com/cart', timeout=60000)
                    try:
                        page.wait_for_selector('a.checkout-button, button.checkout', timeout=15000)
                    except PlaywrightTimeoutError:
                        pass
                    # click checkout
                    try:
                        page.click('a.checkout-button')
                    except Exception:
                        try:
                            page.click('button.checkout')
                        except Exception:
                            pass
                    # wait for onepage checkout route
                    try:
                        page.wait_for_selector('#checkout', timeout=15000)
                    except PlaywrightTimeoutError:
                        pass
                    # NOTE: demo site's checkout may require more complex interactions; keep skeleton
                    artifacts = self._save_artifact('checkout', page=page)
                    browser.close()
                    return {'status':'started', 'artifacts': artifacts}
                except Exception as e:
                    try:
                        self._save_artifact('checkout-exc', page=page)
                    except:
                        pass
                    try:
                        browser.close()
                    except:
                        pass
                    time.sleep(1 + attempt * 1.2)
                    continue
        return {'status':'error', 'message':'failed'}

    def run_workflow(self, workflow_id: int, user_id: int = None, params: dict = None):
        params = params or {}
        action = params.get('action', 'search')
        # support composite chains
        if action == 'login':
            return self.login(params.get('email', 'test@example.com'), params.get('password', 'Password1'))
        elif action == 'add_to_cart':
            # expect either product_index or search term
            if 'query' in params:
                sr = self.search(params.get('query', ''), take_screenshot=True)
                if sr.get('title'):
                    return self.add_to_cart(params.get('product_index', 0))
                else:
                    return {'status':'no-items', 'search': sr}
            else:
                return self.add_to_cart(params.get('product_index', 0))
        elif action == 'checkout':
            # do search + add + checkout in sequence if query provided
            if 'query' in params:
                sr = self.search(params.get('query', ''), take_screenshot=True)
                if sr.get('title'):
                    add = self.add_to_cart(params.get('product_index', 0))
                    if add.get('status') == 'added':
                        return self.checkout(params.get('payment_method', 'COD'))
                    else:
                        return {'status':'failed_add', 'add': add}
                else:
                    return {'status':'no-items', 'search': sr}
            else:
                return self.checkout(params.get('payment_method', 'COD'))
        else:
            return self.search(params.get('query', 'laptop'), take_screenshot=True)