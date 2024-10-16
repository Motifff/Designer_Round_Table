import lancedb
import ollama
from langchain_community.embeddings import OllamaEmbeddings
import pyarrow as pa

class AgentMemory:
    def __init__(self, agent_name, embedding_model="phi3"):
        self.db = lancedb.connect("data/memory.lance")
        self.embeddings = OllamaEmbeddings(model=embedding_model)
        embedding_size = len(self.embeddings.embed_query("test query"))
        schema = pa.schema([
            ("text", pa.string()),
            ("embedding", pa.list_(pa.float32(), embedding_size))
        ])
        # Check if table exists, if exists, remove anything in it, if not create it
        if agent_name in self.db.table_names():
            self.db.drop_table(agent_name)
            self.table = self.db.create_table(agent_name, schema=schema)
        else:
            self.table = self.db.create_table(agent_name, schema=schema)

    def add(self, memory):
        embedding = self.embeddings.embed_query(memory)
        self.table.add([{"text": memory, "embedding": embedding}])

    def search(self, query, k=5):
        embedding = self.embeddings.embed_query(query)
        results = self.table.search(embedding).limit(k).to_list()
        return [r['text'] for r in results]
