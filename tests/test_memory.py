import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import memory


class MemoryFallbackTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_persist_dir = memory.PERSIST_DIR
        self._original_collection_name = memory.COLLECTION_NAME
        self._clear_embedding_cache()

    def tearDown(self) -> None:
        memory.PERSIST_DIR = self._original_persist_dir
        memory.COLLECTION_NAME = self._original_collection_name
        self._clear_embedding_cache()

    def _clear_embedding_cache(self) -> None:
        for attr in ("_ef_cache", "_ef_backend"):
            if hasattr(memory.get_collection, attr):
                delattr(memory.get_collection, attr)

    def test_offline_fallback_collection_can_save_and_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            memory.PERSIST_DIR = str(Path(tmp_dir) / "chroma")
            memory.COLLECTION_NAME = "test_memory"

            with patch.object(
                memory.embedding_functions,
                "SentenceTransformerEmbeddingFunction",
                side_effect=RuntimeError("forced-init-failure"),
            ):
                client = memory.get_memory_client()
                collection = memory.get_collection(client)
                self.assertEqual(collection.name, "test_memory_offline")

                doc_id = memory.save_memory("offline memory test entry", collection=collection)
                self.assertIsInstance(doc_id, str)

                results = memory.search_memory("offline memory", n_results=3, collection=collection)
                self.assertGreaterEqual(len(results), 1)
                self.assertIn("document", results[0])
                self.assertIn("metadata", results[0])


if __name__ == "__main__":
    unittest.main()
