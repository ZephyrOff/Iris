import __main__
import os
import ast
from flask import Blueprint, request, render_template, redirect, url_for, flash, make_response, jsonify
from models.database import db, ApiScript, ApiToken, User, LogSystem, LogWeb, LogApi, LogSocket
from core.auth import generate_token, auth_required
from views.utils import construct_context
from core.logging import logs, flash_notification
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

FABRIC_DIR = 'fabric'


# Helper function to send email (placeholder for now)
def send_login_info_email(email, username, password):
    # In a real application, you would integrate with an email service (e.g., SendGrid, Mailgun)
    print(f"Sending login info to {email}: Username={username}, Password={password}")
    # Example: mail.send(msg)
    logs(f"Envoi de l'email de connexion à {email} pour {username}", status='debug', component='web')


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    username_value = None
    if request.method == 'POST':
        username = request.form.get('username')
        username_value = username
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Compte désactivé', 'danger')
                logs(f"Tentative de connexion de l'utilisateur désactivé {username}", status='warning', component='web', request_info=request.url)
                return render_template('login.html', username=username_value)

            token = generate_token(user.id, user.role)
            response = make_response(redirect(url_for('admin.dashboard')))
            response.set_cookie('iris_key', token)
            logs(f'Utilisateur {username} connecté.', status='success', component='web', user_id=user.id, request_info=request.url)
            return response
        else:
            if __main__.backend.enable_auto_protect:
                response = __main__.backend.protect.auto_protect()
                if response:
                    return response

            if user:
                flash('Utilisateur invalide', 'danger')
                logs(f"Erreur lors de la connexion de l'utilisateur {username}: Utilisateur invalide", status='error', component='web', request_info=request.url)
            else:
                flash('Mot de passe invalide', 'danger')
                logs(f"Erreur lors de la connexion de l'utilisateur {username}: Mot de passe invalide", status='error', component='web', request_info=request.url)
    """
    else:
        session.pop('_flashes', None)
    """

    return render_template('login.html', username=username_value)

@admin_bp.route('/logout')
def logout():
    response = make_response(redirect(url_for('admin.login')))
    response.delete_cookie('iris_key')
    return response

@admin_bp.route('/')
@auth_required(required_roles=['admin', 'user'])
def dashboard():
    context = construct_context()

    if __main__.backend.debug:
        logs(f'Envoi du dashboard', status='debug', component='web', request_info=request.url)

    return render_template('admin/index.html', **context)

@admin_bp.route('/dashboard-content')
@auth_required(required_roles=['admin', 'user'])
def dashboard_content():
    if __main__.backend.debug:
        logs(f'Récupération du contenu du dashboard', status='debug', component='web', request_info=request.url)

    # Synchroniser les scripts du dossier fabric avec la DB
    scripts_in_db = {s.id for s in ApiScript.query.all()}
    scripts_in_fs = {f.replace('.py', '') for f in os.listdir(FABRIC_DIR) if f.endswith('.py') and f != 'core.py'}
    
    for script_name in scripts_in_fs - scripts_in_db:
        new_script = ApiScript(id=script_name, is_online=False) # New scripts are offline by default
        db.session.add(new_script)
    
    for script_name in scripts_in_db - scripts_in_fs:
        script_to_delete = ApiScript.query.get(script_name)
        db.session.delete(script_to_delete)
        
    db.session.commit()

    context = construct_context()

    return render_template('admin/partials/dashboard.html', **context)

@admin_bp.route('/api/<script_name>/toggle-public', methods=['POST'])
@auth_required(required_roles=['admin'])
def toggle_api_public_status(script_name):
    try:
        script = ApiScript.query.get_or_404(script_name)
        script.is_public = not script.is_public
        db.session.commit()

        if script.is_public:
            logs(f"Passage de {script_name} en public", status='info', component='web', request_info=request.url)
            flash_notification(f"Passage de {script_name} en public", 'success')
        else:
            logs(f"Passage de {script_name} en private", status='info', component='web', request_info=request.url)
            flash_notification(f"Passage de {script_name} en private", 'success')

    except Exception as err:
        logs(f"Erreur lors du changement du mode: {err}", status='error', component='web', request_info=request.url)
        flash_notification(f"Erreur lors du changement du mode: {err}", 'danger')


    context = construct_context()
    html = render_template('admin/partials/_api_scripts_table.html', **context)
    return jsonify(success=True, html=html)

