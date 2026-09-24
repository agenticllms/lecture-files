"""Husky Tech support agent — data and tools.

Transfer target for W03b.1 sections 1 and 2.
"""

from datetime import datetime, date

from langchain.tools import tool

# ---- section 1: the scenario and the data -----------------------------------

# TODO: paste the data cell from section 1 here
# (ORDERS, RETURN_POLICY_DAYS, FAQ — and ESCALATIONS from section 2's escalation tool cell)


# ---- section 2: the tools ----------------------------------------------------

# TODO: paste the four tool definitions from section 2 here, in order:
#   look_up_order, check_return_eligibility, search_faq, escalate_to_human


# When everything above is in place, uncomment:
# TOOLS = [look_up_order, check_return_eligibility, search_faq, escalate_to_human]
