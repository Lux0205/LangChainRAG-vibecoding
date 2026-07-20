"""
retriever.py unit tests
Covers: bm25_search / reciprocal_rank_fusion
(vector_search and hybrid_retrieve skipped - require MySQL)
"""
import unittest
import sys
import os

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(os.path.dirname(_THIS_DIR))
sys.path.insert(0, _BACKEND_DIR)

from app.rag.retriever import bm25_search, reciprocal_rank_fusion


class TestBm25Search(unittest.TestCase):
    """Tests for bm25_search"""

    def setUp(self):
        self.docs = [
            {"content": "苹果手机 价格 参数", "document_id": 1, "chunk_index": 0},
            {"content": "华为手机 配置 屏幕", "document_id": 2, "chunk_index": 0},
            {"content": "苹果手机 屏幕 电池", "document_id": 3, "chunk_index": 0},
            {"content": "小米手机 价格 快充", "document_id": 4, "chunk_index": 0},
        ]

    def test_query_matching_docs_returned(self):
        """Query '苹果' should return Apple docs"""
        results = bm25_search("苹果手机", self.docs, k=10)
        self.assertGreater(len(results), 0)
        contents = [r["content"] for r in results]
        # First result should contain 苹果
        self.assertIn("苹果", results[0]["content"])

    def test_k_limits_results(self):
        """k=2 should return at most 2 results"""
        results = bm25_search("手机", self.docs, k=2)
        self.assertLessEqual(len(results), 2)

    def test_no_match_returns_empty(self):
        """Non-matching query returns empty list"""
        results = bm25_search("飞机火箭", self.docs, k=10)
        self.assertEqual(len(results), 0)

    def test_results_have_score(self):
        """Results should have numeric score > 0"""
        results = bm25_search("苹果", self.docs, k=10)
        for r in results:
            self.assertIn("score", r)
            self.assertGreater(r["score"], 0)

    def test_empty_docs_raises_or_empty(self):
        """Empty documents list - BM25Okapi raises ZeroDivisionError"""
        # rank_bm25 library raises ZeroDivisionError on empty corpus
        with self.assertRaises(ZeroDivisionError):
            bm25_search("苹果", [], k=10)


class TestReciprocalRankFusion(unittest.TestCase):
    """Tests for reciprocal_rank_fusion"""

    def setUp(self):
        self.vector_results = [
            {"content": "A"},
            {"content": "B"},
            {"content": "C"},
        ]
        self.bm25_results = [
            {"content": "B"},
            {"content": "D"},
            {"content": "A"},
        ]

    def test_fusion_returns_results(self):
        """Fusion should return combined results"""
        v = self.vector_results
        b = [{"content": "B"}, {"content": "D"}, {"content": "A"}]
        fused = reciprocal_rank_fusion(v, b)
        self.assertGreater(len(fused), 0)
        # Should include A, B, C, D
        contents = {r["content"] for r in fused}
        self.assertIn("A", contents)
        self.assertIn("B", contents)
        self.assertIn("C", contents)
        self.assertIn("D", contents)

    def test_fusion_respects_top_k(self):
        """top_k limits the number of results"""
        fused = reciprocal_rank_fusion(
            self.vector_results, self.bm25_results, top_k=2
        )
        self.assertLessEqual(len(fused), 2)

    def test_fusion_no_duplicates(self):
        """Same content should not appear twice"""
        fused = reciprocal_rank_fusion(self.vector_results, self.bm25_results)
        contents = [r["content"] for r in fused]
        self.assertEqual(len(contents), len(set(contents)))

    def test_empty_inputs_returns_empty(self):
        """Both empty lists should return empty"""
        fused = reciprocal_rank_fusion([], [])
        self.assertEqual(len(fused), 0)

    def test_b_ranked_higher_than_c(self):
        """B appears in both lists, should outrank C (only in vector)"""
        fused = reciprocal_rank_fusion(self.vector_results, self.bm25_results)
        contents = [r["content"] for r in fused]
        b_idx = contents.index("B")
        c_idx = contents.index("C")
        self.assertLess(b_idx, c_idx)

    def test_default_k_parameter(self):
        """Default k=60 should work without specifying"""
        fused = reciprocal_rank_fusion(self.vector_results, self.bm25_results)
        self.assertIsInstance(fused, list)


if __name__ == "__main__":
    unittest.main()