@admin_bp.route('/api/<script_name>/toggle-online', methods=['POST'])
@auth_required(required_roles=['admin'])
def toggle_api_online_status(script_name):
    try:
        script = ApiScript.query.get_or_404(script_name)
        script.is_online = not script.is_online
        db.session.commit()

        if script.is_online:
            logs(f"Passage de {script_name} en ligne", status='info', component='web', request_info=request.url)
            flash_notification(f"Passage de {script_name} en ligne", 'success')
        else:
            logs(f"Passage de {script_name} en hors-ligne", status='info', component='web', request_info=request.url)
            flash_notification(f"Passage de {script_name} en hors-ligne", 'success')

    except Exception as err:
        logs(f"Erreur lors du changement du mode: {err}", status='error', component='web', request_info=request.url)
        flash_notification(f"Erreur lors du changement du mode: {err}", 'danger')

    context = construct_context()
    html = render_template('admin/partials/_api_scripts_table.html', **context)
    return jsonify(success=True, html=html)

@admin_bp.route('/api-scripts/<script_id>/edit-content', methods=['GET'])
@auth_required(required_roles=['admin'])
def edit_api_script_content(script_id):
    if __main__.backend.debug:
        logs(f"Edition de l'api", status='debug', component='web', request_info=request.url)

    context = construct_context()
    context['script_obj'] = ApiScript.query.get_or_404(script_id)
    
    return render_template('admin/modals/api_script_form.html', **context)

@admin_bp.route('/api-scripts/<script_id>/edit', methods=['POST'])
@auth_required(required_roles=['admin'])
def edit_api_script(script_id):
    script = ApiScript.query.get_or_404(script_id)
    description = request.form.get('description')
    doc = request.form.get('doc')

    script.description = description
    script.doc = doc
    db.session.commit()

    logs(f"API Script {script_id} updated successfully.", status='success', component='web')
    return jsonify(success=True, message='API Script updated successfully!')

@admin_bp.route('/token/create-form', methods=['GET'])
@auth_required(required_roles=['admin', 'user'])
def create_token_form():
    if __main__.backend.debug:
        logs(f"Envoi du formulaire de création d'un token", status='debug', component='web', request_info=request.url)

    context = construct_context()
    context['token_obj'] = None
    
    return render_template('admin/modals/token_form.html', **context)

