import os, random
from typing import List, Optional

class ProxyManager:
    """Simple ProxyManager that reads proxies from environment variable PROXY_LIST (comma-separated)
    or from a file at /app/proxies.txt (one per line). It returns proxy URLs suitable for Playwright launch.
    Example proxy format: http://username:password@host:port or http://host:port
    """
    def __init__(self, proxies: Optional[List[str]] = None):
        self.proxies = proxies or []
        env = os.getenv('PROXY_LIST', '')
        if env:
            self.proxies.extend([p.strip() for p in env.split(',') if p.strip()])
        # file fallback
        fpath = os.getenv('PROXY_FILE', '/app/proxies.txt')
        if os.path.exists(fpath):
            try:
                with open(fpath, 'r') as fh:
                    for line in fh:
                        line = line.strip()
                        if line:
                            self.proxies.append(line)
            except Exception:
                pass
        # dedupe
        self.proxies = list(dict.fromkeys(self.proxies))

    def has_proxies(self) -> bool:
        return len(self.proxies) > 0

    def get_random(self) -> Optional[str]:
        if not self.proxies:
            return None
        return random.choice(self.proxies)

    def get_round_robin(self) -> Optional[str]:
        if not self.proxies:
            return None
        # store index in env (simple approach)
        idx = int(os.getenv('PROXY_IDX', '0')) % len(self.proxies)
        next_idx = (idx + 1) % len(self.proxies)
        try:
            os.environ['PROXY_IDX'] = str(next_idx)
        except Exception:
            pass
        return self.proxies[idx]