from flask_jwt_extended import create_access_token, get_jwt_identity


def create_access_token_for_user(user):
    """
    Generate a JWT access token for a user.

    We store the user id as the token identity and include role/email as claims.
    """
    return create_access_token(
        identity=str(user.user_id),
        additional_claims={
            "role": user.role,
            "email": user.email,
        },
    )


def current_user_id():
    """Helper to get the current user id from the JWT."""
    return get_jwt_identity()
