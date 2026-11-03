class DbApiHook:
    def strip_sql_string(self, sql):
        return sql.strip()


def free_fn():
    return "free"


def get_build_status(client, branch):
    return {"branch": branch}
