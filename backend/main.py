from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from typing import List
import uuid
import json
import os
import shutil
import datetime

from database import engine, Base, get_db
import models
import schemas

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Teknik Doküman Yönetimi API",
    docs_url=None, 
    redoc_url=None,
    openapi_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STORAGE_DIR = "/app/storage"
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR, exist_ok=True)
if not os.path.exists("./storage"):
    os.makedirs("./storage", exist_ok=True)
STORAGE_DIR = "/app/storage" if os.path.exists("/app/storage") else "./storage"


@app.post("/setup")
def setup_initial_data(db: Session = Depends(get_db)):
    if db.query(models.User).count() == 0:
        default_users = [
            {"username": "1001", "name": "Sistem Yöneticisi", "role": "Sistem Yöneticisi"},
            {"username": "2001", "name": "Ahmet Yılmaz", "role": "Kalite Müdürü"},
            {"username": "2002", "name": "Fatma Demir", "role": "Kalite Müdürü"},
            {"username": "3001", "name": "Ali Çelik", "role": "Mühendis / Kontrolör"},
            {"username": "3002", "name": "Veli Öz", "role": "Mühendis / Kontrolör"},
            {"username": "4001", "name": "Ayşe Kaya", "role": "Üretim Müdürü"},
            {"username": "5001", "name": "Mehmet Şahin", "role": "Operatör"},
        ]
        for u in default_users:
            db.add(models.User(**u))
        db.commit()
    return {"status": "success"}


