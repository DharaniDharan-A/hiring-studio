import json
import logging
import azure.functions as func
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex, SimpleField, edm

# Config
search_service = "hiring-studio"
api_key = "tXfLAUnRjeBONn3sDLZdKRu4EL64sew60Z3NRLlLRvAzSeAWV1FU"
endpoint = f"https://{search_service}.search.windows.net"
resumes_index = "resumes"
jd_index = "job-descriptions"
match_index = "jd-resume-matches"

credential = AzureKeyCredential(api_key)
search_client = SearchClient(endpoint, resumes_index, credential)
jd_client = SearchClient(endpoint, jd_index, credential)
index_client = SearchIndexClient(endpoint, credential)

def ensure_match_index_exists():
    if match_index not in [i.name for i in index_client.list_indexes()]:
        schema = SearchIndex(
            name=match_index,
            fields=[
                SimpleField(name="id", type=edm.String, key=True),
                SimpleField(name="jd_id", type=edm.String, filterable=True),
                SimpleField(name="resume_id", type=edm.String, filterable=True),
                SimpleField(name="score", type=edm.Double),
                SimpleField(name="match_status", type=edm.String, filterable=True)
            ]
        )
        index_client.create_index(schema)

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Parse query params
        jd_id = req.params.get("jd_id")
        val1 = float(req.params.get("val1", 0.85))  # matched threshold
        val2 = float(req.params.get("val2", 0.65))  # partially matched threshold

        if not jd_id:
            return func.HttpResponse("Missing jd_id in query parameters", status_code=400)

        # Get JD vector from JD index
        jd_doc = next(jd_client.search(search_text=None, filter=f"id eq '{jd_id}'"))
        jd_vector = jd_doc["content_vector"]

        # Vector search resumes
        results = search_client.search(
            search_text=None,
            vector_queries=[{
                "kind": "vector",
                "vector": jd_vector,
                "fields": "resume_vector",
                "k": 20
            }]
        )

        # Ensure output index exists
        ensure_match_index_exists()
        match_upload_client = SearchClient(endpoint, match_index, credential)

        to_upload = []
        for res in results:
            score = res["@search.score"]
            status = (
                "matched" if score >= val1 else
                "partially_matched" if score >= val2 else
                "not_matched"
            )

            to_upload.append({
                "id": f"{jd_id}_{res['id']}",
                "jd_id": jd_id,
                "resume_id": res["id"],
                "score": score,
                "match_status": status
            })

        if to_upload:
            match_upload_client.upload_documents(documents=to_upload)

        return func.HttpResponse("Matching complete and results stored.", status_code=200)

    except Exception as e:
        logging.exception("Error in JD to Resume match process")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
