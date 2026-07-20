"""
chain.py unit tests
Covers: build_prompt / format_context / format_chat_history / get_llm
"""
import unittest
import sys
import os

# add backend/ to path so "app" package is importable
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(os.path.dirname(_THIS_DIR))
sys.path.insert(0, _BACKEND_DIR)

from app.rag.chain import build_prompt, format_context, format_chat_history, get_llm


class TestBuildPrompt(unittest.TestCase):
    """Tests for build_prompt()"""

    def test_returns_chat_prompt_template(self):
        """Should return a ChatPromptTemplate instance"""
        from langchain_core.prompts import ChatPromptTemplate
        result = build_prompt()
        self.assertIsInstance(result, ChatPromptTemplate)

    def test_template_contains_placeholders(self):
        """Template must include context, chat_history, question"""
        prompt = build_prompt()
        # Check that template includes placeholders via format
        formatted = prompt.format(
            context="ctx", chat_history="hist", question="q"
        )
        self.assertIn("ctx", formatted)
        self.assertIn("hist", formatted)
        self.assertIn("q", formatted)


class TestFormatContext(unittest.TestCase):
    """Tests for format_context()"""

    def test_empty_list_returns_default(self):
        """Empty list should return default text"""
        result = format_context([])
        self.assertEqual(result, "（暂无相关参考资料）")

    def test_single_result_contains_index_and_title(self):
        """Single result should contain [1] index and doc_title"""
        results = [
            {"metadata": {"doc_title": "DocA"}, "content": "ContentA"}
        ]
        result = format_context(results)
        self.assertIn("[1]", result)
        self.assertIn("DocA", result)
        self.assertIn("ContentA", result)

    def test_multiple_results_sequentially_numbered(self):
        """Multiple results should be numbered [1] [2] [3]"""
        results = [
            {"metadata": {"doc_title": f"Doc{i}"}, "content": f"Content{i}"}
            for i in range(3)
        ]
        result = format_context(results)
        self.assertIn("[1]", result)
        self.assertIn("[2]", result)
        self.assertIn("[3]", result)
        self.assertIn("Doc0", result)
        self.assertIn("Doc2", result)

    def test_missing_metadata_uses_default(self):
        """Missing metadata should show '未知文档'"""
        results = [{"content": "Some content"}]
        result = format_context(results)
        self.assertIn("未知文档", result)

    def test_missing_content_no_error(self):
        """Missing content should not raise"""
        results = [{"metadata": {"doc_title": "TitleOnly"}}]
        result = format_context(results)
        self.assertIn("TitleOnly", result)


class TestFormatChatHistory(unittest.TestCase):
    """Tests for format_chat_history()"""

    def test_empty_returns_default(self):
        """Empty list returns default"""
        result = format_chat_history([])
        self.assertEqual(result, "（无历史对话）")

    def test_user_role_label(self):
        """role=user should show '用户:'"""
        msgs = [{"role": "user", "content": "Hello"}]
        result = format_chat_history(msgs)
        self.assertIn("用户:", result)
        self.assertIn("Hello", result)

    def test_assistant_role_label(self):
        """role=assistant should show '助手:'"""
        msgs = [{"role": "assistant", "content": "Reply"}]
        result = format_chat_history(msgs)
        self.assertIn("助手:", result)
        self.assertIn("Reply", result)

    def test_more_than_10_keeps_last_10(self):
        """Only last 10 messages kept"""
        msgs = [{"role": "user", "content": f"Msg{i}"} for i in range(15)]
        result = format_chat_history(msgs)
        self.assertNotIn("Msg0", result)
        self.assertNotIn("Msg4", result)
        self.assertIn("Msg5", result)
        self.assertIn("Msg14", result)

    def test_long_content_truncated_to_200(self):
        """Content over 200 chars should be truncated"""
        long_content = "A" * 300
        msgs = [{"role": "user", "content": long_content}]
        result = format_chat_history(msgs)
        self.assertNotIn("A" * 201, result)


class TestGetLlm(unittest.TestCase):
    """Tests for get_llm()"""

    def test_unknown_provider_raises_valueerror(self):
        """Unknown provider should raise ValueError"""
        with self.assertRaises(ValueError) as ctx:
            get_llm(provider="nonexistent_xyz")
        self.assertIn("不支持", str(ctx.exception))

    def test_none_provider_uses_default(self):
        """provider=None should use settings default without error"""
        try:
            llm = get_llm(provider=None)
            self.assertIsNotNone(llm)
        except ValueError:
            self.fail("get_llm(None) should not raise")


if __name__ == "__main__":
    unittest.main()
