"""Builds the LangGraph agent by connecting guardrails, model, tools and nodes."""

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langgraph.graph import END, START, StateGraph

from src.agent.nodes import (
    AgentState,
    agent_node,
    input_guardrail_node,
    output_guardrail_node,
    route_after_agent,
    route_after_input,
    tool_node,
)

# Max graph steps per question (protects against endless tool loops).
RECURSION_LIMIT = 15


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("input_guardrail", input_guardrail_node)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_node("output_guardrail", output_guardrail_node)

    graph.add_edge(START, "input_guardrail")
    graph.add_conditional_edges(
        "input_guardrail", route_after_input, {"blocked": END, "agent": "agent"}
    )
    graph.add_conditional_edges(
        "agent", route_after_agent, {"tools": "tools", "output_guardrail": "output_guardrail"}
    )
    graph.add_edge("tools", "agent")
    graph.add_edge("output_guardrail", END)

    return graph.compile()


agent_graph = build_graph()


def to_langchain_messages(history: list[dict]) -> list[AnyMessage]:
    """Convert stored chat messages ({role, content}) into LangChain messages."""
    converted: list[AnyMessage] = []
    for m in history:
        if m["role"] == "user":
            converted.append(HumanMessage(m["content"]))
        elif m["role"] == "assistant":
            converted.append(AIMessage(m["content"]))
    return converted


async def run_agent(question: str, history: list[dict] | None = None) -> str:
    """Answer `question` using previous chat `history` as context."""
    messages = to_langchain_messages(history or []) + [HumanMessage(question)]
    result = await agent_graph.ainvoke(
        {"messages": messages, "blocked": False, "final_answer": ""},
        config={"recursion_limit": RECURSION_LIMIT},
    )
    return result["final_answer"]
