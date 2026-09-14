import json, urllib.request, urllib.parse, urllib.error, hmac, hashlib, time, re

BASE = 'http://localhost:8788'
def req(path, method='GET', body=None, headers=None):
    h = dict(headers or {})
    data = None
    if body is not None:
        data = json.dumps(body).encode() if isinstance(body, dict) else body
        h.setdefault('content-type', 'application/json')
    r = urllib.request.Request(BASE + path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read() or b'{}')
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b'{}')

def hook(event):
    raw = json.dumps(event); t = str(int(time.time()))
    sig = hmac.new(b'whsec_testsecret_local', f'{t}.{raw}'.encode(), hashlib.sha256).hexdigest()
    return req('/v1/stripe/webhook', 'POST', raw.encode(),
               headers={'stripe-signature': f't={t},v1={sig}', 'content-type': 'application/json'})

st, out = req('/v1/auth/request-link', 'POST', {'email': 'buyer@test.dev'})
print('1 request-link:', st)
token = re.search(r'token=([^&]+)', out['dev_link']).group(1)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None
opener = urllib.request.build_opener(NoRedirect)
try:
    resp = opener.open(f"{BASE}/v1/auth/callback?token={token}"); loc = resp.headers.get('location')
except urllib.error.HTTPError as e:
    loc = e.headers.get('location')
session = urllib.parse.unquote(loc.split('#session=')[1])
AUTH = {'authorization': 'Bearer ' + session}
st, me = req('/v1/me', headers=AUTH)
print('2 me before purchase:', st, me['tier'])

st, out = req('/v1/billing/checkout', 'POST', {'plan': 'pro'}, headers=AUTH)
print('3 checkout w/ dummy key (expect 500 stripe error):', st, out.get('error'))

st, out = hook({'type': 'checkout.session.completed', 'data': {'object': {
    'id': 'cs_1', 'mode': 'subscription', 'customer': 'cus_1',
    'customer_details': {'email': 'buyer@test.dev'}, 'metadata': {'plan': 'pro'}}}})
print('4 webhook checkout.completed:', st, out)
st, me = req('/v1/me', headers=AUTH)
print('  me:', me['tier'], '| src', me['tierSource'], '| hasBilling', me['hasBilling'])

pe = int(time.time()) + 30*86400
hook({'type': 'customer.subscription.updated', 'data': {'object': {
    'id': 'sub_1', 'customer': 'cus_1', 'status': 'active',
    'current_period_end': pe, 'cancel_at_period_end': False}}})
st, me = req('/v1/me', headers=AUTH)
print('5 after sub.updated: tier', me['tier'], '| expires', me['tierExpiresAt'])

raw = json.dumps({'type': 'customer.subscription.updated', 'data': {'object': {'id': 'x', 'customer': 'cus_1', 'status': 'active', 'current_period_end': pe}}})
t = str(int(time.time()))
st, out = req('/v1/stripe/webhook', 'POST', raw.encode(),
              headers={'stripe-signature': f't={t},v1=deadbeef', 'content-type': 'application/json'})
print('6 bad signature rejected:', st, out.get('error'))

hook({'type': 'customer.subscription.deleted', 'data': {'object': {
    'id': 'sub_1', 'customer': 'cus_1', 'status': 'canceled'}}})
st, me = req('/v1/me', headers=AUTH)
print('7 after cancellation: tier', me['tier'])

hook({'type': 'checkout.session.completed', 'data': {'object': {
    'id': 'cs_2', 'mode': 'payment', 'customer': 'cus_1',
    'customer_details': {'email': 'buyer@test.dev'}, 'metadata': {'plan': 'pass'}}}})
st, me = req('/v1/me', headers=AUTH)
print('8 after weekend pass: tier', me['tier'], '| src', me['tierSource'], '| expires', me['tierExpiresAt'])
print('DONE')

# Run: start `npx wrangler dev --port 8788` (with .dev.vars from the example),
# apply migrations locally, then `python3 test/billing_e2e.py`.
