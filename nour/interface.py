"""Bel écran de Nour, dans le navigateur, sur le Mac uniquement (127.0.0.1 : rien n'est visible depuis dehors)."""
import json
import queue
import threading
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

PAGE = Path(__file__).with_name("interface.html")


class Bus:
    """Fait circuler les événements (état, messages) entre Nour et l'écran."""

    def __init__(self):
        self.abonnes: list[queue.Queue] = []
        self.messages: deque = deque(maxlen=60)
        self.etat = "veille"
        self.verrou = threading.Lock()

    def emettre(self, type_: str, **data):
        evt = {"type": type_, **data}
        with self.verrou:
            if type_ == "message":
                self.messages.append(evt)
            if type_ == "etat":
                self.etat = data["etat"]
            for q in list(self.abonnes):
                q.put(evt)

    def abonner(self) -> queue.Queue:
        q: queue.Queue = queue.Queue()
        with self.verrou:
            for m in self.messages:
                q.put(m)
            q.put({"type": "etat", "etat": self.etat})
            self.abonnes.append(q)
        return q

    def desabonner(self, q):
        with self.verrou:
            if q in self.abonnes:
                self.abonnes.remove(q)


def demarrer(bus: Bus, routeur, sur_demande, port: int = 8765) -> str:
    """Lance le serveur en arrière-plan. sur_demande(texte) traite une demande tapée à l'écran."""

    class Gestion(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _json(self, obj, code=200):
            corps = json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(corps)))
            self.end_headers()
            self.wfile.write(corps)

        def _hote_ok(self) -> bool:
            """Protection contre les sites piégés (« DNS rebinding ») : seule l'adresse locale est acceptée."""
            hote = self.headers.get("Host", "").split(":")[0]
            return hote in ("127.0.0.1", "localhost")

        def do_GET(self):
            if not self._hote_ok():
                return self.send_error(403)
            if self.path == "/":
                corps = PAGE.read_bytes().replace(b"{{NOM}}", routeur.r["nom"].encode())
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(corps)
            elif self.path == "/events":
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                q = bus.abonner()
                try:
                    while True:
                        try:
                            evt = q.get(timeout=15)
                            self.wfile.write(f"data: {json.dumps(evt, ensure_ascii=False)}\n\n".encode())
                        except queue.Empty:
                            self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    pass
                finally:
                    bus.desabonner(q)
            elif self.path == "/api/competences":
                self._json([c.DESCRIPTION for c in routeur.competences])
            elif self.path == "/api/memoire":
                self._json(routeur.memoire.faits())
            elif self.path == "/api/sante":
                from . import sante
                controles = sante.bilan(routeur, getattr(routeur, "url_ecran", ""))
                self._json({"controles": controles, "rapport": sante.rapport(controles)})
            elif self.path == "/api/erreurs":
                f = routeur.r["dossier"] / "a-ameliorer.json"
                self._json(json.loads(f.read_text(encoding="utf-8")) if f.exists() else [])
            else:
                self.send_error(404)

        def do_POST(self):
            if self.path != "/demande" or not self._hote_ok():
                return self.send_error(404)
            # protection : seul l'écran de Nour (même origine) peut envoyer des demandes
            origine = self.headers.get("Origin", "")
            if origine and urlparse(origine).hostname not in ("127.0.0.1", "localhost"):   # pas « 127.0.0.1.piege.com »
                return self.send_error(403)
            n = int(self.headers.get("Content-Length", 0))
            if n > 20_000:                       # une demande, pas un roman : on refuse le reste
                return self.send_error(413)
            texte = json.loads(self.rfile.read(n) or b"{}").get("texte", "").strip()
            if texte:
                threading.Thread(target=sur_demande, args=(texte,), daemon=True).start()
            self._json({"ok": True})

    for p in range(port, port + 10):
        try:
            serveur = ThreadingHTTPServer(("127.0.0.1", p), Gestion)
            break
        except OSError:
            continue
    else:
        raise OSError("aucun port libre")
    threading.Thread(target=serveur.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{serveur.server_address[1]}/"
