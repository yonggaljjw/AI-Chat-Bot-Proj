import getpass
import os

if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = getpass.getpass("OpenAI API Key:")

from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()
docsearch = OpenSearchVectorSearch(
    index_name="*",
    embedding_function=embeddings,
    opensearch_url="https://" + os.getenv("OPENSEARCH_HOST")+ ":" + os.getenv("OPENSEARCH_PORT"),
    http_auth=(os.getenv("OPENSEARCH_ID"), os.getenv("OPENSEARCH_PASSWORD")),
    use_ssl = True,
    verify_certs = False,
    ssl_assert_hostname = False,
    ssl_show_warn = False,
)

query = "what is currency exchange rate? answer in Korean."
docs = docsearch.similarity_search(query)

