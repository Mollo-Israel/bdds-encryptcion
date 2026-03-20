from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from pymongo import MongoClient

from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster, ExecutionProfile, EXEC_PROFILE_DEFAULT
from cassandra.query import dict_factory

from neo4j import GraphDatabase

from config import DB_URL, DB_ENGINE

Base = declarative_base()

engine = None
SessionLocal = None
mongo_client = None
mongo_db = None
cassandra_cluster = None
cassandra_session = None
neo4j_driver = None

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

elif DB_ENGINE == "neo4j":
    # URL esperada: neo4j://neo4j:admin123@localhost:7687
    parsed = urlparse(DB_URL)
    neo4j_uri = f"neo4j://{parsed.hostname}:{parsed.port or 7687}"
    neo4j_user = parsed.username or "neo4j"
    neo4j_password = parsed.password or "admin123"
    neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

else:
    connect_args = {"check_same_thread": False} if "sqlite" in DB_URL else {}
    engine = create_engine(DB_URL, connect_args=connect_args)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    if DB_ENGINE == "mongodb":
        yield mongo_db
    elif DB_ENGINE == "cassandra":
        yield cassandra_session
    elif DB_ENGINE == "neo4j":
        session = neo4j_driver.session(database="neo4j")
        try:
            yield session
        finally:
            session.close()
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

    elif DB_ENGINE == "neo4j":
        # Modelo de grafos: (Cliente)-[:TIENE_CUENTA]->(Cuenta)
        with neo4j_driver.session(database="neo4j") as session:
            session.run(
                "CREATE CONSTRAINT cuenta_id_unique IF NOT EXISTS "
                "FOR (c:Cuenta) REQUIRE c.cuenta_id IS UNIQUE"
            )
            session.run(
                "CREATE CONSTRAINT cliente_ci_unique IF NOT EXISTS "
                "FOR (cl:Cliente) REQUIRE cl.ci IS UNIQUE"
            )

    else:
        from models.account import AccountORM  # noqa: F401
        Base.metadata.create_all(bind=engine)
