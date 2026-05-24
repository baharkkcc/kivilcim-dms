from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    name = Column(String)
    role = Column(String) # Sistem Yöneticisi, Mühendis / Kontrolör, Kalite Müdürü, Üretim Müdürü, Operatör
    password = Column(String, default="123456")

    revisions = relationship("Revision", back_populates="uploader")
    approvals = relationship("Approval", back_populates="user")
    comments = relationship("Comment", back_populates="user")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    doc_no = Column(String, unique=True, index=True)
    doc_name = Column(String)
    category = Column(String)
    department = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    revisions = relationship("Revision", back_populates="document", cascade="all, delete-orphan", order_by="desc(Revision.rev_no)")

class Revision(Base):
    __tablename__ = "revisions"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    rev_no = Column(Integer, default=0)
    status = Column(String, default="Taslak") # Taslak, İncelemede, Onaylandı, Reddedildi, Arşivlendi
    file_path = Column(String)
    
    rev_reason = Column(Text, nullable=True)
    affected_op = Column(Text, nullable=True)
    diff_desc = Column(Text, nullable=True)
    
    uploader_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    document = relationship("Document", back_populates="revisions")
    uploader = relationship("User", back_populates="revisions")
    approvals = relationship("Approval", back_populates="revision", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="revision", cascade="all, delete-orphan", order_by="desc(Comment.created_at)")

class Approval(Base):
    __tablename__ = "approvals"
    id = Column(Integer, primary_key=True, index=True)
    revision_id = Column(Integer, ForeignKey("revisions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="Bekliyor") # Bekliyor, Onaylandı, Reddedildi
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.datetime.utcnow)
    
    revision = relationship("Revision", back_populates="approvals")
    user = relationship("User", back_populates="approvals")

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    revision_id = Column(Integer, ForeignKey("revisions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    revision = relationship("Revision", back_populates="comments")
    user = relationship("User", back_populates="comments")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user_name = Column(String)
    role = Column(String)
    action = Column(String)
    target = Column(String)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String)
    is_read = Column(Boolean, default=False)
    is_starred = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User")
