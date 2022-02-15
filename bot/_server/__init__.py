#!/bot/_server
import os

from .core import *
from .middlewares import *
from .routes import *
from .app import *


if not os.path.exists("./server"):
    os.mkdir("./server")
if not os.path.exists("./server/image"):
    os.mkdir("./server/image")
if not os.path.exists("./server/audio"):
    os.mkdir("./server/audio")
