import importlib.util
import sys
import inspect
from models.database import db, ApiScript
from pathlib import Path
from core.logging import logs


def refresh_db(FABRIC_DIR):
    fabric_path = Path(FABRIC_DIR)

    # Scripts trouvés sur le FS : {basename: path_rel}
    scripts_in_fs = {}
    for p in fabric_path.rglob("*.py"):
        if p.is_file() and p.name != "core.py":
            script_id = p.stem
            script_path_rel = str(p.relative_to(fabric_path))
            
            # Dynamically load the module and check for entrypoint decorator
            try:
                spec = importlib.util.spec_from_file_location(script_id, p)
                module = importlib.util.module_from_spec(spec)
                sys.modules[script_id] = module
                spec.loader.exec_module(module)

                has_entrypoint = False
                for name, obj in inspect.getmembers(module):
                    if inspect.isfunction(obj) and hasattr(obj, '_is_entrypoint') and obj._is_entrypoint:
                        has_entrypoint = True
                        break
                
                if has_entrypoint:
                    scripts_in_fs[script_id] = script_path_rel
                else:
                    logs(f"Script {script_id} ignored: no entrypoint decorator found.", status='info', component='system')

            except Exception as e:
                logs(f"Error loading script {script_id} from {p}: {e}", status='error', component='system')
                continue

    # Scripts en DB sous forme {id: path}
    db_rows = db.session.query(ApiScript.id, ApiScript.path).all()
    scripts_in_db = {row[0]: row[1] for row in db_rows}

    # Ajouts : id présent sur FS mais pas en DB
    to_add = scripts_in_fs.keys() - scripts_in_db.keys()

    # Suppressions : id présent en DB mais plus sur FS
    to_delete = scripts_in_db.keys() - scripts_in_fs.keys()

    # Mises à jour : id présent mais chemin différent
    to_update = {
        script_id
        for script_id in (scripts_in_fs.keys() & scripts_in_db.keys())
        if scripts_in_fs[script_id] != scripts_in_db[script_id]
    }

    try:
        # Ajout
        for script_id in to_add:
            db.session.add(ApiScript(id=script_id, path=scripts_in_fs[script_id], is_online=False))
            logs(f"api {script_id} ajouté dans la base", status='info', component='system')

        # Suppression
        if to_delete:
            db.session.query(ApiScript).filter(ApiScript.id.in_(list(to_delete))).delete(synchronize_session=False)
            logs(f"Suppression des api obsolète dans la DB : {', '.join(to_delete)}", status='info', component='system')

        # Mise à jour du chemin
        for script_id in to_update:
            logs(f"api {script_id} mise à jour dans la base", status='info', component='system')
            script_obj = db.session.query(ApiScript).get(script_id)
            script_obj.path = scripts_in_fs[script_id]

        db.session.commit()
    except Exception as err:
        logs(f"Erreur lors de la synchronisation des scripts", status='error', component='system', result=err)
        raise