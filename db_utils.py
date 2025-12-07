"""
Database utilities and context managers
"""
from contextlib import contextmanager
from flask import current_app


@contextmanager
def get_db_connection(db_pool):
    """
    Context manager for database connections.
    
    Usage:
        with get_db_connection(db_pool) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ...")
            cursor.close()
    """
    conn = db_pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Database error: {str(e)}", exc_info=True)
        raise
    finally:
        db_pool.putconn(conn)


@contextmanager
def get_db_cursor(db_pool):
    """
    Context manager for database cursor.
    
    Usage:
        with get_db_cursor(db_pool) as cursor:
            cursor.execute("SELECT ...")
            results = cursor.fetchall()
    """
    conn = db_pool.getconn()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        current_app.logger.error(f"Database error: {str(e)}", exc_info=True)
        raise
    finally:
        cursor.close()
        db_pool.putconn(conn)
