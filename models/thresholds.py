from sqlalchemy import String, Column, Integer, JSON
from tools import db_tools, db


class SecurityThresholds(db_tools.AbstractBaseMixin, db.Base):
    __tablename__ = "security_dependency_thresholds"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, unique=False, nullable=False)
    test_uid = Column(String, unique=True, nullable=False)
    params = Column(JSON, nullable=False)