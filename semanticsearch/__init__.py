import azure.functions as func
import json
from . import resume_search

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        query = body.get("query")

        if not query:
            return func.HttpResponse("Missing 'query' in request body", status_code=400)

        results = resume_search.search_resumes_by_text(query)
        return func.HttpResponse(json.dumps(results), mimetype="application/json", status_code=200)

    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
