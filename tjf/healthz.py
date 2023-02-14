from flask_restful import Resource


class Healthz(Resource):
    def get(self):
        return "OK"
