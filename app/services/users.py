from uuid import uuid4

users: dict[str, dict] = {}


def register_user(user_name: str, password: str) -> dict:
    user_id = str(uuid4())
    token = str(uuid4())
    users[token] = {
        "userId": user_id,
        "userName": user_name,
        "password": password,
    }
    return {"userId": user_id, "userName": user_name, "token": token}


def get_user_by_token(token: str) -> dict | None:
    return users.get(token)
