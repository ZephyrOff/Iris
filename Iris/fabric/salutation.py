from core.decorator import entrypoint
from core.environment_manager import get_environment

@entrypoint
def saluer(nom: str, titre: str="Monsieur/Madame"):
    """
    Retourne un message de salutation personnalisé.
    """
    api_context = get_environment()
    
    # Exemple d'utilisation des données de l'environnement
    # Vous pouvez accéder à api_context.request, api_context.token_str, api_context.token_id
    token_info = f" (via token ID: {api_context.token_id})" if api_context and api_context.token_id else ""
    
    return {"message": f"Bonjour {titre} {nom} !{api_context.environment_vars.bonjour} {api_context.environment_vars.t12345}"}

def une_autre_fonction():
    """
    Cette fonction ne sera pas appelée par le hub.
    """
    return {"info": "Ceci est une autre fonction."}