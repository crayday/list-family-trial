from datetime import datetime
from decimal import Decimal
from gino import Gino
from sqlalchemy import func, case


db = Gino()


class InsufficientBalanceError(ValueError):
    pass


class InvalidTransactionTypeError(ValueError):
    pass


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.BigInteger, primary_key=True)
    uid = db.Column(db.String(36), nullable=False, unique=True)
    type = db.Column(db.String, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

    @classmethod
    async def get_user_balance(cls, user_id: int, date: timestamp) -> Decimal:
        total_amount = await db.select([func.sum(
            case([(cls.type == 'DEPOSIT', cls.amount)],
                 else_=cls.amount * -1))
        ]).where(
            (Transaction.user_id == user_id) & (Transaction.timestamp <= date)
        ).gino.scalar()
        return total_amount or Decimal(0)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    balance = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    async def create_transaction(
        self, txn_type: str, amount: Decimal, uid: str, timestamp: datetime
    ) -> Transaction:
        async with db.transaction():
            if txn_type == 'DEPOSIT':
                self.balance += amount
            elif txn_type == 'WITHDRAW':
                if amount > self.balance:
                    raise InsufficientBalanceError("Insufficient balance")
                self.balance -= amount
            else:
                raise InvalidTransactionTypeError("Invalid transaction type")

            await self.update(
                balance=self.balance
            ).apply()

            transaction = await Transaction.create(
                uid=uid,
                type=txn_type,
                amount=amount,
                user_id=self.id,
                timestamp=timestamp,
            )

            return transaction
