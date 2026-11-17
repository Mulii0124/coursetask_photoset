"""Collect candidate IPs for a host across repeated DoH queries and test TLS."""
import json
import socket
import ssl
import sys
import time
import urllib.request

DOH = ["https://dns.alidns.com/resolve?name={}&type=A",
       "https://doh.pub/resolve?name={}&type=A",
       "https://1.12.12.12/dns-query?name={}&type=A",
       "https://223.5.5.5/resolve?name={}&type=A"]

host = sys.argv[1] if len(sys.argv) > 1 else "github.com"
rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 8

cands = []
for i in range(rounds):
    for tpl in DOH:
        try:
            req = urllib.request.Request(tpl.format(host), headers={"Accept": "application/dns-json"})
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read().decode("utf-8"))
            for a in data.get("Answer", []):
                if a.get("type") == 1 and a["data"] not in cands:
                    cands.append(a["data"])
        except Exception:
            pass
    time.sleep(0.4)

print("candidates for %s: %s" % (host, cands))
good = []
for ip in cands:
    try:
        s = socket.create_connection((ip, 443), timeout=6)
        w = ssl.create_default_context().wrap_socket(s, server_hostname=host)
        cn = dict(w.getpeercert().get("subjectAltName", []))
        ok = host in " ".join(cn.values())
        print("  %-16s TLS OK  alt=%s  match=%s" % (ip, ",".join(list(cn.values())[:2]), ok))
        if ok:
            good.append(ip)
        w.close()
    except Exception as e:
        print("  %-16s FAIL %s" % (ip, e))
print("GOOD:", good)
