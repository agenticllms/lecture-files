"""The Husky Tech store: its orders, its policy, and the agent's tools.

The orders and today's date are fixed, so an evaluation task has exactly one correct outcome. The tools
that act, issue_refund and escalate_to_human, record what they did in `env` instead of moving money.
The evaluation reads `env` after each run. Call `reset()` before each run.
"""
from datetime import date, datetime

from langchain.tools import tool

TODAY = date(2026, 11, 13)
RETURN_DAYS = 30
REFUND_LIMIT = 300

ORDERS = {
    "HT-2001": {"item": "Wireless headphones", "status": "delivered", "delivered_on": "2026-11-03", "price": 79.99},
    "HT-2002": {"item": "Mechanical keyboard", "status": "delivered", "delivered_on": "2026-09-29", "price": 129.00},
    "HT-2003": {"item": "USB-C dock", "status": "shipped", "ordered_on": "2026-11-08", "eta": "2026-11-15", "price": 59.50},
    "HT-2004": {"item": "27-inch monitor", "status": "delivered", "delivered_on": "2026-10-14", "price": 219.00},
    "HT-2005": {"item": "Webcam", "status": "delivered", "delivered_on": "2026-10-13", "price": 64.00},
    "HT-2006": {"item": "Laptop stand", "status": "delivered", "delivered_on": "2026-10-01", "price": 45.00},
    "HT-2007": {"item": "Gaming laptop", "status": "delivered", "delivered_on": "2026-11-06", "price": 1299.00},
    "HT-2008": {"item": "Bluetooth speaker", "status": "delivered", "delivered_on": "2026-10-30", "price": 89.00},
    "HT-2009": {"item": "Phone charger", "status": "delivered", "delivered_on": "2026-11-10", "price": 24.99},
}

FAQ = {
    "shipping": "Standard shipping takes 3-5 business days. Orders over $50 ship free.",
    "return": "Delivered items can be returned within 30 days of delivery for a full refund.",
    "warranty": "All electronics include a one-year manufacturer warranty.",
    "hours": "Support is available Monday through Friday, 9am to 6pm ET.",
}

POLICY_PROMPT = """You are the customer support assistant for Husky Tech, an online electronics store.

Refund policy:
- A delivered order can be refunded within 30 days of delivery. Check it with check_return_eligibility
  before you refund it.
- Refunds over $300 must be approved by a person. For those, use escalate_to_human instead of issue_refund.
- An order that has not been delivered yet cannot be refunded.
- Past 30 days, do not refund. Offer the one-year manufacturer warranty instead.

Other rules:
- Use the tools for every order detail. Do not rely on what the customer says about dates or prices.
- If the customer asks for a person, use escalate_to_human.
- Act on a clear request without asking for confirmation. Be concise and polite."""

CHECK_PROMPT = POLICY_PROMPT + """

Before you call issue_refund or escalate_to_human, write one line for each order in the request: its
delivery age and price as the tools report them, and the rule above that applies. Then act on those lines."""

env = {"refunds": [], "escalations": []}


def reset():
    env["refunds"] = []
    env["escalations"] = []


def _order(order_id):
    return ORDERS.get(order_id.strip().upper())


def days_since_delivery(order_id):
    order = _order(order_id)
    delivered = datetime.strptime(order["delivered_on"], "%Y-%m-%d").date()
    return (TODAY - delivered).days


@tool
def look_up_order(order_id: str) -> str:
    """Look up an order by its id (e.g. HT-2001) and return its current details."""
    order = _order(order_id)
    if order is None:
        return f"No order found with id {order_id}. Ask the customer to double-check it."
    return str(order)


@tool
def check_return_eligibility(order_id: str) -> str:
    """Check whether an order can still be returned under the 30-day policy. Takes the order id."""
    order = _order(order_id)
    if order is None:
        return f"No order found with id {order_id}."
    if order["status"] != "delivered":
        return f"Order {order_id} has not been delivered yet, so it cannot be returned yet."
    days = days_since_delivery(order_id)
    if days <= RETURN_DAYS:
        return f"Eligible: delivered {days} days ago; returns are accepted within {RETURN_DAYS} days of delivery."
    return f"Not eligible: delivered {days} days ago, which is past the {RETURN_DAYS}-day window."


@tool
def issue_refund(order_id: str, reason: str) -> str:
    """Refund an order in full. Give the order id and a one-sentence reason."""
    order = _order(order_id)
    if order is None:
        return f"No order found with id {order_id}. No refund was issued."
    env["refunds"].append(order_id.strip().upper())
    return f"Refund of ${order['price']:.2f} issued for {order_id.strip().upper()}."


@tool
def escalate_to_human(reason: str) -> str:
    """Hand the conversation to a human support agent. Provide a one-sentence reason."""
    env["escalations"].append(reason)
    return "Escalation ticket created. A human agent will follow up within one business day."


@tool
def search_faq(question: str) -> str:
    """Answer general questions about shipping, returns, warranty, or support hours from the store FAQ."""
    q = question.lower()
    for topic, answer in FAQ.items():
        if topic in q:
            return answer
    return "No FAQ entry matched. Topics available: " + ", ".join(FAQ)


TOOLS = [look_up_order, check_return_eligibility, issue_refund, escalate_to_human, search_faq]

