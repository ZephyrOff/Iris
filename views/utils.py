from core.auth import get_user_id, get_username, get_role, get_api_all_access, get_api_permissions
from models.database import db, ApiScript, ApiToken, User
import __main__


def construct_context():
	if hasattr(__main__, "backend") and hasattr(__main__.backend, "auth_required") and __main__.backend.auth_required:
		context = {
			"username": get_username(),
			"role": get_role(),
			"user_id": get_user_id(),
			"api_all_access": get_api_all_access(),
			"api_permissions": get_api_permissions(),
		}
	else:
		#Fake context lorsque l'authentification est désactivé
		context = {
			"user_id": 1,
			"username": get_username(user_id=1),
			"role": get_role(user_id=1),
			"api_all_access": get_api_all_access(user_id=1),
			"api_permissions": get_api_permissions(user_id=1),
		}

		
	if context["role"] == 'admin':
		context['scripts'] = ApiScript.query.all()
		context['tokens'] = ApiToken.query.all()
		context['users'] = User.query.all()
	else: # role == 'user'
		user = User.query.filter_by(id=context["user_id"]).first()
		if user:
			if user.api_all_access==True:
				context['scripts'] = ApiScript.query.all()
			else:
				context['scripts'] = user.api_permissions # Scripts for which the user has permission to generate tokens
		context['tokens'] = ApiToken.query.filter_by(creator_id=context["user_id"]).all() # Tokens created by this user


	return context