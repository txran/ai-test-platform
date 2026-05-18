from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import TestExecution, TestScreenshot, TestCaseResult, TestCase
from app.utils import format_datetime

router = APIRouter(prefix="/api", tags=["executions"])


def serialize_execution(ex: TestExecution, include_screenshots: bool = False, include_case_results: bool = False):
    data = {
        "id": ex.id,
        "suite_id": ex.suite_id,
        "script_id": ex.script_id,
        "status": ex.status,
        "start_time": format_datetime(ex.start_time),
        "end_time": format_datetime(ex.end_time),
        "duration": ex.duration,
        "total_cases": ex.total_cases or 0,
        "completed_cases": ex.completed_cases or 0,
        "passed_cases": ex.passed_cases or 0,
        "failed_cases": ex.failed_cases or 0,
        "error_message": ex.error_message,
        "created_at": format_datetime(ex.created_at),
    }
    if include_screenshots:
        data["screenshots"] = [
            {
                "id": s.id,
                "execution_id": s.execution_id,
                "case_id": s.case_id,
                "step_number": s.step_number,
                "step_description": s.step_description,
                "screenshot_path": s.screenshot_path.replace("/home/tang/ai-test-platform", "http://192.168.5.200:8000") if s.screenshot_path else None,
                "created_at": format_datetime(s.created_at),
            }
            for s in sorted(ex.screenshots, key=lambda x: x.step_number)
        ]
    if include_case_results:
        data["case_results"] = [
            {
                "id": r.id,
                "case_id": r.case_id,
                "case_name": r.case.name if r.case else "-",
                "status": r.status,
                "error_message": r.error_message,
                "duration": r.duration,
                "created_at": format_datetime(r.created_at),
            }
            for r in ex.case_results
        ]
    return data


@router.get("/executions")
def list_all_executions(db: Session = Depends(get_db)):
    execs = db.query(TestExecution).order_by(TestExecution.created_at.desc()).limit(50).all()
    return [serialize_execution(e) for e in execs]


@router.get("/executions/{execution_id}")
def get_execution(execution_id: int, db: Session = Depends(get_db)):
    ex = db.query(TestExecution).filter(TestExecution.id == execution_id).first()
    if not ex:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    return serialize_execution(ex, include_screenshots=True, include_case_results=True)


@router.get("/executions/{execution_id}/screenshots")
def get_execution_screenshots(execution_id: int, db: Session = Depends(get_db)):
    """获取执行的截图列表"""
    ex = db.query(TestExecution).filter(TestExecution.id == execution_id).first()
    if not ex:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    
    screenshots = [
        {
            "id": s.id,
            "execution_id": s.execution_id,
            "case_id": s.case_id,
            "step_number": s.step_number,
            "step_description": s.step_description,
            "screenshot_path": s.screenshot_path.replace("/home/tang/ai-test-platform", "http://192.168.5.200:8000") if s.screenshot_path else None,
            "created_at": format_datetime(s.created_at),
        }
        for s in sorted(ex.screenshots, key=lambda x: x.step_number)
    ]
    
    return {"screenshots": screenshots}
