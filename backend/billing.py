"""Stripe one-time Checkout for lifetime VIP (CNY)."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import stripe

from database import (
    complete_purchase,
    create_purchase,
    is_event_processed,
    mark_event_processed,
    refund_purchase,
    set_stripe_customer_id,
)

logger = logging.getLogger(__name__)

FREE_DAILY_DOWNLOAD_LIMIT = 3


def _require_stripe_key() -> str:
    key = os.getenv("STRIPE_SECRET_KEY", "").strip()
    if not key:
        raise RuntimeError("STRIPE_SECRET_KEY is not configured")
    return key


def _price_id() -> str:
    price_id = os.getenv("STRIPE_PRICE_ID", "").strip()
    if not price_id or price_id == "price_xxx":
        raise RuntimeError(
            "STRIPE_PRICE_ID 未配置。请在 Stripe Dashboard 创建 CNY ¥29 一次性 Price，"
            "并写入 backend/.env 的 STRIPE_PRICE_ID"
        )
    return price_id


def _frontend_origin() -> str:
    return os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").rstrip("/")


def _webhook_secret() -> str:
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    if not secret:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET is not configured")
    return secret


def configure_stripe() -> None:
    stripe.api_key = _require_stripe_key()


def create_checkout_session(user: dict[str, Any]) -> dict[str, str]:
    """Create a one-time payment Checkout Session; returns {checkout_url, session_id}."""
    configure_stripe()
    user_id = user["id"]
    email = user["email"]
    idempotency_key = f"checkout-user-{user_id}-{int(time.time()) // 300}"

    params: dict[str, Any] = {
        "mode": "payment",
        "line_items": [{"price": _price_id(), "quantity": 1}],
        "success_url": f"{_frontend_origin()}/?checkout=success&session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{_frontend_origin()}/?checkout=cancel",
        "client_reference_id": str(user_id),
        "customer_email": email,
        "metadata": {"user_id": str(user_id), "product": "lifetime_vip"},
        "payment_intent_data": {
            "metadata": {"user_id": str(user_id), "product": "lifetime_vip"},
        },
    }
    if user.get("stripe_customer_id"):
        params["customer"] = user["stripe_customer_id"]
        params.pop("customer_email", None)

    try:
        session = stripe.checkout.Session.create(**params, idempotency_key=idempotency_key)
    except stripe.error.InvalidRequestError as e:
        if "No such price" in str(e):
            raise RuntimeError(
                "STRIPE_PRICE_ID 无效。请在 Stripe Dashboard 创建 CNY ¥29 一次性 Price，"
                "并更新 backend/.env 中的 STRIPE_PRICE_ID"
            ) from e
        raise RuntimeError(f"Stripe 请求失败: {str(e)[:200]}") from e
    except stripe.error.StripeError as e:
        raise RuntimeError(f"Stripe 请求失败: {str(e)[:200]}") from e

    create_purchase(user_id=user_id, checkout_session_id=session.id)
    return {"checkout_url": session.url, "session_id": session.id}


def _session_value(session: Any, key: str, default: Any = None) -> Any:
    if isinstance(session, dict):
        return session.get(key, default)
    return getattr(session, key, default)


def fulfill_paid_checkout(session: Any) -> bool:
    """Grant VIP when checkout is paid. Safe to call from webhook and verify (idempotent)."""
    session_id = _session_value(session, "id")
    if not session_id:
        logger.warning("fulfill_paid_checkout: missing session id")
        return False

    payment_status = _session_value(session, "payment_status")
    if payment_status not in ("paid", "no_payment_required"):
        logger.info(
            "Session %s payment_status=%s, skip VIP grant",
            session_id,
            payment_status,
        )
        return False

    user_id_raw = _session_value(session, "client_reference_id") or (
        _session_value(session, "metadata") or {}
    ).get("user_id")
    if not user_id_raw:
        logger.error("fulfill_paid_checkout missing user reference: %s", session_id)
        return False

    user_id = int(user_id_raw)
    customer_id = _session_value(session, "customer")
    if customer_id:
        set_stripe_customer_id(user_id, customer_id)

    amount_total = _session_value(session, "amount_total")
    currency = (_session_value(session, "currency") or "cny").lower()
    amount_cny = amount_total if currency == "cny" else None
    payment_intent = _session_value(session, "payment_intent")
    payment_intent_id = (
        payment_intent
        if isinstance(payment_intent, str)
        else _session_value(payment_intent, "id") if payment_intent else None
    )

    purchase = complete_purchase(
        checkout_session_id=session_id,
        payment_intent_id=payment_intent_id,
        amount_cny=amount_cny,
    )
    if purchase is None:
        logger.error("Purchase record not found for session %s", session_id)
        return False
    logger.info("VIP granted for user_id=%s session=%s", user_id, session_id)
    return True


def verify_checkout_session(session_id: str, user_id: int) -> dict[str, Any]:
    """Verify payment and fulfill VIP if paid (covers webhook delay / local dev)."""
    configure_stripe()
    session = stripe.checkout.Session.retrieve(session_id)
    if session.client_reference_id != str(user_id):
        raise PermissionError("无权查看该订单")

    fulfilled = False
    if session.payment_status in ("paid", "no_payment_required"):
        fulfilled = fulfill_paid_checkout(session)

    return {
        "session_id": session.id,
        "payment_status": session.payment_status,
        "status": session.status,
        "fulfilled": fulfilled,
    }


def handle_webhook(payload: bytes, sig_header: str | None) -> dict[str, str]:
    configure_stripe()
    if not sig_header:
        raise ValueError("Missing Stripe-Signature header")

    event = stripe.Webhook.construct_event(payload, sig_header, _webhook_secret())
    event_id = event["id"]
    event_type = event["type"]

    if is_event_processed(event_id):
        logger.info("Stripe event already processed: %s", event_id)
        return {"status": "already_processed"}

    data_object = event["data"]["object"]

    if event_type == "checkout.session.completed":
        fulfill_paid_checkout(data_object)
    elif event_type == "checkout.session.async_payment_succeeded":
        fulfill_paid_checkout(data_object)
    elif event_type in ("charge.refunded", "charge.refund.updated"):
        _handle_charge_refunded(data_object)
    elif event_type == "refund.created":
        _handle_refund_object(data_object)
    else:
        logger.debug("Unhandled Stripe event type: %s", event_type)

    mark_event_processed(event_id, event_type)
    return {"status": "ok"}


def _handle_charge_refunded(charge: dict[str, Any]) -> None:
    payment_intent = charge.get("payment_intent")
    if not payment_intent:
        logger.warning("charge.refunded without payment_intent")
        return
    pi_id = payment_intent if isinstance(payment_intent, str) else payment_intent.get("id")
    if not pi_id:
        return
    purchase = refund_purchase(pi_id)
    if purchase:
        logger.info("VIP revoked after refund payment_intent=%s user_id=%s", pi_id, purchase.get("user_id"))
    else:
        logger.warning("Refund received but no matching purchase for payment_intent=%s", pi_id)


def _handle_refund_object(refund: dict[str, Any]) -> None:
    payment_intent = refund.get("payment_intent")
    if not payment_intent:
        return
    pi_id = payment_intent if isinstance(payment_intent, str) else payment_intent.get("id")
    if not pi_id:
        return
    status = refund.get("status")
    if status == "succeeded":
        purchase = refund_purchase(pi_id)
        if purchase:
            logger.info("VIP revoked via refund.created payment_intent=%s", pi_id)

