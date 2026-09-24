"""Husky Tech support agent — assembly and command-line chat.

Transfer target for W03b.1 sections 4 and 8. Run from the project folder:

    python -m agent.agent
"""

from dotenv import load_dotenv

load_dotenv()

from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver

from .prompts import SYSTEM_PROMPT
from .tools import TOOLS

model = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

# TODO: paste the create_agent(...) call from section 4 here.
# Name the result `support_agent` and keep the checkpointer.
support_agent = ...


def ask(text: str, thread: str) -> dict:
    config = {"configurable": {"thread_id": thread}}
    return support_agent.invoke({"messages": [HumanMessage(content=text)]}, config)


if __name__ == "__main__":
    from .records import file_ticket

    print("Husky Tech support. Type 'quit' to end the conversation.")
    result = None
    while True:
        user = input("You: ")
        if user.lower() in {"quit", "exit"}:
            break
        result = ask(user, "cli-demo")
        print("Agent:", result["messages"][-1].text)
    if result is not None:
        record = file_ticket(model, result)
        print("\nFiled ticket:", record)
