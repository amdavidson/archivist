#!/usr/bin/env python

import sys, logging
from archivist import Archivist

command = sys.argv[1] if len(sys.argv) > 1 else "backup"
service = sys.argv[2] if len(sys.argv) > 2 else None  

a = Archivist()
a.run(command, service)

