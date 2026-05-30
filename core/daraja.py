import json
import base64
import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from django.conf import settings


def _b64(data):
    return base64.b64encode(data.encode()).decode()


def get_access_token():
    url = f"{settings.DARAJA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    auth = _b64(f"{settings.DARAJA_CONSUMER_KEY}:{settings.DARAJA_CONSUMER_SECRET}")
    req = Request(url, headers={"Authorization": f"Basic {auth}"})
    try:
        resp = urlopen(req, timeout=30)
        return json.loads(resp.read().decode()).get("access_token")
    except URLError as e:
        raise RuntimeError(f"Auth failed: {e}")


def stk_push(phone, amount, account_ref="RentEase", transaction_desc="Rent Payment"):
    token = get_access_token()
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    password = _b64(f"{settings.DARAJA_SHORTCODE}{settings.DARAJA_PASSKEY}{timestamp}")

    phone = _fmt_phone(phone)

    payload = json.dumps({
        "BusinessShortCode": settings.DARAJA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": str(int(amount)),
        "PartyA": phone,
        "PartyB": settings.DARAJA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": settings.DARAJA_CALLBACK_URL,
        "AccountReference": account_ref[:12],
        "TransactionDesc": transaction_desc[:13],
    }).encode()

    url = f"{settings.DARAJA_BASE_URL}/mpesa/stkpush/v1/processrequest"
    req = Request(
        url, data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        resp = urlopen(req, timeout=30)
        return json.loads(resp.read().decode())
    except URLError as e:
        raise RuntimeError(f"STK Push failed: {e}")


def _fmt_phone(phone):
    if phone.startswith("+"):
        phone = phone[1:]
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    if not phone.startswith("254"):
        phone = "254" + phone
    return phone


def c2b_simulate_transaction(amount, phone, bill_ref, command_id="CustomerPayBillOnline"):
    """Tell Safaricom sandbox to simulate a C2B payment (triggers our confirmation callback)."""
    token = get_access_token()
    phone = _fmt_phone(phone)
    payload = json.dumps({
        "ShortCode": settings.DARAJA_C2B_SHORTCODE,
        "CommandID": command_id,
        "Amount": str(int(amount)),
        "Msisdn": phone,
        "BillRefNumber": bill_ref,
    }).encode()

    url = f"{settings.DARAJA_BASE_URL}/mpesa/c2b/v1/simulate"
    req = Request(url, data=payload, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    try:
        resp = urlopen(req, timeout=30)
        return json.loads(resp.read().decode())
    except HTTPError as e:
        raise RuntimeError(f"C2B simulate failed ({e.code}): {e.read().decode()}")


def c2b_register_urls():
    """Register C2B validation & confirmation URLs with Safaricom."""
    token = get_access_token()
    payload = json.dumps({
        "ShortCode": settings.DARAJA_C2B_SHORTCODE,
        "ResponseType": settings.DARAJA_C2B_RESPONSE_TYPE,
        "ConfirmationURL": settings.DARAJA_C2B_CONFIRMATION_URL,
        "ValidationURL": settings.DARAJA_C2B_VALIDATION_URL,
    }).encode()

    url = f"{settings.DARAJA_BASE_URL}/mpesa/c2b/v1/registerurl"
    req = Request(url, data=payload, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    try:
        resp = urlopen(req, timeout=30)
        return json.loads(resp.read().decode())
    except HTTPError as e:
        body = e.read().decode()
        # Duplicate means already registered — treat as success
        if "Duplicate" in body:
            return {"ResponseCode": "0", "ResponseDescription": "URLs already registered"}
        raise RuntimeError(f"C2B register failed ({e.code}): {body}")
