from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv

load_dotenv()

search_service = os.getenv("AZURE_SEARCH_SERVICE")
api_key = os.getenv("AZURE_SEARCH_API_KEY")
index_name = os.getenv("AZURE_RESUME_SEARCH_INDEX")
endpoint = f"https://{search_service}.search.windows.net"

credential = AzureKeyCredential(api_key)
search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)

def search_resumes_by_text(query: str):
    results = search_client.search(
        search_text=query,
        select=["id", "resume_text"],
        top=5
    )

    response_data = []
    for result in results:
        response_data.append({
            "id": result["id"],
            "resume_text": result["resume_text"]
        })
    return response_data
