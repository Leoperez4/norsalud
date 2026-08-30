import pymysql

# Django espera el driver mysqlclient; PyMySQL lo imita para no depender
# de compilar nada en Windows (evita necesitar Visual C++ Build Tools).
pymysql.install_as_MySQLdb()
