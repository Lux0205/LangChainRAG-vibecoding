"""聊天服务 - 会话管理、消息存储、问答编排"""
import json
from typing import List, Optional, Dict, AsyncGenerator
from sqlalchemy.orm import Session
from app.models.session import ChatSession
from app.models.message import ChatMessage
from app.models.user import User
from app.rag.retriever import hybrid_retrieve
from app.rag.chain import stream_chat
from app.services.knowledge_service import KnowledgeService
from app.config import settings


class ChatService:

    @staticmethod
    def create_session(db: Session, user_id: int) -> ChatSession:
        """创建新会话"""
        session = ChatSession(user_id=user_id, title="新会话")
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_user_sessions(db: Session, user_id: int) -> List[ChatSession]:
        """获取用户所有会话"""
        return db.query(ChatSession).filter(
            ChatSession.user_id == user_id
        ).order_by(ChatSession.updated_at.desc()).all()

    @staticmethod
    def get_session(db: Session, session_id: int, user_id: int) -> Optional[ChatSession]:
        """获取指定会话（验证所有权）"""
        return db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        ).first()

    @staticmethod
    def delete_session(db: Session, session_id: int, user_id: int) -> bool:
        """删除会话"""
        session = ChatService.get_session(db, session_id, user_id)
        if not session:
            return False
        db.delete(session)
        db.commit()
        return True

    @staticmethod
    def get_messages(db: Session, session_id: int, user_id: int) -> List[ChatMessage]:
        """获取会话消息历史"""
        session = ChatService.get_session(db, session_id, user_id)
        if not session:
            return []
        return session.messages

    @staticmethod
    def save_message(
        db: Session,
        session_id: int,
        role: str,
        content: str,
        citations: list = None,
    ) -> ChatMessage:
        """保存消息"""
        msg = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            citations=citations,
        )
        db.add(msg)

        # 更新会话时间
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            # 如果是第一条用户消息，设为会话标题
            if role == "user" and not session.messages:
                session.title = content[:30] + ("..." if len(content) > 30 else "")

        db.commit()
        db.refresh(msg)
        return msg

    @staticmethod
    async def chat_stream(
        db: Session,
        session_id: int,
        user_id: int,
        question: str,
        provider: str = None,
    ) -> AsyncGenerator[str, None]:
        """
        流式问答主流程
        1. 保存用户消息
        2. 混合检索
        3. 流式生成回答（或纯检索模式）
        4. 保存助手消息
        """
        # 验证会话
        session = ChatService.get_session(db, session_id, user_id)
        if not session:
            yield json.dumps({"error": "会话不存在"})
            return

        # 保存用户消息
        ChatService.save_message(db, session_id, "user", question)

        # 获取对话历史
        history_msgs = [
            {"role": m.role, "content": m.content}
            for m in session.messages[-10:]
        ]

        # 混合检索
        all_chunks = KnowledgeService.get_all_chunks(db)
        search_results = hybrid_retrieve(question, all_chunks=all_chunks)

        # 整理引用信息
        citations = []
        for i, result in enumerate(search_results[:settings.RAG_TOP_K]):
            citations.append({
                "index": i + 1,
                "doc_title": result.get("metadata", {}).get("doc_title", "未知"),
                "content": result.get("content", "")[:200],
                "score": result.get("score", 0),
            })

        # 检查是否使用纯检索模式（provider=none 时跳过LLM）
        use_retrieval_only = (provider == "none")

        if use_retrieval_only:
            # 纯检索模式：直接返回知识库检索结果
            full_response = ChatService._format_retrieval_answer(question, search_results[:settings.RAG_TOP_K])
        else:
            # LLM 生成模式
            full_response = ""
            try:
                if provider == "tongyi":
                    # 通义千问：直接用原生SDK
                    async for token in ChatService._tongyi_stream(question, search_results, history_msgs):
                        full_response += token
                        yield json.dumps({"type": "token", "content": token}, ensure_ascii=False)
                else:
                    async for token in stream_chat(
                        question=question,
                        search_results=search_results,
                        chat_history=history_msgs,
                        provider=provider,
                    ):
                        full_response += token
                        yield json.dumps({"type": "token", "content": token}, ensure_ascii=False)
            except Exception as e:
                # LLM 调用失败（如余额不足），降级为纯检索模式
                print(f"[Chat] LLM调用失败: {type(e).__name__}，降级为纯检索模式")
                full_response = ChatService._format_retrieval_answer(question, search_results[:settings.RAG_TOP_K])

        # 逐字流式输出回答（纯检索模式也模拟流式效果）
        if use_retrieval_only:
            for char in full_response:
                yield json.dumps({"type": "token", "content": char}, ensure_ascii=False)

        # 保存助手消息（带引用）
        ChatService.save_message(db, session_id, "assistant", full_response, citations)

        # 发送引用信息
        yield json.dumps({"type": "citations", "data": citations}, ensure_ascii=False)
        yield json.dumps({"type": "done"}, ensure_ascii=False)

    @staticmethod
    async def _tongyi_stream(question: str, search_results: list, chat_history: list):
        """通义千问原生SDK流式输出"""
        import dashscope
        from app.config import settings
        dashscope.api_key = settings.DASHSCOPE_API_KEY

        # 组装 prompt
        context_parts = []
        for i, r in enumerate(search_results[:settings.RAG_TOP_K], 1):
            title = r.get("metadata", {}).get("doc_title", "未知")
            content = r.get("content", "")
            context_parts.append(f"[{i}] 来源: {title}\n{content}")
        context = "\n\n".join(context_parts)

        history_parts = []
        for msg in chat_history[-5:]:
            role = "用户" if msg["role"] == "user" else "助手"
            history_parts.append(f"{role}: {msg['content'][:200]}")

        prompt = f"""你是电商知识库智能问答助手。请严格根据参考资料回答。

## 回答规则
- 优先使用参考资料，标注来源 [1] [2]
- 知识库没有的信息，明确告知"暂未收录"
- 不要编造参数、价格

## 参考资料
{context}

## 对话历史
{chr(10).join(history_parts) if history_parts else "(无)"}

## 用户问题
{question}

请回答："""

        def sync_stream():
            """同步生成器：调用 dashscope"""
            return dashscope.Generation.call(
                model=settings.TONGYI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                result_format="message",
                stream=True,
                incremental_output=True,
            )

        # 在线程池中运行同步 streaming
        import asyncio, concurrent.futures
        loop = asyncio.get_event_loop()

        def run():
            for resp in sync_stream():
                if resp.status_code == 200 and resp.output:
                    token = resp.output.choices[0].message.content
                    if token:
                        yield token

        # 使用线程运行
        import queue
        q = queue.Queue()
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        def producer():
            try:
                for token in run():
                    q.put(token)
            except Exception as e:
                q.put(e)
            finally:
                q.put(None)

        fut = executor.submit(producer)

        while True:
            try:
                item = await loop.run_in_executor(None, q.get)
                if item is None:
                    break
                if isinstance(item, Exception):
                    raise item
                yield item
            except queue.Empty:
                await asyncio.sleep(0.01)

        executor.shutdown(wait=False)

    @staticmethod
    def _format_retrieval_answer(question: str, results: list) -> str:
        """纯检索模式：将搜索结果格式化为可读回答"""
        if not results:
            return "抱歉，知识库中暂未找到与您问题相关的信息。"

        lines = [f"根据知识库检索，找到以下相关信息：\n"]
        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            title = metadata.get("doc_title", "未知文档")
            content = result.get("content", "")
            score = result.get("score", 0)
            lines.append(f"【{i}】{title}（相关度: {score:.0%}）")
            lines.append(f"{content}\n")

        lines.append("---")
        lines.append("💡 当前为纯检索模式（未使用AI生成回答）。如需智能回答，请配置有效的API。")
        return "\n".join(lines)
