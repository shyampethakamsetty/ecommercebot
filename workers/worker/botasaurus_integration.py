
# botasaurus_integration.py - optional integration shim.
# If botasaurus package is installed, this will apply its stealth measures.

def apply_botasaurus(page):
    try:
        import botasaurus
        # Try different possible API methods
        try:
            botasaurus.stealth(page)
            return True
        except Exception:
            try:
                # older API possibility
                botasaurus.apply_stealth(page)
                return True
            except Exception:
                return False
    except ImportError:
        return False
