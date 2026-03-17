from typing import Tuple

import mysql.connector
from mysql.connector import Error

from app.config import settings


def probe_mysql() -> Tuple[bool, str | None]:
    try:
        connection = mysql.connector.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name,
        )
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        connection.close()
        return True, None
    except Error as error:
        return False, str(error)
