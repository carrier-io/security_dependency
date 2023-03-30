from flask import request
from flask_restful import Resource
from sqlalchemy import and_

from ...models.tests import SecurityDependencyTests


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        query_result = SecurityDependencyTests.query.with_entities(SecurityDependencyTests.description).filter(
            SecurityDependencyTests.name == request.args.get("name"),
            SecurityDependencyTests.project_id == project.id
        ).distinct(SecurityDependencyTests.description).all()
        return [i[0] for i in query_result], 200