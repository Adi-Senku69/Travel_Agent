import streamlit as st
import datetime

# Page Configuration
st.set_page_config(page_title="TravelBuddy", layout="wide")

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "conversations" not in st.session_state:
    st.session_state["conversations"] = []

# Sidebar
with st.sidebar:
    st.markdown("# ✈️ TravelBuddy")
    if st.button("+ New Chat", use_container_width=True):
        # Save current chat to conversations if not empty
        if st.session_state["messages"]:
            timestamp = datetime.datetime.now().strftime("%b %d, %Y %H:%M")
            st.session_state["conversations"].insert(0, {"title": f"Chat {timestamp}",
                                                         "messages": st.session_state["messages"]})

        # Clear chat history for a new conversation
        st.session_state["messages"] = []

    st.markdown("### Conversations")
    for i, conv in enumerate(st.session_state["conversations"]):
        if st.button(conv["title"], key=f"conv_{i}", use_container_width=True):
            st.session_state["messages"] = conv["messages"]

    st.markdown("---")
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image("https://via.placeholder.com/40", width=40)
    with col2:
        st.markdown("**Sarah Johnson**\nMarketing Director")
    st.button("Logout", use_container_width=True)

# Main Chat Interface
st.title("💬 TravelBuddy AI Chat")
st.markdown("---")

# Default message for a new chat
if not st.session_state["messages"]:
    st.session_state["messages"].append({"role": "assistant",
                                         "content": "Hello! I'm TravelBuddy, your AI travel assistant. How can I help you plan your next business trip?"})

# Display chat messages
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if user_input := st.chat_input("Type your message here..."):
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Simulate a bot response
    bot_response = f"I'm here to help with your trip! You said: {user_input}"
    st.session_state["messages"].append({"role": "assistant", "content": bot_response})
    with st.chat_message("assistant"):
        st.markdown(bot_response)
