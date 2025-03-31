# -*- coding: utf-8 -*-
"""
Created on Sat Nov 16 20:08:52 2024

@author: ravivarman.balaiyan
"""
#from langchain.chains import LLMChain

from langchain_community.utilities.sql_database import SQLDatabase
from dotenv import load_dotenv
import os
import time
import google.generativeai as genai
#from langchain_core.prompts import PromptTemplate
#from langchain_core.output_parsers import StrOutputParser

load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=google_api_key)

model = genai.GenerativeModel(model_name="gemini-1.5-flash")

def initialize_db_connection():
    # Connect to the SQL database
    db = SQLDatabase.from_uri("sqlite:///./data/newSynthetic70k.db")
    
    return db

def get_schema_db(db):
    # Schema of the db
    schema = db.get_table_info()
    return schema

def build_few_shots_prompt(db,chat_history=None):
    # Get schema
    db_schema = get_schema_db(db)

    few_shots = [
        {
            "input": "How many Customers are present?",
            "query": "SELECT COUNT(*) FROM customer;"},
        {
            "input": "List 10 claims with the highest claim amount",
            "query": "SELECT claim_id FROM claim ORDER BY claim_amount DESC LIMIT 10;",
        },
        {
            "input": "List the top 3 agents with highest commission",
            "query": "SELECT a.first_name, a.last_name, b.commission_amount FROM commission b LEFT JOIN agent a ON a.agent_id = b.agent_id ORDER BY b.commission_amount DESC LIMIT 3;",
        }
        ,{
           "input": "which agent sold highest number of policies yesterday",
           "query": "SELECT a.agent_id,a.first_name || ' ' || a.last_name AS agent_name,COUNT(s.sale_id) AS policies_sold FROM sales s JOIN agent a ON s.agent_id = a.agent_id WHERE DATE(s.sale_date) = DATE('now', '-1 day') GROUP BY a.agent_id, a.first_name, a.last_name ORDER BY policies_sold DESC LIMIT 1;",
        },
        {
           "input": "which customer has made claims",
           "query": "SELECT c.first_name, c.last_name FROM customer c JOIN policy p ON c.customer_id = p.customer_id JOIN claim cl ON p.policy_id = cl.policy_id;",
        }
    ]
    chat_history_section = ""
    if chat_history:
        chat_history_section = f"""
        Previous conversation:
        {chat_history}
        """
    prompt = [
    f"""
    You are a SQL expert and an intelligent assistant. Your task is to translate natural language requests into accurate and efficient SQL queries based on a given database schema. Follow the guidelines below for every request:
    The SQL database has multiple tables, and these are the schemas: {db_schema},{chat_history_section}
    1. **Understand the Request**:
        - Carefully analyze the natural language request to determine the exact data requirements.
        - Identify the necessary tables, columns, and operations (e.g., filtering, sorting, joins, aggregations).
        - If the request seems ambiguous, state the ambiguity clearly and provide suggestions to resolve it.

    2. **Database Schema Awareness**:
        - Use only the provided schema, including table names, column names, and their relationships (e.g., primary and foreign keys).
        - Adhere to the data types mentioned in the schema and avoid mismatches (e.g., strings vs. integers).

    3. **Generate Efficient SQL Queries**:
        - Prioritize performance by using SQL best practices, such as minimizing subqueries where JOINs suffice and using indexed columns effectively.
        - Write queries that avoid unnecessary complexity and optimize for readability.
        - If the question is about the schema, return a SQL query to fetch table names and column names of all tables.

    4. **Edge Case Handling**:
        - Anticipate potential edge cases, such as null values, empty results, or large datasets.
        - Provide explanations or suggestions to handle such cases, if applicable.

    5. **Return Executable SQL**:
        - Provide ONLY the SQL query that can be directly executed on the specified database.
        - Remove three single quotes (```) in the beginning or end of the SQL query.
        - Also remove the word 'sql' in the beginning of the SQL.
        - In the SQL response, ONLY give the SQL, don't respond with the question along with the SQL. I want ONLY SQL, NOTHING ELSE ALONG WITH THAT.
        - Give only ONE SQL QUERY, DO NOT GIVE MULTIPLE SQL QUERIES.

    You can order the results by a relevant column to return the most interesting examples in the database.
    Never query for all the columns from a specific table, only ask for the relevant columns given the question.
    Also, the SQL code should not have ``` in the beginning or end and no 'sql' word in the output.
    You SHOULD respond ONLY the SQL QUERY, DO NOT RESPOND ANY SPECIAL CHARACTERS BEFORE OR AFTER THE SQL QUERY.
    You MUST double-check your query before executing it. If you get an error while executing a query, rewrite the query and try again.

    DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

    If the question does not seem related to the database, just return "I don't know" as the answer.
    If you get any error while running SQL query in the database, please answer politely as I can't fetch an answer due to a technical error.

    Here are some examples of user inputs and their corresponding SQL queries:
    """
]

    # Append each example to the prompt
    for sql_example in few_shots:
        prompt.append(
            f"\nExample - {sql_example['input']}, the SQL command will be something like this {sql_example['query']}")

    # Join prompt sections into a single string
    formatted_prompt = [''.join(prompt)]
    
    return formatted_prompt
    
