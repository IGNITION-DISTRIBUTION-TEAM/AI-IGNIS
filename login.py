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

        #email = st.text_input("User")
        #password = st.text_input("Password", type="password")

        # --- Hide Streamlit default menu/footer ---
        hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
        """
        st.markdown(hide_streamlit_style, unsafe_allow_html=True)
        
        # --- Initialize page ---
        if "page" not in st.session_state:
            st.session_state.page = "login"
        
        # --- Page navigation helper ---
        def go_to(page_name):
            st.session_state.page = page_name
        
        # --- Login page ---
        if st.session_state.page == "login":
            st.title("Login")
            
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
        
            if st.button("Login", key="login_btn"):
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
                    go_to("app")  # Navigate to main app page
                elif status == "wrong_password":
                    st.error("Incorrect password.")
        
        # --- Set password page ---
        elif st.session_state.page == "set_password":
            st.title("Set Password")
        
            # Initialize flag
            if "password_set_done" not in st.session_state:
                st.session_state.password_set_done = False
        
            if not st.session_state.password_set_done:
                input_placeholder = st.empty()
                button_placeholder = st.empty()
        
                new_password = input_placeholder.text_input("New Password", type="password")
        
                if button_placeholder.button("Set Password"):
                    status, role = check_user(st.session_state.email, new_password=new_password)
                    if status == "password_set":
                        # Clear UI elements
                        input_placeholder.empty()
                        button_placeholder.empty()
                        # Show success
                        st.success("Password set successfully. Please log in again.")
                        st.session_state.password_set_done = True
                        go_to("login")  # Go back to login page
        
        # --- Main app page ---
        elif st.session_state.page == "app":
            st.title("Main App")
            st.write(f"Welcome, {st.session_state.email}!")
            st.write(f"Your role: {st.session_state.role}")
        
            if st.button("Logout"):
                st.session_state.page = "login"
                st.session_state.userpass = None
                st.session_state.email = None
                st.session_state.role = None
                st.experimental_rerun()

        
