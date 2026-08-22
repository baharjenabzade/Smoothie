from rag.database import collection

print("Documents:", collection.count())

results = collection.get(
    include=["metadatas"]
)

for metadata in results["metadatas"]:
    print(metadata)