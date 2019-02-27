import pymysql


class Sql:

    def __init__(self, database, host, port, user, password):
        self._client = pymysql.Connect(host=host, port=port, user=user, password=password, database=database)

    def close_connect(self):
        self._client.close()

    def update_or_insert_sql(self, sql_text: str) -> None:
        cursor = self._client.cursor()
        cursor.execute(sql_text)
        self._client.commit()
        cursor.close()
