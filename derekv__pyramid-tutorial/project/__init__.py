import os

from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

from sqlalchemy import engine_from_config
from sqlalchemy import create_engine

from project.models import Base
from project.models import DBSession


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    
    herokuDb = os.environ.get('DATABASE_URL')
    if herokuDb is not None:
        engine = create_engine(herokuDb)
    else:
        engine = engine_from_config(settings, 'sqlalchemy.')

    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings)


    authn_policy = AuthTktAuthenticationPolicy(secret='sosecret',
                                               callback=lambda userid, request: [])
    authz_policy = ACLAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)

    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('user_created', '/user-created', request_method='POST')
    config.add_route('create_user', '/create-user')
    config.add_route('event_type_created', '/event-type-created', request_method='POST')
    config.add_route('create_event_type', '/create-event-type')
    config.add_route('event_type', '/event-types/{eventid:\d+}')
    config.add_route('add_occurance', '/add-occurance')
    config.scan()
    return config.make_wsgi_app()
