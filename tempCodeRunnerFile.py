
        if parent_cur is None and parent_conn is None:
            cur.close()
            conn.commit()
            conn.close()

        else:
            parent_conn.commit()

    # Some SQL error, could be bad login or something else