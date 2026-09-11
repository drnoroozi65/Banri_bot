import json
import urllib.request
import urllib.parse
import os
import sys
import re

SCRAPER_KEY = os.environ.get('SCRAPER_API_KEY', '')
API_BASE = "https://banriland.com/wp-json/wc/store/v1/products"

def fetch_via_scraperapi(target_url):
    params = {
        'api_key': SCRAPER_KEY,
        'url': target_url,
        'country_code': 'ir',
    }
    url = 'https://api.scraperapi.com/?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode('utf-8'))

def fetch_all():
    if not SCRAPER_KEY:
        print("SCRAPER_API_KEY not set")
        return []
    all_products = []
    for page in range(1, 11):
        target = f"{API_BASE}?per_page=100&page={page}"
        try:
            data = fetch_via_scraperapi(target)
            if not data or len(data) == 0:
                break
            all_products.extend(data)
            print(f"Page {page}: {len(data)}")
        except Exception as e:
            print(f"Page {page} error: {e}")
            break
    return all_products

def build_db(products):
    db = []
    for p in products:
        if not p.get('prices') or not p['prices'].get('price'):
            continue
        try:
            price = int(p['prices']['price'])
        except:
            continue
        if price <= 0:
            continue
        db.append({
            'name': p['name'],
            'price': price,
            'link': p['permalink'],
            'img': (p['images'][0]['src'] if p.get('images') else '') or '',
            'sale': bool(p.get('on_sale')),
            'cat': [c['name'] for c in p.get('categories', [])]
        })
    return db

def update_html(db):
    with open('index.html', encoding='utf-8') as f:
        content = f.read()
    data_json = json.dumps(db, ensure_ascii=False).replace('</', '<\\/')
    new_content = re.sub(r'var DB\s*=\s*\[.*?\];', f'var DB = {data_json};', content, count=1, flags=re.DOTALL)
    if new_content == content:
        return False
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    return True

def main():
    print("Fetching products...")
    products = fetch_all()
    if not products:
        print("No products")
        sys.exit(0)
    db = build_db(products)
    print(f"{len(db)} valid products")
    if len(db) < 10:
        print("Too few, aborting")
        sys.exit(0)
    if update_html(db):
        print(f"Updated: {len(db)} products")
    else:
        print("No changes")

if __name__ == '__main__':
    main()
