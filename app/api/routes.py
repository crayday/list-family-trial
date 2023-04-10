from aiohttp import web
from datetime import datetime
from decimal import Decimal
from asyncpg.exceptions import UniqueViolationError
from app.models import (
    User, Transaction, InvalidTransactionTypeError, InsufficientBalanceError
)


async def create_user(request):
    data = await request.json()
    name = data.get("name")

    if not name:
        return web.json_response({"error": "Name is required"}, status=400)

    try:
        user = await User.create(name=name)

        return web.json_response({
            "id": user.id,
            "name": user.name,
        }, status=201)
    except UniqueViolationError:
        raise web.HTTPBadRequest(text="User with this name already exists")


async def get_user(request):
    user_id = int(request.match_info.get('id'))
    user = await User.query.where(User.id == user_id).gino.first()

    if not user:
        raise web.HTTPNotFound(text="User not found")

    date_str = request.query.get('date')
    if date_str:
        date = datetime.fromisoformat(date_str[:26])
        balance = await Transaction.get_user_balance(user_id, date)
    else:
        balance = user.balance

    return web.json_response({
        "id": user.id,
        "name": user.name,
        "balance": str(balance),
    })


async def add_transaction(request):
    data = await request.json()
    user_id = data.get("user_id")
    user = await User.query.where(User.id == user_id).gino.first()

    if not user:
        raise web.HTTPNotFound(text="User not found")

    txn_type = data.get("type")
    amount = Decimal(data.get("amount"))
    uid = data.get("uid")
    timestamp = datetime.fromisoformat(data.get("timestamp"))

    transaction = await Transaction.query.where(
        Transaction.uid == uid
    ).gino.first()
    if not transaction:
        try:
            transaction = await user.create_transaction(
                txn_type, amount, uid, timestamp)
        except InsufficientBalanceError:
            raise web.HTTPPaymentRequired(text="Insufficient balance")
        except InvalidTransactionTypeError:
            raise web.HTTPBadRequest(text="Invalid transaction type")

    return web.json_response({"transaction_id": transaction.id})


async def get_transaction(request):
    uid = request.match_info.get("id")
    transaction = await Transaction.query.where(
        Transaction.uid == uid
    ).gino.first()

    if not transaction:
        raise web.HTTPNotFound(text="Transaction not found")

    return web.json_response({
        "id": transaction.id,
        "uid": transaction.uid,
        "type": transaction.type,
        "amount": str(transaction.amount),
        "user_id": transaction.user_id,
        "timestamp": transaction.timestamp.isoformat(),
    })


def add_routes(app):
    app.router.add_route('POST', r'/v1/user', create_user, name='create_user')
    app.router.add_route('GET', r'/v1/user/{id}', get_user, name='get_user')
    app.router.add_route('POST', r'/v1/transaction', add_transaction, name='add_transaction')
    app.router.add_route('GET', r'/v1/transaction/{id}', get_transaction, name='incoming_transaction')
