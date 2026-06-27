# this tool lets the agent answer questions about bangladeshi hospitals
# it converts a plain english question into sql, runs it, then explains the result in plain english

import os
from langchain.tools import BaseTool
from langchain_groq import ChatGroq
from tools.db_helper import get_table_schema, get_sample_rows, run_sql_query, format_rows_as_text

DB_PATH = os.path.join("data", "hospitals.db")
TABLE_NAME = "hospitals"


class HospitalsDBTool(BaseTool):
    name: str = "HospitalsDBTool"
    description: str = (
        "Use this tool for questions about hospitals and health facilities "
        "in Bangladesh, including community clinics, upazila health "
        "complexes, diagnostic centers, and whether a facility is private "
        "or government run. Examples: how many hospitals are in a district, "
        "list private hospitals in a division, how many community clinics "
        "are in an upazila. This database does not contain bed capacity or "
        "doctor counts."
    )

    def _run(self, query: str) -> str:
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

        schema = get_table_schema(DB_PATH, TABLE_NAME)
        sample_columns, sample_rows = get_sample_rows(DB_PATH, TABLE_NAME)
        sample_text = format_rows_as_text(sample_columns, sample_rows)

        sql_prompt = f"""You write SQLite queries for a table named {TABLE_NAME}.
Table columns: {schema}
Sample rows:
{sample_text}

Important notes about this table:
Always compare text columns like division, district, and type with UPPER() on both sides to avoid case mismatches, for example WHERE UPPER(district) = UPPER('Dhaka').
private is 1 for private facilities and 0 for government facilities.
There is no bed count or doctor count column, do not invent one.

Write one single SELECT query that answers this question: {query}
Reply with only the raw SQL query and nothing else, no explanation, no markdown formatting."""

        sql_response = llm.invoke(sql_prompt)
        generated_sql = sql_response.content.strip()
        generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()

        try:
            result_columns, result_rows = run_sql_query(DB_PATH, generated_sql)
        except Exception as error:
            return f"the query could not be run against the hospitals database, error: {error}"

        result_text = format_rows_as_text(result_columns, result_rows)

        answer_prompt = f"""Question: {query}
SQL used: {generated_sql}
Raw database result:
{result_text}

Write a short natural language answer to the question using only this data."""

        final_answer = llm.invoke(answer_prompt)
        return final_answer.content.strip()

    async def _arun(self, query: str) -> str:
        return self._run(query)
