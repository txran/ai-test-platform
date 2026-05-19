-- AI 测试平台 - 数据库建表语句
-- 数据库: MySQL 8.0
-- 字符集: utf8mb4

CREATE DATABASE IF NOT EXISTS ai_test_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ai_test_platform;

-- LLM 模型配置
CREATE TABLE model_configs (
    id INTEGER NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    base_url VARCHAR(500),
    api_key VARCHAR(500),
    model_name VARCHAR(255) NOT NULL,
    is_default BOOL,
    created_at DATETIME,
    PRIMARY KEY (id)
);

-- 功能模块
CREATE TABLE test_functions (
    id INTEGER NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL COMMENT '功能名称',
    description TEXT COMMENT '功能描述',
    url VARCHAR(500) COMMENT '功能URL',
    status VARCHAR(50) COMMENT '状态',
    created_at DATETIME,
    updated_at DATETIME,
    PRIMARY KEY (id)
);

-- 测试场景
CREATE TABLE test_suites (
    id INTEGER NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50),
    created_at DATETIME,
    updated_at DATETIME,
    PRIMARY KEY (id)
);

-- 场景-功能关联
CREATE TABLE test_suite_functions (
    id INTEGER NOT NULL AUTO_INCREMENT,
    suite_id INTEGER NOT NULL,
    function_id INTEGER NOT NULL,
    created_at DATETIME,
    PRIMARY KEY (id),
    FOREIGN KEY(suite_id) REFERENCES test_suites (id) ON DELETE CASCADE,
    FOREIGN KEY(function_id) REFERENCES test_functions (id) ON DELETE CASCADE
);

-- 测试用例
CREATE TABLE test_cases (
    id INTEGER NOT NULL AUTO_INCREMENT,
    function_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL COMMENT '用例名称',
    description TEXT COMMENT '用例描述',
    case_type VARCHAR(20) COMMENT '正例/反例',
    focus_point TEXT COMMENT '关注点',
    preconditions TEXT COMMENT '前提条件',
    expected_result TEXT COMMENT '预期结果',
    actual_result TEXT COMMENT '测试结果',
    executed_at DATETIME COMMENT '执行时间',
    issues TEXT COMMENT '存在问题',
    status VARCHAR(20) COMMENT '状态',
    created_at DATETIME,
    updated_at DATETIME,
    PRIMARY KEY (id),
    FOREIGN KEY(function_id) REFERENCES test_functions (id) ON DELETE CASCADE
);

-- 功能-用例关联
CREATE TABLE test_function_cases (
    id INTEGER NOT NULL AUTO_INCREMENT,
    function_id INTEGER NOT NULL,
    test_case_id INTEGER NOT NULL,
    created_at DATETIME,
    PRIMARY KEY (id),
    FOREIGN KEY(function_id) REFERENCES test_functions (id),
    FOREIGN KEY(test_case_id) REFERENCES test_cases (id)
);

-- 测试脚本（版本管理）
CREATE TABLE test_scripts (
    id INTEGER NOT NULL AUTO_INCREMENT,
    suite_id INTEGER NOT NULL,
    version INTEGER,
    script_content TEXT NOT NULL,
    is_current BOOL,
    created_at DATETIME,
    PRIMARY KEY (id),
    FOREIGN KEY(suite_id) REFERENCES test_suites (id) ON DELETE CASCADE
);

-- 执行记录
CREATE TABLE test_executions (
    id INTEGER NOT NULL AUTO_INCREMENT,
    suite_id INTEGER NOT NULL,
    script_id INTEGER,
    status VARCHAR(20),
    start_time DATETIME,
    end_time DATETIME,
    duration INTEGER,
    total_cases INTEGER,
    completed_cases INTEGER,
    passed_cases INTEGER,
    failed_cases INTEGER,
    error_message TEXT,
    created_at DATETIME,
    PRIMARY KEY (id),
    FOREIGN KEY(suite_id) REFERENCES test_suites (id) ON DELETE CASCADE,
    FOREIGN KEY(script_id) REFERENCES test_scripts (id) ON DELETE SET NULL
);

-- 用例执行结果
CREATE TABLE test_case_results (
    id INTEGER NOT NULL AUTO_INCREMENT,
    execution_id INTEGER NOT NULL,
    case_id INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    duration INTEGER,
    screenshot_path VARCHAR(500),
    created_at DATETIME,
    PRIMARY KEY (id),
    FOREIGN KEY(execution_id) REFERENCES test_executions (id) ON DELETE CASCADE,
    FOREIGN KEY(case_id) REFERENCES test_cases (id) ON DELETE CASCADE
);

-- 截图记录
CREATE TABLE test_screenshots (
    id INTEGER NOT NULL AUTO_INCREMENT,
    execution_id INTEGER NOT NULL,
    case_id INTEGER,
    step_number INTEGER NOT NULL,
    step_description TEXT,
    screenshot_path VARCHAR(500),
    created_at DATETIME,
    PRIMARY KEY (id),
    FOREIGN KEY(execution_id) REFERENCES test_executions (id) ON DELETE CASCADE,
    FOREIGN KEY(case_id) REFERENCES test_cases (id) ON DELETE SET NULL
);

-- 上传文档
CREATE TABLE uploaded_documents (
    id INTEGER NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50),
    file_path VARCHAR(500),
    file_size INTEGER,
    created_at DATETIME,
    PRIMARY KEY (id)
);
