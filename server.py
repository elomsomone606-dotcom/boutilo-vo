#!/usr/bin/env python3
"""BoutiquePilot: single-shop-per-account MVP with server-side tenancy.
Python standard library. Deploy behind HTTPS; see Guide-BoutiquePilot.md.
"""
import os, json, sqlite3, secrets, hashlib, hmac, time, re, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from http.cookies import SimpleCookie
from pathlib import Path
from collections import defaultdict, deque
from workspace_schema import validate_workspace

ROOT = Path(__file__).resolve().parent
DATABASE_URL = os.environ.get('DATABASE_URL')
PORT = int(os.environ.get('PORT', '3000'))
SESSION_TTL = 7 * 24 * 3600
attempts = defaultdict(deque)
rate_lock = threading.Lock()

if DATABASE_URL:
    import psycopg
    from psycopg.rows import dict_row
    IntegrityError = psycopg.IntegrityError
else:
    if os.environ.get('VERCEL'):
        raise RuntimeError('DATABASE_URL is required on Vercel')
    DATA = ROOT / 'private_data'
    DATA.mkdir(mode=0o700, exist_ok=True)
    DB = DATA / 'boutiquepilot.sqlite3'
    IntegrityError = sqlite3.IntegrityError

def log_failure(stage, error):
    # Never log exception text, request data, database URLs or credentials.
    state = getattr(error, 'sqlstate', None)
    if not isinstance(state, str) or not re.fullmatch(r'[0-9A-Z]{5}', state):
        state = 'none'
    print(f'Boutilo diagnostic: stage={stage} type={type(error).__name__} sqlstate={state}', flush=True)

class PostgresConnection:
    def __init__(self):
        try:
            self.conn = psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=10, sslmode="verify-full")
        except Exception as error:
            log_failure('db_connect', error)
            raise
        try:
            self.conn.execute('SET search_path TO boutique_private')
        except Exception as error:
            self.conn.close()
            log_failure('db_schema', error)
            raise
    def __enter__(self):
        return self
    def __exit__(self, typ, value, traceback):
        try:
            if typ is None:
                self.conn.commit()
            else:
                self.conn.rollback()
        finally:
            self.conn.close()
    def execute(self, sql, params=()):
        return self.conn.execute(sql.replace('?', '%s'), params)
    def commit(self):
        self.conn.commit()

def connection():
    if DATABASE_URL:
        return PostgresConnection()
    c = sqlite3.connect(DB, timeout=15)
    c.execute('PRAGMA foreign_keys=ON')
    c.row_factory = sqlite3.Row
    return c