@admin_bp.route('/token/create', methods=['POST'])
@auth_required(required_roles=['admin', 'user'])
def create_token():
    context = construct_context()

    name = request.form.get('name')
    description = request.form.get('description')
    token_type = request.form.get('token_type') # 'universal' or 'app'
    selected_api_ids = request.form.getlist('selected_apis') # List of API IDs for 'app' tokens

    if not name:
        flash('Nom du token requis', 'danger')
        logs(f"Création d'un token: Nom du token requis", status='error', component='web', request_info=request.url)
        return jsonify(success=False, message='Token name is required.')

    if token_type == 'universal':
        if context['role'] != 'admin':
            flash('Seul les administrateurs peuvent créer un token universal', 'danger')
            logs(f"Création d'un token: Seul les administrateurs peuvent créer un token universal", status='error', component='web', request_info=request.url)
            return jsonify(success=False, message='Only administrators can create universal tokens.')
        
        new_token = ApiToken(name=name, description=description, creator_id=context['user_id'], token_type='universal')
        db.session.add(new_token)
        db.session.commit()
        flash_notification(f"Création du token universal {name} réussi", 'success')
        logs(f"Création du token universal {name} réussi", status='success', component='web', request_info=request.url)
        return jsonify(success=True, redirect_url=url_for('admin.dashboard_content'))

    elif token_type == 'app':
        if not selected_api_ids:
            flash('Aucune API a été selectionnée', 'danger')
            logs(f"Création d'un token: Aucune API a été selectionnée", status='error', component='web', request_info=request.url)
            return jsonify(success=False, message='Please select at least one API for an app token.')

        # Validate selected APIs based on user's permissions
        if context['role'] == 'user' and not context['api_all_access']:
            allowed_api_ids = {s.id for s in context['api_permissions']}
        else:
            allowed_api_ids = {s.id for s in ApiScript.query.all()}
        
        invalid_apis = [api_id for api_id in selected_api_ids if api_id not in allowed_api_ids]
        if invalid_apis:
            flash(f"Vous n'avez pas les droits de créer un token pour {', '.join(invalid_apis)}", 'danger')
            logs(f"Création d'un token: L'utilisateur n'a pas les droits de créer un token pour {', '.join(invalid_apis)}", status='error', component='web', request_info=request.url)
            return jsonify(success=False, message=f'You do not have permission to create tokens for: {', '.join(invalid_apis)}')

        new_token = ApiToken(name=name, description=description, creator_id=context['user_id'], token_type='app')
        db.session.add(new_token)
        db.session.commit() # Commit to get token.id for association

        # Associate token with selected APIs
        for api_id in selected_api_ids:
            script = ApiScript.query.get(api_id)
            if script:
                new_token.accessible_scripts.append(script)
        db.session.commit()
        flash_notification(f"Création du token app {name} réussi", 'success')
        logs(f"Création du token app {name} réussi", status='success', component='web', request_info=request.url)
        return jsonify(success=True, redirect_url=url_for('admin.dashboard_content'))

    else:
        flash('Type de token invalide', 'danger')
        logs(f"Création d'un token: Type de token invalide", status='error', component='web', request_info=request.url)
        return jsonify(success=False, message='Invalid token type selected.')
    

@admin_bp.route('/token/<int:token_id>/edit-content', methods=['GET'])
@auth_required(required_roles=['admin', 'user'])
def edit_token_content(token_id):
    logs(f"Edition du contenu du token", status='info', component='web', request_info=request.url)

    context = construct_context()
    context['token_obj'] = ApiToken.query.get_or_404(token_id)

    return render_template('admin/modals/token_form.html', **context)

@admin_bp.route('/token/<int:token_id>/edit', methods=['POST'])
@auth_required(required_roles=['admin', 'user'])
def edit_token(token_id):
    context = construct_context()

    token = ApiToken.query.get_or_404(token_id)
    # Users can only edit their own tokens
    if context['role'] == 'user' and token.creator_id != context['user_id']:
        flash("Vous n'avez pas les permissions pour éditer ce token", 'danger')
        logs(f"Edition du token: L'utilisateur n'a pas les permissions pour éditer ce token", status='error', component='web', request_info=request.url)
        return jsonify(success=False, message='You do not have permission to edit this token.')

    name = request.form.get('name')
    description = request.form.get('description')
    # token_type cannot be changed for existing tokens, especially universal ones
    selected_api_ids = request.form.getlist('selected_apis')

    if not name:
        flash('Nom du token invalide', 'danger')
        logs(f"Edition du token: Nom du token invalide", status='error', component='web', request_info=request.url)
        return jsonify(success=False, message='Token name is required.')

    token.name = name
    token.description = description

    # Update accessible APIs only if it's an 'app' token
    if token.token_type == 'app':
        if not selected_api_ids:
            flash('Aucune API a été selectionnée', 'danger')
            logs(f"Edition du token: Aucune API a été selectionnée", status='error', component='web', request_info=request.url)
            return jsonify(success=False, message='Please select at least one API for an app token.')

        if context['role'] == 'user' and not context['api_all_access']:
            allowed_api_ids = {s.id for s in context['api_permissions']}
        else:
            allowed_api_ids = {s.id for s in ApiScript.query.all()}

        invalid_apis = [api_id for api_id in selected_api_ids if api_id not in allowed_api_ids]
        if invalid_apis:
            flash(f"Vous n'avez pas les droits pour mettre à jour un token pour {', '.join(invalid_apis)}", 'danger')
            logs(f"Edition du token: L'utilisateur n'a pas les droits de mettre à jour un token pour {', '.join(invalid_apis)}", status='error', component='web', request_info=request.url)
            return jsonify(success=False, message=f'You do not have permission to update tokens for: {', '.join(invalid_apis)}')

        token.accessible_scripts = [] # Clear existing
        for api_id in selected_api_ids:
            script = ApiScript.query.get(api_id)
            if script:
                token.accessible_scripts.append(script)
    
    db.session.commit()
    flash_notification(f"Token {name} mis à jour", 'success')
    logs(f"Token mis à jour", status='success', component='web', request_info=request.url)
    return jsonify(success=True, redirect_url=url_for('admin.dashboard_content'))

