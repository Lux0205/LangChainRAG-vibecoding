"""
LangChain RAG Chain组装 - 支持流式输出
"""
from typing import AsyncGenerator, List, Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel
from app.config import settings

# 系统Prompt模板
SYSTEM_PROMPT = """你是电商知识库智能问答助手。请严格根据以下参考资料回答用户问题。

## 回答规则
1. 优先使用参考资料中的信息回答，确保准确
2. 每个事实性陈述必须标注来源编号 [1] [2] [3]
3. 参考资料中没有的信息，明确告知"知识库中暂无相关信息"
4. 不要编造商品参数、价格等信息
5. 回答要简洁、专业、有帮助
6. 如果参考资料之间有矛盾，以最新的为准

## 参考资料
{context}

## 对话历史
{chat_history}

## 用户问题
{question}

请给出准确、有帮助的回答："""


def build_prompt() -> ChatPromptTemplate:
    """构建Prompt模板"""
    return ChatPromptTemplate.from_template(SYSTEM_PROMPT)


def format_context(results: List[Dict]) -> str:
    """格式化检索结果为Prompt上下文"""
    if not results:
        return "（暂无相关参考资料）"

    context_parts = []
    for i, result in enumerate(results, 1):
        title = result.get("metadata", {}).get("doc_title", "未知文档")
        content = result.get("content", "")
        context_parts.append(f"[{i}] 来源: {title}\n{content}")

    return "\n\n".join(context_parts)


def format_chat_history(messages: List[Dict]) -> str:
    """格式化对话历史"""
    if not messages:
        return "（无历史对话）"

    history_parts = []
    for msg in messages[-10:]:  # 最多取最近10轮
        role = "用户" if msg["role"] == "user" else "助手"
        content = msg["content"][:200]  # 截断过长内容
        history_parts.append(f"{role}: {content}")

    return "\n".join(history_parts)


class TongyiChatModel(BaseChatModel):
    """通义千问原生SDK封装 - 兼容LangChain接口"""

    model: str = settings.TONGYI_MODEL
    api_key: str = settings.DASHSCOPE_API_KEY
    temperature: float = 0.3

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        import dashscope
        dashscope.api_key = self.api_key
        dash_messages = [{"role": m.type, "content": m.content} for m in messages]
        resp = dashscope.Generation.call(
            model=self.model,
            messages=dash_messages,
            result_format="message",
            stop=stop,
        )
        from langchain_core.messages import AIMessage
        from langchain_core.outputs import ChatResult, ChatGeneration
        text = resp.output.choices[0].message.content
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])

    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        import dashscope
        dashscope.api_key = self.api_key
        dash_messages = [{"role": m.type, "content": m.content} for m in messages]
        resp = dashscope.Generation.call(
            model=self.model,
            messages=dash_messages,
            result_format="message",
        )
        from langchain_core.messages import AIMessage
        from langchain_core.outputs import ChatResult, ChatGeneration
        text = resp.output.choices[0].message.content
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])

    async def astream(self, input, **kwargs):
        """流式输出"""
        import dashscope
        dashscope.api_key = self.api_key
        text = input
        if hasattr(input, 'to_messages'):
            msgs = input.to_messages()
            text = "\n".join([f"{m.type}: {m.content}" for m in msgs])
        resp_stream = dashscope.Generation.call(
            model=self.model,
            messages=[{"role": "user", "content": text}],
            result_format="message",
            stream=True,
            incremental_output=True,
        )
        output_text = ""
        for resp in resp_stream:
            if resp.status_code == 200:
                chunk = resp.output.choices[0].message.content
                new_text = chunk[len(output_text):]
                output_text = chunk
                if new_text:
                    yield type('Obj', (), {'content': new_text})()

    @property
    def _llm_type(self) -> str:
        return "tongyi"


def get_llm(provider: str = None, streaming: bool = True) -> BaseChatModel:
    """
    获取LLM实例
    支持通义千问和智谱GLM
    """
    provider = provider or settings.LLM_PROVIDER

    if provider == "tongyi":
        return TongyiChatModel()
    elif provider == "zhipu":
        from langchain_community.chat_models import ChatZhipuAI
        return ChatZhipuAI(
            model=settings.ZHIPU_MODEL,
            api_key=settings.ZHIPU_API_KEY,
            streaming=streaming,
            temperature=0.3,
        )
    else:
        raise ValueError(f"不支持的LLM提供商: {provider}")


async def stream_chat(
    question: str,
    search_results: List[Dict],
    chat_history: List[Dict],
    provider: str = None,
) -> AsyncGenerator[str, None]:
    """
    流式生成回答
    逐token返回
    """
    llm = get_llm(provider=provider, streaming=True)
    prompt = build_prompt()

    # 组装完整prompt
    context = format_context(search_results)
    history = format_chat_history(chat_history)

    full_prompt = prompt.format(
        context=context,
        chat_history=history,
        question=question,
    )

    # 流式调用
    async for chunk in llm.astream(full_prompt):
        if chunk.content:
            yield chunk.content


def chat(
    question: str,
    search_results: List[Dict],
    chat_history: List[Dict],
    provider: str = None,
) -> str:
    """
    非流式生成回答（同步）
    """
    llm = get_llm(provider=provider, streaming=False)
    prompt = build_prompt()

    context = format_context(search_results)
    history = format_chat_history(chat_history)

    full_prompt = prompt.format(
        context=context,
        chat_history=history,
        question=question,
    )

    response = llm.invoke(full_prompt)
    return response.content
