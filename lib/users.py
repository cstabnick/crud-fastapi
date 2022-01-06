from lib.util import ITUtil

class ITUsers:
    @staticmethod
    def update_session(user_id: int):
        return ITUtil.pg_select_one("select update_session(%(user_id)s) as session_id", {"user_id": user_id}, True)
