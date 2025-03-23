import traceback


def info(msg: str):
    print(msg)
  

def exception(e: Exception):
    print(e)
    print(traceback.format_exc())
