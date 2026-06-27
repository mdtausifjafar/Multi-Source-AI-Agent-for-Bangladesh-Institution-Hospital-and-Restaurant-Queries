# this tool lets the agent answer questions about bangladeshi institutions
# it converts a plain english question into sql, runs it, then explains the result in plain english

import os
from langchain.tools import BaseTool
from langchain_groq import ChatGroq
from tools.db_helper import get_table_schema, get_sample_rows, run_sql_query, format_rows_as_text

DB_PATH = os.path.join("data", "institutions.db")
TABLE_NAME = "institutions"


class InstitutionsDBTool(BaseTool):
    # the name and description below are what the main agent reads to decide
    # whether this tool fits the user's question, so keep the description specific
    name: str = "InstitutionsDBTool"
    description: str = (
        "Use this tool for questions about schools, madrashas, colleges, and "
        "technical or vocational institutes in Bangladesh, including their "
        "location, education level, and management type. Examples: how many "
        "institutions are in a district, list madrashas in a division, "
        "how many government schools are in an upazila, institutions by "
        "education level such as secondary or higher secondary."
    )

    def _run(self, query: str) -> str:
        # we keep one shared llm instance for turning natural language into sql
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

        # pull the real schema and a few sample rows so the llm writes sql
        # that actually matches the real column names instead of guessing
        schema = get_table_schema(DB_PATH, TABLE_NAME)
        sample_columns, sample_rows = get_sample_rows(DB_PATH, TABLE_NAME)
        sample_text = format_rows_as_text(sample_columns, sample_rows)

        sql_prompt = f"""You write SQLite queries for a table named {TABLE_NAME}.
Table columns: {schema}
Sample rows:
{sample_text}

Important notes about this table:
Text columns like division, district, institute_type, and management_type can be mixed case or all uppercase, so always compare them with UPPER() on both sides to avoid missing matches, for example WHERE UPPER(division) = UPPER('Dhaka').
There is no university type in this data, institute_type is one of Madrasha, College, School, Technical and Vocational, or School and College.
District name mapping — the database uses old names, so always apply these substitutions before querying: Chattogram → CHITTAGONG, Cumilla → COMILLA, Jashore → JESSORE, Barishal → BARISAL, Sylhet → SYLHET. Always use UPPER() when comparing district names.
Management type mapping — there is no 'Private' value. The actual values are: NON-GOVERNMENT (use this for private/non-government), GOVERNMENT, GOVERNMENT PRIMARY, LOCAL GOVERNMENT, AUTONOMOUS, OTHERS. When a user asks about private institutions, use NON-GOVERNMENT.

Write one single SELECT query that answers this question: {query}
Reply with only the raw SQL query and nothing else, no explanation, no markdown formatting."""

        sql_response = llm.invoke(sql_prompt)
        generated_sql = sql_response.content.strip()

        # strip markdown code fences in case the model wraps the query in them anyway
        generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()

        try:
            result_columns, result_rows = run_sql_query(DB_PATH, generated_sql)
        except Exception as error:
            return f"the query could not be run against the institutions database, error: {error}"

        result_text = format_rows_as_text(result_columns, result_rows)

        # ask the llm to turn the raw rows into a natural sounding answer
        answer_prompt = f"""Question: {query}
SQL used: {generated_sql}
Raw database result:
{result_text}

Write a short natural language answer to the question using only this data."""

        final_answer = llm.invoke(answer_prompt)
        return final_answer.content.strip()

    async def _arun(self, query: str) -> str:
        # async version just calls the sync version since sqlite here is fast enough
        return self._run(query)
