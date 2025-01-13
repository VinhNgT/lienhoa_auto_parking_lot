import asyncio

from uvicorn.main import Server


class CancelTasksOnShutdown:
    _tasks_to_close: set[asyncio.Task] = set()

    @classmethod
    def add(cls, task):
        cls._tasks_to_close.add(task)

    @classmethod
    def remove(cls, task):
        cls._tasks_to_close.remove(task)

    @classmethod
    def get_tasks(cls) -> set[asyncio.Task]:
        return cls._tasks_to_close


original_handler = Server.handle_exit


class AppStatus:
    @staticmethod
    def handle_exit(*args, **kwargs):
        for task in CancelTasksOnShutdown.get_tasks():
            task.cancel()

        original_handler(*args, **kwargs)


Server.handle_exit = AppStatus.handle_exit
