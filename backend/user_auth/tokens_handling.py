"""
JWT Authentication Utilities Module

This module provides decorators and helper functions to handle JSON Web Token (JWT)
based authentication in a Flask application.

Functions:
----------
- token_required(f):
    A decorator that protects Flask routes by requiring a valid JWT bearer token
    in the Authorization header. It verifies the token, checks expiration, and
    extracts the current user identity for use in the route.

- generate_token(username):
    Generates a JWT token encoding the specified username as the subject (`sub`),
    along with issued-at and expiration claims, using the application's secret key
    and configured expiration time.

Usage:
------
Apply the `@token_required` decorator to routes that require authenticated access.
Call `generate_token` to create tokens for authenticated users during login.
"""

from datetime import datetime, timedelta
from functools import wraps
import jwt
from flask import request, jsonify, current_app as app
def token_required(f):
    """
    Decorator to enforce JWT token authentication on Flask route handlers.

    This decorator extracts the JWT token from the Authorization header,
    validates it using the application's secret key, and verifies expiration.
    If the token is valid, the decorated function is called with the current
    user's identity (from the token 'sub' claim) as the first argument.

    Returns:
        401 Unauthorized JSON response if the token is missing, expired,
        invalid, or verification fails.

    Args:
        f (function): The Flask route handler function to decorate.

    Returns:
        function: The decorated function that requires a valid JWT token.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', None)
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]

        if not token:
            return jsonify({'error': 'Authorization token is missing'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['sub']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            return jsonify({'error': f'Token verification failed: {str(e)}'}), 401
        return f(current_user, *args, **kwargs)

    return decorated


def generate_token(username):
    """
    Generate a JWT token for a given username with issued-at and expiration claims.

    The token payload includes:
        - 'sub': Subject claim set to the username.
        - 'iat': Issued at timestamp (current UTC time).
        - 'exp': Expiration timestamp (current UTC time + configured duration).

    The token is signed using the application's SECRET_KEY with HS256 algorithm.

    Args:
        username (str): The username to encode in the token's subject.

    Returns:
        str: The encoded JWT token as a string.
    """
    token = jwt.encode({
        'sub': username,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(seconds=app.config['JWT_EXPIRATION'])
    }, app.config['SECRET_KEY'], algorithm='HS256')
    return token
