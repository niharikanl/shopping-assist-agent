import streamlit as st
from agent import get_gemini_response

st.set_page_config(
    page_title="Shopping Assistant Agent",
    page_icon="🛍️",
    layout="centered"
)

# ---------------- DESIGN ----------------

st.markdown("""
<style>
.stApp {
    background: linear-gradient(
        135deg,
        #d9c7ff,
        #b8d8ff,
        #f5d5ff
    );
}

h1 {
    color: #35205f;
    text-align: center;
    font-weight: 800;
}

h2, h3 {
    color: #432878;
}

p, label {
    color: #292044;
    font-weight: 500;
}

.stButton > button {
    background: linear-gradient(90deg, #7041c5, #3978d5);
    color: white;
    border-radius: 12px;
    border: none;
    padding: 10px 22px;
    font-weight: bold;
}

.stButton > button:hover {
    background: #39216d;
    color: white;
    border: none;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,0.65);
    border-radius: 15px;
    padding: 12px;
}
</style>
""", unsafe_allow_html=True)


# ---------------- SESSION MEMORY ----------------

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_response" not in st.session_state:
    st.session_state.last_response = ""


# ---------------- MAIN PAGE ----------------

st.title("🛍️ Shopping Assistant Agent")

st.write(
    "Find suitable products, compare specifications "
    "and get AI-powered recommendations."
)

with st.form("product_search_form"):

    product = st.text_input(
        "What product are you looking for?",
        placeholder="Example: Laptop"
    )

    budget = st.number_input(
        "Enter your budget (₹)",
        min_value=0,
        value=60000,
        step=1000
    )

    question = st.text_input(
        "Additional requirements or questions",
        placeholder="Example: I need 16GB RAM for programming"
    )

    search_clicked = st.form_submit_button("Search Products")

if search_clicked:

    if not product.strip():
        st.warning("Please enter a product name.")

    else:
        user_query = (
            f"Find {product} under ₹{budget}. "
            f"Additional requirements: {question}"
        )

        previous_history = st.session_state.chat_history.copy()

        st.session_state.chat_history.append({
            "role": "user",
            "content": user_query
        })

        with st.spinner("AI is searching the catalogue..."):

            response = get_gemini_response(
                user_query,
                conversation_history=previous_history
            )

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response
        })

        st.session_state.last_response = response


# ---------------- DISPLAY CONVERSATION ----------------

st.divider()
st.subheader("AI Shopping Recommendations")

for message in st.session_state.chat_history:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ---------------- FOLLOW-UP QUESTIONS ----------------

st.subheader("Ask a Follow-up Question")

follow_up = st.text_input(
    "Ask about the recommended products",
    placeholder="Example: Which one is better for programming?"
)

if st.button("Ask AI"):

    if not follow_up.strip():
        st.warning("Please enter your question.")

    else:
        previous_history = st.session_state.chat_history.copy()

        st.session_state.chat_history.append({
            "role": "user",
            "content": follow_up
        })

        with st.spinner("Preparing your answer..."):

            response = get_gemini_response(
                follow_up,
                conversation_history=previous_history
            )

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response
        })

        st.rerun()


# ---------------- ADDITIONAL FEATURES ----------------

st.divider()
st.header("🛍️ Shopping Assistance Features")

tab1, tab2, tab3 = st.tabs([
    "Compatibility Check",
    "Size & Fit",
    "Nearby Stock"
])

with tab1:

    st.subheader("Device Compatibility")

    device = st.text_input(
        "Enter your device model",
        placeholder="Example: HP Laptop"
    )

    if st.button("Check Compatibility"):

        if device.strip():

            query = (
                f"Based only on available catalogue information, "
                f"explain whether the selected product is compatible "
                f"with {device}. Do not invent compatibility details."
            )

            history = st.session_state.chat_history.copy()

            with st.spinner("Checking available information..."):
                answer = get_gemini_response(
                    query,
                    conversation_history=history
                )

            st.markdown(answer)

        else:
            st.warning("Please enter your device model.")


with tab2:

    st.subheader("Size & Fit Assistant")

    st.info(
        "Size and fit recommendations are a planned feature. "
        "The current product catalogue does not contain verified "
        "body measurements or fit data."
    )


with tab3:

    st.subheader("Nearby Store Availability")

    location = st.text_input(
        "Enter your location",
        placeholder="Example: Mangaluru"
    )

    st.info(
        "Live nearby-store inventory is not connected yet. "
        "The current catalogue does not provide location-based stock data."
    )


# ---------------- CLEAR CHAT ----------------

if st.button("Clear Conversation"):

    st.session_state.chat_history = []
    st.session_state.last_response = ""

    st.rerun()