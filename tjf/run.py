from common.k8sclient import KubectlClient
from tjf.job import Job
from flask_restful import Resource, Api, reqparse
from tjf.containers import validate_container_type

# arguments that the API understands
parser = reqparse.RequestParser()
parser.add_argument('cmd')
parser.add_argument('type')
parser.add_argument('schedule')
parser.add_argument('continuous')
parser.add_argument('name')

class Run(Resource):
    def post(self):
        args = parser.parse_args()

        # TODO: figure this out from the client TLS cert
        ns = "tool-test"
        username = "test"
        kubeconfig_file = "/data/project/test/.kube/config"

        if not validate_container_type(args.type):
            return "Invalid container type", 500

        # TODO: add support for schedule & continuous
        job = Job(args.cmd, args.type, args.name, ns, username, status=None)

        # TODO: replace this with proper k8sclient usage instead of kubectl
        return KubectlClient.kubectl("apply", job.get_k8s_object())
