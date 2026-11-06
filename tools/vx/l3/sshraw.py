import subprocess
E = "/home/claude/tools/askpass"
def run(script, user="vortex3", pw="xRMRVus8g", timeout=180):
    cmd=["env","OTW_PASS="+pw,"SSH_ASKPASS="+E,"SSH_ASKPASS_REQUIRE=force","DISPLAY=:0","ssh","-T",
    "-o","UserKnownHostsFile=/home/claude/tools/known_hosts","-o","PreferredAuthentications=password",
    "-o","PubkeyAuthentication=no","-o","LogLevel=ERROR","-p","2228",user+"@vortex.labs.overthewire.org",script]
    r=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
    return r.stdout, r.stderr
