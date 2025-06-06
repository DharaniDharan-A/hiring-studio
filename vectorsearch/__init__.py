import json
import logging
import azure.functions as func
from . import resume_search

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Parse the input JSON
        body = req.get_json()

        jd_id = body.get("jd_id")
        val1 = body.get("val1")
        val2 = body.get("val2")

        # Validate input
        if jd_id is None or val1 is None or val2 is None:
            return func.HttpResponse(
                json.dumps({"error": "jd_id, val1, and val2 are required"}),
                mimetype="application/json",
                status_code=400
            )

        # Convert threshold values to float
        try:
            val1 = float(val1)
            val2 = float(val2)
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "val1 and val2 must be numeric"}),
                mimetype="application/json",
                status_code=400
            )

        # Perform matching and store results
        resume_search.match_and_store_results(jd_id, val1, val2)

        return func.HttpResponse(
            json.dumps({"message": "Matching results stored."}),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.exception("Error during vector matching")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
