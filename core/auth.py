import streamlit as st
from supabase import create_client

def get_auth_client():
"""Create a Supabase client using the publishable key."""
try:
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
return create_client(url, key)
except Exception as exc:
raise RuntimeError(
"Supabase is not configured. Check SUPABASE_URL and SUPABASE_KEY "
"in Streamlit Secrets."
) from exc

def init_auth_state():
"""Initialize authentication-related session state."""
defaults = {
"auth_user": None,
"auth_access_token": None,
"auth_refresh_token": None,
}

```
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value
```

def get_authenticated_client():
"""Return a client authenticated as the current user."""
init_auth_state()

```
access_token = st.session_state.auth_access_token
refresh_token = st.session_state.auth_refresh_token

if not access_token or not refresh_token:
    return None

client = get_auth_client()

try:
    client.auth.set_session(access_token, refresh_token)
    user_response = client.auth.get_user()

    user = getattr(user_response, "user", None)
    if not user:
        return None

    st.session_state.auth_user = {
        "id": str(user.id),
        "email": user.email,
    }

    session = client.auth.get_session()
    if session:
        st.session_state.auth_access_token = session.access_token
        st.session_state.auth_refresh_token = session.refresh_token

    client.postgrest.auth(st.session_state.auth_access_token)
    return client

except Exception:
    st.session_state.auth_user = None
    st.session_state.auth_access_token = None
    st.session_state.auth_refresh_token = None
    return None
```

def show_auth_page():
"""Display login and registration forms."""
init_auth_state()

```
st.title("🤖 AgentForge AI")
st.subheader("Your AI workspace starts here")
st.write("Sign in or create an account to access your workspace.")

try:
    client = get_auth_client()
except Exception as exc:
    st.error(str(exc))
    st.stop()

login_tab, signup_tab = st.tabs(["Log In", "Create Account"])

with login_tab:
    with st.form("agentforge_login"):
        email = st.text_input("Email address", key="login_email")
        password = st.text_input(
            "Password",
            type="password",
            key="login_password",
        )
        login_clicked = st.form_submit_button(
            "Log In",
            type="primary",
            use_container_width=True,
        )

    if login_clicked:
        if not email.strip() or not password:
            st.error("Enter your email address and password.")
        else:
            try:
                response = client.auth.sign_in_with_password(
                    {
                        "email": email.strip(),
                        "password": password,
                    }
                )

                session = response.session
                user = response.user

                if session and user:
                    st.session_state.auth_user = {
                        "id": str(user.id),
                        "email": user.email,
                    }
                    st.session_state.auth_access_token = session.access_token
                    st.session_state.auth_refresh_token = session.refresh_token
                    st.session_state.session_id = str(user.id)
                    st.session_state.task_history = []
                    st.session_state.active_task = None
                    st.session_state.navigation = "Dashboard"

                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error(
                        "No active session was returned. If email verification "
                        "is enabled, verify your email before logging in."
                    )

            except Exception:
                st.error(
                    "Login failed. Check your credentials and confirm your "
                    "email address if verification is required."
                )

with signup_tab:
    with st.form("agentforge_signup"):
        new_email = st.text_input("Email address", key="signup_email")
        new_password = st.text_input(
            "Password",
            type="password",
            key="signup_password",
        )
        confirm_password = st.text_input(
            "Confirm password",
            type="password",
            key="signup_confirm_password",
        )

        signup_clicked = st.form_submit_button(
            "Create Account",
            type="primary",
            use_container_width=True,
        )

    if signup_clicked:
        if not new_email.strip():
            st.error("Enter your email address.")
        elif len(new_password) < 8:
            st.error("Use a password with at least 8 characters.")
        elif new_password != confirm_password:
            st.error("The passwords do not match.")
        else:
            try:
                response = client.auth.sign_up(
                    {
                        "email": new_email.strip(),
                        "password": new_password,
                    }
                )

                if response.session and response.user:
                    st.session_state.auth_user = {
                        "id": str(response.user.id),
                        "email": response.user.email,
                    }
                    st.session_state.auth_access_token = (
                        response.session.access_token
                    )
                    st.session_state.auth_refresh_token = (
                        response.session.refresh_token
                    )
                    st.session_state.session_id = str(response.user.id)
                    st.session_state.task_history = []
                    st.session_state.active_task = None
                    st.session_state.navigation = "Dashboard"

                    st.success("Account created successfully!")
                    st.rerun()
                else:
                    st.success(
                        "Registration received. Check your email for the "
                        "verification link, then return here to log in."
                    )

            except Exception:
                st.error(
                    "Account creation failed. Check the email address, "
                    "password requirements, and Supabase Auth settings."
                )
```
