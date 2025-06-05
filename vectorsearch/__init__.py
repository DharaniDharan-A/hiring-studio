import json
import logging
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
import azure.functions as func

# Azure Cognitive Search credentials
search_service = "hiring-studio"
api_key = "tXfLAUnRjeBONn3sDLZdKRu4EL64sew60Z3NRLlLRvAzSeAWV1FU"
endpoint = f"https://{search_service}.search.windows.net"
index_name = "resumes"

# Setup client
credential = AzureKeyCredential(api_key)
search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        jd_vector = body.get("jd_vector")

        if not jd_vector:
            return func.HttpResponse("Missing 'jd_vector' in request body", status_code=400)

        results = search_client.search(
            search_text=None,
            vector_queries=[{
                "kind": "vector",
                "vector": jd_vector,
                "fields": "resume_vector",
                "k": 5,
                "filter": None
            }]
        )

        response_data = []
        for result in results:
            response_data.append({
                "id": result["id"],
                "score": result["@search.score"],
                "resume_text": result["resume_text"]
            })

        return func.HttpResponse(json.dumps(response_data), mimetype="application/json", status_code=200)

    except Exception as e:
        logging.exception("Error in resume vector search")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
