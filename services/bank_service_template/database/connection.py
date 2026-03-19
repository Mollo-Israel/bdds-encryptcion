from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from pymongo import MongoClient

from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from cassandra.query import dict_factory

from config import DB_URL, DB_ENGINE

Base = declarative_base()

engine = None
SessionLocal = None
mongo_client = None
mongo_db = None
cassandra_cluster = None
cassandra_session = None

if DB_ENGINE == "mongodb":
    parsed = urlparse(DB_URL)
    db_name = parsed.path.lstrip("/")
    mongo_client = MongoClient(DB_URL)
    mongo_db = mongo_client[db_name]

elif DB_ENGINE == "cassandra":
    parsed = urlparse(DB_URL)
    host = parsed.hostname or "localhost"
    port = parsed.port or 9042
    keyspace = parsed.path.lstrip("/")

    cassandra_profile = ExecutionProfile(
        consistency_level=ConsistencyLevel.ONE,
        request_timeout=30,
        row_factory=dict_factory,
    )

    cassandra_cluster = Cluster(
        [host],
        port=port,
        execution_profiles={EXEC_PROFILE_DEFAULT: cassandra_profile},
        connect_timeout=30,
        control_connection_timeout=30,
    )

    cassandra_session = cassandra_cluster.connect(keyspace)

else:
    connect_args = {"check_same_thread": False} if "sqlite" in DB_URL else {}
    engine = create_engine(DB_URL, connect_args=connect_args)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    if DB_ENGINE == "mongodb":
        yield mongo_db
    elif DB_ENGINE == "cassandra":
        yield cassandra_session
    else:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()


def init_db():
    if DB_ENGINE == "mongodb":
        if "cuentas" not in mongo_db.list_collection_names():
            mongo_db.create_collection("cuentas")

        mongo_db["cuentas"].create_index("cuenta_id", unique=True)
        mongo_db["cuentas"].create_index("banco_id")
        mongo_db["cuentas"].create_index("numero_cuenta")

    elif DB_ENGINE == "cassandra":
        cassandra_session.execute("""
            CREATE TABLE IF NOT EXISTS cuentas (
                cuenta_id bigint PRIMARY KEY,
                banco_id int,
                ci text,
                nombre text,
                apellido text,
                numero_cuenta text,
                saldo_usd_encrypted text,
                saldo_bs decimal,
                codigo_verificacion text,
                fecha_conversion timestamp,
                created_at timestamp,
                updated_at timestamp
            )
        """)

    else:
        from models.account import AccountORM  # noqa: F401
        Base.metadata.create_all(bind=engine)