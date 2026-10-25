"""Husky Tech support agent — data and tools.

Transfer target for W03b.1 sections 1 and 2.
"""

from datetime import datetime, date

from langchain.tools import tool

# ---- section 1: the scenario and the data -----------------------------------

# TODO: paste the data cell from section 1 here
# (ORDERS, RETURN_POLICY_DAYS, FAQ — and ESCALATIONS from section 2's escalation tool cell)
ORDERS = {
    "HT-1001": {"item": "Wireless headphones", "status": "delivered", "delivered_on": "2026-09-05", "price": 79.99},
    "HT-1002": {"item": "Mechanical keyboard",  "status": "shipped",   "ordered_on": "2026-09-15", "eta": "2026-09-23", "price": 129.00},
    "HT-1003": {"item": "USB-C dock",           "status": "processing","ordered_on": "2026-09-18", "price": 59.50},
}

RETURN_POLICY_DAYS = 30

FAQ = {
    "shipping": "Standard shipping takes 3-5 business days. Orders over $50 ship free.",
    "return":   "Items can be returned within 30 days of delivery for a full refund.",
    "warranty": "All electronics include a one-year manufacturer warranty.",
    "hours":    "Support is available Monday through Friday, 9am to 6pm ET.",
}

ESCALATIONS = {}


# ---- section 2: the tools ----------------------------------------------------

# TODO: paste the four tool definitions from section 2 here, in order:
#   look_up_order, check_return_eligibility, search_faq, escalate_to_human

@tool
def look_up_order(order_id: str) -> str:
    """Look up an order by its id (e.g. HT-1001) and return its current details."""
    order = ORDERS.get(order_id.upper())

    if order is None:
        return f"No order found with this order ID {order_id}. Ask the customer to double check the order ID."

    return str(order)


@tool
def check_return_eligibility(order_id: str) -> str:
    """Check whether an order can still be returned under the 30-day policy. Takes the order id."""
    
    order = ORDERS.get(order_id.upper())
    
    if order is None:
        return f"No order found with id {order_id}."
    if order["status"] != "delivered":
        return f"Order {order_id} has not been delivered yet, so the return window has not started."
    
    delivered = datetime.strptime(order["delivered_on"], "%Y-%m-%d").date()
    days = (date.today() - delivered).days
    
    if days <= RETURN_POLICY_DAYS:
        return f"Eligible: delivered {days} days ago; returns are accepted within {RETURN_POLICY_DAYS} days of delivery."
    return f"Not eligible: delivered {days} days ago, which is past the {RETURN_POLICY_DAYS}-day window."


@tool
def search_faq(question: str) -> str:
    """Answer general questions about shipping, returns, warranty, or support hours from the store FAQ."""
    
    q = question.lower()
    
    for topic, answer in FAQ.items():
        if topic in q:
            return answer
    return "No FAQ entry matched. Topics available: " + ", ".join(FAQ.keys())

@tool
def escalate_to_human(reason: str) -> str:
    """Escalate the conversation to a human support agent. Use when the customer is upset, asks for a person, or the available tools cannot resolve the issue. Provide a one-sentence reason."""
    ticket_id = f"ESC-{1001 + len(ESCALATIONS)}"
    ESCALATIONS[ticket_id] = {"reason": reason, "status": "waiting for a human"}
    return f"Escalation ticket {ticket_id} created. Reason: {reason.rstrip('.')}. A human agent will follow up within one business day."

# When everything above is in place, uncomment:
TOOLS = [look_up_order, check_return_eligibility, search_faq, escalate_to_human]
