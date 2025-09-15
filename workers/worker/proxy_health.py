
import os, json, time, requests
from .proxy_manager import ProxyManager

STATUS_FILE = os.getenv('PROXY_STATUS_FILE', '/tmp/proxy-status.json')

def probe_once(timeout=5):
    pm = ProxyManager()
    statuses = {}
    for p in pm.proxies:
        try:
            proxies = {'http': p, 'https': p}
            r = requests.get('https://httpbin.org/ip', proxies=proxies, timeout=timeout)
            statuses[p] = {'ok': True, 'code': r.status_code, 'time': time.time()}
        except Exception as e:
            statuses[p] = {'ok': False, 'error': str(e), 'time': time.time()}
    try:
        with open(STATUS_FILE, 'w') as fh:
            json.dump(statuses, fh)
    except Exception:
        pass
    return statuses

if __name__ == '__main__':
    # run once when invoked manually
    print(probe_once())
