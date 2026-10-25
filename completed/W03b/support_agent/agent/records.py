"""Husky Tech support agent — the ticket record.

Transfer target for W03b.1 section 7, with one change you must make:
file_ticket takes the model as an ARGUMENT instead of reaching for a
notebook global. Files have no globals to lean on; dependencies are passed in.
"""

from typing import Literal

from pydantic import BaseModel, Field

# TODO: paste the TicketRecord class from section 7 here
class TicketRecord(BaseModel):
    """A structured record of a finished support conversation."""
    order_id: str | None = Field(
        default=None,
        description="The order id discussed, e.g. HT-1001. Null if no order came up.")
    category: Literal["billing", "shipping", "returns", "general", "other"] = Field(
        description="What the conversation was about")
    resolved: bool = Field(description="Whether the customer's question was fully answered")
    summary: str = Field(description="One-sentence summary of the conversation")

TICKETS = []


def file_ticket(model, result):
    """Extract a structured record from a finished conversation and save it."""
    transcript = "\n".join(f"{type(m).__name__}: {m.text}" for m in result["messages"] if m.text)
    record = model.with_structured_output(TicketRecord).invoke(
        f"Create a ticket record for this support conversation:\n\n{transcript}")
    TICKETS.append(record)
    return record
