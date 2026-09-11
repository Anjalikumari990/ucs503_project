from flask import session


# Demo credentials for the prototype
DEMO_USERNAME = "anjali"
DEMO_PASSWORD = "password123"


def authenticate(username, password):
    """Check whether the supplied credentials are valid."""
    return username == DEMO_USERNAME and password == DEMO_PASSWORD


def create_session(username):
    """Store the authenticated user in the Flask session."""
    session["username"] = username
    session["authenticated"] = True


def logout():
    """Remove the authenticated user's session."""
    session.clear()


def is_authenticated():
    """Return True if a user currently has an authenticated session."""
    return session.get("authenticated", False)


def get_current_user():
    """Return the currently logged-in username."""
    return session.get("username")