import streamlit as st

def check_authorization():
    if "user" not in st.session_state:
        with st.sidebar:
            st.write("### Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.button("Login"):
                if username == "admin" and password == "password":  # Replace with real auth
                    st.session_state.user = username
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        return False
    return True