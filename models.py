from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class UnitAkademik(Base):
    __tablename__ = "academic_units"

    unit_id = Column(Integer, primary_key=True)
    unit_name = Column(String, nullable=False)
    unit_type = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("academic_units.unit_id"), nullable=True)

    parent = relationship("UnitAkademik", remote_side=[unit_id])