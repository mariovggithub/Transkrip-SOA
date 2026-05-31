from nameko.rpc import rpc
from database import SessionLocal

class MasterService:
    name = "master-service"

    # @rpc
    # def hello(self, name):
    #     return f"Hello {name}"

    @rpc
    def test_db(self):
        db = SessionLocal()
        return "DB Connected"