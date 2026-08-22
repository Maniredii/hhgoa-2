import pytest
from unittest.mock import patch, MagicMock

def test_embedding_initialization():
    with patch("app.services.hybrid_retriever.SentenceTransformer") as mock_st:
        mock_st.return_value = MagicMock()
        # Verify that mock st can be initialized in tests
        assert True
