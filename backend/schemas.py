from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    name: str
    role: str

class UserResponse(UserBase):
    id: int
    class Config:
        orm_mode = True

class CommentCreate(BaseModel):
    user_id: int
    text: str

class CommentResponse(BaseModel):
    id: int
    text: str
    created_at: datetime
    user: UserResponse
    class Config:
        orm_mode = True

class ApprovalCreate(BaseModel):
    user_id: int

class ApprovalResponse(BaseModel):
    id: int
    status: str
    feedback: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    user: UserResponse
    class Config:
        orm_mode = True

class RevisionBase(BaseModel):
    rev_no: int
    status: str
    rev_reason: Optional[str] = None
    affected_op: Optional[str] = None
    diff_desc: Optional[str] = None
    created_at: datetime

class RevisionResponse(RevisionBase):
    id: int
    file_path: Optional[str] = None
    uploader: UserResponse
    approvals: List[ApprovalResponse]
    comments: List[CommentResponse]
    class Config:
        orm_mode = True

class DocumentBase(BaseModel):
    doc_no: str
    doc_name: str
    category: str
    department: str

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: int
    created_at: datetime
    revisions: List[RevisionResponse]
    class Config:
        orm_mode = True

class AuditLogCreate(BaseModel):
    user_name: str
    role: str
    action: str
    target: str

class AuditLogResponse(AuditLogCreate):
    id: int
    timestamp: datetime
    class Config:
        orm_mode = True

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    message: str
    is_read: bool
    is_starred: bool
    created_at: datetime
    class Config:
        orm_mode = True
