import sys

from app.main import SpineTracker

app = SpineTracker(sys.argv[1:])
try:
    app.mainloop()
except(KeyboardInterrupt, SystemExit):
    raise
