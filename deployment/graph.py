from nodes import *
from tools import tools_node
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.prebuilt import tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore



graph_summarizer_builder = StateGraph(SummaryGraphInput, output=SummaryGraphOutput)

graph_summarizer_builder.add_node("read documents", read_docs)
graph_summarizer_builder.add_node("summarize documents", summarize)

graph_summarizer_builder.add_edge(START, "read documents")
graph_summarizer_builder.add_edge("read documents", "summarize documents")
graph_summarizer_builder.add_edge("summarize documents", END)

graph_summarizer = graph_summarizer_builder.compile()


graph_chatbot_builder = StateGraph(TravelAgent)

graph_chatbot_builder.add_node("read profile", read_profile)
graph_chatbot_builder.add_node("summary graph", graph_summarizer)
graph_chatbot_builder.add_node("add travellers", add_travellers)
graph_chatbot_builder.add_node("chatbot", chatbot)
graph_chatbot_builder.add_node("summarizer and updater", summarizer_and_updater)
graph_chatbot_builder.add_node("tools", tools_node)
graph_chatbot_builder.add_node("update profile", update_profile)

graph_chatbot_builder.add_conditional_edges(START, to_create_profile, ['summary graph', 'read profile', "add travellers"])
graph_chatbot_builder.add_edge("summary graph", "add travellers")
graph_chatbot_builder.add_edge("add travellers", "read profile")
graph_chatbot_builder.add_conditional_edges("read profile", check_profiles, ["chatbot", END])
graph_chatbot_builder.add_conditional_edges("chatbot", route_ai, ["summarizer and updater", END])
graph_chatbot_builder.add_conditional_edges("chatbot", tools_condition)
graph_chatbot_builder.add_conditional_edges("chatbot", route_to_update, ["update profile", END])
graph_chatbot_builder.add_edge("tools", "chatbot")
graph_chatbot_builder.add_edge("summarizer and updater", END)
graph_chatbot_builder.add_edge("update profile", END)

memory = MemorySaver()
store = InMemoryStore()
graph_chatbot = graph_chatbot_builder.compile(checkpointer=memory, store=store, debug=False)