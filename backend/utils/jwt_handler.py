from flask_jwt_extended import create_access_token, get_jwt_identity


def create_access_token_for_user(user):
    return create_access_token(
        identity=str(user.id),
        additional_claims={
            "role": user.role,
            "email": user.email,
        },
    )


def current_user_id():
    return get_jwt_identity()
