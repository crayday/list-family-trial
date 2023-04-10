from aiohttp import web


async def create_database(app: web.Application):
    await app['db'].gino.drop_all()
    await app['db'].gino.create_all()


async def init_db(app: web.Application):
    await app['db'].set_bind(app['config'].DATABASE_URI)
    await create_database(app)