@app.get("/users/", response_model=List[schemas.UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()


@app.post("/login", response_model=schemas.UserResponse)
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username, models.User.password == password).first()
    if not user:
        raise HTTPException(status_code=401, detail="Hatalı kullanıcı adı veya şifre")
    return user



@app.post("/documents/", response_model=schemas.DocumentResponse)
def create_document(
    doc_no: str = Form(...),
    doc_name: str = Form(...),
    category: str = Form(...),
    department: str = Form(None),
    rev_reason: str = Form(None),
    affected_op: str = Form(None),
    diff_desc: str = Form(None),
    uploader_id: int = Form(...),
    approvals: str = Form(...), # JSON string of user_ids for approval
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Save file
    file_extension = file.filename.split(".")[-1]
    filename = f"{doc_no}_{uuid.uuid4().hex[:8]}.{file_extension}"
    file_path = os.path.join(STORAGE_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    doc = db.query(models.Document).filter(models.Document.doc_no == doc_no).first()
    if not doc:
        doc = models.Document(
            doc_no=doc_no,
            doc_name=doc_name,
            category=category,
            department=department or "Belirtilmemiş"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        new_rev_no = 0
    else:
        new_rev_no = max([r.rev_no for r in doc.revisions]) + 1
        
    revision = models.Revision(
        document_id=doc.id,
        rev_no=new_rev_no,
        status="İncelemede",
        file_path=filename,
        rev_reason=rev_reason,
        affected_op=affected_op,
        diff_desc=diff_desc,
        uploader_id=uploader_id
    )
    db.add(revision)
    db.commit()
    db.refresh(revision)
    
    approval_list = json.loads(approvals)
    for app_user_id in approval_list:
        app_entry = models.Approval(
            revision_id=revision.id,
            user_id=int(app_user_id),
            status="Bekliyor"
        )
        db.add(app_entry)
        
        # Create notification for the approver
        notif = models.Notification(
            user_id=int(app_user_id),
            message=f"{doc_no} dokümanının {new_rev_no}. revizyonu incelemeniz/onayınız için size gönderildi."
        )
        db.add(notif)
        
    uploader = db.query(models.User).filter(models.User.id == uploader_id).first()
    log = models.AuditLog(
        user_name=uploader.name, 
        role=uploader.role, 
        action="Yeni Revizyon Yükledi" if new_rev_no > 0 else "Yeni Doküman Yükledi", 
        target=f"{doc_no} (Rev {new_rev_no})"
    )
    db.add(log)
    
    db.commit()
    db.refresh(doc)
    return doc


@app.get("/documents/", response_model=List[schemas.DocumentResponse])
def get_documents(db: Session = Depends(get_db)):
    return db.query(models.Document).order_by(models.Document.id.desc()).all()


@app.get("/documents/{doc_id}", response_model=schemas.DocumentResponse)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@app.get("/files/{filename}")
def get_file(filename: str):
    file_path = os.path.join(STORAGE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="application/pdf")


@app.post("/approvals/{approval_id}/approve")
def approve_document(approval_id: int, user_id: int, db: Session = Depends(get_db)):
    approval = db.query(models.Approval).filter(models.Approval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
        
    approval.status = "Onaylandı"
    approval.feedback = "Uygun"
    db.commit()
    
    revision = db.query(models.Revision).filter(models.Revision.id == approval.revision_id).first()
    all_approved = all(a.status == "Onaylandı" for a in revision.approvals)
    
    if all_approved:
        revision.status = "Onaylandı"
        # Archive older revisions
        doc = revision.document
        for r in doc.revisions:
            if r.id != revision.id and r.status == "Onaylandı":
                r.status = "Arşivlendi"
                
    user = db.query(models.User).filter(models.User.id == user_id).first()
    log = models.AuditLog(user_name=user.name, role=user.role, action="Onayladı", target=f"{revision.document.doc_no} (Rev {revision.rev_no})")
    db.add(log)
    db.commit()
    return {"status": "success"}


@app.post("/approvals/{approval_id}/reject")
def reject_document(approval_id: int, user_id: int, feedback: str = Form(...), db: Session = Depends(get_db)):
    approval = db.query(models.Approval).filter(models.Approval.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
        
    approval.status = "Reddedildi"
    approval.feedback = feedback
    
    revision = db.query(models.Revision).filter(models.Revision.id == approval.revision_id).first()
    revision.status = "Reddedildi"
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    log = models.AuditLog(user_name=user.name, role=user.role, action="Reddetti", target=f"{revision.document.doc_no} (Rev {revision.rev_no})")
    db.add(log)
    db.commit()
    return {"status": "success"}


@app.post("/revisions/{revision_id}/comments")
def add_comment(revision_id: int, user_id: int = Form(...), text: str = Form(...), db: Session = Depends(get_db)):
    comment = models.Comment(revision_id=revision_id, user_id=user_id, text=text)
    db.add(comment)
    
    revision = db.query(models.Revision).filter(models.Revision.id == revision_id).first()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    log = models.AuditLog(user_name=user.name, role=user.role, action="Yorum Yaptı", target=f"{revision.document.doc_no} (Rev {revision.rev_no})")
    db.add(log)
    
    # Notify related users (uploader + approvers)
    notified_users = set()
    if revision.uploader_id != user_id:
        notified_users.add(revision.uploader_id)
    for app in revision.approvals:
        if app.user_id != user_id:
            notified_users.add(app.user_id)
            
    for n_user_id in notified_users:
        notif = models.Notification(
            user_id=n_user_id,
            message=f"{user.name}, {revision.document.doc_no} dokümanına yeni bir yorum yaptı."
        )
        db.add(notif)
    
    db.commit()
    return {"status": "success"}

@app.put("/documents/{doc_id}/departments")
def add_department_to_doc(doc_id: int, departments: str = Form(...), db: Session = Depends(get_db)):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    doc.department = departments
    db.commit()
    return {"status": "success"}

@app.delete("/documents/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    return {"status": "success"}

@app.get("/notifications/{user_id}", response_model=List[schemas.NotificationResponse])
def get_notifications(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.Notification).filter(models.Notification.user_id == user_id).order_by(models.Notification.id.desc()).all()

@app.post("/notifications/{notif_id}/read")
def read_notification(notif_id: int, db: Session = Depends(get_db)):
    notif = db.query(models.Notification).filter(models.Notification.id == notif_id).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"status": "ok"}

@app.post("/notifications/{notif_id}/star")
def toggle_star_notification(notif_id: int, db: Session = Depends(get_db)):
    notif = db.query(models.Notification).filter(models.Notification.id == notif_id).first()
    if notif:
        notif.is_starred = not notif.is_starred
        db.commit()
        return {"status": "ok", "is_starred": notif.is_starred}
    return {"status": "error", "message": "Not found"}


@app.get("/audit-logs/", response_model=List[schemas.AuditLogResponse])
def get_audit_logs(db: Session = Depends(get_db)):
    return db.query(models.AuditLog).order_by(models.AuditLog.id.desc()).limit(50).all()


@app.get("/dashboard-stats/")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_docs = db.query(models.Document).count()
    pending = db.query(models.Revision).filter(models.Revision.status == "İncelemede").count()
    approved = db.query(models.Revision).filter(models.Revision.status == "Onaylandı").count()
    rejected = db.query(models.Revision).filter(models.Revision.status == "Reddedildi").count()
    
    return {
        "total_documents": total_docs,
        "pending_approvals": pending,
        "approved_revisions": approved,
        "rejected_revisions": rejected
    }
