# this tool lets the agent answer questions about bangladeshi restaurants
# it converts a plain english question into sql, runs it, then explains the result in plain english

import os
from langchain.tools import BaseTool
from langchain_groq import ChatGroq
from tools.db_helper import get_table_schema, get_sample_rows, run_sql_query, format_rows_as_text

DB_PATH = os.path.join("data", "restaurants.db")
TABLE_NAME = "restaurants"


class RestaurantsDBTool(BaseTool):
    name: str = "RestaurantsDBTool"
    description: str = (
        "Use this tool for questions about restaurants and eateries in "
        "Bangladesh, including their rating, number of reviews, address, "
        "and approximate location. Examples: top rated restaurants in an "
        "area, restaurants near a place name, restaurants with the most "
        "reviews. This database does not contain a cuisine type column, "
        "and location must be matched against free text addresses rather "
        "than a clean city field."
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
There is no separate city or cuisine column, location names appear inside the address column as free text.
To filter by a place name, use the LIKE operator on the address column, for example WHERE address LIKE '%Chattogram%'.
Some addresses use alternate spellings such as Chittagong for Chattogram or Sylhet for Srihatta, consider trying the common alternate spelling too if the first one returns nothing.
rating is on a 0 to 5 scale, number_of_reviews is how many people reviewed the place, affluence is a rough price or affluence tier and is missing for most rows.

Write one single SELECT query that answers this question: {query}
Reply with only the raw SQL query and nothing else, no explanation, no markdown formatting."""

        sql_response = llm.invoke(sql_prompt)
        generated_sql = sql_response.content.strip()
        generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()

        try:
            result_columns, result_rows = run_sql_query(DB_PATH, generated_sql)
        except Exception as error:
            return f"the query could not be run against the restaurants database, error: {error}"

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
