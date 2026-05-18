from datetime import datetime
from sqlalchemy import func
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.database import Base


class TestSuite(Base):
    __tablename__ = "test_suites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    functions = relationship("TestFunction", secondary="test_suite_functions", back_populates="suites")
    scripts = relationship("TestScript", back_populates="suite", cascade="all, delete-orphan")
    executions = relationship("TestExecution", back_populates="suite", cascade="all, delete-orphan")


class TestFunction(Base):
    __tablename__ = "test_functions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment="功能名称")
    description = Column(Text, comment="功能描述")
    url = Column(String(500), comment="功能URL")
    status = Column(String(50), default="active", comment="状态")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cases = relationship("TestCase", back_populates="function", cascade="all, delete-orphan")
    suites = relationship("TestSuite", secondary="test_suite_functions", back_populates="functions")


class TestSuiteFunction(Base):
    __tablename__ = "test_suite_functions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    suite_id = Column(Integer, ForeignKey("test_suites.id", ondelete="CASCADE"), nullable=False)
    function_id = Column(Integer, ForeignKey("test_functions.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    function_id = Column(Integer, ForeignKey("test_functions.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False, comment="用例名称")
    description = Column(Text, comment="用例描述")
    case_type = Column(String(20), default="positive", comment="正例/反例")
    focus_point = Column(Text, comment="关注点")
    preconditions = Column(Text, comment="前提条件")
    expected_result = Column(Text, comment="预期结果")
    actual_result = Column(Text, comment="测试结果")
    executed_at = Column(DateTime, comment="执行时间")
    issues = Column(Text, comment="存在问题")
    status = Column(String(20), default="pending", comment="状态")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    function = relationship("TestFunction", back_populates="cases")


class TestScript(Base):
    __tablename__ = "test_scripts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    suite_id = Column(Integer, ForeignKey("test_suites.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, default=1)
    script_content = Column(Text, nullable=False)
    is_current = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    suite = relationship("TestSuite", back_populates="scripts")


class TestExecution(Base):
    __tablename__ = "test_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    suite_id = Column(Integer, ForeignKey("test_suites.id", ondelete="CASCADE"), nullable=False)
    script_id = Column(Integer, ForeignKey("test_scripts.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(20), default="pending")
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)
    total_cases = Column(Integer, default=0)  # 总用例数
    completed_cases = Column(Integer, default=0)  # 已完成用例数
    passed_cases = Column(Integer, default=0)  # 通过用例数
    failed_cases = Column(Integer, default=0)  # 失败用例数
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    suite = relationship("TestSuite", back_populates="executions")
    screenshots = relationship("TestScreenshot", back_populates="execution", cascade="all, delete-orphan")
    case_results = relationship("TestCaseResult", back_populates="execution", cascade="all, delete-orphan")


class TestScreenshot(Base):
    __tablename__ = "test_screenshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(Integer, ForeignKey("test_executions.id", ondelete="CASCADE"), nullable=False)
    case_id = Column(Integer, ForeignKey("test_cases.id", ondelete="SET NULL"), nullable=True)
    step_number = Column(Integer, nullable=False)
    step_description = Column(Text, nullable=True)
    screenshot_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    execution = relationship("TestExecution", back_populates="screenshots")


class TestCaseResult(Base):
    """执行结果-用例关联表"""
    __tablename__ = "test_case_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(Integer, ForeignKey("test_executions.id", ondelete="CASCADE"), nullable=False)
    case_id = Column(Integer, ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False)  # passed / failed / error
    error_message = Column(Text, nullable=True)
    duration = Column(Integer, nullable=True)  # 毫秒
    screenshot_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    execution = relationship("TestExecution", back_populates="case_results")
    case = relationship("TestCase")


class ModelConfig(Base):
    __tablename__ = "model_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    provider = Column(String(100), nullable=False)
    base_url = Column(String(500), nullable=True)
    api_key = Column(String(500), nullable=True)
    model_name = Column(String(255), nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class UploadedDocument(Base):
    __tablename__ = "uploaded_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=True)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TestFunctionCase(Base):
    """功能-用例关联表"""
    __tablename__ = "test_function_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    function_id = Column(Integer, ForeignKey("test_functions.id"), nullable=False)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
