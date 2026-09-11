import json
import urllib.request
import urllib.parse
import time
import re
import sys

API_BASE = "https://banriland.com/wp-json/wc/store/v1/products"
PROXIES = [
    "https://api.allorigins.win/raw?url={}",
    "https://corsproxy.io/?{}",
    "https://api.codetabs.com/v1/proxy?quest={}",
    "https://thingproxy.freeboard.io/fetch/{}",
    "https://cors-anywhere.herokuapp.com/{}",
]

def fetch_page(url, proxy_template):
    target = proxy_template.format(urllib.parse.quote(url, safe=''))
    req = urllib.request.Request(target, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))

def fetch_all_products():
    # اول مستقیم امتحان کن
    for source in ['direct'] + PROXIES:
        try:
            all_products = []
            page = 1
            while page <= 10:
                url = f"{API_BASE}?per_page=100&page={page}"
                if source == 'direct':
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=20) as r:
                        data = json.loads(r.read().decode('utf-8'))
                else:
                    data = fetch_page(url, source)
                if not data or len(data) == 0:
                    break
                all_products.extend(data)
                page += 1
                time.sleep(0.5)
            if all_products:
                print(f"✅ از {source}: {len(all_products)} محصول")
                return all_products
        except Exception as e:
            print(f"⚠️ {source}: {e}")
            continue
    return None

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
        print("⚠️ تغییری پیدا نشد")
        return False
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    return True

def main():
    print("🔄 در حال استخراج محصولات...")
    products = fetch_all_products()
    if not products:
        print("❌ هیچ منبعی جواب نداد")
        sys.exit(0)  # بدون خطا خارج شو
    
    db = build_db(products)
    print(f"📊 {len(db)} محصول معتبر")
    
    if len(db) < 10:
        print("❌ تعداد محصولات خیلی کمه، به‌روزرسانی لغو شد")
        sys.exit(0)
    
    if update_html(db):
        print(f"✅ index.html به‌روز شد: {len(db)} محصول")
    else:
        print("ℹ️ تغییری لازم نبود")

if __name__ == '__main__':
    main()
