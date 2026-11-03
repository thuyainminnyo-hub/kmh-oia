from airflow.sql.hooks.sql import DbApiHook, free_fn, get_build_status


class PrestoHook(DbApiHook):
    def get_records(self, sql):
        free_fn()
        return self.strip_sql_string(sql)

    def get_build_status(self, branch):
        return get_build_status(None, branch)
