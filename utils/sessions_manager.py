session_data_store = {}

def get_session_level(session_id):
    return session_data_store.get(session_id, {}).get("level", 0)

def update_session_level(session_id, level, extra_data=None):
    if session_id not in session_data_store:
        session_data_store[session_id] = {}
    session_data_store[session_id]["level"] = level
    if extra_data:
        session_data_store[session_id].update(extra_data)
    return session_data_store[session_id]
