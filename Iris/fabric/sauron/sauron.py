import urllib.parse
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Date
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import datetime
from core.decorator import entrypoint
from database import *


@entrypoint
def main(codeapp=None, obsolete=None):
    # --- Définition du modèle ---
    Base = declarative_base()


    server = 'VICPRDINFRSQL02.vc-ic.grpsc.net\\vprd001,4380'
    database = 'KPI_HOSTING'
    username = 'user_rw'
    password = 'wq83cjkZcJwIqGvp09AX'

    driver = 'ODBC Driver 18 for SQL Server'
    driver = '{SQL Server}'
    driver = '{ODBC Driver 17 for SQL Server}'


    params = urllib.parse.quote_plus(
        f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
    )
    connection_string = f"mssql+pyodbc:///?odbc_connect={params}"
    engine = create_engine(connection_string)

    # --- Configuration de la session SQLAlchemy ---
    Session = sessionmaker(bind=engine)
    session = Session()

    # --- Exécution de la requête SELECT ---
    try:
        print("Connexion réussie et requête en cours...")

        if codeapp:
            # Exemple 1: Sélectionner tous les serveurs
            """
            tous_les_serveurs = session.query(Server).filter(Server.vinci_division.has(VinciDivision.division_code == 'VIC')).all()

            for a in tous_les_serveurs[0].agents:
                print(a.agent.agent_name)
                print(a.status)
            print(dir(tous_les_serveurs[0]))
            exit()
            for a in tous_les_serveurs:
                print(a.server_name)
            print(f"\n--- Nombre total de serveurs : {len(tous_les_serveurs)} ---")
            """
            # Utilisez .filter() avec .like()
            recherche_wcom = "wcom"
            serveurs_wcom = session.query(Server).filter(Server.server_name.like(f"%{codeapp}%")).all()

            results = []
            for srv in serveurs_wcom:
                results.append({"server_name": srv.server_name, "power_state": srv.power_state})

            return results
            """
            # Parcourez et affichez les résultats
            for server in serveurs_wcom:
                print(server.vinci_division)
                print(f"{server.server_name}: {server.power_state}")
            for server in tous_les_serveurs[:5]:  # Afficher les 5 premiers pour l'exemple
                print(f"Serveur : {server.server_name}, État : {server.power_state}")
            
            # Exemple 2: Sélectionner un serveur par son nom
            nom_a_rechercher = 'nom_de_votre_serveur'  # Remplacez par un nom de serveur réel
            serveur_trouve = session.query(Server).filter_by(server_name=nom_a_rechercher).first()
            if serveur_trouve:
                print(f"\n--- Serveur trouvé par nom : {serveur_trouve.server_name} ---")
                print(f"ID : {serveur_trouve.id_server}, Risque : {serveur_trouve.r7_risk_score}")
            else:
                print(f"\nLe serveur avec le nom '{nom_a_rechercher}' n'a pas été trouvé.")

            # Exemple 3: Sélectionner tous les serveurs qui ne sont pas obsolètes
            serveurs_actifs = session.query(Server).filter(Server.is_obsolete == False).all()
            print(f"\n--- Serveurs actifs : {len(serveurs_actifs)} ---")
            for server in serveurs_actifs[:5]:  # Afficher les 5 premiers pour l'exemple
                print(f"Serveur actif : {server.server_name}")
            """
        if obsolete:
            tous_les_serveurs = session.query(Server).filter_by(is_obsolete=True).all()
            
            results = []
            for srv in tous_les_serveurs:
                results.append({"server_name": srv.server_name})

            return results

    except Exception as e:
        print(f"\nUne erreur est survenue lors de la requête : {e}")
        session.rollback()  # Annule les changements si une erreur se produit
    finally:
        session.close()  # Ferme toujours la session pour libérer les ressources