import json

with open('scripts/config.json') as f:
    config = json.load(f)

kubehost = ''
for sysType in config["testMachines"]["systems"]:
    if sysType["type"] == "pi3B":
        for host in sysType["hosts"]:
            if host["kubeRole"] == 'M':
                kubehost = host["IP"]
                break
print(kubehost)