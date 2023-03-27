import openai
import os
import requests
from langchain import PromptTemplate
from requests.exceptions import HTTPError
import json
import colorama 
from termcolor import colored

colorama.init()


openai.organization = os.getenv('OPENAI_ORG')
openai.api_key = os.getenv('OPENAI_API_KEY')

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

def load_schema_files(filename="schemas/yelp.schema"):
    with open(filename) as f:
        schema = f.read()
    return schema

def create_write_gql_query_prompt():
    template = """
    Answer the user question: {question} as much as you can. You will write a Graphql query to get intermediate answers, and those will be fed into another large language model to compile the final answer.
    Please ensure that the graphql query you write is valid for the provided schema. If such query does not exist, answer N/A. Don't include any comment or explanation.\n

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
    Given the results {results}, answer the user question: {question} in plain english with a delightful, helpful tone.

    """
    prompt = PromptTemplate(
        input_variables=["results", "question"],
        template=template,
    )
    return prompt 


def execute_graphql_command(endpoint, data, headers):
    """
    execute a graphql query
    """
    try:
        r = requests.post(endpoint, data=data, headers=headers)
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
        schema = load_schema_files('schemas/yelp.schema')
        endpoint = "https://api.yelp.com/v3/graphql"
        headers={
            "Authorization": f"Bearer 1RosRHvtDF8zosm9SM-xOz8cUCt0YTp_nVPjqSIwy5PBqFPanbLIQoCPdKH8NMbrGflkpGoS4FqMtjHqx1Fz7IpZ6v8ZqZ338lXXbkC27V8wBPUaSHd4E0yD7ZwKWXYx",
            "Content-Type": "application/graphql"
        }
        tool = "yelp"

    elif 'tmdb' in tool_response.lower():
       
        schema = load_schema_files('schemas/tmdb.schema')
        endpoint = "https://tmdb.apps.quintero.io/"
        headers={
            "Content-Type": "application/json",
        }
        tool = "tmdb"

    elif 'pokemon' in tool_response.lower():
        schema = load_schema_files('schemas/tcg.schema')
        endpoint = "https://api.tcgdex.net/v2/graphql"
        headers={
            "Content-Type": "application/json",
        }
        tool = "pokemon"

    else:
        print("No available tool for this. ")
        exit(0)

    print(colored(f'Using {tool} GraphQL API', 'light_green', 'on_dark_grey'))

    feedback = None
    while True:
        response_history = ""
        gql_query_response = ask_gpt4(write_gql_query_prompt.format(question=user_question, schema=schema), feedback=feedback)
        print(colored(f"Here is gql query to help answer your question: \n {gql_query_response}", 'light_green', 'on_dark_grey'))

        ## Execute the query
        # print("Executing the query ...")
        
        data = gql_query_response
        if tool != "yelp":
            data = json.dumps({"query": gql_query_response}) 
        response = execute_graphql_command(endpoint=endpoint, data=data, headers=headers)

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





