"""Husky Tech support agent — the ticket record.

Transfer target for W03b.1 section 7, with one change you must make:
file_ticket takes the model as an ARGUMENT instead of reaching for a
notebook global. Files have no globals to lean on; dependencies are passed in.
"""

from typing import Literal

from pydantic import BaseModel, Field

# TODO: paste the TicketRecord class from section 7 here


TICKETS = []


def file_ticket(model, result):
    """Extract a structured record from a finished conversation and save it."""
    # TODO: paste the body of file_ticket from section 7 here.
    # It already works unchanged — model now arrives as the parameter above.
    pass