if not DATABASE_URL:
    with connection() as c:
        c.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE COLLATE NOCASE, password TEXT NOT NULL, created INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS shops(user_id TEXT PRIMARY KEY REFERENCES users(id), data TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), expires INTEGER NOT NULL);
        """)
    try:
        os.chmod(DB, 0o600)
    except OSError:
        pass

def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()
    return salt + ':' + digest

def valid_password(password, stored):
    try:
        return hmac.compare_digest(password_hash(password, stored.split(':')[0]), stored)
    except (ValueError, TypeError):
        return False

def empty_store(name):
    return {'version': 1, 'demo': False, 'shop': {'name': name, 'phone': '', 'address': ''}, 'products': [], 'customers': [], 'sales': []}

def validate_store(d):
    if isinstance(d, dict):
        validate_workspace(d.get('workspace'))
    def integer(n, low=0):
        return type(n) is int and low <= n <= 9007199254740991
    def text(v, maxlen=200):
        return isinstance(v, str) and len(v) <= maxlen
    if not isinstance(d, dict) or d.get('version') != 1 or type(d.get('demo')) is not bool:
        raise ValueError('Format de boutique invalide.')
    shop = d.get('shop')
    if not isinstance(shop, dict) or not text(shop.get('name'), 100) or not shop['name'].strip():
        raise ValueError('Nom de boutique invalide.')
    if not all(text(shop.get(k, ''), 200) for k in ('phone', 'address')):
        raise ValueError('Informations boutique invalides.')
    for key in ('products', 'customers', 'sales'):
        if not isinstance(d.get(key), list) or len(d[key]) > 50000:
            raise ValueError('Catalogue ou historique invalide.')
    pids, cids, sids = set(), set(), set()
    debts, payments = {}, {}
    for p in d['products']:
        if not isinstance(p, dict) or not text(p.get('id'), 100) or not p['id'] or p['id'] in pids or not text(p.get('name'), 100) or not p['name'].strip() or not text(p.get('category', ''), 100) or not all(integer(p.get(k)) for k in ('price', 'cost', 'stock', 'min')):
            raise ValueError('Produit invalide.')
        pids.add(p['id'])
    for customer in d['customers']:
        if not isinstance(customer, dict) or not text(customer.get('id'), 100) or not customer['id'] or customer['id'] in cids or not text(customer.get('name'), 100) or not customer['name'].strip() or not text(customer.get('phone', ''), 100) or not isinstance(customer.get('payments'), list):
            raise ValueError('Client invalide.')
        cids.add(customer['id'])
        debts[customer['id']] = 0
        payments[customer['id']] = 0
        for p in customer['payments']:
            if not isinstance(p, dict) or not integer(p.get('amount'), 1) or not text(p.get('date'), 60) or p.get('method') not in ('cash', 'mobile'):
                raise ValueError('Remboursement invalide.')
            payments[customer['id']] += p['amount']
    for s in d['sales']:
        if not isinstance(s, dict) or not text(s.get('id'), 100) or not s['id'] or s['id'] in sids or not text(s.get('number'), 100) or not text(s.get('date'), 60) or not all(integer(s.get(k)) for k in ('total', 'paid')) or s['paid'] > s['total'] or s.get('method') not in ('cash', 'mobile', 'credit') or not isinstance(s.get('items'), list) or not s['items']:
            raise ValueError('Vente invalide.')
        sids.add(s['id'])
        cid = s.get('customerId')
        if (cid is not None and cid not in cids) or (s['paid'] < s['total'] and not cid):
            raise ValueError('Client de vente invalide.')
        total = 0
        for i in s['items']:
            if not isinstance(i, dict) or not text(i.get('name'), 100) or not all(integer(i.get(k)) for k in ('price', 'cost')) or not integer(i.get('qty'), 1):
                raise ValueError('Ligne de vente invalide.')
            total += i['price'] * i['qty']
        if total != s['total'] or not integer(total):
            raise ValueError('Total invalide.')
        if cid:
            debts[cid] += s['total'] - s['paid']
    if any(payments[cid] > debts[cid] for cid in cids):
        raise ValueError('Remboursement supérieur au crédit.')

class Handler(BaseHTTPRequestHandler):
    server_version = 'BoutiquePilot'
    def log_message(self, format, *args):
        # Never log credentials, cookies, or request bodies.
        super().log_message(format, *args)

    def send(self, status, data, cookie=None, html=False):
        raw = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8' if html else 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'same-origin')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; media-src 'self'; font-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'")
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.end_headers()
        self.wfile.write(raw)

    def body(self):
        if self.headers.get('X-BoutiquePilot') != '1':
            raise PermissionError('Requête non autorisée.')
        if 'application/json' not in self.headers.get('Content-Type', ''):
            raise ValueError('JSON attendu.')
        size = int(self.headers.get('Content-Length', '0'))
        if size < 1 or size > 10 * 1024 * 1024:
            raise ValueError('Requête trop volumineuse ou vide.')
        body = json.loads(self.rfile.read(size))
        if not isinstance(body, dict):
            raise ValueError('Format JSON invalide.')
        return body

    def session(self, c):
        try:
            cookie = SimpleCookie(self.headers.get('Cookie', ''))
            token = cookie['bp_session'].value
        except (KeyError, ValueError):
            return None
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return c.execute('SELECT users.*, sessions.token_hash FROM sessions JOIN users ON users.id=sessions.user_id WHERE token_hash=? AND expires>?', (token_hash, int(time.time()))).fetchone()

    def new_session(self, c, user_id):
        token = secrets.token_urlsafe(32)
        c.execute('DELETE FROM sessions WHERE expires<?', (int(time.time()),))
        c.execute('INSERT INTO sessions VALUES(?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), user_id, int(time.time()) + SESSION_TTL))
        secure = '; Secure' if self.headers.get('X-Forwarded-Proto', '').split(',')[0].strip() == 'https' or os.environ.get('COOKIE_SECURE') == '1' else ''
        return f'bp_session={token}; HttpOnly; SameSite=Lax; Path=/; Max-Age={SESSION_TTL}{secure}'

    def limited(self, key):
        with rate_lock:
            now = time.time()
            q = attempts[key]
            while q and q[0] < now - 900:
                q.popleft()
            if len(q) >= 30:
                return True
            q.append(now)
            if len(attempts) > 20000:
                for k in list(attempts):
                    if not attempts[k] or attempts[k][-1] < now - 900:
                        del attempts[k]
            return False

    def serve_brand_video(self, filename, head=False):
        # Only explicitly whitelisted public marketing assets; never expose private data.
        path = ROOT / 'assets' / filename
        if not path.is_file():
            return self.send(404, {'error': 'Vidéo indisponible.'})
        size = path.stat().st_size
        start, end, status = 0, size - 1, 200
        requested = self.headers.get('Range')
        if requested:
            match = re.fullmatch(r'bytes=(\d*)-(\d*)', requested.strip())
            try:
                if not match or not any(match.groups()):
                    raise ValueError()
                first, last = match.groups()
                if first:
                    start = int(first)
                    end = min(int(last), size - 1) if last else size - 1
                else:
                    suffix = int(last)
                    if suffix <= 0:
                        raise ValueError()
                    start = max(0, size - suffix)
                if start >= size or start > end:
                    raise ValueError()
                status = 206
            except (ValueError, OverflowError):
                self.send_response(416)
                self.send_header('Content-Range', f'bytes */{size}')
                self.send_header('Content-Length', '0')
                self.end_headers()
                return
        self.send_response(status)
        self.send_header('Content-Type', 'video/mp4')
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Length', str(end - start + 1))
        self.send_header('Cache-Control', 'public, max-age=3600')
        self.send_header('X-Content-Type-Options', 'nosniff')
        if status == 206:
            self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.end_headers()
        if head:
            return
        try:
            with path.open('rb') as stream:
                stream.seek(start)
                remaining = end - start + 1
                while remaining:
                    chunk = stream.read(min(65536, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_HEAD(self):
        path = self.path.split('?')[0]
        videos = {'/assets/boutiquepilot-accueil.mp4', '/assets/boutiquepilot-accueil-mobile.mp4', '/assets/boutiquepilot-titre-anime.mp4'}
        if path in videos:
            return self.serve_brand_video(path.rsplit('/', 1)[1], head=True)
        self.send_response(404)
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_GET(self):
        path = self.path.split('?')[0]
        if path in ('/assets/boutiquepilot-accueil.mp4', '/assets/boutiquepilot-accueil-mobile.mp4', '/assets/boutiquepilot-titre-anime.mp4'):
            return self.serve_brand_video(path.rsplit('/', 1)[1])
        if path in ('/', '/index.html'):
            return self.send(200, (ROOT / 'index.html').read_bytes(), html=True)
        if path == '/api/health':
            return self.send(200, {'ok': True})
        if path != '/api/me':
            return self.send(404, {'error': 'Page introuvable.'})
        with connection() as c:
            user = self.session(c)
            if not user:
                return self.send(401, {'error': 'Connectez-vous pour accéder à votre boutique.'})
            shop = c.execute('SELECT data,revision FROM shops WHERE user_id=?', (user['id'],)).fetchone()
            self.send(200, {'user': {'name': user['name'], 'email': user['email']}, 'store': json.loads(shop['data']), 'revision': shop['revision']})

    def do_POST(self):
        try:
            body = self.body()
            path = self.path.split('?')[0]
            if path not in ('/api/register', '/api/login', '/api/logout'):
                return self.send(404, {'error': 'Action introuvable.'})
            with connection() as c:
                if path == '/api/logout':
                    user = self.session(c)
                    if user:
                        c.execute('DELETE FROM sessions WHERE token_hash=?', (user['token_hash'],))
                        c.commit()
                    return self.send(200, {'ok': True}, 'bp_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0')
                email = body.get('email', '')
                password = body.get('password', '')
                if not isinstance(email, str) or not isinstance(password, str):
                    raise ValueError('Identifiants invalides.')
                email = email.strip().lower()
                if len(email) > 254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email) or len(password) > 128:
                    raise ValueError('Saisissez une adresse e-mail valide et un mot de passe de 128 caractères maximum.')
                if self.limited(('email', email)) or self.limited(('ip', self.client_address[0])):
                    return self.send(429, {'error': 'Trop de tentatives. Réessayez dans 15 minutes.'})
                if path == '/api/register':
                    name, shop_name = body.get('name', ''), body.get('shop', '')
                    if not isinstance(name, str) or not isinstance(shop_name, str) or not name.strip() or not shop_name.strip() or len(name) > 80 or len(shop_name) > 80 or len(password) < 10:
                        raise ValueError('Renseignez votre nom, votre boutique et un mot de passe d’au moins 10 caractères.')
                    user_id = secrets.token_hex(16)
                    store = empty_store(shop_name.strip())
                    try:
                        c.execute('INSERT INTO users VALUES(?,?,?,?,?)', (user_id, name.strip(), email, password_hash(password), int(time.time())))
                    except IntegrityError:
                        return self.send(409, {'error': 'Impossible de créer ce compte avec cette adresse. Essayez de vous connecter.'})
                    c.execute('INSERT INTO shops VALUES(?,?,1)', (user_id, json.dumps(store, ensure_ascii=False)))
                    cookie = self.new_session(c, user_id)
                    # Commit before sending success so a following request sees the account.
                    c.commit()
                    return self.send(201, {'user': {'name': name.strip(), 'email': email}, 'store': store, 'revision': 1}, cookie)
                user = c.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
                # Perform the expensive hash even for an unknown account.
                stored = user['password'] if user else '0' * 32 + ':' + '0' * 128
                ok = valid_password(password, stored)
                if not user or not ok:
                    return self.send(401, {'error': 'Adresse e-mail ou mot de passe incorrect.'})
                shop = c.execute('SELECT data,revision FROM shops WHERE user_id=?', (user['id'],)).fetchone()
                cookie = self.new_session(c, user['id'])
                c.commit()
                self.send(200, {'user': {'name': user['name'], 'email': user['email']}, 'store': json.loads(shop['data']), 'revision': shop['revision']}, cookie)
        except PermissionError as e:
            self.send(403, {'error': str(e)})
        except (ValueError, TypeError, KeyError, OverflowError) as e:
            self.send(400, {'error': str(e) if isinstance(e, ValueError) else 'Données invalides.'})
        except Exception as error:
            log_failure('request', error)
            self.send(500, {'error': 'Erreur serveur. Réessayez dans un instant.'})

    def do_PUT(self):
        try:
            if self.path != '/api/store':
                return self.send(404, {'error': 'Action introuvable.'})
            body = self.body()
            with connection() as c:
                user = self.session(c)
                if not user:
                    return self.send(401, {'error': 'Votre session a expiré. Reconnectez-vous.'})
                store = body.get('store')
                validate_store(store)
                revision = body.get('revision')
                if type(revision) is not int:
                    raise ValueError('Version des données invalide.')
                # Account identity always comes from the session, never from request input.
                updated = c.execute('UPDATE shops SET data=?,revision=revision+1 WHERE user_id=? AND revision=?', (json.dumps(store, ensure_ascii=False), user['id'], revision))
                if updated.rowcount != 1:
                    return self.send(409, {'error': 'Votre boutique a changé sur un autre appareil ou onglet. Actualisez la page avant de recommencer.', 'conflict': True})
                c.commit()
                self.send(200, {'revision': revision + 1})
        except PermissionError as e:
            self.send(403, {'error': str(e)})
        except (ValueError, TypeError, KeyError, OverflowError) as e:
            self.send(400, {'error': str(e) if isinstance(e, ValueError) else 'Données invalides.'})
        except Exception as error:
            log_failure('request', error)
            self.send(500, {'error': 'Erreur serveur. Réessayez dans un instant.'})

if __name__ == '__main__':
    print(f'BoutiquePilot listening on 0.0.0.0:{PORT}', flush=True)
    ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
