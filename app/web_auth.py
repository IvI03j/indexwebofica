from datetime import datetime, timedelta, timezone
from itsdangerous import URLSafeSerializer
from .config import WEB_SESSION_SECRET, WEB_PLANS
from .supabase_client import supabase


def utcnow():
    return datetime.now(timezone.utc)


def get_serializer():
    return URLSafeSerializer(WEB_SESSION_SECRET, salt="indexwebofica-session")


def make_session_cookie(user_id: int, session_source: str = "telegram_webapp"):
    serializer = get_serializer()
    return serializer.dumps({
        "user_id": user_id,
        "session_source": session_source
    })


def read_session_cookie(cookie_value: str):
    try:
        serializer = get_serializer()
        return serializer.loads(cookie_value)
    except Exception:
        return None


def get_user_by_id(user_id: int):
    if not supabase:
        return None

    res = (
        supabase.table("users")
        .select("*")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def get_user_by_telegram_id(telegram_id: int):
    if not supabase:
        return None

    res = (
        supabase.table("users")
        .select("*")
        .eq("telegram_id", telegram_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def consume_web_login_token(token: str):
    if not supabase or not token:
        return None

    now_iso = utcnow().isoformat()

    res = (
        supabase.table("web_login_tokens")
        .select("*")
        .eq("token", token)
        .is_("used_at", "null")
        .gt("expires_at", now_iso)
        .limit(1)
        .execute()
    )

    if not res.data:
        return None

    token_row = res.data[0]

    supabase.table("web_login_tokens").update({
        "used_at": now_iso
    }).eq("id", token_row["id"]).execute()

    return token_row


def get_active_web_pass(user_id: int):
    if not supabase:
        return None

    now_iso = utcnow().isoformat()

    res = (
        supabase.table("web_access_passes")
        .select("*")
        .eq("user_id", user_id)
        .gt("expires_at", now_iso)
        .order("expires_at", desc=True)
        .limit(1)
        .execute()
    )

    return res.data[0] if res.data else None


def get_user_devices(user_id: int):
    if not supabase:
        return []

    res = (
        supabase.table("web_user_devices")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=False)
        .execute()
    )

    return res.data or []


def can_register_device(user_id: int, device_id: str, device_limit: int):
    if not device_id:
        return False, []

    devices = get_user_devices(user_id)

    for d in devices:
        if d["device_id"] == device_id:
            return True, devices

    if len(devices) >= device_limit:
        return False, devices

    return True, devices


def register_or_touch_device(user_id: int, device_id: str, user_agent: str = "", ip_address: str = ""):
    if not supabase or not device_id:
        return

    now_iso = utcnow().isoformat()

    existing = (
        supabase.table("web_user_devices")
        .select("*")
        .eq("user_id", user_id)
        .eq("device_id", device_id)
        .limit(1)
        .execute()
    )

    if existing.data:
        supabase.table("web_user_devices").update({
            "last_seen_at": now_iso,
            "user_agent": (user_agent or "")[:500],
            "ip_address": (ip_address or "")[:120],
            "device_name": (user_agent or "Dispositivo")[:120],
        }).eq("id", existing.data[0]["id"]).execute()
    else:
        supabase.table("web_user_devices").insert({
            "user_id": user_id,
            "device_id": device_id,
            "device_name": (user_agent or "Dispositivo")[:120],
            "user_agent": (user_agent or "")[:500],
            "ip_address": (ip_address or "")[:120],
            "last_seen_at": now_iso,
        }).execute()


def activate_web_plan(user_id: int, plan_code: str):
    if not supabase:
        return {"ok": False, "error": "Supabase no configurado"}

    plan = WEB_PLANS.get(plan_code)
    if not plan:
        return {"ok": False, "error": "Plan inválido"}

    user = get_user_by_id(user_id)
    if not user:
        return {"ok": False, "error": "Usuario no encontrado"}

    current_coins = int(user.get("coins") or 0)
    plan_cost = int(plan["coins"])

    if current_coins < plan_cost:
        return {"ok": False, "error": "No tienes suficientes monedas"}

    current_pass = get_active_web_pass(user_id)
    now = utcnow()

    if current_pass:
        current_exp = datetime.fromisoformat(current_pass["expires_at"].replace("Z", "+00:00"))
        new_expires_at = current_exp + timedelta(days=plan["days"])
    else:
        new_expires_at = now + timedelta(days=plan["days"])

    new_balance = current_coins - plan_cost

    supabase.table("users").update({
        "coins": new_balance,
        "updated_at": now.isoformat()
    }).eq("id", user_id).execute()

    created_pass = (
        supabase.table("web_access_passes")
        .insert({
            "user_id": user_id,
            "plan_code": plan_code,
            "coins_spent": plan_cost,
            "device_limit": plan["device_limit"],
            "starts_at": now.isoformat(),
            "expires_at": new_expires_at.isoformat(),
        })
        .execute()
    )

    created_pass_id = created_pass.data[0]["id"] if created_pass.data else None

    supabase.table("web_access_transactions").insert({
        "user_id": user_id,
        "pass_id": created_pass_id,
        "action": "purchase",
        "coins_amount": plan_cost,
        "plan_code": plan_code,
    }).execute()

    return {
        "ok": True,
        "balance": new_balance,
        "expires_at": new_expires_at.isoformat(),
        "plan": plan,
    }


def build_access_context(user, device_id="", user_agent="", ip_address=""):
    if not user:
        return {
            "web_user": None,
            "coins": 0,
            "has_web_access": False,
            "web_access_pass": None,
            "device_limit_reached": False,
            "web_devices": [],
        }

    active_pass = get_active_web_pass(user["id"])
    coins = int(user.get("coins") or 0)

    if not active_pass:
        return {
            "web_user": user,
            "coins": coins,
            "has_web_access": False,
            "web_access_pass": None,
            "device_limit_reached": False,
            "web_devices": get_user_devices(user["id"]),
        }

    device_limit = int(active_pass.get("device_limit") or 3)
    allowed, devices = can_register_device(user["id"], device_id, device_limit)

    if not allowed:
        return {
            "web_user": user,
            "coins": coins,
            "has_web_access": False,
            "web_access_pass": active_pass,
            "device_limit_reached": True,
            "web_devices": devices,
        }

    if device_id:
        register_or_touch_device(
            user["id"],
            device_id=device_id,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        devices = get_user_devices(user["id"])

    return {
        "web_user": user,
        "coins": coins,
        "has_web_access": True,
        "web_access_pass": active_pass,
        "device_limit_reached": False,
        "web_devices": devices,
    }
