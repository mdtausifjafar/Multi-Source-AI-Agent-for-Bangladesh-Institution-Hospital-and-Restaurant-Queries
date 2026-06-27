# Multi-Source AI Agent for Bangladesh Institution, Hospital, and Restaurant Queries

This project is an intelligent multi-source AI agent that answers natural language questions about Bangladeshi institutions, hospitals, and restaurants. It automatically routes queries to the correct tool, writes and runs SQLite queries against local databases, and uses live web search as a fallback for general knowledge or real-time queries.

---

## Core Technologies and Libraries Used

I selected the following libraries to build this system:

- **LangChain (v0.3.26)**: Provides the core framework for constructing the AI agent. I used it to connect the language model, tools, prompt template, and AgentExecutor.
- **langchain-groq (v0.2.4)**: Used to integrate Groq's high-speed inference engine.
- **LLaMA 3.3 70B (via Groq)**: The core language model ("brain") used to decide which tool to route questions to, write SQLite queries, and formulate natural-sounding answers from raw data.
- **Tavily Python SDK (v0.7.26)**: Connects the agent to Tavily Search, a search engine optimized for LLMs that returns clean, structured content rather than raw HTML.
- **Pandas**: Used in the database build pipeline to load the source CSV datasets, clean column headers, drop empty data, and detect/convert numeric columns.
- **sqlite3**: Used to write cleaned DataFrames into SQLite database files (.db) and handle lightweight, safe SELECT queries.
- **python-dotenv**: Loads secret keys (Groq and Tavily API keys) from a local .env file.
- **ipykernel**: Enables running the project interactively inside a Jupyter Notebook environment.

---

## Database Architecture and Preprocessing

The system utilizes three local SQLite databases built from the source CSV files. During the ingestion pipeline (handled by build_databases.py), I applied the following preprocessing steps:

1. **Header Cleaning**: Meshy CSV headers (like "Hospital Name ") are sanitized using a custom regex function into SQL-friendly snake_case column names (e.g., "hospital_name").
2. **Type Inference**: The script detects numeric-looking text columns (like ratings) and casts them to numeric types (REAL or INTEGER). This ensures aggregations like COUNT, MAX, and AVG work as expected in SQLite.
3. **Empty Value Stripping**: Rows containing entirely null values are removed.

### 1. Institutions Database (institutions.db)

- **Table Name**: institutions
- **Row Count**: 34,901 rows
- **Data Scope**: A registry of primary schools, secondary schools, madrashas, colleges, and vocational/technical institutes.
- **Key Columns**: `institute_name`, `institute_type`, `division`, `district`, `thana`, `management_type`, `education_level`, `mpo_status`.

### 2. Hospitals Database (hospitals.db)

- **Table Name**: hospitals
- **Row Count**: 38,886 rows
- **Data Scope**: A registry of health facilities in Bangladesh including community clinics, upazila health complexes, hospitals, and blood banks.
- **Key Columns**: `name`, `type`, `agency`, `division`, `district`, `upazila`, `private` (1 for private, 0 for government).

### 3. Restaurants Database (restaurants.db)

- **Table Name**: restaurants
- **Row Count**: 12,703 rows
- **Data Scope**: Sourced from Google Maps place listings for food businesses.
- **Key Columns**: `name`, `latitude`, `longitude`, `rating`, `number_of_reviews`, `address`.

---

## Query Mapping and Routing Logic

A common issue with natural language to SQL converters is the mismatch between user colloquial terms and database representations. I addressed this by hardcoding mapping logic directly into the prompt templates of the database tools:

- **Colonial vs. Modern Names**: The database contains older names (e.g., district is stored as "CHITTAGONG" rather than "Chattogram"). The prompt instructs the LLM to map modern names (Chattogram, Cumilla, Jashore, Barishal, Sylhet) to their database values (CHITTAGONG, COMILLA, JESSORE, BARISAL, SYLHET).
- **Management Types**: Users ask for "private schools", but the database classifies them under the management type "NON-GOVERNMENT". The prompt instructs the LLM to translate "private" to "NON-GOVERNMENT" for institutions. For hospitals, it maps "private" to the boolean flag `private = 1`.
- **Address-based Location**: The restaurant database has no clean city column. The prompt guides the LLM to search for locations using wildcard operators on the free-text address field (e.g., `address LIKE '%Chattogram%'`).

### Tool Routing Design

The agent uses a system prompt that outlines the exact capabilities of the tools. It decides:

- To use **InstitutionsDBTool** if the query is about schools, colleges, or madrashas.
- To use **HospitalsDBTool** if the query is about medical facilities.
- To use **RestaurantsDBTool** if the query is about food joints, ratings, or reviews.
- To use **WebSearchTool** if the query is general, covers policy, or asks for missing database data (like hospital bed capacity or restaurant cuisine types).
- To execute **Multi-Tool Routing** if a query contains both a database lookup and a general knowledge question (e.g., looking up hospitals in a region and asking about local tourism).

---

