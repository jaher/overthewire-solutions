"""Run a command as vortex3 on the lab over plain ssh (no pipe into python)."""
import subprocess

E = "/home/claude/tools/askpass"


def ssh3(script):
    sc = ("OTW_PASS='xRMRVus8g' SSH_ASKPASS=%s SSH_ASKPASS_REQUIRE=force DISPLAY=:0 ssh -T "
          "-o UserKnownHostsFile=/home/claude/tools/known_hosts -o PreferredAuthentications=password "
          "-o PubkeyAuthentication=no -o LogLevel=ERROR -p 2228 vortex3@vortex.labs.overthewire.org "
          "%r" % (E, script))
    r = subprocess.run(["bash", "-c", sc], capture_output=True, text=True, timeout=120)
    return r.stdout + r.stderr
