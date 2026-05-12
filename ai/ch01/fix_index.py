from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType
import os
from dotenv import load_dotenv

load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
)

client.create_payload_index(
    collection_name="card_benefits",
    field_name="card_type",
    field_schema=PayloadSchemaType.KEYWORD
)

info = client.get_collection("card_benefits")
print(info.payload_schema)