## Notebook Demos and Results

Below are the exact queries I executed inside the `agent.ipynb` notebook along with the natural language responses returned by the agent. You can view these execution logs directly in the notebook cells without re-running them:

### Demo 1 - Institutions Database

- **Query**: How many madrashas are there in Sylhet division?
  **Answer**: There are 400 madrashas in Sylhet division.
- **Query**: Which district has the most government colleges?
  **Answer**: Dhaka district has the most government colleges.

### Demo 2 - Hospitals Database

- **Query**: How many private hospitals are in Dhaka?
  **Answer**: There are 5684 private hospitals in Dhaka.
- **Query**: List private hospitals in Chattogram.
  **Answer**: There are several private hospitals in Chattogram, including BGC Trust Medical College, Central Medical College, and Chottagram Ma O Shishu Medical College, among others. Additionally, there are various NGO hospitals and clinics in the division, such as those operated by BRAC (BHP) in different upazilas of Brahmanbaria district.

### Demo 3 - Restaurants Database

- **Query**: What are the top 3 highest rated restaurants in Dhaka?
  **Answer**: The top 3 highest rated restaurants in Dhaka are শুভ এন্টারপ্রাইজ অলটাইম ডিলার, ভাত ঘর, and আপন নিবাস, all with a perfect 5.0 rating.
- **Query**: Which restaurant in Chattogram has the most reviews?
  **Answer**: The restaurant with the most reviews in Chattogram is Hotel Noorjahan, with 17,655 reviews.

### Demo 4 - Web Search Tool

- **Query**: What is the current education policy for primary schools in Bangladesh?
  **Answer**: The current education policy for primary schools in Bangladesh is that primary education will be universal, compulsory, free, and of uniform quality for all. The Ministry of Primary and Mass Education implements policies for primary education, and education in Bangladesh is compulsory for all citizens until the end of primary school. The government has also extended free primary school education up to grade eight, in line with the National Education Policy.
- **Query**: What is the national healthcare budget of Bangladesh in 2024?
  **Answer**: The national healthcare budget of Bangladesh in 2024 is BDT 419 billion, which is approximately 5.19% of the proposed national budget.

### Demo 5 - Multi-Tool Routing

- **Query**: How many hospitals are in Cox's Bazar, and what kind of tourists visit the area?
  **Answer**: There are numerous hospitals and health centers in Cox's Bazar, including the Cox's Bazar 250 Bed District Sadar Hospital, Cox's Bazar Chest Disease Clinic, and several Upazila Health Complexes such as Chakaria, Kutubdia, Moheshkhali, and Pekua. Additionally, there are many Union Health Sub Centers throughout the district, providing healthcare services to local communities. Cox's Bazar is a popular tourist destination in Bangladesh, known for its natural beauty, including the world's longest natural sea beach, and various attractions such as Himchori, Kutubdia Lighthouse, Safari park, Moheshkhali Island, and St. Martin Island. The area attracts tourists who come to enjoy the scenic beauty, relax on the beach, and explore the local culture.

---

## Project File Structure

```
Multi-Source AI Agent for Bangladesh Institution, Hospital, and Restaurant Queries/
  agent.ipynb              # Main interactive notebook containing the agent and pre-run outputs
  build_databases.py       # Preprocessing pipeline that compiles the SQLite databases from CSVs
  requirements.txt         # List of Python dependencies
  .env.example             # Template for adding your API credentials
  data/                    # Contains source CSVs and generated .db files (created on run)
  tools/
    __init__.py
    db_helper.py           # Shared database utility functions
    institutions_tool.py   # SQL-generation tool for institutions
    hospitals_tool.py      # SQL-generation tool for hospitals
    restaurants_tool.py    # SQL-generation tool for restaurants
    web_search_tool.py     # Live Web search tool via Tavily API
```

---

## Step-by-Step Installation and Execution Guide

### 1. Extract the Project and Set Up the Virtual Environment

Open PowerShell or your command terminal in the project directory:

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 2. Install Dependencies

Install all required libraries into your virtual environment:

```powershell
pip install -r requirements.txt
```

*Note: If you run into Windows path limit errors during installation, you can enable Long Paths in Windows Group Policy/Registry, or run the installation inside a mapped drive (using `subst Z: "."` and running pip from the Z drive).*

### 3. Add API Keys

Create a file named `.env` in the root of the project and insert your credentials:

```env
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

- Get a free Groq API Key at: https://console.groq.com
- Get a free Tavily API Key at: https://tavily.com

### 4. Run the Ingestion Pipeline

Compile the local SQLite databases from the raw CSV data:

```powershell
python build_databases.py
```

Verify that `institutions.db`, `hospitals.db`, and `restaurants.db` have been successfully created inside the `data` directory.

### 5. Running the Notebook

Open VS Code, navigate to `agent.ipynb`, select the virtual environment `venv` as your kernel, and run the cells.

---

## Author

* **Md. Tausif Jafar**
* **Email:** mdtausifjafar@gmail.com
