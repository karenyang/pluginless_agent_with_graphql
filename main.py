import openai
import numpy as np
import langchain
import requests
from langchain import PromptTemplate
from requests.exceptions import HTTPError
import json
import colorama 
from termcolor import colored

colorama.init()


openai.organization = ""
openai.api_key = ""

OPENAI_PARAMS={
    "temperature": 0,
    "max_tokens": 1024,
    "top_p": 1.0,
}

def ask_gpt4(input_str, feedback):
    messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": input_str},                
            ]

    if feedback:
        messages += feedback
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=OPENAI_PARAMS.get("temperature", 0),
        max_tokens=OPENAI_PARAMS.get("max_tokens", 2048),
        top_p=OPENAI_PARAMS.get("top_p", 1.0),        
    )
    



    return response['choices'][0]['message']['content']

def ask_chatgpt(input_str):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": input_str},                
            ],
        temperature=OPENAI_PARAMS.get("temperature", 0),
        max_tokens=OPENAI_PARAMS.get("max_tokens", 2048),
        top_p=OPENAI_PARAMS.get("top_p", 1.0),        
    )

    return response['choices'][0]['message']['content']

def load_schema_files(filename="yelp.schema"):
    with open(filename) as f:
        schema = f.read()
    return schema

def create_write_gql_query_prompt():
    template = """
    Given the GraphQL Schema, respond with a graphql query that can answer the user question: {question}. 
    Please ensure that the graphql query is valid for the provided schema. If such query does not exist, answer N/A. Don't include any comment.\n

    GraphQL Schema:
    {schema}
    """
    prompt = PromptTemplate(
        input_variables=["question", "schema"],
        template=template,
    )
    return prompt 

def create_tool_choice_prompt():
    template = """
    Given the user question: {question}, what tools will be helpful? If you don't konw, answer N/A. 
    Reply with just one word answer: Yelp, TMDB, Pokemon or N/A. For example: where can I eat? Yelp
    """
    prompt = PromptTemplate(
        input_variables=["question"],
        template=template,
    )
    return prompt 

def create_compile_answer_prompt():
    template = """
    Given the results {results}, answer the user question: {question} in plain english with a delightful tone, with emojis.

    """
    prompt = PromptTemplate(
        input_variables=["results", "question"],
        template=template,
    )
    return prompt 


def execute_graphql_command(endpoint, query, headers):
    """
    execute a graphql query
    """
    if endpoint != "https://api.yelp.com/v3/graphql":
        data = json.dumps({"query": query})
        try:
            r = requests.post(endpoint, data=data, headers=headers)
            # print(r.request.url)
            # print(r.request.body)
            # print(r.request.headers)
        except HTTPError as e:
            print(e.response.text)
        
    else:
        try:
            r = requests.post(endpoint, data=query, headers=headers)
        except HTTPError as e:
            print(e.response.text)

    return r

     
def main():
    tool_choice_prompt = create_tool_choice_prompt()
    write_gql_query_prompt = create_write_gql_query_prompt()
    compile_answer_prompt = create_compile_answer_prompt()

    user_question = input("How can I help you today?\n\n")
    tool_response = ask_chatgpt(tool_choice_prompt.format(question=user_question))
    
    schema = None 
    endpoint = None 
    headers = None 
    print("\n")
    if "yelp" in tool_response.lower():
        print(colored('Using Yelp GraphQL API', 'light_green', 'on_dark_grey'))

        schema = load_schema_files('yelp.schema')
        endpoint = "https://api.yelp.com/v3/graphql"
        headers={
            "Authorization": f"Bearer 1RosRHvtDF8zosm9SM-xOz8cUCt0YTp_nVPjqSIwy5PBqFPanbLIQoCPdKH8NMbrGflkpGoS4FqMtjHqx1Fz7IpZ6v8ZqZ338lXXbkC27V8wBPUaSHd4E0yD7ZwKWXYx",
            "Content-Type": "application/graphql"
        }

    elif 'tmdb' in tool_response.lower():
        print("Using TMDB GraphQL API") 
        schema = load_schema_files('tmdb.schema')
        endpoint = "https://tmdb.apps.quintero.io/"
        headers={
            "Content-Type": "application/json",
        }

    elif 'pokemon' in tool_response.lower():
        print(colored('Using Pokemon Trading cards GraphQL API', 'light_green', 'on_dark_grey'))
        schema = load_schema_files('tcg.schema')
        endpoint = "https://api.tcgdex.net/v2/graphql"
        headers={
            "Content-Type": "application/json",
        }

    else:
        print("No available tool for this. ")
        exit(0)

    feedback = None
    while True:
        response_history = ""
        gql_query_response = ask_gpt4(write_gql_query_prompt.format(question=user_question, schema=schema), feedback=feedback)
        print(colored(f"Here is gql query to help answer your question: \n {gql_query_response}", 'light_green', 'on_dark_grey'))

        ## Execute the query
        # print("Executing the query ...")

        response = execute_graphql_command(endpoint=endpoint, query=gql_query_response, headers=headers)

        print(colored(response.text, 'light_green', 'on_dark_grey'))

        if response.status_code == 200 and response.text != "N/A" and "errors" not in response.text: 
            response_history += response.text
            final_answer = ask_chatgpt(compile_answer_prompt.format( question=user_question, results=response_history))
            print(f"\nAnswer:{final_answer}\n")
        else:
            error_feedback =  input("Retrying the query again, can you provide some feedback?\n")
            feedback = [
                {"role": "assistant", "content": gql_query_response},
                {"role": "user", "content": f"previous answer: {response.text}, Feedback: {error_feedback}"},
            ]
            continue
        user_feedback = input("Does this answer look right? Hit enter if Yes. If not, please provide feedback.\n")
        if len(user_feedback) > 4:
            feedback = [
                {"role": "assistant", "content": gql_query_response},
                {"role": "user", "content": user_feedback},
            ]
            user_question += user_feedback
        else:
            print("I'm glad you are happy with the answer!\n")
            break

if __name__ == '__main__':
    while True:
        main()


    # Execute the query



