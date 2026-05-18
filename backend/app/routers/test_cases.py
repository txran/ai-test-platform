from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.models.database import get_db
from app.models.models import TestCase, TestFunction

router = APIRouter(prefix="/api", tags=["test-cases"])


@router.post("/cases")
def create_case(data: dict, db: Session = Depends(get_db)):
    """创建测试用例"""
    case = TestCase(
        function_id=data.get("function_id"),
        name=data.get("name", ""),
        case_type=data.get("case_type", "positive"),
        description=data.get("description", ""),
        focus_point=data.get("focus_point", ""),
        preconditions=data.get("preconditions", ""),
        expected_result=data.get("expected_result", ""),
        status=data.get("status", "未测试"),
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    
    # 如果有function_id，创建关联
    if case.function_id:
        from app.models.models import TestFunctionCase
        assoc = TestFunctionCase(
            function_id=case.function_id,
            test_case_id=case.id
        )
        db.add(assoc)
        db.commit()
    
    return {
        "id": case.id,
        "function_id": case.function_id,
        "name": case.name,
        "case_type": case.case_type,
        "description": case.description,
        "status": case.status,
    }


@router.get("/cases")
def list_cases(function_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    """获取用例列表"""
    query = db.query(TestCase)
    if function_id:
        query = query.filter(TestCase.function_id == function_id)
    cases = query.all()
    return [{
        "id": c.id,
        "function_id": c.function_id,
        "name": c.name,
        "case_type": c.case_type,
        "description": c.description,
        "status": c.status,
        "created_at": str(c.created_at) if c.created_at else None,
    } for c in cases]


@router.get("/cases/{case_id}")
def get_case(case_id: int, db: Session = Depends(get_db)):
    """获取单个用例详情"""
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    return {
        "id": case.id,
        "function_id": case.function_id,
        "name": case.name,
        "case_type": case.case_type,
        "description": case.description,
        "focus_point": case.focus_point,
        "preconditions": case.preconditions,
        "expected_result": case.expected_result,
        "status": case.status,
    }


@router.put("/cases/{case_id}")
def update_case(case_id: int, data: dict, db: Session = Depends(get_db)):
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")

    for field in ["name", "description", "case_type", "focus_point", "preconditions",
                  "expected_result", "actual_result", "issues", "status"]:
        if field in data:
            setattr(case, field, data[field])

    if "actual_result" in data:
        from datetime import datetime
        case.executed_at = datetime.utcnow()

    db.commit()
    db.refresh(case)
    return {
        "id": case.id,
        "function_id": case.function_id,
        "name": case.name,
        "description": case.description,
        "case_type": case.case_type,
        "focus_point": case.focus_point,
        "preconditions": case.preconditions,
        "expected_result": case.expected_result,
        "actual_result": case.actual_result,
        "status": case.status,
    }


@router.delete("/cases/{case_id}")
def delete_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    db.delete(case)
    db.commit()
    return {"message": "删除成功"}
