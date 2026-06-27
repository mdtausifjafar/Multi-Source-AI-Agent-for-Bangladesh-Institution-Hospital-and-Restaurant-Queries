# this is a shared helper module used by all three db tools
# it knows how to connect to a sqlite db, read its schema, and run a query safely

import sqlite3


def get_table_schema(db_path, table_name):
    # this function reads the column names and types directly from the database
    # we use this so the llm always sees the real columns instead of guessed ones
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns_info = cursor.fetchall()
    connection.close()

    # pragma table_info returns tuples like (index, name, type, notnull, default, pk)
    schema_lines = [f"{row[1]} ({row[2]})" for row in columns_info]
    return ", ".join(schema_lines)


def get_sample_rows(db_path, table_name, limit=3):
    # this function grabs a few sample rows so the llm understands what real values look like
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
    rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]
    connection.close()
    return column_names, rows


def run_sql_query(db_path, sql_query):
    # this function runs the actual sql query and returns rows plus column names
    # only select statements are allowed here to keep the database read only and safe
    cleaned_query = sql_query.strip().rstrip(";")
    if not cleaned_query.lower().startswith("select"):
        raise ValueError("only select queries are allowed for this tool")

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute(cleaned_query)
    rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]
    connection.close()
    return column_names, rows


def format_rows_as_text(column_names, rows, max_rows=15):
    # this function turns raw sql rows into a readable text block the llm can summarize
    if not rows:
        return "no matching rows were found"

    lines = []
    for row in rows[:max_rows]:
        # pair up each column name with its value for that row
        row_text = ", ".join(f"{col}: {val}" for col, val in zip(column_names, row))
        lines.append(row_text)

    extra_note = ""
    if len(rows) > max_rows:
        extra_note = f"\n...and {len(rows) - max_rows} more rows not shown here"

    return "\n".join(lines) + extra_note