def generate_sql_query(prompt, user_question):
    # Model to generate SQL query
    #model = genai.GenerativeModel('gemini-1.5-flash')
    # Generate SQL query
    
    sql_query = model.generate_content(prompt[0] + user_question)

    return sql_query.text

def run_query(db, sql_query):
    # Run sql query
    return db.run(sql_query)

# def get_gemini_llm():
#     # LLM
#     llm = model
#     #llm = genai.GenerativeModel(model_name="gemini-1.5-flash")
#     return llm
def second_llm_call(sql_response,user_question):
    #model = genai.GenerativeModel('gemini-1.5-flash')
    secondprompt = [f"""Based on the sql response, write an answer relating to the user question:
                {user_question} , don't show any error messages, if sql response is empty, please respond any polite user friendly message
            SQL response:""",  ]                
    # Generate SQL query
    finalanswer = model.generate_content([secondprompt[0], sql_response])
    return finalanswer.text

    
import streamlit as st

def main():
    # Configure settings of the page
    st.set_page_config(
        page_title="AIWA Chat with SQL Databases",
        page_icon="🧊",
        layout="wide")

    # Add a header
    st.header("AIWA - Conversational Insights - Talk 2 data")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    # Widget to provide questions
    user_question = st.chat_input("Ask me a question about Insurance database that contains Policy, Customer, Agent, Quote, Sales, Claims, Address etc",key="user_input")

    if user_question is not None:
        with st.chat_message("user"):
            st.write(user_question)

        with st.spinner("Fetching..."):
            st.session_state.chat_history.append({"role": "user", "content": user_question})
            # DB connection
            db = initialize_db_connection()


            chat_history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.chat_history])
            # Generate few shots prompt
            few_shots_prompt = build_few_shots_prompt(db, chat_history)

            # Generate SQL query
            sql_query = generate_sql_query(prompt=few_shots_prompt, user_question = user_question)

            # Execute SQL query
            sql_query = sql_query.strip()
            if sql_query != "I don't know":
                query_results = run_query(db = db, sql_query = sql_query)
                if query_results is None:
                    query_results = "No result found in database"                    
            else:
                query_results = "No result found in database"
                
            # LLM
            #llm = get_gemini_llm()

            # Final answer
            answer = second_llm_call(query_results, user_question)


            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                for chunk in answer.split():
                    full_response += chunk + " "
                    time.sleep(0.05)
                    response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)
                st.write(sql_query)

            
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            
            #st.write(sql_query)
            #st.write(query_results)
            #st.success("Done")

if __name__ == "__main__":
    main()
