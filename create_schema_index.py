import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings
import graphql
import os
import argparse
import tiktoken 

parser = argparse.ArgumentParser()
parser.add_argument("file", help="schema file to load in to vector DB",
                    type=str)
args = parser.parse_args()

def iterdict(d):
  for k,v in d.items():        
     if isinstance(v, dict):
         return iterdict(v)
     else:  
         if k == "value" and v[0].isupper():
           if v not in ["Int", "String", "ID", "Boolean", "Float", "ALL", "Json", "DateTime"]:
             return v
           
def main():
    file_name = args.file
    print(f"Parsing {file_name} ...")
    with open(file_name) as f:
        schema_string = f.read()

    # Parse the schema into an AST using the graphql module
    schema_ast = graphql.parse(schema_string)
    documents = []
    metadatas = []
    ids = []
    encoding = tiktoken.encoding_for_model("text-embedding-ada-002")
    for d in schema_ast.definitions:
        text = schema_string[d.loc.start: d.loc.end]
        text_token_size = len(encoding.encode(text))
        while text_token_size > 8000:
            delta = text_token_size - 8000
            num_chars = delta // 4 + 1
            text = text[:-num_chars]
            text_token_size = len(text)
        documents.append(text)
        schema_definitions = d.to_dict()
        metadata = {"fields": ''}
        if "fields" in schema_definitions:
            for f in schema_definitions['fields']:
                field_type = iterdict(f['type'])
                if field_type:
                    metadata['fields'] += field_type + ', '
            metadata['fields'] = metadata['fields'][:-2]
        metadatas.append(metadata)
        ids.append(schema_definitions['name']['value'])

    chroma_client = chromadb.Client(
       Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=".chromadb/" # Optional, defaults to .chromadb/ in the current directory
        )
    )
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                    api_key=os.getenv('OPENAI_API_KEY'),
                    model_name="text-embedding-ada-002"
                )
    
    collection_name = f"{file_name.split('/')[-1].replace('.','-')}-index"
    print(f'Creating {collection_name}')

    collection = chroma_client.create_collection(name=collection_name, embedding_function=openai_ef)
    collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )



if __name__ == '__main__':
    main()