@admin_bp.route('/token/<int:token_id>/toggle', methods=['POST'])
@auth_required(required_roles=['admin', 'user'])
def toggle_token_status(token_id):
    try:
        context = construct_context()

        token = ApiToken.query.get_or_404(token_id)
        # Users can only toggle their own tokens
        if context['role'] == 'user' and token.creator_id != context['user_id']:
            flash(f"Vous n'avez pas les droits pour mettre à jour le token {token.name}", 'danger')
            logs(f"Edition du token: L'utilisateur n'a pas les droits de mettre à jour le token {token.name}", status='error', component='web', request_info=request.url)
            return jsonify(success=False, message='You do not have permission to modify this token.')

        token.is_active = not token.is_active
        db.session.commit()

        if token.is_active:
            logs(f"Activation du token {token.name}", status='success', component='web', request_info=request.url)
            flash_notification(f"Activation du token {token.name}", 'success')
        else:
            logs(f"Désactivation du token {token.name}", status='success', component='web', request_info=request.url)
            flash_notification(f"Désactivation du token {token.name}", 'success')

    except Exception as err:
        logs(f"Erreur lors du changement du token {token.name}: {err}", status='error', component='web', request_info=request.url)
        flash_notification(f"Erreur lors du changement du token {token.name}: {err}", 'error')

    context = construct_context()
    html = render_template('admin/partials/_api_tokens_table.html', **context)
    return jsonify(success=True, html=html)

@admin_bp.route('/token/<int:token_id>/delete', methods=['POST'])
@auth_required(required_roles=['admin', 'user'])
def delete_token(token_id):
    context = construct_context()

    token = ApiToken.query.get_or_404(token_id)
    # Users can only delete their own tokens
    if context['role'] == 'user' and token.creator_id != context['user_id']:
        flash(f"Vous n'avez pas les droits pour supprimer le token {token.name}", 'danger')
        logs(f"Suppression du token: L'utilisateur n'a pas les droits pour supprimer le token {token.name}", status='error', component='web', request_info=request.url)
        return jsonify(success=False, message='You do not have permission to delete this token.')

    db.session.delete(token)
    db.session.commit()
    flash_notification(f'Token {token.name} supprimé', 'success')
    logs(f"Token {token.name} supprimé", status='success', component='web', request_info=request.url)
    return jsonify(success=True)

# --- User Management Routes (Admin only) ---

@admin_bp.route('/change_password', methods=['POST'])
@auth_required(required_roles=['admin', 'user'])
def change_password():
    try:
        context = construct_context()

        user_id = context.get('user_id') # Assuming this gets the current user's ID
        user = User.query.get(user_id)

        if not user:
            logs(f"Changement de mot de passe: Utilisateur non trouvé pour l'ID {user_id}", status='error', component='web', request_info=request.url)
            return jsonify(success=False, message='Utilisateur non trouvé.'), 404

        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not current_password or not new_password:
            logs(f"Changement de mot de passe: Mots de passe manquants", status='error', component='web', request_info=request.url, user_id=user_id)
            return jsonify(success=False, message='Tous les champs sont requis.'), 400

        if not user.check_password(current_password):
            logs(f"Changement de mot de passe: Mot de passe actuel incorrect pour l'utilisateur {user.username}", status='warning', component='web', request_info=request.url, user_id=user_id)
            return jsonify(success=False, message='Mot de passe actuel incorrect.'), 401

        # Add password complexity/validation if needed
        if len(new_password) < 6: # Example: minimum 6 characters
            logs(f"Changement de mot de passe: Nouveau mot de passe trop court pour l'utilisateur {user.username}", status='warning', component='web', request_info=request.url, user_id=user_id)
            return jsonify(success=False, message='Le nouveau mot de passe est trop court (minimum 6 caractères).'), 400

        user.set_password(new_password)
        db.session.commit()

        logs(f"Mot de passe de l'utilisateur {user.username} changé avec succès", status='success', component='web', request_info=request.url, user_id=user_id)
        return jsonify(success=True, message='Mot de passe changé avec succès !'), 200

    except Exception as e:
        logs(f"Erreur lors du changement de mot de passe: {e}", status='error', component='web', request_info=request.url)
        return jsonify(success=False, message=f'Une erreur est survenue: {e}'), 500

