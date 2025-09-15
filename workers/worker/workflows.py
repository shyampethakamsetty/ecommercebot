
from typing import Optional, Dict, Any
from .playwright_runner import PlaywrightRunner

class AuthBot:
    def __init__(self, runner: PlaywrightRunner):
        self.runner = runner

    def login(self, email: str, password: str) -> Dict[str, Any]:
        return self.runner.login(email, password)

class CartBot:
    def __init__(self, runner: PlaywrightRunner):
        self.runner = runner

    def search(self, query: str, take_screenshot: bool = True) -> Dict[str, Any]:
        return self.runner.search(query, take_screenshot=take_screenshot)

    def add_to_cart(self, product_index: int = 0) -> Dict[str, Any]:
        return self.runner.add_to_cart(product_index=product_index)

class CheckoutBot:
    def __init__(self, runner: PlaywrightRunner):
        self.runner = runner

    def checkout(self, payment_method: str = 'COD') -> Dict[str, Any]:
        return self.runner.checkout(payment_method=payment_method)

class WorkflowManager:
    def __init__(self, proxy: Optional[str] = None, headless: bool = True, storage_path: Optional[str] = None):
        self.runner = PlaywrightRunner(proxy=proxy, headless=headless, storage_path=storage_path)
        self.auth = AuthBot(self.runner)
        self.cart = CartBot(self.runner)
        self.checkout_bot = CheckoutBot(self.runner)

    def run_login(self, email: str, password: str) -> Dict[str, Any]:
        return self.auth.login(email, password)

    def run_search(self, query: str) -> Dict[str, Any]:
        return self.cart.search(query, take_screenshot=True)

    def run_add_to_cart(self, query: Optional[str] = None, product_index: int = 0) -> Dict[str, Any]:
        # optionally perform search first
        if query:
            sr = self.cart.search(query, take_screenshot=True)
            if not sr.get('title'):
                return {'status':'no-items', 'search': sr}
        return self.cart.add_to_cart(product_index=product_index)

    def run_checkout(self, query: Optional[str] = None, product_index: int = 0, payment_method: str = 'COD') -> Dict[str, Any]:
        # if query provided, perform search and add first
        if query:
            sr = self.cart.search(query, take_screenshot=True)
            if not sr.get('title'):
                return {'status':'no-items', 'search': sr}
            add = self.cart.add_to_cart(product_index=product_index)
            if add.get('status') != 'added':
                return {'status':'failed_add', 'add': add}
        # run checkout
        return self.checkout_bot.checkout(payment_method=payment_method)

    def run_composite(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        # Use the enhanced PlaywrightRunner unified workflow method with session continuity
        return self.runner.run_unified_workflow(workflow_id=1, user_id=params.get('user_id', 1), params=params)
