from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.models.database import get_db
from app.models.models import TestFunction, TestCase, TestSuite, TestSuiteFunction
from app.utils import format_datetime

router = APIRouter(prefix="/api", tags=["functions"])


def serialize_function(func: TestFunction, include_cases: bool = False):
    data = {
        "id": func.id,
        "name": func.name,
        "description": func.description,
        "url": func.url,
        "status": func.status,
        "cases_count": len(func.cases) if func.cases else 0,
        "created_at": format_datetime(func.created_at),
        "updated_at": format_datetime(func.updated_at),
    }
    if include_cases:
        data["cases"] = [serialize_case(c) for c in func.cases]
    return data


def serialize_case(case: TestCase):
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
        "executed_at": format_datetime(case.executed_at),
        "issues": case.issues,
        "status": case.status,
        "created_at": format_datetime(case.created_at),
        "updated_at": format_datetime(case.updated_at),
    }


# ============ 功能管理 ============

@router.get("/functions")
def list_functions(
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(TestFunction)
    if keyword:
        query = query.filter(TestFunction.name.contains(keyword))

    total = query.count()
    items = query.order_by(TestFunction.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [serialize_function(f) for f in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/functions/{func_id}")
def get_function(func_id: int, db: Session = Depends(get_db)):
    func = db.query(TestFunction).filter(TestFunction.id == func_id).first()
    if not func:
        raise HTTPException(status_code=404, detail="功能不存在")
    return serialize_function(func, include_cases=True)


@router.post("/functions")
def create_function(data: dict, db: Session = Depends(get_db)):
    func = TestFunction(
        name=data.get("name", ""),
        description=data.get("description"),
        url=data.get("url"),
    )
    db.add(func)
    db.commit()
    db.refresh(func)
    return serialize_function(func)


@router.put("/functions/{func_id}")
def update_function(func_id: int, data: dict, db: Session = Depends(get_db)):
    func = db.query(TestFunction).filter(TestFunction.id == func_id).first()
    if not func:
        raise HTTPException(status_code=404, detail="功能不存在")

    for field in ["name", "description", "url", "status"]:
        if field in data:
            setattr(func, field, data[field])

    db.commit()
    db.refresh(func)
    return serialize_function(func)


@router.delete("/functions/{func_id}")
def delete_function(func_id: int, db: Session = Depends(get_db)):
    func = db.query(TestFunction).filter(TestFunction.id == func_id).first()
    if not func:
        raise HTTPException(status_code=404, detail="功能不存在")
    db.delete(func)
    db.commit()
    return {"message": "删除成功"}


# ============ 用例管理（属于功能） ============

@router.get("/functions/{func_id}/cases")
def list_function_cases(func_id: int, db: Session = Depends(get_db)):
    func = db.query(TestFunction).filter(TestFunction.id == func_id).first()
    if not func:
        raise HTTPException(status_code=404, detail="功能不存在")
    return [serialize_case(c) for c in func.cases]


@router.post("/functions/{func_id}/cases")
def create_case(func_id: int, data: dict, db: Session = Depends(get_db)):
    func = db.query(TestFunction).filter(TestFunction.id == func_id).first()
    if not func:
        raise HTTPException(status_code=404, detail="功能不存在")

    case = TestCase(
        function_id=func_id,
        name=data.get("name", ""),
        description=data.get("description"),
        case_type=data.get("case_type", "positive"),
        focus_point=data.get("focus_point"),
        preconditions=data.get("preconditions"),
        expected_result=data.get("expected_result"),
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return serialize_case(case)


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
    return serialize_case(case)


@router.delete("/cases/{case_id}")
def delete_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    db.delete(case)
    db.commit()
    return {"message": "删除成功"}


# ============ 套件关联功能 ============

@router.get("/suites/{suite_id}/functions")
def list_suite_functions(suite_id: int, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="套件不存在")
    return [serialize_function(f, include_cases=True) for f in suite.functions]


@router.post("/suites/{suite_id}/functions")
def add_functions_to_suite(suite_id: int, data: dict, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="套件不存在")

    func_ids = data.get("function_ids", [])
    added = 0
    for func_id in func_ids:
        exists = db.query(TestSuiteFunction).filter(
            TestSuiteFunction.suite_id == suite_id,
            TestSuiteFunction.function_id == func_id
        ).first()
        if not exists:
            db.add(TestSuiteFunction(suite_id=suite_id, function_id=func_id))
            added += 1
    db.commit()
    return {"message": f"添加了{added}个功能", "added": added}


@router.delete("/suites/{suite_id}/functions/{func_id}")
def remove_function_from_suite(suite_id: int, func_id: int, db: Session = Depends(get_db)):
    assoc = db.query(TestSuiteFunction).filter(
        TestSuiteFunction.suite_id == suite_id,
        TestSuiteFunction.function_id == func_id
    ).first()
    if not assoc:
        raise HTTPException(status_code=404, detail="关联关系不存在")
    db.delete(assoc)
    db.commit()
    return {"message": "移除成功"}
