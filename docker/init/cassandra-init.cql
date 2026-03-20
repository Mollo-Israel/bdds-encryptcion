CREATE KEYSPACE IF NOT EXISTS banco_pyme_comunidad
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

-- banco_desarrollo_productivo (banco 13) migrado a Neo4j

CREATE KEYSPACE IF NOT EXISTS banco_nacion_argentina
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
