from nameko.rpc import rpc
from database import SessionLocal

from models import UnitAkademik

class MasterService:
    name = "master_service"

    @rpc
    def create_unit(self, name, type, parent_id=None):
        db = SessionLocal()
        try:
            unit = UnitAkademik(
                unit_name = name,
                unit_type = type,
                parent_id = parent_id
            )
            db.add(unit)
            db.commit()
            db.refresh(unit)

            return {
                "id": unit.unit_id,
                "name": unit.unit_name,
                "type": unit.unit_type
            }
        finally:
            db.close()
    
    @rpc
    def get_units(self):
        db = SessionLocal()
        units = db.query(UnitAkademik).all()

        try:
            return [
                {
                    "id": u.unit_id,
                    "name": u.unit_name,
                    "type": u.unit_type,
                    "parent_id": u.parent_id
                }
                for u in units
            ]
        finally:
            db.close()