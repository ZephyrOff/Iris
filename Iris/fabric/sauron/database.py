import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Déclaration de la base pour les classes
Base = declarative_base()

# Modèles générés à partir du script SQL
class OperatingSystem(Base):
    __tablename__ = 'operating_system'
    __table_args__ = {'schema': 'dbo'}

    id_Operating_System = Column(Integer, primary_key=True, autoincrement=True)
    os_name = Column(String(75), nullable=True)
    os_description = Column(String(255), nullable=True)

    # Relation inverse pour la table `server`
    servers = relationship("Server", back_populates="operating_system")

    def __repr__(self):
        return f"<OperatingSystem(name='{self.os_name}')>"


class Application(Base):
    __tablename__ = 'application'
    __table_args__ = {'schema': 'dbo'}

    id_application = Column(Integer, primary_key=True, autoincrement=True)
    app_name = Column(String(100), nullable=True)
    app_code = Column(String(10), nullable=True)
    app_owner = Column(String(100), nullable=True)

    # Relation inverse pour la table `server`
    servers = relationship("Server", back_populates="application")
    
    def __repr__(self):
        return f"<Application(name='{self.app_name}')>"


class ServerRole(Base):
    __tablename__ = 'server_role'
    __table_args__ = {'schema': 'dbo'}

    id_server_role = Column(Integer, primary_key=True, autoincrement=True)
    role_code = Column(String(45), nullable=True)
    role_description = Column(String(100), nullable=True)

    # Relation inverse pour la table `server`
    servers = relationship("Server", back_populates="server_role")

    def __repr__(self):
        return f"<ServerRole(code='{self.role_code}')>"


class ServerTier(Base):
    __tablename__ = 'server_tier'
    __table_args__ = {'schema': 'dbo'}

    id_tier = Column(Integer, primary_key=True, autoincrement=True)
    tier_name = Column(String(45), nullable=True)

    # Relations inverses pour les tables `server` et `cloud_subscription`
    servers = relationship("Server", back_populates="server_tier")
    cloud_subscriptions = relationship("CloudSubscription", back_populates="server_tier")

    def __repr__(self):
        return f"<ServerTier(name='{self.tier_name}')>"


class ServerSource(Base):
    __tablename__ = 'server_source'
    __table_args__ = {'schema': 'dbo'}

    id_source = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(String(45), nullable=True)
    source_description = Column(String(100), nullable=True)

    # Relation inverse pour la table `server`
    servers = relationship("Server", back_populates="server_source")

    def __repr__(self):
        return f"<ServerSource(name='{self.source_name}')>"


class VinciDivision(Base):
    __tablename__ = 'vinci_division'
    __table_args__ = {'schema': 'dbo'}

    id_vinci_division = Column(Integer, primary_key=True, autoincrement=True)
    division_name = Column(String(255), nullable=True)
    division_code = Column(String(255), nullable=True)

    # Relations inverses pour les tables `cloud_subscription`, `server` et `network`
    cloud_subscriptions = relationship("CloudSubscription", back_populates="vinci_division")
    servers = relationship("Server", back_populates="vinci_division")
    networks = relationship("Network", back_populates="vinci_division")

    def __repr__(self):
        return f"<VinciDivision(name='{self.division_name}')>"


class Environnement(Base):
    __tablename__ = 'environnement'
    __table_args__ = {'schema': 'dbo'}

    id_environnement = Column(Integer, primary_key=True, autoincrement=True)
    env_name = Column(String(45), nullable=True)
    env_code = Column(String(45), nullable=True)

    # Relations inverses pour les tables `cloud_subscription` et `server`
    cloud_subscriptions = relationship("CloudSubscription", back_populates="environnement")
    servers = relationship("Server", back_populates="environnement")

    def __repr__(self):
        return f"<Environnement(name='{self.env_name}')>"


