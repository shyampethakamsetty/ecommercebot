from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time, os, random, json
from typing import Optional
from .botasaurus_adapter import apply_stealth
from .proxy_manager import ProxyManager

# Check if botasaurus is available
try:
    from .botasaurus_integration import apply_botasaurus
    BOTASAURUS_AVAILABLE = True
except ImportError:
    BOTASAURUS_AVAILABLE = False
    def apply_botasaurus(page):
        pass  # No-op function

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

    def _save_multiple_artifacts(self, name_prefix='artifact', page=None, step_name=''):
        """Save artifact with step-specific naming for multi-step workflows"""
        ts = int(time.time() * 1000)
        step_suffix = f'-{step_name}' if step_name else ''
        fname = f'/tmp/worker-data/{name_prefix}{step_suffix}-{ts}.png'
        fhtml = f'/tmp/worker-data/{name_prefix}{step_suffix}-{ts}.html'
        try:
            if page:
                page.screenshot(path=fname, full_page=True)
                with open(fhtml, 'w', encoding='utf-8') as fh:
                    fh.write(page.content())
                print(f"✅ Screenshot saved: {fname}")
            else:
                print(f"⚠️ No page provided for screenshot: {fname}")
                fname = None
        except Exception as e:
            print(f"❌ Screenshot failed: {fname} - Error: {str(e)}")
            try:
                open(fhtml, 'w').close()
            except:
                pass
            fname = None
        return {'screenshot': fname, 'html': fhtml}

    def login_with_detailed_screenshots(self, email: str, password: str, wait_for_selector: str = 'input#Email'):
        """Enhanced login with 3 screenshots: login page, credentials filled, landing page"""
        artifacts_list = []
        
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
                
                # Step 1: Navigate to login page and take screenshot
                page.goto('https://demo.nopcommerce.com/login', timeout=60000)
                page.wait_for_selector(wait_for_selector, timeout=30000)
                self._human_delay()
                
                # Screenshot 1: Login page loaded
                artifact1 = self._save_multiple_artifacts('login', page=page, step_name='page-loaded')
                artifacts_list.append(artifact1)
                
                # Step 2: Fill credentials and take screenshot BEFORE clicking login
                page.fill('input#Email', email, timeout=15000)
                self._human_delay()
                page.fill('input#Password', password, timeout=15000)
                self._human_delay()
                
                # Screenshot 2: Credentials filled (before clicking login)
                artifact2 = self._save_multiple_artifacts('login', page=page, step_name='credentials-filled')
                artifacts_list.append(artifact2)
                
                # Step 3: Click login and wait for successful redirect
                # Wait for the login button to be clickable and click it
                login_button = page.locator('button.login-button')
                login_button.wait_for(state='visible', timeout=10000)
                login_button.click()
                
                # Wait for successful login by checking for logout link or redirect to home
                try:
                    # Wait for logout link to appear (indicates successful login)
                    page.wait_for_selector('a.ico-logout', timeout=20000)
                    # Also wait for page to fully load after login
                    page.wait_for_load_state('networkidle', timeout=10000)
                except PlaywrightTimeoutError:
                    # If logout link doesn't appear, check if we're redirected to home
                    try:
                        # Check if we're on home page or any page other than login
                        current_url = page.url
                        if current_url and '/login' not in current_url.lower():
                            # We've been redirected, wait a bit more for page to load
                            page.wait_for_load_state('networkidle', timeout=5000)
                        else:
                            # Still on login page, login might have failed
                            print("Warning: Still on login page after clicking login")
                    except:
                        pass
                
                # Screenshot 3: Landing page after successful login
                artifact3 = self._save_multiple_artifacts('login', page=page, step_name='landing-page')
                artifacts_list.append(artifact3)
                
                # persist storage state if requested
                if self.storage_path:
                    os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
                    context.storage_state(path=self.storage_path)
                
                browser.close()
                return {'status':'ok', 'artifacts': artifacts_list, 'screenshots_count': len(artifacts_list)}
                
            except PlaywrightTimeoutError as e:
                artifacts = self._save_artifact('login-err', page=page)
                try:
                    browser.close()
                except:
                    pass
                return {'status':'error', 'error':'timeout', 'message': str(e), 'artifacts': [artifacts]}
            except Exception as e:
                artifacts = self._save_artifact('login-exc', page=page)
                try:
                    browser.close()
                except:
                    pass
                return {'status':'error', 'error':'exception', 'message': str(e), 'artifacts': [artifacts]}

    def search_with_detailed_screenshots(self, query: str, retries: int = 2):
        """Enhanced search with 2 screenshots: product page navigation, filter applied"""
        artifacts_list = []
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
                    
                    # Navigate to homepage first
                    page.goto('https://demo.nopcommerce.com/', timeout=60000)
                    try:
                        page.wait_for_load_state('networkidle', timeout=45000)
                    except PlaywrightTimeoutError:
                        pass
                    
                    # Perform search
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
                    
                    # Wait for search results
                    try:
                        page.wait_for_selector('.product-item', timeout=15000)
                    except PlaywrightTimeoutError:
                        pass
                    
                    # Screenshot 1: Product category page with search results
                    artifact1 = self._save_multiple_artifacts('search', page=page, step_name='results-page')
                    artifacts_list.append(artifact1)
                    
                    # Try to apply a filter if available (price filter example)
                    try:
                        # Look for price filter slider or filter options
                        price_filter = page.query_selector('#price-range-slider')
                        if price_filter:
                            # Simulate filter interaction - adjust price range
                            page.evaluate("""
                                const slider = document.querySelector('#price-range-slider');
                                if (slider && window.$ && $.fn.slider) {
                                    $(slider).slider('values', [0, 2000]);
                                    $(slider).trigger('slidestop');
                                }
                            """)
                            self._human_delay(500, 1000)  # Wait for filter to apply
                    except Exception:
                        # Filter interaction failed, continue without it
                        pass
                    
                    # Screenshot 2: Page with filter applied (or same page if filter failed)
                    artifact2 = self._save_multiple_artifacts('search', page=page, step_name='filter-applied')
                    artifacts_list.append(artifact2)
                    
                    # Get product information
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
                    return {
                        'title': title, 
                        'price': price, 
                        'artifacts': artifacts_list,
                        'screenshots_count': len(artifacts_list)
                    }
                    
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
        return {'title':'', 'price':'', 'error': 'failed', 'message': last_err, 'artifacts': artifacts_list}

    def login(self, email: str, password: str, wait_for_selector: str = 'input#Email'):
        with sync_playwright() as p:
            browser = self._launch_browser(p)
            context = self._make_context(browser)
            page = context.new_page()
            try:
                apply_stealth(page)
                if BOTASAURUS_AVAILABLE:
                    apply_botasaurus(page)
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
        
        # Extract credentials from params
        credentials = params.get('credentials', {})
        email = credentials.get('email', 'test@example.com')
        password = credentials.get('password', 'password1')
        
        print(f"🔐 Using login credentials: {email}")
        
        # Always start with detailed login (3 screenshots)
        login_result = self.login_with_detailed_screenshots(email, password)
        
        # If login failed, return login result
        if login_result.get('status') != 'ok':
            return login_result
        
        # Proceed with the requested action using detailed screenshots
        if action == 'login':
            # Just return login result since that's all that was requested
            return login_result
        elif action == 'search':
            # Perform detailed search (2 screenshots)
            search_result = self.search_with_detailed_screenshots(params.get('query', 'laptop'))
            # Combine artifacts from login and search
            all_artifacts = login_result.get('artifacts', []) + search_result.get('artifacts', [])
            return {
                **search_result,
                'login': login_result,
                'artifacts': all_artifacts,
                'total_screenshots': len(all_artifacts)
            }
        elif action == 'add_to_cart':
            # For add to cart, do search first, then add to cart
            if 'query' in params:
                search_result = self.search_with_detailed_screenshots(params.get('query', ''))
                if search_result.get('title'):
                    cart_result = self.add_to_cart(params.get('product_index', 0))
                    all_artifacts = login_result.get('artifacts', []) + search_result.get('artifacts', [])
                    if cart_result.get('artifacts'):
                        all_artifacts.append(cart_result['artifacts'])
                    return {
                        'status': cart_result.get('status', 'unknown'),
                        'login': login_result,
                        'search': search_result,
                        'cart': cart_result,
                        'artifacts': all_artifacts,
                        'total_screenshots': len(all_artifacts)
                    }
                else:
                    all_artifacts = login_result.get('artifacts', []) + search_result.get('artifacts', [])
                    return {
                        'status':'no-items', 
                        'login': login_result,
                        'search': search_result,
                        'artifacts': all_artifacts,
                        'total_screenshots': len(all_artifacts)
                    }
            else:
                cart_result = self.add_to_cart(params.get('product_index', 0))
                all_artifacts = login_result.get('artifacts', [])
                if cart_result.get('artifacts'):
                    all_artifacts.append(cart_result['artifacts'])
                return {
                    'status': cart_result.get('status', 'unknown'),
                    'login': login_result,
                    'cart': cart_result,
                    'artifacts': all_artifacts,
                    'total_screenshots': len(all_artifacts)
                }
        elif action == 'checkout':
            # do search + add + checkout in sequence if query provided
            if 'query' in params:
                search_result = self.search_with_detailed_screenshots(params.get('query', ''))
                if search_result.get('title'):
                    cart_result = self.add_to_cart(params.get('product_index', 0))
                    if cart_result.get('status') == 'added':
                        checkout_result = self.checkout(params.get('payment_method', 'COD'))
                        all_artifacts = login_result.get('artifacts', []) + search_result.get('artifacts', [])
                        if cart_result.get('artifacts'):
                            all_artifacts.append(cart_result['artifacts'])
                        if checkout_result.get('artifacts'):
                            all_artifacts.append(checkout_result['artifacts'])
                        return {
                            'status': checkout_result.get('status', 'unknown'),
                            'login': login_result,
                            'search': search_result,
                            'cart': cart_result,
                            'checkout': checkout_result,
                            'artifacts': all_artifacts,
                            'total_screenshots': len(all_artifacts)
                        }
                    else:
                        all_artifacts = login_result.get('artifacts', []) + search_result.get('artifacts', [])
                        if cart_result.get('artifacts'):
                            all_artifacts.append(cart_result['artifacts'])
                        return {
                            'status':'failed_add', 
                            'login': login_result,
                            'search': search_result,
                            'cart': cart_result,
                            'artifacts': all_artifacts,
                            'total_screenshots': len(all_artifacts)
                        }
                else:
                    all_artifacts = login_result.get('artifacts', []) + search_result.get('artifacts', [])
                    return {
                        'status':'no-items', 
                        'login': login_result,
                        'search': search_result,
                        'artifacts': all_artifacts,
                        'total_screenshots': len(all_artifacts)
                    }
            else:
                checkout_result = self.checkout(params.get('payment_method', 'COD'))
                all_artifacts = login_result.get('artifacts', [])
                if checkout_result.get('artifacts'):
                    all_artifacts.append(checkout_result['artifacts'])
                return {
                    'status': checkout_result.get('status', 'unknown'),
                    'login': login_result,
                    'checkout': checkout_result,
                    'artifacts': all_artifacts,
                    'total_screenshots': len(all_artifacts)
                }
        else:
            # Default to search
            search_result = self.search_with_detailed_screenshots(params.get('query', 'laptop'))
            all_artifacts = login_result.get('artifacts', []) + search_result.get('artifacts', [])
            return {
                **search_result,
                'login': login_result,
                'artifacts': all_artifacts,
                'total_screenshots': len(all_artifacts)
            }

    def run_unified_workflow(self, workflow_id: int, user_id: int = None, params: dict = None):
        """
        Unified workflow that maintains browser session throughout login -> search -> add_to_cart -> checkout
        """
        params = params or {}
        action = params.get('action', 'search')
        all_artifacts = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-blink-features=AutomationControlled']
            )
            
            # Create a single context that will be used throughout the workflow
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                viewport={'width': 1280, 'height': 720}
            )
            
            try:
                page = context.new_page()
                
                # Extract credentials
                credentials = params.get('credentials', {})
                email = credentials.get('email', 'test@example.com')
                password = credentials.get('password', 'password1')
                
                print(f"🔐 Using login credentials: {email}")
                
                # STEP 1: Login (3 screenshots) - Always first
                print("=== Starting Login Phase ===")
                login_artifacts = self._perform_login_in_session(page, email, password)
                all_artifacts.extend(login_artifacts)
                
                # Check if login was successful by looking for logout link
                try:
                    page.wait_for_selector('a.ico-logout', timeout=5000)
                    login_success = True
                    print("✅ Login successful - logout link found")
                except:
                    login_success = False
                    print("❌ Login may have failed - no logout link found")
                
                if not login_success:
                    return {
                        'status': 'login_failed',
                        'artifacts': all_artifacts,
                        'total_screenshots': len(all_artifacts)
                    }
                
                # STEP 2: Search (2 screenshots) - if requested
                if action in ['search', 'add_to_cart', 'checkout']:
                    print("=== Starting Intelligent Search Phase ===")
                    search_artifacts = self._perform_intelligent_search_in_session(page, params)
                    all_artifacts.extend(search_artifacts)
                
                # STEP 3: Add to Cart (1 screenshot) - if requested  
                if action in ['add_to_cart', 'checkout']:
                    print("=== Starting Add ALL to Cart Phase ===")
                    cart_artifacts = self._perform_add_all_to_cart_in_session(page)
                    all_artifacts.extend(cart_artifacts)
                
                # STEP 4: Checkout (2 screenshots) - if requested
                if action == 'checkout':
                    print("=== Starting Checkout Phase ===")
                    checkout_artifacts = self._perform_checkout_in_session(page)
                    all_artifacts.extend(checkout_artifacts)
                
                # Save session state if needed
                if self.storage_path:
                    os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
                    context.storage_state(path=self.storage_path)
                
                return {
                    'status': 'ok',
                    'title': 'Workflow Complete',
                    'artifacts': all_artifacts,
                    'total_screenshots': len(all_artifacts),
                    'workflow_steps': {
                        'login': len([a for a in all_artifacts if a and 'login' in (a.get('screenshot') or '')]),
                        'search': len([a for a in all_artifacts if a and 'search' in (a.get('screenshot') or '')]),
                        'cart': len([a for a in all_artifacts if a and 'cart' in (a.get('screenshot') or '')]),
                        'checkout': len([a for a in all_artifacts if a and 'checkout' in (a.get('screenshot') or '')])
                    }
                }
                
            except Exception as e:
                print(f"Workflow error: {str(e)}")
                return {
                    'status': 'error',
                    'message': str(e),
                    'artifacts': all_artifacts,
                    'total_screenshots': len(all_artifacts)
                }
            finally:
                browser.close()

    def _perform_login_in_session(self, page, email='test@example.com', password='password1'):
        """Perform login in existing session/page - returns list of artifacts"""
        artifacts_list = []
        
        try:
            # Step 1: Navigate to login page and take screenshot
            page.goto('https://demo.nopcommerce.com/login')
            page.wait_for_load_state('networkidle', timeout=10000)
            artifact1 = self._save_multiple_artifacts('login', page=page, step_name='page-loaded')
            artifacts_list.append(artifact1)
            
            # Step 2: Fill credentials and take screenshot BEFORE clicking login
            page.fill('input#Email', email, timeout=15000)
            self._human_delay()
            page.fill('input#Password', password, timeout=15000)
            self._human_delay()
            
            artifact2 = self._save_multiple_artifacts('login', page=page, step_name='credentials-filled')
            artifacts_list.append(artifact2)
            
            # Step 3: Click login and wait for redirect
            login_button = page.locator('button.login-button')
            login_button.wait_for(state='visible', timeout=10000)
            login_button.click()
            
            # Wait for successful login
            try:
                page.wait_for_selector('a.ico-logout', timeout=20000)
                page.wait_for_load_state('networkidle', timeout=10000)
            except:
                # Check if redirected away from login page
                current_url = page.url
                if '/login' not in current_url.lower():
                    page.wait_for_load_state('networkidle', timeout=5000)
            
            artifact3 = self._save_multiple_artifacts('login', page=page, step_name='landing-page')
            artifacts_list.append(artifact3)
            
        except Exception as e:
            print(f"Login error: {str(e)}")
            # Still return whatever artifacts we managed to capture
        
        return artifacts_list

    def _perform_search_in_session(self, page, query='laptop'):
        """Perform search in existing session/page - returns list of artifacts"""
        artifacts_list = []
        
        try:
            # Step 1: Navigate to search and take screenshot
            page.goto(f'https://demo.nopcommerce.com/search?q={query}')
            page.wait_for_load_state('networkidle', timeout=10000)
            artifact1 = self._save_multiple_artifacts('search', page=page, step_name='results-page')
            artifacts_list.append(artifact1)
            
            # Step 2: Apply some filters and take screenshot
            try:
                # Try to apply a price filter if available
                price_filter = page.locator('input[name="pf"]').first
                if price_filter.is_visible():
                    price_filter.click()
                    page.wait_for_load_state('networkidle', timeout=5000)
                    artifact2 = self._save_multiple_artifacts('search', page=page, step_name='filter-applied')
                    artifacts_list.append(artifact2)
                else:
                    # If no filters, just take another screenshot after waiting
                    self._human_delay()
                    artifact2 = self._save_multiple_artifacts('search', page=page, step_name='filter-applied')
                    artifacts_list.append(artifact2)
            except:
                # Fallback: just take another screenshot
                artifact2 = self._save_multiple_artifacts('search', page=page, step_name='filter-applied')
                artifacts_list.append(artifact2)
                
        except Exception as e:
            print(f"Search error: {str(e)}")
        
        return artifacts_list

    def _perform_intelligent_search_in_session(self, page, params):
        """Perform intelligent search using LLM-parsed parameters"""
        artifacts_list = []
        
        try:
            # Extract intelligent parameters
            category = params.get('category', '')
            subcategory = params.get('subcategory', '')
            filters = params.get('filters', {})
            query = filters.get('query', params.get('query', 'products'))
            max_price = filters.get('max_price')
            min_price = filters.get('min_price')
            
            # Step 1: Navigate to appropriate category or search
            if category and category.startswith('/'):
                # Navigate to specific category
                if subcategory and subcategory.startswith('/'):
                    # Use subcategory for more specific navigation
                    page.goto(f'https://demo.nopcommerce.com{subcategory}')
                else:
                    page.goto(f'https://demo.nopcommerce.com{category}')
            else:
                # Fallback to search
                page.goto(f'https://demo.nopcommerce.com/search?q={query}')
            
            page.wait_for_load_state('networkidle', timeout=10000)
            artifact1 = self._save_multiple_artifacts('search', page=page, step_name='results-page')
            artifacts_list.append(artifact1)
            
            # Step 2: Apply price filters if specified
            try:
                min_price = params.get('filters', {}).get('min_price')
                max_price = params.get('filters', {}).get('max_price')
                
                if min_price is not None or max_price is not None:
                    # Wait for price slider to be available
                    price_slider = page.locator('#price-range-slider')
                    if price_slider.is_visible():
                        # Determine filter type and set appropriate values
                        if min_price is None and max_price is not None:
                            # BELOW filter: 0 to max_price
                            filter_type = "below"
                            from_val = 0
                            to_val = max_price
                            print(f"Applying BELOW price filter: $0 - ${max_price}")
                        elif min_price is not None and max_price is None:
                            # ABOVE filter: min_price to 10000
                            filter_type = "above" 
                            from_val = min_price
                            to_val = 10000
                            print(f"Applying ABOVE price filter: ${min_price} - $10000")
                        else:
                            # BETWEEN filter: min_price to max_price
                            filter_type = "between"
                            from_val = min_price
                            to_val = max_price
                            print(f"Applying BETWEEN price filter: ${min_price} - ${max_price}")
                        
                        # Apply the filter using jQuery UI slider
                        page.evaluate(f"""
                            const slider = $('#price-range-slider');
                            if (slider.length && slider.slider) {{
                                // Set the slider values
                                slider.slider('values', [{from_val}, {to_val}]);
                                
                                // Update the display
                                $('.selected-price-range .from').text('{from_val}');
                                $('.selected-price-range .to').text('{to_val}');
                                
                                // Trigger the actual filtering by calling CatalogProducts.getProducts()
                                if (typeof CatalogProducts !== 'undefined' && CatalogProducts.getProducts) {{
                                    CatalogProducts.getProducts();
                                }}
                                
                                console.log('Price filter applied: {filter_type} ${from_val}-${to_val}');
                            }}
                        """)
                        
                        # Wait for the filter to be applied and page to reload
                        print("Waiting for filtered results to load...")
                        page.wait_for_timeout(5000)  # 5 second delay to allow AJAX to complete
                        page.wait_for_load_state('networkidle', timeout=15000)
                        
                        print(f"Price filter applied successfully: {filter_type} ${from_val}-${to_val}")
                    else:
                        print("Price slider not found, skipping price filter")
                        
            except Exception as e:
                print(f"Error applying price filter: {str(e)}")
                # Continue without filtering
                
            # Take screenshot after filter is applied (or if no filter)
            self._human_delay()
            artifact2 = self._save_multiple_artifacts('search', page=page, step_name='filter-applied')
            artifacts_list.append(artifact2)
                
        except Exception as e:
            print(f"Intelligent search error: {str(e)}")
            # Fallback to basic search
            return self._perform_search_in_session(page, query)
        
        return artifacts_list

    def _perform_add_to_cart_in_session(self, page, product_index=0):
        """Perform add to cart in existing session/page - returns list of artifacts"""
        artifacts_list = []
        
        try:
            # Find and click first product
            products = page.locator('.product-item')
            if products.count() > product_index:
                product = products.nth(product_index)
                product.click()
                page.wait_for_load_state('networkidle', timeout=10000)
                
                # Add to cart
                add_to_cart_btn = page.locator('button.add-to-cart-button')
                if add_to_cart_btn.is_visible():
                    add_to_cart_btn.click()
                    page.wait_for_load_state('networkidle', timeout=5000)
                
                artifact1 = self._save_multiple_artifacts('cart', page=page, step_name='product-added')
                artifacts_list.append(artifact1)
                
        except Exception as e:
            print(f"Add to cart error: {str(e)}")
            
        return artifacts_list

    def _perform_add_all_to_cart_in_session(self, page):
        """Add ALL visible products to cart from the current filtered results page"""
        artifacts_list = []
        
        try:
            # Find all products on the current page
            products = page.locator('.product-item')
            product_count = products.count()
            
            if product_count == 0:
                print("No products found to add to cart")
                artifact1 = self._save_multiple_artifacts('cart', page=page, step_name='no-products')
                artifacts_list.append(artifact1)
                return artifacts_list
            
            print(f"Found {product_count} products to add to cart")
            
            # Take screenshot before adding products
            artifact1 = self._save_multiple_artifacts('cart', page=page, step_name='before-adding-all')
            artifacts_list.append(artifact1)
            
            added_count = 0
            
            # Add each product to cart using the direct "Add to cart" buttons
            for i in range(product_count):
                try:
                    product = products.nth(i)
                    
                    # Find the "Add to cart" button within this product
                    add_to_cart_btn = product.locator('button.product-box-add-to-cart-button')
                    
                    if add_to_cart_btn.is_visible():
                        # Get product name for logging
                        try:
                            product_title = product.locator('.product-title a').text_content()
                            print(f"Adding to cart: {product_title}")
                        except:
                            print(f"Adding product {i+1} to cart")
                        
                        # Click the add to cart button
                        add_to_cart_btn.click()
                        
                        # Wait a moment for the AJAX request to complete
                        page.wait_for_timeout(1000)
                        
                        added_count += 1
                    else:
                        print(f"No add to cart button found for product {i+1}")
                        
                except Exception as product_error:
                    print(f"Error adding product {i+1} to cart: {str(product_error)}")
                    continue
            
            print(f"✅ Successfully added {added_count} products to cart")
            
            # Wait for all AJAX requests to complete
            page.wait_for_load_state('networkidle', timeout=10000)
            
            # Take screenshot after adding all products
            artifact2 = self._save_multiple_artifacts('cart', page=page, step_name='after-adding-all')
            artifacts_list.append(artifact2)
            
            # Navigate to cart page to show the results
            print("Navigating to cart to show added products...")
            page.goto('https://demo.nopcommerce.com/cart')
            page.wait_for_load_state('networkidle', timeout=10000)
            
            # Take screenshot of cart with all added products
            artifact3 = self._save_multiple_artifacts('cart', page=page, step_name='cart-with-all-products')
            artifacts_list.append(artifact3)
                
        except Exception as e:
            print(f"Add all to cart error: {str(e)}")
            # Still try to take a screenshot of current state
            try:
                artifact_error = self._save_multiple_artifacts('cart', page=page, step_name='add-all-error')
                artifacts_list.append(artifact_error)
            except:
                pass
            
        return artifacts_list

    def _fill_billing_address(self, page, artifacts_list):
        """Handle billing address step - use existing address if available"""
        try:
            print("📝 Step 1: Checking billing address...")
            
            # Check if billing form is visible
            billing_form = page.locator('#co-billing-form')
            if not billing_form.is_visible():
                print("⚠️ Billing form not visible, skipping...")
                return
            
            # Check if there's an existing address selected (dropdown with saved address)
            address_select = page.locator('#billing-address-select')
            if address_select.is_visible():
                selected_value = address_select.input_value()
                if selected_value and selected_value != "":
                    print(f"✅ Using existing billing address (ID: {selected_value})")
                else:
                    print("📝 No existing address, will use new address form...")
                    # If needed, could add form filling logic here, but usually not required
            
            # Take screenshot of billing address step
            artifact = self._save_multiple_artifacts('checkout', page=page, step_name='billing-address')
            artifacts_list.append(artifact)
            
            # Click continue button for billing (be specific to billing section)
            billing_continue_btn = page.locator('#billing-buttons-container button.new-address-next-step-button')
            if billing_continue_btn.is_visible():
                print("✅ Proceeding with billing address...")
                billing_continue_btn.click()
                page.wait_for_load_state('networkidle', timeout=10000)
                
                print("🔄 Starting subsequent checkout steps...")
                # Handle subsequent checkout steps automatically
                self._complete_checkout_steps(page, artifacts_list)
                print("✅ All checkout steps completed!")
            else:
                print("❌ Billing continue button not found!")
            
        except Exception as e:
            print(f"⚠️ Error handling billing address: {e}")
    
    def _complete_checkout_steps(self, page, artifacts_list):
        """Complete remaining checkout steps automatically with screenshots"""
        try:
            print("🚀 Entering _complete_checkout_steps method...")
            
            # Step 2: Shipping Address (usually skipped if same as billing)
            print("🔍 Waiting for shipping step to become visible...")
            try:
                shipping_btn = page.locator('#shipping-buttons-container button.new-address-next-step-button')
                shipping_btn.wait_for(state='visible', timeout=15000)
                print("📦 Step 2: Shipping address (same as billing)...")
                shipping_btn.click()
                page.wait_for_load_state('networkidle', timeout=10000)
                artifact = self._save_multiple_artifacts('checkout', page=page, step_name='shipping-address')
                artifacts_list.append(artifact)
                self._human_delay(1)
            except Exception as e:
                print(f"⚠️ Shipping step skipped or not visible: {e}")
            
            # Step 3: Shipping Method - Choose Ground ($0.00)
            print("🔍 Waiting for shipping method step to become visible...")
            try:
                shipping_method_btn = page.locator('button.shipping-method-next-step-button')
                shipping_method_btn.wait_for(state='visible', timeout=15000)
                print("🚚 Step 3: Selecting Ground shipping method...")
                # Select first shipping option (Ground)
                ground_option = page.locator('#shippingoption_0')
                if ground_option.is_visible():
                    ground_option.check()
                    self._human_delay(0.5)
                
                artifact = self._save_multiple_artifacts('checkout', page=page, step_name='shipping-method')
                artifacts_list.append(artifact)
                
                shipping_method_btn.click()
                page.wait_for_load_state('networkidle', timeout=10000)
                self._human_delay(1)
            except Exception as e:
                print(f"⚠️ Shipping method step failed: {e}")
            
            # Step 4: Payment Method - Choose Check / Money Order
            print("🔍 Waiting for payment method step to become visible...")
            try:
                payment_method_btn = page.locator('button.payment-method-next-step-button')
                payment_method_btn.wait_for(state='visible', timeout=15000)
                print("💳 Step 4: Selecting Check / Money Order payment...")
                # Select first payment option (Check / Money Order)
                check_option = page.locator('#paymentmethod_0')
                if check_option.is_visible():
                    check_option.check()
                    self._human_delay(0.5)
                
                artifact = self._save_multiple_artifacts('checkout', page=page, step_name='payment-method')
                artifacts_list.append(artifact)
                
                payment_method_btn.click()
                page.wait_for_load_state('networkidle', timeout=10000)
                self._human_delay(1)
            except Exception as e:
                print(f"⚠️ Payment method step failed: {e}")
            
            # Step 5: Payment Information - Continue
            print("🔍 Waiting for payment info step to become visible...")
            try:
                payment_info_btn = page.locator('button.payment-info-next-step-button')
                payment_info_btn.wait_for(state='visible', timeout=15000)
                print("ℹ️ Step 5: Payment information...")
                artifact = self._save_multiple_artifacts('checkout', page=page, step_name='payment-info')
                artifacts_list.append(artifact)
                
                payment_info_btn.click()
                page.wait_for_load_state('networkidle', timeout=10000)
                self._human_delay(1)
            except Exception as e:
                print(f"⚠️ Payment info step failed: {e}")
            
            # Step 6: Confirm Order - Final step
            print("🔍 Waiting for confirm order step to become visible...")
            try:
                confirm_btn = page.locator('button.confirm-order-next-step-button')
                confirm_btn.wait_for(state='visible', timeout=15000)
                print("✅ Step 6: Confirming order...")
                artifact = self._save_multiple_artifacts('checkout', page=page, step_name='confirm-order')
                artifacts_list.append(artifact)
                
                confirm_btn.click()
                print("⏳ Waiting for order processing and redirect to thank you page...")
                
                # Wait for URL to change to the order completed page
                try:
                    print("🔄 Waiting for redirect to /checkout/completed...")
                    page.wait_for_url('**/checkout/completed*', timeout=30000)  # Wait up to 30 seconds for redirect
                    print("✅ Successfully redirected to order completion page!")
                    
                    # Wait for the page to fully load after redirect
                    page.wait_for_load_state('networkidle', timeout=10000)
                    
                    # Additional delay to ensure all elements are rendered
                    self._human_delay(2)
                    
                    # Verify we're on the correct page
                    current_url = page.url
                    print(f"📍 Final page URL: {current_url}")
                    
                    # Final screenshot of thank you page
                    final_artifact = self._save_multiple_artifacts('checkout', page=page, step_name='thank-you-page')
                    artifacts_list.append(final_artifact)
                    print("🎉 Order completed successfully! Thank you page captured!")
                    
                except Exception as redirect_error:
                    print(f"⚠️ URL redirect timeout or failed: {redirect_error}")
                    print(f"📍 Current URL: {page.url}")
                    
                    # Still take a screenshot of whatever page we're on for debugging
                    fallback_artifact = self._save_multiple_artifacts('checkout', page=page, step_name='order-processing-fallback')
                    artifacts_list.append(fallback_artifact)
                    print("📸 Fallback screenshot taken")
            except Exception as e:
                print(f"⚠️ Confirm order step failed: {e}")
                
            print("✅ _complete_checkout_steps method finished successfully!")
                
        except Exception as e:
            print(f"⚠️ Error completing checkout steps: {e}")
            import traceback
            traceback.print_exc()

    def _perform_checkout_in_session(self, page):
        """Perform checkout in existing session/page - returns list of artifacts"""
        artifacts_list = []
        
        try:
            # Go to cart
            page.goto('https://demo.nopcommerce.com/cart')
            page.wait_for_load_state('networkidle', timeout=10000)
            
            # CRITICAL: Check the terms of service checkbox before checkout
            terms_checkbox = page.locator('#termsofservice')
            if terms_checkbox.is_visible():
                if not terms_checkbox.is_checked():
                    print("✅ Accepting terms of service...")
                    terms_checkbox.check()
                    self._human_delay()  # Small delay after checking
                else:
                    print("✅ Terms of service already accepted")
            else:
                print("⚠️ Terms of service checkbox not found")
            
            # Take screenshot AFTER accepting terms
            artifact1 = self._save_multiple_artifacts('checkout', page=page, step_name='cart-page')
            artifacts_list.append(artifact1)
            
            # Proceed to checkout
            checkout_btn = page.locator('button.checkout-button')
            if checkout_btn.is_visible():
                print("🛒 Proceeding to checkout...")
                checkout_btn.click()
                page.wait_for_load_state('networkidle', timeout=10000)
                
                # Fill billing address form if visible and complete checkout
                self._fill_billing_address(page, artifacts_list)
            else:
                print("❌ Checkout button not found or not visible")
                
        except Exception as e:
            print(f"Checkout error: {str(e)}")
            
        return artifacts_list