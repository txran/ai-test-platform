from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.database import get_db
from app.models.models import TestSuite, TestSuiteFunction, TestFunctionCase
from app.utils import format_datetime
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api", tags=["suites"])


def serialize_suite(suite: TestSuite, cases_count: int = 0):
    data = {
        "id": suite.id,
        "name": suite.name,
        "description": suite.description,
        "status": suite.status,
        "cases_count": cases_count,
        "created_at": format_datetime(suite.created_at),
        "updated_at": format_datetime(suite.updated_at),
    }
    return data


class SuiteCreate(BaseModel):
    name: str
    description: Optional[str] = None


class SuiteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


@router.post("/suites")
def create_suite(body: SuiteCreate, db: Session = Depends(get_db)):
    suite = TestSuite(name=body.name, description=body.description)
    db.add(suite)
    db.commit()
    db.refresh(suite)
    return serialize_suite(suite)


@router.get("/suites")
def list_suites(db: Session = Depends(get_db)):
    suites = db.query(TestSuite).order_by(TestSuite.created_at.desc()).all()
    
    result = []
    for suite in suites:
        # 计算该套件的用例数
        cases_count = (
            db.query(func.count(TestFunctionCase.id))
            .join(TestSuiteFunction, TestSuiteFunction.function_id == TestFunctionCase.function_id)
            .filter(TestSuiteFunction.suite_id == suite.id)
            .scalar()
        ) or 0
        result.append(serialize_suite(suite, cases_count))
    
    return result


@router.get("/suites/{suite_id}")
def get_suite(suite_id: int, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="套件不存在")

    # 从关联的功能中获取用例
    cases = []
    for func in suite.functions:
        for c in func.cases:
            cases.append({
                "id": c.id,
                "function_id": c.function_id,
                "name": c.name,
                "case_type": c.case_type,
                "description": c.description,
                "expected_result": c.expected_result,
                "actual_result": c.actual_result,
                "status": c.status,
                "created_at": format_datetime(c.created_at),
                "updated_at": format_datetime(c.updated_at),
            })

    result = serialize_suite(suite)
    result["cases"] = cases
    result["functions"] = [{"id": f.id, "name": f.name} for f in suite.functions]
    result["test_cases_count"] = len(cases)
    return result


@router.put("/suites/{suite_id}")
def update_suite(suite_id: int, body: SuiteUpdate, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="套件不存在")

    if body.name is not None:
        suite.name = body.name
    if body.description is not None:
        suite.description = body.description
    if body.status is not None:
        suite.status = body.status

    db.commit()
    db.refresh(suite)
    return serialize_suite(suite)


@router.delete("/suites/{suite_id}")
def delete_suite(suite_id: int, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="套件不存在")
    db.delete(suite)
    db.commit()
    return {"message": "删除成功"}
