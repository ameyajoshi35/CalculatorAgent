import json
import os

import fastapi
import uvicorn
from sse_starlette.sse import EventSourceResponse
from llama_index.core.agent.workflow import AgentOutput, AgentStream, ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.core.workflow import Context
from llama_index.core.memory import ChatMemoryBuffer
# REMOVED: OpenAI import
# ADDED: Groq import
from llama_index.llms.groq import Groq

# CHANGED: Read from environment or prompt console verification for GROQ
print("---groq key status----:", "Set" if os.environ.get("GROQ_API_KEY") else "Missing")


def add(a: float, b: float) -> float:
    """Adds two numbers."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Subtracts two numbers."""
    return a - b


def multiply(a: float, b: float) -> float:
    """Multiplies two numbers."""
    return a * b


def divide(a: float, b: float) -> float:
    """Divides two numbers."""
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b


add_tool = FunctionTool.from_defaults(add)
subtract_tool = FunctionTool.from_defaults(subtract)
multiply_tool = FunctionTool.from_defaults(multiply)
divide_tool = FunctionTool.from_defaults(divide)


sessions: dict[int, Context] = {}


agent_app = fastapi.FastAPI()

# CHANGED: Swapped OpenAI with Groq using a fast tool-use model like llama3-70b
llm = Groq(model="llama-3.3-70b-versatile")

agent = ReActAgent(
    tools=[add_tool, subtract_tool, multiply_tool, divide_tool],
    llm=llm,
)


@agent_app.get("/ping")
async def ping():
    return {"ok": True}


@agent_app.get("/test")
async def test():
    import asyncio, requests
    def call():
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": "hello"}]},
            timeout=10,
        )
        return r.json()
    return await asyncio.to_thread(call)


@agent_app.post("/messages")
async def send_message(session_id: int, message: str):
    if session_id not in sessions:
        sessions[session_id] = Context(agent)
    handler = agent.run(message, ctx=sessions[session_id])

    async def event_stream():
        async for ev in handler.stream_events():
            print(f"EVENT: {type(ev).__name__} -> {ev}")
            if isinstance(ev, AgentStream):
                yield {"data": json.dumps({"delta": ev.delta})}
            if isinstance(ev, AgentOutput):
                yield {"data": json.dumps({"delta": "\n"})}
        await handler
        yield {"data": "[DONE]"}

    return EventSourceResponse(event_stream())


@agent_app.get("/messages")
async def get_messages(session_id: int):
    if session_id not in sessions:
        raise ValueError("Session not found.")
    ctx = sessions[session_id]

    memory: ChatMemoryBuffer = await ctx.store.get("memory", default=None)
    if memory is None:
        return {"messages": []}
    return {
        "messages": [
            {"role": msg.role, "content": msg.content}
            for msg in await memory.aget_all()
        ]
    }


def main():
    uvicorn.run(agent_app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
