from datetime import datetime
from typing import Optional

from sqlalchemy.sql import func, LABEL_STYLE_TABLENAME_PLUS_COL
from sqlalchemy import desc

from ..models.tests import SecurityDependencyTests
from ..models.pd.security_test import SecurityTestParams, SecurityTestCommon
from ..models.reports import SecurityReport
from ..models.results import SecurityDependencyResults
from ..utils import run_test

from tools import rpc_tools

from pylon.core.tools import web
from pydantic import ValidationError

from ...shared.models.pd.test_parameters import TestParamsBase
from pylon.core.tools import log


class RPC:
    @web.rpc('security_dependency_results_or_404', 'results_or_404')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def results_or_404(self, run_id: int) -> SecurityDependencyResults:
        return SecurityDependencyResults.query.get_or_404(run_id)

    @web.rpc('security_dependency_overview_data', 'overview_data')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def overview_data(self, project_id: int) -> dict:
        queries = [
            func.sum(getattr(SecurityDependencyResults, i)).label(f'sum_{i}')
            for i in SecurityReport.SEVERITY_CHOICES.keys()
        ]
        q = SecurityDependencyResults.query.with_entities(
            *queries
        ).filter(
            SecurityDependencyResults.project_id == project_id,
        )
        return dict(zip([i['name'] for i in q.column_descriptions], q.first()))

    @web.rpc('infrastructure_security_get_tests')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def security_get_tests(self, project_id: int) -> dict:
        return SecurityDependencyTests.query.filter_by(project_id=project_id).all()

    @web.rpc('infrastructure_security_get_reports')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def security_get_reports(
            self, project_id: int,
            start_time: datetime | None = None,
            end_time: datetime | None = None,
            unique: bool = False,
    ) -> list[SecurityDependencyResults]:
        """ Gets all reports filtered by time"""

        def _get_unique_reports(objects: list[SecurityDependencyResults]) -> list[SecurityDependencyResults]:
            unique_combinations = {}
            for obj in objects:
                # combination = (obj.test_uid, obj.environment, obj.type)
                combination = (obj.test_uid, obj.environment)
                stored_obj = unique_combinations.get(combination)
                if stored_obj is None or obj.start_date > stored_obj.start_date:
                    unique_combinations[combination] = obj

            return list(unique_combinations.values())

        query = SecurityDependencyResults.query.filter(
            SecurityDependencyResults.project_id == project_id,
        ).order_by(
            desc(SecurityDependencyResults.start_date)
        )

        if start_time:
            query = query.filter(SecurityDependencyResults.start_date >= start_time.isoformat())
        #
        # if end_time:
        #     query = query.filter(SecurityDependencyResults.end_time <= end_time.isoformat())

        reports = query.all()
        if unique:
            reports = _get_unique_reports(reports)

        return reports

    @web.rpc('security_dependency_test_create_test_parameters', 'parse_test_parameters')
    @rpc_tools.wrap_exceptions(ValidationError)
    def parse_test_parameters(self, data: list, **kwargs) -> dict:
        pd_object = SecurityTestParams(test_parameters=data)
        return pd_object.dict(**kwargs)

    @web.rpc('security_dependency_test_create_common_parameters', 'parse_common_test_parameters')
    @rpc_tools.wrap_exceptions(ValidationError)
    def parse_common_test_parameters(self, project_id: int, name: str, description: str, source: dict, **kwargs) -> dict:
        project = self.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        pd_object = SecurityTestCommon(
            project_id=project.id,
            project_name=project.name,
            name=name,
            description=description,
            source=source,
        )
        return pd_object.dict(**kwargs)

    @web.rpc('security_dependency_run_scheduled_test', 'run_scheduled_test')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def run_scheduled_test(self, test_id: int, test_params: list) -> dict:
        test = SecurityDependencyTests.query.filter(SecurityDependencyTests.id == test_id).one()
        test_params_schedule_pd = TestParamsBase(test_parameters=test_params)
        test_params_existing_pd = SecurityTestParams.from_orm(test)
        test_params_existing_pd.update(test_params_schedule_pd)
        test.__dict__.update(test_params_existing_pd.dict())
        return run_test(test)

    @web.rpc('security_dependency_job_type_by_uid')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def job_type_by_uid(self, project_id: int, test_uid: str) -> Optional[str]:
        if SecurityDependencyTests.query.filter(
            SecurityDependencyTests.get_api_filter(project_id, test_uid)
        ).first():
            return 'dependency'
