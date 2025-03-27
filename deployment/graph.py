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

builder = StateGraph(TravelGraphState)


builder.add_node("start", lambda state: state)
builder.add_node("fetch_flight_status", fetch_flight_status)
builder.add_node("fetch_hotel_availability", fetch_hotel_availability)
builder.add_node("fetch_booking_status", fetch_booking_status)
builder.add_node("fetch_weather_status", fetch_weather_status)

builder.add_node("memory_store", store_memory)

builder.set_entry_point("start")

builder.add_edge("start", "fetch_flight_status")
builder.add_edge("start", "fetch_hotel_availability")
builder.add_edge("start", "fetch_booking_status")
builder.add_edge("start", "fetch_weather_status")

builder.add_edge("fetch_flight_status", "memory_store")
builder.add_edge("fetch_hotel_availability", "memory_store")
builder.add_edge("fetch_booking_status", "memory_store")
builder.add_edge("fetch_weather_status", "memory_store")
builder.add_edge("memory_store", END)

graph_alert = builder.compile(store=store)