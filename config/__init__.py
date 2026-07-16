# PyMySQL como alternativa a mysqlclient (útil en Windows).
# Si usas mysqlclient puedes comentar este bloque por completo.
try:
    import pymysql  # noqa

    pymysql.install_as_MySQLdb()
except ImportError:
    # mysqlclient está instalado; no se requiere PyMySQL.
    pass
