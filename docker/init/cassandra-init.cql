CREATE KEYSPACE IF NOT EXISTS banco_pyme_comunidad
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

CREATE KEYSPACE IF NOT EXISTS banco_desarrollo_productivo
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

CREATE KEYSPACE IF NOT EXISTS banco_nacion_argentina
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
