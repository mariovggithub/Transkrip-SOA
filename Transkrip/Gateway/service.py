import json

from marshmallow import ValidationError
from nameko import config
from nameko.exceptions import BadRequest
from nameko.rpc import RpcProxy
from werkzeug import Response

from gateway.entrypoints import http

class Transkrip(object):
    name = "transkrip_service"

    # RPC client untuk komunikasi dengan service PRS
    prs_rpc = RpcProxy("prs_service")

    @http("POST", "/push_prs_ke_krs")
    def push_prs_ke_krs(self, request):
        """
        Endpoint HTTP untuk menerima push PRS dari service PRS.
        Menerima JSON body dengan format: {"id_prs": 123}
        Dipanggil oleh service PRS setelah dosen wali approve PRS mahasiswa.
        """
        try:
            data = request.get_json()
            id_prs = data["id_prs"]
        except (json.JSONDecodeError, KeyError) as e:
            raise BadRequest(f"Invalid request body: {e}")

        # Panggil RPC ke service PRS untuk proses lebih lanjut
        try:
            self.prs_rpc.proses_prs_ke_krs(id_prs)
            return Response("PRS diterima dan diproses", status=200)
        except Exception as e:
            raise BadRequest(f"Gagal memproses PRS: {e}")
    
    @http