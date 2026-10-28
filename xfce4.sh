$ sudo apt update
$ sudo apt install xfce4 xserver-xorg xdotool xprintidle
    инсталаторът избор между gdm3 и lightdm: остави gdm3.
$ sudo apt install xfce4-power-manager xfce4-power-manager-plugins

След това logout, избор на потребител и от иконката за настройки избор Xfce Session Xorg от екрана за вход

Ctrl + Alt + ←	Предишен Workspace
Ctrl + Alt + →	Следващ Workspace

$ cat ./insomnia.py 
#!/usr/bin/env python3
import os
import subprocess
script_dir = os.path.dirname(os.path.abspath(__file__))
try:
    pid = subprocess.check_output(["pgrep", "-f", "caf.py"]).decode("utf-8").strip()
    subprocess.Popen(["kill", pid])
    subprocess.Popen(["notify-send", "Computer doesn't stay awake..."])
except:
    subprocess.Popen(["/bin/bash", "-c", script_dir+"/"+"caf.py"])
    subprocess.Popen(["notify-send", "Computer stays awake..."])
$ cat caf.py 
#!/usr/bin/env python3
import subprocess
import time
seconds = 120 # number of seconds to start preventing blank screen / suspend
while True:
    curr_idle = subprocess.check_output(["xprintidle"]).decode("utf-8").strip()
    if int(curr_idle) > seconds*1000:
        subprocess.call(["xdotool", "key", "Control_L"])
    time.sleep(10)
