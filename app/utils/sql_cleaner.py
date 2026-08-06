import re


def clean_sql(sql):

    # Extract SQL from markdown block

    match = re.search(
        r"```sql(.*?)```",
        sql,
        re.DOTALL | re.IGNORECASE
    )

    if match:
        sql = match.group(1)


    else:
        # Remove explanation before SELECT

        select_index = sql.upper().find("SELECT")

        if select_index != -1:
            sql = sql[select_index:]


    return sql.strip()



if __name__ == "__main__":

    test = """
    Here is the query:

    ```sql
    SELECT * FROM users;
    ```
    """


    print(clean_sql(test))