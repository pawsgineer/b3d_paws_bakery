import faulthandler

faulthandler.dump_traceback_later(10, repeat=True)

print("faulthandler on", flush=True)
