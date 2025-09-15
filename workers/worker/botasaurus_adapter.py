# botasaurus_adapter.py - enhanced stealth adapter (best-effort, no external deps)
def apply_stealth(page):
    try:
        # hide webdriver
        page.add_init_script("""() => {
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
        }""")
        # language and plugins spoof
        page.add_init_script("""() => {
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
        }""")
        # chrome runtime and permissions
        page.add_init_script("""() => {
            window.chrome = { runtime: {} };
            const originalQuery = navigator.permissions.query;
            navigator.permissions.__proto__.query = (params) => {
                if (params && params.name === 'notifications') {
                    return Promise.resolve({ state: Notification.permission });
                }
                return originalQuery(params);
            };
        }""")
        # WebGL vendor spoof (best effort)
        page.add_init_script("""() => {
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                // UNMASKED_VENDOR_WEBGL = 37445, UNMASKED_RENDERER_WEBGL = 37446
                if (parameter === 37445) return 'Intel Inc.';
                if (parameter === 37446) return 'Mesa X11';
                return getParameter(parameter);
            };
        }""")
    except Exception:
        pass