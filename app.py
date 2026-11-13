import streamlit as st
from agent import get_gemini_response

st.set_page_config(
    page_title="Shopping Assist AI",
    page_icon="🛍️",
    layout="centered"
)

st.title("Shopping Assist AI")
st.subheader("Your personal AI shopping assistant")

st.write(
    "Describe what you need, your budget, and preferred specifications. "
    "Our AI will help you find suitable products."
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display previous conversation.
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_query = st.chat_input(
    "Example: Find a laptop under ₹60,000 with 16GB RAM"
)

if user_query:

    # Keep a copy of previous messages before adding the new question.
    previous_history = st.session_state.chat_history.copy()

    # Display the new user message.
    with st.chat_message("user"):
        st.markdown(user_query)

    st.session_state.chat_history.append(
        {"role": "user", "content": user_query}
    )

    # Send both the new question and previous conversation to Gemini.
    with st.chat_message("assistant"):
        with st.spinner("Searching products and preparing recommendations..."):

            response = get_gemini_response(
                user_query,
                conversation_history=previous_history
            )

            st.markdown(response)

    st.session_state.chat_history.append(
        {"role": "assistant", "content": response}
    )

if st.button("Clear conversation"):
    st.session_state.chat_history = []
    st.rerun()