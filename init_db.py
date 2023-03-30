from tools import db


def init_db():
    from .models.tests import SecurityDependencyTests
    from .models.results import SecurityDependencyResults
    from .models.thresholds import SecurityThresholds
    from .models.details import SecurityDetails
    from .models.reports import SecurityReport
    db.Base.metadata.create_all(bind=db.engine)

