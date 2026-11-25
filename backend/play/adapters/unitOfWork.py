from contextlib import AbstractContextManager

from django.db import transaction

from play.use_cases.ports import UnitOfWork


class DjangoUnitOfWork(UnitOfWork):
    def atomic(self) -> AbstractContextManager[None]:
        return transaction.atomic()
