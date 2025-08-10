
def entrypoint(func):
    """
    Décorateur pour marquer la fonction principale d'un script API.
    """
    # On attache un attribut à la fonction pour pouvoir l'identifier plus tard.
    func._is_entrypoint = True
    return func