@admin_bp.route('/users-content')
@auth_required(required_roles=['admin'])
def users_content():
    if __main__.backend.debug:
        logs(f'Envoi du dashboard utilisateur', status='debug', component='web', request_info=request.url)

    context = construct_context()
    context['users'] = User.query.all()
    return render_template('admin/partials/users.html', **context)

@admin_bp.route('/users/create-form', methods=['GET'])
@auth_required(required_roles=['admin'])
def create_user_form():
    if __main__.backend.debug:
        logs(f"Envoi du formulaire d'édition d'un utlisateur", status='debug', component='web', request_info=request.url)

    context = construct_context()
    context['user_obj'] = None

    return render_template('admin/modals/user_form.html', **context)

@admin_bp.route('/users/create', methods=['POST'])
@auth_required(required_roles=['admin'])
def create_user():
    username = request.form.get('username')
    email = request.form.get('email')
    if email == '':
        email = None
    password = request.form.get('password')
    role = request.form.get('role')
    access_all_apis = request.form.get('access_all_apis') == 'true'
    selected_api_ids = request.form.getlist('selected_apis')
    send_email = request.form.get('send_email') == 'on' # Checkbox value

    if not username or not password:
        flash('Username ou password manquant', 'danger')
        logs(f"Ajout d'un utilisateur: Username ou password manquant", status='error', component='web', request_info=request.url)
        return jsonify(success=False, message='Username and password are required.')

    if User.query.filter_by(username=username).first():
        flash("L'utilisateur existe déjà", 'danger')
        logs(f"Ajout d'un utilisateur: l'utilisateur existe déjà", status='error', component='web', request_info=request.url)
        return jsonify(success=False, message='Username already exists.')
    
    if email and User.query.filter_by(email=email).first():
        flash("L'email existe déjà", 'danger')
        logs(f"Ajout d'un utilisateur: l'email existe déjà", status='error', component='web', request_info=request.url)
        return jsonify(success=False, message='Email already exists.')

    new_user = User(username=username, email=email, role=role)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    # Handle API permissions
    new_user.api_all_access = access_all_apis # Set the boolean field
    if not access_all_apis: # Only set specific permissions if not all access
        for api_id in selected_api_ids:
            script = ApiScript.query.get(api_id)
            if script:
                new_user.api_permissions.append(script)
    db.session.commit()

    if send_email and email:
        send_login_info_email(email, username, password)

    flash_notification(f"Utilisateur {username} créé", 'success')
    logs(f"Utilisateur {username} créé", status='success', component='web', request_info=request.url)
    return jsonify(success=True, redirect_url=url_for('admin.users_content'))

@admin_bp.route('/users/<int:user_id>/edit-content', methods=['GET'])
@auth_required(required_roles=['admin'])
def edit_user_content(user_id):
    if __main__.backend.debug:
        logs(f"Récupération du contenu de l'utilisateur", status='debug', component='web', request_info=request.url)

    context = construct_context()
    context['user_obj'] = User.query.get_or_404(user_id)

    return render_template('admin/modals/user_form.html', **context)