class CloudSubscription(Base):
    __tablename__ = 'cloud_subscription'
    __table_args__ = {'schema': 'dbo'}

    id_cloud_subscription = Column(Integer, primary_key=True, autoincrement=True)
    sub_name = Column(String(100), nullable=True)
    sub_id = Column(String(100), nullable=True)
    cloud_provider = Column(String(45), nullable=True)
    rg_name = Column(String(100), nullable=True)
    id_vinci_division = Column(Integer, ForeignKey('dbo.vinci_division.id_vinci_division'), nullable=False)
    id_environnement = Column(Integer, ForeignKey('dbo.environnement.id_environnement'), nullable=False)
    id_tier = Column(Integer, ForeignKey('dbo.server_tier.id_tier'), nullable=False)
    update_date = Column(Date, nullable=True, default=datetime.date.today)

    # Relations basées sur les clés étrangères
    vinci_division = relationship("VinciDivision", back_populates="cloud_subscriptions")
    environnement = relationship("Environnement", back_populates="cloud_subscriptions")
    server_tier = relationship("ServerTier", back_populates="cloud_subscriptions")
    servers = relationship("Server", back_populates="cloud_subscription_obj")

    def __repr__(self):
        return f"<CloudSubscription(name='{self.sub_name}')>"


class Server(Base):
    __tablename__ = 'server'
    __table_args__ = {'schema': 'dbo'}

    id_server = Column(Integer, primary_key=True, autoincrement=True)
    server_name = Column(String(255), nullable=True)
    is_appliance = Column(Boolean, nullable=True)
    is_obsolete = Column(Boolean, nullable=True)
    power_state = Column(String(50), nullable=True)
    r7_risk_score = Column(String(45), nullable=True)
    id_operating_system = Column(Integer, ForeignKey('dbo.operating_system.id_Operating_System'), nullable=False)
    id_application = Column(Integer, ForeignKey('dbo.application.id_application'), nullable=False)
    id_server_role = Column(Integer, ForeignKey('dbo.server_role.id_server_role'), nullable=False)
    id_tier = Column(Integer, ForeignKey('dbo.server_tier.id_tier'), nullable=False)
    id_source = Column(Integer, ForeignKey('dbo.server_source.id_source'), nullable=False)
    cloud_subscription = Column(Integer, ForeignKey('dbo.cloud_subscription.id_cloud_subscription'), nullable=True)
    id_environnement = Column(Integer, ForeignKey('dbo.environnement.id_environnement'), nullable=False)
    id_vinci_division = Column(Integer, ForeignKey('dbo.vinci_division.id_vinci_division'), nullable=False)
    update_date = Column(Date, nullable=True, default=datetime.date.today)

    # Relations basées sur les clés étrangères
    operating_system = relationship("OperatingSystem", back_populates="servers")
    application = relationship("Application", back_populates="servers")
    server_role = relationship("ServerRole", back_populates="servers")
    server_tier = relationship("ServerTier", back_populates="servers")
    server_source = relationship("ServerSource", back_populates="servers")
    cloud_subscription_obj = relationship("CloudSubscription", back_populates="servers") # Renamed to avoid conflict
    environnement = relationship("Environnement", back_populates="servers")
    vinci_division = relationship("VinciDivision", back_populates="servers")

    # Relations pour les tables de liaison
    agents = relationship("ServerHasAgent", back_populates="server")
    networks = relationship("ServerHasNetwork", back_populates="server")
    patchings = relationship("Patching", back_populates="server")

    def __repr__(self):
        return f"<Server(name='{self.server_name}')>"


class Network(Base):
    __tablename__ = 'network'
    __table_args__ = {'schema': 'dbo'}

    id_network = Column(Integer, primary_key=True, autoincrement=True)
    subnet_name = Column(String(255), nullable=True)
    is_dmz = Column(Boolean, nullable=True)
    id_vinci_division = Column(Integer, ForeignKey('dbo.vinci_division.id_vinci_division'), nullable=False)

    # Relation basée sur la clé étrangère
    vinci_division = relationship("VinciDivision", back_populates="networks")
    servers = relationship("ServerHasNetwork", back_populates="network")

    def __repr__(self):
        return f"<Network(name='{self.subnet_name}')>"


