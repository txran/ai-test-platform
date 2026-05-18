from sqlalchemy import text
from app.models.database import engine
from app.models.models import *
from app.models.database import Base

with engine.connect() as conn:
    conn.execute(text('SET FOREIGN_KEY_CHECKS = 0'))
    for t in ['test_screenshots','test_executions','test_case_history','test_scripts','test_cases','uploaded_documents','model_configs','test_case_groups']:
        conn.execute(text(f'DROP TABLE IF EXISTS {t}'))
    conn.execute(text('SET FOREIGN_KEY_CHECKS = 1'))
    conn.commit()

Base.metadata.create_all(bind=engine)

with engine.connect() as conn:
    result = conn.execute(text('SHOW TABLES'))
    tables = [row[0] for row in result]
    print('Tables:', tables)
print('DONE')
