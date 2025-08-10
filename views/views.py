from flask import Blueprint, render_template, jsonify, request, Response
from models.database import ApiScript, User
from views.utils import construct_context
import os
import importlib
import inspect
import __main__
import time
import json
from core.logging import logs
from views.api_views import failed_api

route_bp = Blueprint('root', __name__, url_prefix='/')


@route_bp.route('/stream')
def stream():
    def event_stream():
        while True:
            time.sleep(0.5)
            if len(__main__.backend.notification_queue):
                msg, type_ = __main__.backend.notification_queue.pop()
                data = json.dumps({"message": msg, "type": type_})
                yield f"data: {data}\n\n"
    return Response(event_stream(), mimetype="text/event-stream")


@route_bp.route('/')
def index():
    if __main__.backend.debug:
        logs(f"Accès à la page home", status='debug', component='web', request_info=request.url)

    context = construct_context()
    public_apis = ApiScript.query.filter_by(is_public=True).all()
    
    private_apis = []

    if context.get('user_id'):
        user = User.query.get(context['user_id'])
        if user:
            if user.api_all_access or context['role']=="admin":
                private_apis = ApiScript.query.filter_by(is_public=False).all()
            else:
                private_apis = user.api_permissions

        #Pour éviter les doubons avec l'affichage du public et private
        for element in private_apis.copy():
            if element in public_apis:
                private_apis.remove(element)

    return render_template('index.html', public_apis=public_apis, private_apis=private_apis, **context)



@route_bp.route('/details/<script_name>')
def api_details(script_name):
    if __main__.backend.debug:
        logs(f"Accès au détail de l'api {script_name}", status='debug', component='web', request_info=request.url)
    
    context = construct_context()
    FABRIC_DIR = 'fabric'

    if '..' in script_name or '/' in script_name:
        logs(f'api inexistante pour afficher le détail', status='bad_request', component='web', request_info=request.url)
        return failed_api("Invalid script name", 400)

    script_path = os.path.join(FABRIC_DIR, f"{script_name}.py")
    if not os.path.exists(script_path):
        logs(f'api inexistante pour afficher le détail', status='bad_request', component='web', request_info=request.url)
        return failed_api("Script not found", 404)

    api_script = ApiScript.query.get(script_name)
    if not api_script:
        logs(f'api inexistante dans la base pour afficher le détail', status='bad_request', component='web', request_info=request.url)
        return failed_api("API not found in database", 404)

    # Security check
    if not api_script.is_public:
        if not context.get('user_id'):
            return failed_api("Accès refusé", 403)
        
        user = User.query.get(context['user_id'])
        if not user or (not user.api_all_access and user.role!="admin" and api_script not in user.api_permissions):
            return failed_api("Accès refusé", 403)

    try:
        spec = importlib.util.spec_from_file_location(script_name, script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        main_func = None
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if hasattr(func, '_is_entrypoint') and func._is_entrypoint:
                main_func = func
                break
        
        if main_func is None:
            logs(f"Aucun @entrypoint trouvé pour {script_name}", status='error', component='web', request_info=request.url)
            return jsonify({"error": f"No @entrypoint function found in {script_name}.py"}), 500

        parameters = []
        for name, param in inspect.signature(main_func).parameters.items():
            param_type = str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any"
            parameters.append({"name": name, "type": param_type})

        return render_template('modals/api_details.html', script_name=script_name, parameters=parameters, api=api_script, **context)

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500