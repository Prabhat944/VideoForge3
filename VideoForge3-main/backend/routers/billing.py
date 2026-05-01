import logging
from fastapi import APIRouter, Depends, HTTPException, Request

from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, CheckoutSessionRequest,
)

from core.db import db
from core.config import STRIPE_API_KEY, APP_BASE_URL
from core.deps import get_current_user, now_iso
from core.schemas import CheckoutRequest

router = APIRouter(tags=["billing"])

PLANS = {
    "creator": {"name": "Creator", "amount": 29.00, "credits": 1500},
    "studio": {"name": "Studio", "amount": 99.00, "credits": 999999},
    "credits_100": {"name": "100 Credits", "amount": 5.00, "credits": 100},
}


@router.get("/billing/plans")
async def billing_plans():
    return {"plans": PLANS}


@router.post("/billing/checkout")
async def create_checkout(payload: CheckoutRequest, current=Depends(get_current_user)):
    if payload.plan_id not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")
    plan = PLANS[payload.plan_id]
    origin = payload.origin_url.rstrip("/")
    success_url = f"{origin}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin}/pricing"
    webhook_url = f"{APP_BASE_URL}/api/webhook/stripe"

    sc = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    req = CheckoutSessionRequest(
        amount=float(plan["amount"]), currency="usd",
        success_url=success_url, cancel_url=cancel_url,
        metadata={
            "user_id": current["id"], "plan_id": payload.plan_id,
            "credits": str(plan["credits"]),
        },
    )
    session = await sc.create_checkout_session(req)
    await db.payment_transactions.insert_one({
        "session_id": session.session_id,
        "user_id": current["id"],
        "plan_id": payload.plan_id,
        "amount": plan["amount"],
        "currency": "usd",
        "status": "initiated",
        "payment_status": "pending",
        "metadata": {"plan_id": payload.plan_id, "credits": plan["credits"]},
        "created_at": now_iso(),
    })
    return {"url": session.url, "session_id": session.session_id}


@router.get("/billing/status/{session_id}")
async def billing_status(session_id: str, current=Depends(get_current_user)):
    txn = await db.payment_transactions.find_one(
        {"session_id": session_id, "user_id": current["id"]}, {"_id": 0}
    )
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    import stripe as stripe_sdk
    stripe_sdk.api_key = STRIPE_API_KEY
    if "sk_test_emergent" in STRIPE_API_KEY:
        stripe_sdk.api_base = "https://integrations.emergentagent.com/stripe"
    new_payment_status = txn.get("payment_status", "pending")
    new_status = txn.get("status", "open")
    amount_total = int((txn.get("amount") or 0) * 100)
    currency = txn.get("currency", "usd")

    try:
        s = stripe_sdk.checkout.Session.retrieve(session_id)
        new_payment_status = s.get("payment_status") or new_payment_status
        new_status = s.get("status") or new_status
        amount_total = s.get("amount_total") or amount_total
        currency = s.get("currency") or currency
    except Exception as e:
        logging.warning(f"Stripe retrieve unavailable: {e}; relying on DB/webhook state")

    already_credited = txn.get("payment_status") == "paid"

    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {"status": new_status, "payment_status": new_payment_status, "updated_at": now_iso()}},
    )

    if not already_credited and new_payment_status == "paid":
        plan_id = txn["plan_id"]
        plan = PLANS.get(plan_id, {})
        credits = int(plan.get("credits", 0))
        update = {"$inc": {"credits": credits}}
        if plan_id in ("creator", "studio"):
            update["$set"] = {"plan": plan_id}
        await db.users.update_one({"id": current["id"]}, update)

    return {
        "session_id": session_id,
        "status": new_status,
        "payment_status": new_payment_status,
        "amount_total": amount_total,
        "currency": currency,
    }


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    sc = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=f"{APP_BASE_URL}/api/webhook/stripe")
    try:
        evt = await sc.handle_webhook(body, sig)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {e}")

    if evt.payment_status == "paid":
        txn = await db.payment_transactions.find_one({"session_id": evt.session_id})
        if txn and txn.get("payment_status") != "paid":
            await db.payment_transactions.update_one(
                {"session_id": evt.session_id},
                {"$set": {"payment_status": "paid", "status": "complete", "updated_at": now_iso()}},
            )
            plan_id = txn.get("plan_id")
            plan = PLANS.get(plan_id, {})
            credits = int(plan.get("credits", 0))
            update = {"$inc": {"credits": credits}}
            if plan_id in ("creator", "studio"):
                update["$set"] = {"plan": plan_id}
            await db.users.update_one({"id": txn["user_id"]}, update)
    return {"ok": True}
