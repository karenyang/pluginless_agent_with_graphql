## Description

Access services with a public GraphQL API, GPT plugin style, but without writing any plugin code.
Currently supported schema: Yelp, TMDB (movie database), and Pokemon Trading cards. 

You can ask the service any questions, and it will be turned into a GraphQL query, get exdcuted, and return desired answer.

It can be extended to any public and private GraphQL service with a schema file. 

## Requirement
```
pip install openai langchain termcolor
```

## Usage
```
python main.py
```