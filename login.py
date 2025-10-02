import streamlit as st
from db import get_JWT
from db import get_user_by_email, set_user_password
import snowflake.connector

def check_user(email, password=None, new_password=None):
    row = get_user_by_email(email)
    if not row:
        return "not_found", None
    db_email, db_password, db_role = row
    if not db_password:
        if new_password:
            set_user_password(email, new_password)
            return "password_set", db_role
        else:
            return "no_password", None
    if password and password == db_password:
        return "success", db_role
    else:
        return "wrong_password", None

st.set_page_config(page_title="Login", layout="wide")

st.markdown("""
    <style>
        /* Hide Streamlit sidebar completely */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        [data-testid="collapsedControl"] {display: none;}
        [data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([2,2,2], vertical_alignment="center")

with col2:
    with st.container(horizontal_alignment="center", vertical_alignment="center"):
        st.write("")

        st.image("logo.jpg", width=120)

        st.markdown("""
        <h2 style="
            text-align: center;
            background: linear-gradient(to right, #007BFF, #00FFFF);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
        ">
        Login to IGNIS
        </h2>
        """, unsafe_allow_html=True)

        email = st.text_input("User")
        password = st.text_input("Password", type="password")

        if st.button("Login", width="stretch"):
            status, role = check_user(email, password=password)
            if status == "not_found":
                st.error("User not found.")
            elif status == "no_password":
                st.session_state.email = email
                st.session_state.page = "set_password"
                st.info("First-time login. Please set a password below.")
            elif status == "success":
                st.session_state.userpass = "success"
                st.session_state.email = email
                st.session_state.role = role
                st.switch_page("pages/app.py")
            elif status == "wrong_password":
                st.error("Incorrect password.")
        
        #if st.session_state.get("page") == "set_password":
         #   new_password = st.text_input("New Password", type="password")
          #  if st.button("Set Password"):
          #      status, role = check_user(st.session_state.email, new_password=new_password)
          #      if status == "password_set":
          #          st.success("Password set successfully. Please log in again.")
          #          st.session_state.page = "login"


        if st.session_state.get("page") == "set_password":
            new_password = st.text_input("New Password", type="password")
        
            # Create a state flag for the button
            if "login" not in st.session_state:
                st.session_state.set_password_clicked = False
        
            if not st.session_state.set_password_clicked:
                if st.button("Set Password"):
                    st.session_state.set_password_clicked = True  # hide button on next rerun
                    status, role = check_user(st.session_state.email, new_password=new_password)
                    if status == "password_set":
                        st.success("Password set successfully. Please log in again.")
                        st.session_state.page = "login"
