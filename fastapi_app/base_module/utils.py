import asyncio


# callback func called for all tasks
def helper_done_callback(task):
    try:
        # get any exception raised
        ex = task.exception()
        # check task for exception
        if ex:
            # report the exception
            print(ex)
    except asyncio.exceptions.CancelledError:
        pass
