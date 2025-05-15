from .inmemory import InMemoryMetadataStore
from .store import SQLiteMetadataStore

def get_metadata_store(backend: str = "sqlite", **kwargs):
    """
    Factory to get the appropriate metadata store backend.
    Args:
        backend: "sqlite" or "memory"
        kwargs: parameters for backend constructors
    Returns:
        An instance of the selected metadata store.
    """
    if backend == "memory":
        return InMemoryMetadataStore()
    elif backend == "sqlite":
        db_path = kwargs.get("db_path", "knowledgebase.db")
        return SQLiteMetadataStore(db_path=db_path)
    else:
        raise ValueError(f"Unknown metadata store backend: {backend}")