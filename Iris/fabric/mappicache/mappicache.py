from core.decorator import entrypoint
from pony.orm import Database, Required, db_session, select, PrimaryKey

# Définition de la base de données
db = Database()

class Codeapp(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    quadrigram = Required(str)


# Configuration de la base de données
db.bind(provider='sqlite', filename='mappicache.db', create_db=True)
db.generate_mapping(create_tables=True)


@entrypoint
def index(quadri):
	#request.custom.role = readonly
	#request.custom.table = ['cortex', 'checkmk']
	#request.args
	#request.token

	if quadri:
		with db_session:
			exist = db.Codeapp.get(quadrigram=quadri.upper())
			if exist:
				return {"success":True}
			else:
				return {"success":False}
	else:
		return {"error": "Bad request"}
