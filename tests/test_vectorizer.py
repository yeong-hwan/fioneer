import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from fioneer.embeddings.vectorizer import EmbeddingGenerator

class TestEmbeddingGenerator(unittest.TestCase):
    def setUp(self):
        self.embedding_generator = EmbeddingGenerator()
        
    def test_generate_embedding_success(self):
        # Test data
        transcripts = ["Hello world", "Test text"]
        mock_embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        
        # Mock OpenAI API response
        mock_response = {
            "data": [
                {"embedding": mock_embeddings[0]},
                {"embedding": mock_embeddings[1]}
            ]
        }
        
        with patch('openai.Embedding.create', return_value=mock_response):
            result = self.embedding_generator.generate_embedding(transcripts)
            
            self.assertIsInstance(result, np.ndarray)
            self.assertEqual(result.shape, (2, 3))
            np.testing.assert_array_almost_equal(result, np.array(mock_embeddings))

    def test_generate_embedding_empty_input(self):
        with self.assertRaises(ValueError):
            self.embedding_generator.generate_embedding([])

    def test_generate_embedding_api_error(self):
        with patch('openai.Embedding.create', side_effect=Exception("API Error")):
            with self.assertRaises(ValueError) as context:
                self.embedding_generator.generate_embedding(["test"])
            self.assertIn("Failed to generate embeddings", str(context.exception))

    def test_custom_model(self):
        custom_model = "text-embedding-3-large"
        generator = EmbeddingGenerator(model=custom_model)
        self.assertEqual(generator.model, custom_model)

if __name__ == '__main__':
    unittest.main()