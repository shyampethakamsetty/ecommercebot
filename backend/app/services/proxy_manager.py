class ProxyManager:
    def __init__(self):
        self.pool = []

    def add_proxy(self, server, username=None, password=None):
        self.pool.append({'server': server, 'username': username, 'password': password})

    def get_proxy(self):
        # Rotate simple round-robin
        if not self.pool:
            return None
        p = self.pool.pop(0)
        self.pool.append(p)
        if p.get('username'):
            return f"http://{p['username']}:{p['password']}@{p['server']}"
        return f"http://{p['server']}"
