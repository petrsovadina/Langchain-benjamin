"""Dependency injection helpers for FastAPI endpoints."""

from langchain_core.documents import Document

from api.schemas import DocumentMetadata, RetrievedDocument


def document_to_retrieved_doc(doc: Document) -> RetrievedDocument:
    """Transform LangChain Document to RetrievedDocument schema.

    Converts Document with metadata to JSON-serializable Pydantic model
    for API response.

    Args:
        doc: LangChain Document with page_content and metadata.

    Returns:
        RetrievedDocument with DocumentMetadata.

    Example:
        >>> doc = Document(
        ...     page_content="Metformin Teva 500mg",
        ...     metadata={"source": "sukl", "registration_number": "0012345"}
        ... )
        >>> retrieved = document_to_retrieved_doc(doc)
        >>> retrieved.metadata.source
        'sukl'
    """
    # Convert metadata dict to DocumentMetadata (allows extra fields)
    metadata = DocumentMetadata(**doc.metadata)

    return RetrievedDocument(page_content=doc.page_content, metadata=metadata)


def transform_documents(docs: list[Document]) -> list[RetrievedDocument]:
    """Transform list of Documents to RetrievedDocuments.

    Batch transformation helper for state.retrieved_docs.

    Args:
        docs: List of LangChain Documents.

    Returns:
        List of RetrievedDocument schemas.
    """
    return [document_to_retrieved_doc(doc) for doc in docs]
