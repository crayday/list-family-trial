from aiohttp import web
# from models_schema import api_db as db

app = web.Application()


def init_app() -> web.Application:
    from .config import Config
    from .cleanups import close_db
    from .startups import init_db
    from app.api.routes import add_routes
    from app.models import db

    app['config'] = Config
    app['db'] = db

    # Startups
    app.on_startup.append(init_db)

    # Cleanups
    app.on_cleanup.append(close_db)
    add_routes(app)

    return app