class Agents(Base):
    __tablename__ = 'agents'
    __table_args__ = {'schema': 'dbo'}

    id_agent = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String(45), nullable=True)
    agent_process_name = Column(String(255), nullable=True)
    agent_type = Column(String(45), nullable=True)
    agent_criticity = Column(String(45), nullable=True)
    has_api = Column(Boolean, nullable=True)

    # Relation inverse pour la table de liaison `server_has_agent`
    servers = relationship("ServerHasAgent", back_populates="agent")

    def __repr__(self):
        return f"<Agents(name='{self.agent_name}')>"


class ServerHasAgent(Base):
    __tablename__ = 'server_has_agent'
    __table_args__ = {'schema': 'dbo'}

    id_server_has_agent = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(Boolean, nullable=True)
    is_installable = Column(Boolean, nullable=True)
    #is_required = Column(Boolean, nullable=True)
    comment = Column(String(255), nullable=True)
    update_date = Column(Date, nullable=True, default=datetime.date.today)
    id_server = Column(Integer, ForeignKey('dbo.server.id_server'), nullable=False)
    id_agent = Column(Integer, ForeignKey('dbo.agents.id_agent'), nullable=False)

    # Relations basées sur les clés étrangères
    server = relationship("Server", back_populates="agents")
    agent = relationship("Agents", back_populates="servers")

    def __repr__(self):
        return f"<ServerHasAgent(server_id={self.id_server}, agent_id={self.id_agent})>"


class UpdatePhase(Base):
    __tablename__ = 'update_phase'
    __table_args__ = {'schema': 'dbo'}

    id_update_phase = Column(Integer, primary_key=True, autoincrement=True)
    phase_name = Column(String(255), nullable=True)
    phase_description = Column(String(255), nullable=True)
    phase_next_period = Column(String(255), nullable=True)

    # Relation inverse pour la table `patching`
    patchings = relationship("Patching", back_populates="update_phase")

    def __repr__(self):
        return f"<UpdatePhase(name='{self.phase_name}')>"


class Patching(Base):
    __tablename__ = 'patching'
    __table_args__ = {'schema': 'dbo'}

    id_patching = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(Boolean, nullable=True)
    id_server = Column(Integer, ForeignKey('dbo.server.id_server'), nullable=False)
    id_update_phase = Column(Integer, ForeignKey('dbo.update_phase.id_update_phase'), nullable=False)
    update_date = Column(Date, nullable=True, default=datetime.date.today)

    # Relations basées sur les clés étrangères
    server = relationship("Server", back_populates="patchings")
    update_phase = relationship("UpdatePhase", back_populates="patchings")

    def __repr__(self):
        return f"<Patching(server_id={self.id_server}, phase_id={self.id_update_phase})>"


class ServerHasNetwork(Base):
    __tablename__ = 'server_has_network'
    __table_args__ = {'schema': 'dbo'}

    id_server_has_network = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String(255), nullable=True)
    id_network = Column(Integer, ForeignKey('dbo.network.id_network'), nullable=False)
    id_server = Column(Integer, ForeignKey('dbo.server.id_server'), nullable=False)

    # Relations basées sur les clés étrangères
    network = relationship("Network", back_populates="servers")
    server = relationship("Server", back_populates="networks")

    def __repr__(self):
        return f"<ServerHasNetwork(server_id={self.id_server}, network_id={self.id_network})>"

# Exemple de code pour se connecter à une base de données SQL Server
# DATABASE_URI = 'mssql+pyodbc://<user>:<password>@<dsn_name>'
# engine = create_engine(DATABASE_URI)
# Base.metadata.create_all(engine)
# Session = sessionmaker(bind=engine)
# session = Session()

