import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from app.domain.models import ChatTurn
from app.domain.ports import ConversationRepositoryPort


class Base(DeclarativeBase):
    pass


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    messages: Mapped[List["Message"]] = relationship(cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    sources_json: Mapped[str] = mapped_column(Text, default="[]")
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)


class SQLConversationRepository(ConversationRepositoryPort):
    """Aísla el acceso a SQLAlchemy del resto de la aplicación."""

    def __init__(self, database_url: str) -> None:
        if database_url.startswith("sqlite:///"):
            Path(database_url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine = create_engine(database_url, connect_args=connect_args)
        self.session_factory = sessionmaker(self.engine, expire_on_commit=False)
        Base.metadata.create_all(self.engine)

    def add_turn(self, session_id: str, turn: ChatTurn) -> None:
        with self.session_factory.begin() as db:
            conversation = db.get(Conversation, session_id)
            if conversation is None:
                conversation = Conversation(id=session_id)
                db.add(conversation)
            conversation.updated_at = turn.created_at
            db.add(Message(
                conversation_id=session_id,
                role=turn.role,
                content=turn.content,
                sources_json=json.dumps(turn.sources, ensure_ascii=False),
                latency_ms=turn.latency_ms,
                created_at=turn.created_at,
            ))

    def recent_turns(self, session_id: str, limit: int) -> List[ChatTurn]:
        with self.session_factory() as db:
            rows = db.scalars(
                select(Message).where(Message.conversation_id == session_id)
                .order_by(Message.created_at.desc(), Message.id.desc()).limit(limit)
            ).all()
        return [ChatTurn(
            role=row.role,
            content=row.content,
            created_at=row.created_at,
            sources=json.loads(row.sources_json),
            latency_ms=row.latency_ms,
        ) for row in reversed(rows)]

    def list_sessions(self, limit: int, offset: int) -> Iterable[dict]:
        with self.session_factory() as db:
            rows = db.execute(
                select(
                    Conversation.id,
                    Conversation.created_at,
                    Conversation.updated_at,
                    func.count(Message.id).label("message_count"),
                ).outerjoin(Message).group_by(Conversation.id)
                .order_by(Conversation.updated_at.desc()).limit(limit).offset(offset)
            ).all()
        return [{"session_id": row.id, "created_at": row.created_at, "updated_at": row.updated_at,
                 "message_count": row.message_count} for row in rows]

    def metrics(self) -> dict:
        """Calcula métricas de uso y cobertura a partir del historial."""
        with self.session_factory() as db:
            sessions = db.scalar(select(func.count()).select_from(Conversation)) or 0
            messages = db.scalar(select(func.count()).select_from(Message)) or 0
            user_messages = db.scalar(select(func.count()).select_from(Message).where(Message.role == "user")) or 0
            avg_latency = db.scalar(select(func.avg(Message.latency_ms)).where(Message.role == "assistant"))
            active_days = db.scalar(select(func.count(func.distinct(func.date(Message.created_at))))) or 0
            answered_with_sources = db.scalar(
                select(func.count()).select_from(Message).where(
                    Message.role == "assistant", Message.sources_json != "[]"
                )
            ) or 0
            answered_without_sources = db.scalar(
                select(func.count()).select_from(Message).where(
                    Message.role == "assistant", Message.sources_json == "[]"
                )
            ) or 0
            total_answers = answered_with_sources + answered_without_sources
        return {
            "total_sessions": sessions,
            "total_messages": messages,
            "total_questions": user_messages,
            "average_response_latency_ms": round(float(avg_latency or 0), 2),
            "active_days": active_days,
            "average_questions_per_session": round(user_messages / sessions, 2) if sessions else 0,
            "answers_with_sources": answered_with_sources,
            "answers_without_sources": answered_without_sources,
            "source_coverage_percentage": round(answered_with_sources * 100 / total_answers, 2)
            if total_answers else 0,
        }
