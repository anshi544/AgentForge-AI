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
            "Supabase configuration is missing. Check your Streamlit Secrets."
        ) from exc


def init_auth_state():
    """Initialize authentication session state."""
    defaults = {
        "auth_user": None,
        "auth_access_token": None,
        "auth_refresh_token": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_auth_state():
    """Clear local authentication state."""
    st.session_state.auth_user = None
    st.session_state.auth_access_token = None
    st.session_state.auth_refresh_token = None
    st.session_state.task_history = []
    st.session_state.active_task = None


def set_authenticated_session(response):
    """Store the session returned by Supabase Auth."""
    session = getattr(response, "session", None)
    user = getattr(response, "user", None)

    if not session or not user:
        return False

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

    return True


def get_authenticated_client():
    """Restore the authenticated session and return its client."""
    init_auth_state()

    access_token = st.session_state.auth_access_token
    refresh_token = st.session_state.auth_refresh_token

    if not access_token or not refresh_token:
        return None

    client = get_auth_client()

    try:
        client.auth.set_session(access_token, refresh_token)

        # Verify the session against Supabase Auth.
        response = client.auth.get_user()
        user = getattr(response, "user", None)

        if user is None:
            clear_auth_state()
            return None

        session = client.auth.get_session()

        if session is None:
            clear_auth_state()
            return None

        # Preserve refreshed tokens if the SDK refreshed the session.
        st.session_state.auth_access_token = session.access_token
        st.session_state.auth_refresh_token = session.refresh_token

        st.session_state.auth_user = {
            "id": str(user.id),
            "email": user.email,
        }

        # Ensure PostgREST database requests use the user's JWT.
        client.postgrest.auth(session.access_token)

        return client

    except Exception:
        clear_auth_state()
        return None


def logout():
    """Sign out and clear the local session."""
    init_auth_state()

    try:
        client = get_authenticated_client()

        if client is not None:
            client.auth.sign_out()

    except Exception:
        pass

    finally:
        clear_auth_state()


def show_auth_page():
    """Display login, registration, and password recovery forms."""

    init_auth_state()

    st.title("🤖 AgentForge AI")
    st.subheader("Your AI workspace starts here")

    st.write(
        "Sign in, create an account, or recover your password."
    )

    try:
        client = get_auth_client()

    except Exception as exc:
        st.error(str(exc))
        st.stop()

    # --------------------------------------------------
    # PASSWORD RECOVERY LINK HANDLING
    # --------------------------------------------------

    query_params = st.query_params

    token_hash = query_params.get("token_hash")
    recovery_type = query_params.get("type")

    if token_hash and recovery_type == "recovery":

        st.subheader("🔐 Reset Your Password")

        if "recovery_verified" not in st.session_state:
            st.session_state.recovery_verified = False

        if not st.session_state.recovery_verified:

            try:
                response = client.auth.verify_otp({
                    "token_hash": token_hash,
                    "type": "recovery",
                })

                if set_authenticated_session(response):
                    st.session_state.recovery_verified = True
                    st.rerun()

                else:
                    st.error(
                        "Password recovery link could not be verified. "
                        "Please request a new link."
                    )
                    st.stop()

            except Exception as exc:
                st.error(
                    f"Password recovery verification failed: "
                    f"{type(exc).__name__}: {exc}"
                )
                st.stop()

        # New password form
        with st.form("reset_password_form"):

            new_password = st.text_input(
                "New Password",
                type="password",
            )

            confirm_password = st.text_input(
                "Confirm New Password",
                type="password",
            )

            reset_clicked = st.form_submit_button(
                "Update Password",
                type="primary",
                use_container_width=True,
            )

        if reset_clicked:

            if len(new_password) < 8:
                st.error(
                    "Password must contain at least 8 characters."
                )

            elif new_password != confirm_password:
                st.error("Passwords do not match.")

            else:
                try:
                    client.auth.update_user({
                        "password": new_password
                    })

                    st.session_state.recovery_verified = False

                    clear_auth_state()
                    st.query_params.clear()

                    st.success(
                        "Password updated successfully! "
                        "Please log in using your new password."
                    )

                    st.rerun()

                except Exception as exc:
                    st.error(
                        f"Unable to update password: "
                        f"{type(exc).__name__}: {exc}"
                    )

        st.stop()

    # --------------------------------------------------
    # AUTHENTICATION TABS
    # --------------------------------------------------

    login_tab, signup_tab, forgot_tab = st.tabs([
        "Log In",
        "Create Account",
        "Forgot Password?",
    ])

    # --------------------------------------------------
    # LOGIN
    # --------------------------------------------------

    with login_tab:

        with st.form("agentforge_login"):

            email = st.text_input(
                "Email address",
                key="login_email",
            )

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
                st.error(
                    "Enter your email address and password."
                )

            else:
                try:
                    response = client.auth.sign_in_with_password({
                        "email": email.strip(),
                        "password": password,
                    })

                    if set_authenticated_session(response):
                        st.success("Login successful!")
                        st.rerun()

                    else:
                        st.error(
                            "No authenticated session was returned. "
                            "Verify your email address and try again."
                        )

                except Exception:
                    st.error(
                        "Login failed. Check your credentials and "
                        "ensure your email address has been verified."
                    )

    # --------------------------------------------------
    # SIGNUP
    # --------------------------------------------------

    with signup_tab:

        with st.form("agentforge_signup"):

            new_email = st.text_input(
                "Email address",
                key="signup_email",
            )

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
                st.error(
                    "Use a password with at least 8 characters."
                )

            elif new_password != confirm_password:
                st.error("The passwords do not match.")

            else:
                try:
                    response = client.auth.sign_up({
                        "email": new_email.strip(),
                        "password": new_password,
                    })

                    if set_authenticated_session(response):
                        st.success("Account created successfully!")
                        st.rerun()

                    else:
                        st.success(
                            "Registration submitted! Check your inbox "
                            "for the Supabase verification email."
                        )

                except Exception:
                    st.error(
                        "Account creation failed. Check the email "
                        "address and password requirements."
                    )

    # --------------------------------------------------
    # FORGOT PASSWORD
    # --------------------------------------------------

    with forgot_tab:

        st.subheader("🔑 Recover Your Account")

        st.write(
            "Enter your registered email address. "
            "We will send you a password-reset link."
        )

        with st.form("agentforge_forgot_password"):

            recovery_email = st.text_input(
                "Registered Email Address",
                key="recovery_email",
            )

            recovery_clicked = st.form_submit_button(
                "Send Reset Link",
                type="primary",
                use_container_width=True,
            )

        if recovery_clicked:

            if not recovery_email.strip():
                st.error(
                    "Please enter your registered email address."
                )

            else:
                try:
                    client.auth.reset_password_for_email(
                        recovery_email.strip(),
                        {
                            "redirect_to": (
                                "https://agentforge-ai-lvsp6zbtpm3gcln8rcvmmy.streamlit.app/"
                            )
                        },
                    )

                    st.success(
                        "If an account exists for that email, "
                        "a password-reset link has been sent. "
                        "Please check your inbox and spam folder."
                    )

                except Exception as exc:
                    st.error(
                        f"Password reset failed: "
                        f"{type(exc).__name__}: {exc}"
                    )
