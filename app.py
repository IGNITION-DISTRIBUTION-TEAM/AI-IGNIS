import os
import streamlit as st
from snowflake.snowpark import Session

# -----------------------------
# 1️⃣ Snowflake Connection
# -----------------------------
def create_snowflake_session():
    connection_parameters = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),  # or use PASSWORD
        "role": os.getenv("SNOWFLAKE_ROLE"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "database": os.getenv("SNOWFLAKE_DATABASE"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA")
    }
    session = Session.builder.configs(connection_parameters).create()
    return session

session = create_snowflake_session()

# -----------------------------
# 2️⃣ Function to call agent
# -----------------------------
AGENT_NAME = os.getenv("SNOWFLAKE_AGENT_NAME", "AGENT_CHATBOT")

def ask_agent(prompt):
    query = """
    CALL CX_SALES.COMPLETE_WITH_PROMPT(PROMPT => ?)
    """
    # Pass parameters as a list
    result = session.sql(query, [prompt]).collect()
    return result[0][0]  # Adjust if agent returns JSON

# -----------------------------
# 3️⃣ Streamlit Chat UI
# -----------------------------
st.set_page_config(page_title="Snowflake Chatbot")
st.title("💬 Snowflake AI Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

# User input
user_input = st.text_input("You:", "")

if st.button("Send") and user_input:
    try:
        response = ask_agent(user_input)
    except Exception as e:
        response = f"Error: {str(e)}"
    
    st.session_state.messages.append({"user": user_input, "bot": response})

# Display chat messages
for chat in st.session_state.messages:
    st.markdown(f"**You:** {chat['user']}")
    st.markdown(f"**Bot:** {chat['bot']}")
