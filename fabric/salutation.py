from core.decorator import entrypoint

@entrypoint
def saluer(nom: str, titre: str="Monsieur/Madame"):
    """
    Retourne un message de salutation personnalisé.
    """
    return {"message": f"Bonjour {titre} {nom} !"}

def une_autre_fonction():
    """
    Cette fonction ne sera pas appelée par le hub.
    """
    return {"info": "Ceci est une autre fonction."}