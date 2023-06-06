from flask import Flask
from flask_restful import Resource
import pytest
from toolforge_weld.errors import ToolforgeUserError

from tjf.app import TjfApi
from tjf.error import TjfClientError, TjfError


@pytest.fixture()
def error_generating_app():
    class ErrorGeneratingResource(Resource):
        def get(self):
            raise TjfClientError("Invalid foo", data={"options": ["bar", "baz"]})

        def post(self):
            cause = Exception("Failed to contact foo")
            raise TjfError("Failed to create job") from cause

        def put(self):
            cause = Exception("Test")
            error = ToolforgeUserError("Welding failed")
            error.context = {"aaa": "bbb"}
            raise error from cause

    app = Flask(__name__)
    api = TjfApi(app)

    api.add_resource(ErrorGeneratingResource, "/error")

    yield app.test_client()


def test_TjfApi_error_handling(error_generating_app):
    response = error_generating_app.get("/error")
    assert response.status_code == 400
    assert response.json == {"message": "Invalid foo", "data": {"options": ["bar", "baz"]}}


def test_TjfApi_error_handling_context(error_generating_app):
    response = error_generating_app.post("/error")
    assert response.status_code == 500
    assert response.json["message"] == "Failed to create job (Failed to contact foo)"


def test_TjfApi_error_handling_weld_errors(error_generating_app):
    response = error_generating_app.put("/error")
    assert response.status_code == 400
    assert response.json == {"message": "Welding failed (Test)", "data": {"aaa": "bbb"}}
