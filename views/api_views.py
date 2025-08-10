import __main__
import os
import importlib.util
import inspect
from flask import Blueprint, request, jsonify
from models.database import ApiScript, ApiToken
from core.logging import logs

api_bp = Blueprint('api', __name__, url_prefix='/api')

FABRIC_DIR = 'fabric'


def failed_api(message, status_code):
    if __main__.backend.enable_auto_protect:
        response = __main__.backend.protect.auto_protect()
        if response:
            return response

    return jsonify({"error": message}), status_code


@api_bp.route('/<script_name>')
def api_hub(script_name):
    if __main__.backend.debug:
        logs(f"Tentative d'accès à l'api", status='debug', component='api', request_info=request.url, api_name=script_name)

    token_str = None
    token_id = None
    try:
        if '..' in script_name or '/' in script_name:
            logs(f'api inexistante', status='bad_request', component='api', request_info=request.url, api_name=script_name)
            return failed_api("Invalid script name", 400)
            #return jsonify({"error": "Invalid script name"}), 400

        script_path = os.path.join(FABRIC_DIR, f"{script_name}.py")
        if not os.path.exists(script_path):
            logs(f'api inexistante', status='bad_request', component='api', request_info=request.url, api_name=script_name)
            return failed_api("Script not found", 404)
            #return jsonify({"error": "Script not found"}), 404

        # Vérification des permissions
        script_db = ApiScript.query.get(script_name)
        if script_db:
            if not script_db.is_online:
                logs(f'api offline', status='error', component='api', request_info=request.url, api_name=script_name)
                #Pas de Fail2Ban sur cette requête car juste si offline, pas de bruteforce possible
                return jsonify({"error": "API is currently offline"}), 503
            if not script_db.is_public:
                auth_header = request.headers.get('Authorization')
                if not auth_header or not auth_header.startswith('Bearer '):
                    #Pas de Fail2Ban sur cette requête car juste demande d'authentification, pas de bruteforce possible
                    logs(f"Authentification requise", status='unauthorized', component='api', request_info=request.url, api_name=script_name)
                    return jsonify({"error": "Authorization required"}), 401
                
                token_str = auth_header.split(" ")[1]
                token = ApiToken.query.filter_by(token=token_str, is_active=True).first()
                if not token:
                    logs(f"Le token utilisé est invalide ou désactivé", status='unauthorized', component='api', token=token_str, request_info=request.url, api_name=script_name)
                    return failed_api("Invalid or inactive token", 403)
                    #return jsonify({"error": "Invalid or inactive token"}), 403
                
                token_id = token.id

                # Nouvelle logique de vérification des permissions du token
                if token.token_type == 'app':
                    # Vérifier si le script demandé fait partie des scripts accessibles par ce token
                    if script_db not in token.accessible_scripts:
                        logs(f"Le token utilisé n'a pas les permissions pour cette api", status='unauthorized', component='api', token=token_str, request_info=request.url, api_name=script_name)
                        return failed_api("Token does not have access to this API", 403)
                        #return jsonify({"error": "Token does not have access to this API"}), 403
                # Si token.token_type == 'universal', l'accès est implicitement accordé ici

        spec = importlib.util.spec_from_file_location(script_name, script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        main_func = None
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if hasattr(func, '_is_entrypoint') and func._is_entrypoint:
                main_func = func
                break
        
        if main_func is None:
            logs(f"Aucun @entrypoint trouvé", status='error', component='api', token=token_str, request_info=request.url, api_name=script_name)
            return jsonify({"error": f"No @entrypoint function found in {script_name}.py"}), 500

        func_args = inspect.signature(main_func).parameters
        query_params = request.args.to_dict()
        
        missing_args = [name for name, param in func_args.items() if param.default == inspect.Parameter.empty and name not in query_params]
        if missing_args:
            logs(f"Arguments manquants {', '.join(missing_args)}", status='bad_request', component='api', token=token_str, request_info=request.url, result=str(missing_args), api_name=script_name)
            return failed_api(f"Missing required arguments: {', '.join(missing_args)}", 400)
            #return jsonify({"error": f"Missing required arguments: {', '.join(missing_args)}"}), 400

        call_args = {name: query_params[name] for name in func_args if name in query_params}
        result = main_func(**call_args)
        logs(f"Accès à l'api réussi", status='success', component='api', token=token_str, request_info=request.url, result=str(result), api_name=script_name)
        return jsonify(result)

    except Exception as e:
        logs(f"Erreur lors de l'accès à l'api", status='error', component='api', token=token_str, request_info=request.url, result=str(e), api_name=script_name)
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500
