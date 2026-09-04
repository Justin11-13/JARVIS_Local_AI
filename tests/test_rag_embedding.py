import unittest
from unittest.mock import patch

from services.rag.embedding import EmbeddingService


class RagEmbeddingTests(unittest.TestCase):
    @patch("services.rag.embedding._create_embedding_model")
    def test_embedding_model_is_shared_within_the_process(self, create_model):
        shared_model = object()
        create_model.return_value = shared_model
        model_name = "test/shared-embedding-model"

        first = EmbeddingService(model_name)
        second = EmbeddingService(model_name)

        self.assertIs(first.model, shared_model)
        self.assertIs(second.model, shared_model)
        create_model.assert_called_once_with(model_name)


if __name__ == "__main__":
    unittest.main()
