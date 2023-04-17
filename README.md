## Description

Access services with a public GraphQL API, GPT plugin style, but without writing any plugin code.
Currently supported schema: Yelp, TMDB (movie database), and Pokemon Trading cards. 

You can ask the service any questions, and it will be turned into a GraphQL query, get exdcuted, and return desired answer.

It can be extended to any public and private GraphQL service with a schema file. 

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
```
python main.py
```

You can type questions, and if the answers are not good, you can give it feedback to let GPT4 try again. 