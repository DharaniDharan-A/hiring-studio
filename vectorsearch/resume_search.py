import logging
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex, SimpleField
import os

from dotenv import load_dotenv

load_dotenv()

search_service = os.getenv("AZURE_SEARCH_SERVICE")
api_key = os.getenv("AZURE_SEARCH_API_KEY")
resume_index = os.getenv("AZURE_RESUME_SEARCH_INDEX")
endpoint = f"https://{search_service}.search.windows.net"
jd_index = "job-descriptions"
result_index = "match-results"

credential = AzureKeyCredential(api_key)
resume_client = SearchClient(endpoint, resume_index, credential)
jd_client = SearchClient(endpoint, jd_index, credential)
result_client = SearchClient(endpoint, result_index, credential)
index_client = SearchIndexClient(endpoint, credential)

def create_result_index_if_not_exists():
    try:
        index_client.get_index(result_index)
    except Exception:
        fields = [
            SimpleField(name="id", type="Edm.String", key=True),
            SimpleField(name="jd_id", type="Edm.String", filterable=True),
            SimpleField(name="resume_id", type="Edm.String", filterable=True),
            SimpleField(name="score", type="Edm.Double"),
            SimpleField(name="match_status", type="Edm.String", filterable=True)
        ]
        index = SearchIndex(name=result_index, fields=fields)
        index_client.create_index(index)

def match_and_store_results(jd_id, val1, val2):
    # Fetch JD vector
    jd_doc = jd_client.get_document(key=jd_id)
    jd_vector = jd_doc["content_vector"]

    # Run vector search on resume index
    results = resume_client.search(
        search_text=None,
        vector_queries=[{
            "kind": "vector",
            "vector": jd_vector,
            "fields": "resume_vector",
            "k": 50
        }]
    )

    # Create index if not exists
    create_result_index_if_not_exists()

    # Store matches
    actions = []
    for result in results:
        score = result["@search.score"]
        status = "not matched"
        if score >= val1:
            status = "matched"
        elif score >= val2:
            status = "partially matched"

        record = {
            "id": f"{jd_id}_{result['id']}",
            "jd_id": jd_id,
            "resume_id": result["id"],
            "score": score,
            "match_status": status
        }
        actions.append(record)

    if actions:
        result_client.upload_documents(documents=actions)