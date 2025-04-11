# utils/auth.py

from flask import session, redirect, url_for

# Статичні дані для входу (можна зробити динамічними з БД)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def is_logged_in():
    return session.get("logged_in", False)

def require_login(func):
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper
