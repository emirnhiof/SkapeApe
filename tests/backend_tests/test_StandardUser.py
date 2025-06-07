import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base

from backend.model.LockerRoom import LockerRoom
from backend.model.Locker import Locker
from backend.model.StandardUser import create_standard_user, reserve_locker, unlock_locker
from backend.model.LockerLog import LockerLog

# Setup in-memory SQLite database for each test
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.mark.asyncio
async def test_unlock_locker_logs_numeric_id(db):
    # create room and locker
    room = LockerRoom(name="TestRoom")
    db.add(room)
    db.commit()
    db.refresh(room)

    locker = Locker(locker_room_id=room.id, status="Ledig", combi_id=f"{room.name}-1")
    db.add(locker)
    db.commit()
    db.refresh(locker)

    # create user and reserve locker
    user = await create_standard_user("RFID123", db)
    await reserve_locker(user.id, room.id, db)

    # unlock locker and check log entry
    await unlock_locker(user.id, db)

    log = db.query(LockerLog).order_by(LockerLog.id.desc()).first()
    assert isinstance(log.locker_id, str)
    assert log.locker_id == locker.combi_id
