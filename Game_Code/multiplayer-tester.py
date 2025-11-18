""""ALLOWS YOU TO RUN TWO GAMES AT ONCE FOR INDIVIDUAL TESTING"""""

import subprocess
import sys

script_to_run = "main.py"

#launch the first one
process1 = subprocess.Popen([sys.executable, script_to_run])

#launch the second one
process2 = subprocess.Popen([sys.executable, script_to_run])

#wait for both processes to complete
process1.wait()
process2.wait()