import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import UploadedDocument
from app.utils import format_datetime

router = APIRouter(prefix="/api", tags=["documents"])

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)


def serialize_doc(doc: UploadedDocument):
    return {
        "id": doc.id,
        "name": doc.name,
        "file_type": doc.file_type,
        "file_path": doc.file_path,
        "file_size": doc.file_size,
        "created_at": format_datetime(doc.created_at),
    }


@router.get("/documents")
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(UploadedDocument).order_by(UploadedDocument.created_at.desc()).all()
    return [serialize_doc(d) for d in docs]


@router.post("/documents")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = os.path.join(UPLOADS_DIR, file.filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    doc = UploadedDocument(
        name=file.filename,
        file_type=file.content_type,
        file_path=file_path,
        file_size=len(content),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return serialize_doc(doc)


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(UploadedDocument).filter(UploadedDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    db.delete(doc)
    db.commit()
    return {"message": "删除成功"}
