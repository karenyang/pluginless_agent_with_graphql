## Description

Access services with a public GraphQL API, GPT plugin style, but without writing any plugin code.
Currently supported schema: Github, Yelp, TMDB (movie database), and Pokemon Trading cards. 

You can ask the service any questions, and it will be turned into a GraphQL query, get exdcuted, and return desired answer.

It can be extended to any public and private GraphQL service with a schema file of any size. You need to create a index for each tool by using provided scirpt, and at run time the index will be used to provide the most relevant part of the schema for Language models to build a query. 

## Requirement
```
pip install openai langchain termcolor colorama chromadb tiktoken
```

```
source OPENAI_ORG="<your_openai_org>"
source OPENAI_API_KEY="<your_openai_api_key>"
```

If you want to try it on another schema, you need to provide a schema file and modify the code to include it.
- You can use [gql-sdl tool](https://www.npmjs.com/package/gql-sdl) to download a graphql schema from an endpoint. 
- Then, you can then modify the code to add that schema. Add payload and headers of the new graphql endpoint in `main()`, and add the name of the service in the prompt template inside `create_tool_choice_prompt()`

## Usage
First, create index for the schema to use. We provide a few example schemas in the `schemas` folder.You can specify which file to index. By default, it will create schemas for all of the files in `schemas` folder
```
python create_schema_index.py #this will index all files in schemas/ 
python create_schema_index.py --file schemas/github.schema # this will index a particular file
``` 
You can replace github.schema to any schema files. It will be stored to your local `.chromadb/`. 

Note if you add new schema for a tool you are interested in trying, you need to modify the `main.py` in two places in order to use new tools. 
- in `def create_tool_choice_prompt`, add new tool's name into the prompt.
- in `main`, follow the logic of other tools, add logic to load index from the index file you just created, and specify endpoint and headers for making queries.

```
python main.py
```

You can then type questions, and if the answers are not good, you can give it feedback to let GPT try again. 
Have fun! 