@admin_bp.route('/users/<int:user_id>/edit', methods=['POST'])
@auth_required(required_roles=['admin'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    username = request.form.get('username')
    email = request.form.get('email')
    if email == '':
        email = None
    password = request.form.get('password')
    role = request.form.get('role')
    access_all_apis = request.form.get('access_all_apis') == 'true'
    selected_api_ids = request.form.getlist('selected_apis')
    send_email = request.form.get('send_email') == 'on'

    if not username:
        flash("Nom d'utilisateur requis", 'danger')
        logs(f"Edition d'un utilisateur: Nom d'utilisateur requis", status='error', component='web', request_info=request.url)
        return jsonify(success=False, message='Username is required.')

    # Check for unique username/email if changed
    if username != user.username and User.query.filter_by(username=username).first():
        flash("L'utilisateur existe déjà", 'danger')
        logs(f"Edition d'un utilisateur: l'utilisateur existe déjà", status='error', component='web', request_info=request.url)
        return jsonify(success=False, message='Username already exists.')
    if email and email != user.email and User.query.filter_by(email=email).first():
        flash("L'email existe déjà", 'danger')
        logs(f"Edition d'un utilisateur: l'email existe déjà", status='error', component='web', request_info=request.url)
        return jsonify(success=False, message='Email already exists.')

    user.username = username
    user.email = email
    user.role = role
    if password:
        user.set_password(password)

    # Handle API permissions
    user.api_all_access = access_all_apis # Set the boolean field
    user.api_permissions = [] # Clear existing specific permissions
    if not access_all_apis: # Only set specific permissions if not all access
        for api_id in selected_api_ids:
            script = ApiScript.query.get(api_id)
            if script:
                user.api_permissions.append(script)
    db.session.commit()

    if send_email and email and password: # Only send if password was set/changed
        send_login_info_email(email, username, password)

    flash_notification(f'Utilisateur {username} mis à jour', 'success')
    logs(f"Utilisateur {username} mis à jour", status='success', component='web', request_info=request.url)
    return jsonify(success=True, redirect_url=url_for('admin.users_content'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@auth_required(required_roles=['admin'])
def delete_user(user_id):
    context = construct_context()

    user = User.query.get_or_404(user_id)
    if user.username == context['username']: # Prevent deleting self
        flash('Vous ne pouvez pas supprimer votre propre compte', 'danger')
        logs(f"Suppression d'un utilisateur: L'utilisateur ne peut pas supprimer son propre compte", status='error', component='web', request_info=request.url)
        return jsonify(success=False, message='You cannot delete your own account.')
    
    # Disassociate tokens created by this user before deleting
    for token in user.created_tokens:
        token.creator_id = None # Or reassign to admin, or delete token
    db.session.delete(user)
    db.session.commit()
    flash_notification(f'Utilisateur {user.username} supprimé', 'success')
    logs(f"Utilisateur {user.username} supprimé", status='success', component='web', request_info=request.url)
    return jsonify(success=True)

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@auth_required(required_roles=['admin'])
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from deactivating themselves
    context = construct_context()
    if user.username == context['username']:
        flash('Vous ne pouvez pas désactiver votre propre compte', 'danger')
        return jsonify(success=False, message='You cannot deactivate your own account.')

    user.is_active = not user.is_active
    db.session.commit()

    if user.is_active:
        flash_notification(f'Utilisateur {user.username} activé', 'success')
        logs(f'Utilisateur {user.username} activé', status='success', component='web', request_info=request.url)
    else:
        flash_notification(f'Utilisateur {user.username} désactivé', 'success')
        logs(f'Utilisateur {user.username} désactivé', status='success', component='web', request_info=request.url)

    return jsonify(success=True, redirect_url=url_for('admin.users_content'))

@admin_bp.route('/logs-content')
@auth_required(required_roles=['admin'])
def logs_content():
    if __main__.backend.debug:
        logs(f"Récupération du contenu des logs", status='debug', component='web', request_info=request.url)

    context = construct_context()
    log_type = request.args.get('log_type', 'system') # Default to system logs
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Initialize base query
    query = None

    if log_type == 'system':
        query = LogSystem.query
        # Apply filters for LogSystem
        level_filter = request.args.get('level_filter')
        message_filter = request.args.get('message_filter')
        timestamp_filter = request.args.get('timestamp_filter') # New
        if level_filter:
            query = query.filter(LogSystem.level.ilike(f'%{level_filter}%'))
        if message_filter:
            query = query.filter(LogSystem.message.ilike(f'%{message_filter}%'))
        if timestamp_filter: # New
            query = query.filter(db.cast(LogSystem.timestamp, db.String).ilike(f'%{timestamp_filter}%')) # New
        query = query.order_by(db.desc(LogSystem.timestamp)) # Order by timestamp

    elif log_type == 'web':
        query = LogWeb.query
        # Apply filters for LogWeb
        ip_address_filter = request.args.get('ip_address_filter')
        request_filter = request.args.get('request_filter')
        status_filter = request.args.get('status_filter')
        message_filter = request.args.get('message_filter')
        timestamp_filter = request.args.get('timestamp_filter') # New
        user_filter = request.args.get('user_filter') # New
        if ip_address_filter:
            query = query.filter(LogWeb.ip_address.ilike(f'%{ip_address_filter}%'))
        if request_filter:
            query = query.filter(LogWeb.request.ilike(f'%{request_filter}%'))
        if status_filter:
            query = query.filter(LogWeb.status.ilike(f'%{status_filter}%'))
        if message_filter:
            query = query.filter(LogWeb.message.ilike(f'%{message_filter}%'))
        if timestamp_filter: # New
            query = query.filter(db.cast(LogWeb.timestamp, db.String).ilike(f'%{timestamp_filter}%')) # New
        if user_filter: # New
            # Assuming LogWeb.user is a relationship to User model and User has a username field
            query = query.join(User).filter(User.username.ilike(f'%{user_filter}%')) # New
        query = query.order_by(db.desc(LogWeb.timestamp)) # Order by timestamp

    elif log_type == 'api':
        query = LogApi.query
        # Apply filters for LogApi
        name_filter = request.args.get('name_filter')
        token_filter = request.args.get('token_filter')
        ip_address_filter = request.args.get('ip_address_filter')
        request_filter = request.args.get('request_filter')
        status_filter = request.args.get('status_filter')
        message_filter = request.args.get('message_filter')
        timestamp_filter = request.args.get('timestamp_filter') # New
        if name_filter:
            query = query.filter(LogApi.name.ilike(f'%{name_filter}%'))
        if token_filter:
            query = query.filter(LogApi.token.ilike(f'%{token_filter}%'))
        if ip_address_filter:
            query = query.filter(LogApi.ip_address.ilike(f'%{ip_address_filter}%'))
        if request_filter:
            query = query.filter(LogApi.request.ilike(f'%{request_filter}%'))
        if status_filter:
            query = query.filter(LogApi.status.ilike(f'%{status_filter}%'))
        if message_filter:
            query = query.filter(LogApi.message.ilike(f'%{message_filter}%'))
        if timestamp_filter: # New
            query = query.filter(db.cast(LogApi.timestamp, db.String).ilike(f'%{timestamp_filter}%')) # New
        query = query.order_by(db.desc(LogApi.timestamp)) # Order by timestamp

    elif log_type == 'socket':
        query = LogSocket.query
        # Apply filters for LogSocket
        ip_address_filter = request.args.get('ip_address_filter')
        method_filter = request.args.get('method_filter')
        path_filter = request.args.get('path_filter')
        status_code_filter = request.args.get('status_code_filter')
        request_body_filter = request.args.get('request_body_filter')
        timestamp_filter = request.args.get('timestamp_filter') # New
        if ip_address_filter:
            query = query.filter(LogSocket.ip_address.ilike(f'%{ip_address_filter}%'))
        if method_filter:
            query = query.filter(LogSocket.method.ilike(f'%{method_filter}%'))
        if path_filter:
            query = query.filter(LogSocket.path.ilike(f'%{path_filter}%'))
        if status_code_filter:
            query = query.filter(LogSocket.status_code == int(status_code_filter)) # Exact match for status code
        if request_body_filter:
            query = query.filter(LogSocket.request_body.ilike(f'%{request_body_filter}%'))
        if timestamp_filter: # New
            query = query.filter(db.cast(LogSocket.timestamp, db.String).ilike(f'%{timestamp_filter}%')) # New
        query = query.order_by(db.desc(LogSocket.timestamp)) # Order by timestamp

    else: # Default to system logs if log_type is invalid
        query = LogSystem.query
        # Apply filters for LogSystem (same as above)
        level_filter = request.args.get('level_filter')
        message_filter = request.args.get('message_filter')
        timestamp_filter = request.args.get('timestamp_filter') # New
        if level_filter:
            query = query.filter(LogSystem.level.ilike(f'%{level_filter}%'))
        if message_filter:
            query = query.filter(LogSystem.message.ilike(f'%{message_filter}%'))
        if timestamp_filter: # New
            query = query.filter(db.cast(LogSystem.timestamp, db.String).ilike(f'%{timestamp_filter}%')) # New
        query = query.order_by(db.desc(LogSystem.timestamp)) # Order by timestamp

    # Paginate the query
    if query is not None:
        logs_data = query.paginate(page=page, per_page=per_page, error_out=False)
    else:
        logs_data = None # Or handle error

    context['logs'] = logs_data
    context['log_type'] = log_type

    # Pass current filter values back to the template for persistence
    # Create a mutable copy of request.args.to_dict()
    current_filters = request.args.to_dict()
    # Remove 'page', 'per_page', and 'log_type' as they are handled explicitly in templates
    current_filters.pop('page', None)
    current_filters.pop('per_page', None)
    current_filters.pop('log_type', None)
    context['filters'] = current_filters

    return render_template('admin/partials/logs.html', **context)

@admin_bp.route('/logs/api/<int:log_id>/response', methods=['GET'])
@auth_required(required_roles=['admin'])
def get_api_log_response(log_id):
    log_entry = LogApi.query.get_or_404(log_id)
    response_content = ast.literal_eval(log_entry.response) if log_entry.response else "No response content available."

    print(type(response_content))
    return render_template('admin/modals/api_log_response_modal.html', response_content=response_content)

@admin_bp.route('/banned')
@auth_required(required_roles=['admin'])
def banned_ips():
    context = construct_context()
    banned_ips_with_time = []
    for ip, ts in __main__.backend.protect.ban_timestamps.items():
        ban_start_time = datetime.fromtimestamp(ts)
        ban_end_time = ban_start_time + timedelta(seconds=__main__.backend.protect.ban_time)
        banned_ips_with_time.append({
            'ip': ip,
            'ban_time': ban_start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'ban_end_time': ban_end_time.strftime('%Y-%m-%d %H:%M:%S')
        })
    context['banned_ips'] = banned_ips_with_time
    return render_template('admin/partials/banned_ips.html', **context)

@admin_bp.route('/unban/<ip>', methods=['POST'])
@auth_required(required_roles=['admin'])
def unban_ip(ip):
    if ip in __main__.backend.protect.ban_timestamps:
        del __main__.backend.protect.ban_timestamps[ip]
        __main__.backend.protect.failed_attempts.pop(ip, None)
        flash_notification(f'IP {ip} a été dé-bannie.', 'success')
        logs(f'IP {ip} dé-bannie par un administrateur.', status='info', component='system')
    else:
        flash(f"L'IP {ip} n'a pas été trouvée dans la liste des bannis.", 'warning')
    
    context = construct_context()
    banned_ips_with_time = []
    for ip_addr, ts in __main__.backend.protect.ban_timestamps.items():
        ban_start_time = datetime.fromtimestamp(ts)
        ban_end_time = ban_start_time + timedelta(seconds=__main__.backend.protect.ban_time)
        banned_ips_with_time.append({
            'ip': ip_addr,
            'ban_time': ban_start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'ban_end_time': ban_end_time.strftime('%Y-%m-%d %H:%M:%S')
        })
    context['banned_ips'] = banned_ips_with_time
    return jsonify(success=True, html=render_template('admin/partials/banned_ips.html', **context))