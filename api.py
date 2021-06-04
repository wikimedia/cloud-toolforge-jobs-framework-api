from flask import Flask
from flask_restful import Api
from tjf.run import Run
from tjf.show import Show
from tjf.list import List
from tjf.delete import Delete
from tjf.flush import Flush
from tjf.containers import Containers

app = Flask(__name__)
api = Api(app)

api.add_resource(Run, "/api/v1/run/")
api.add_resource(Show, "/api/v1/show/<name>")
api.add_resource(List, "/api/v1/list/")
api.add_resource(Delete, "/api/v1/delete/<name>")
api.add_resource(Flush, "/api/v1/flush/")
api.add_resource(Containers, "/api/v1/containers/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
