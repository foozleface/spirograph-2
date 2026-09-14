"""Where "that layer is done" goes.

A plot is a sequence of unattended stretches separated by moments that need a
human: swap the nib, check the registration, start the next layer. Those
moments are worth a phone buzz, and they are the only thing this module is
for.

Transports are deliberately dumb -- a title, a message, and a dict of extras --
so the plot loop never learns what Home Assistant is, and adding ntfy or a
Slack hook later means one class, not a rewrite. Everything is best-effort:
a notifier that fails records the error and returns False. A plot must never
die because a phone was unreachable.
"""

import json
import os
import socket
import struct
import threading
import urllib.request


def _fmt_hms(seconds):
    seconds = int(round(seconds or 0))
    if seconds < 60:
        return "%d s" % seconds
    if seconds < 3600:
        return "%d min %02d s" % (seconds // 60, seconds % 60)
    return "%d h %02d min" % (seconds // 3600, (seconds % 3600) // 60)


def layer_message(layer, index, total, seconds=None, next_layer=None):
    """The text a person actually wants on their phone: which layer finished,
    what is left, and whether they have to get up."""
    name = layer.get("label") or layer.get("hex") or "layer %d" % (index + 1)
    title = "Layer %d/%d done -- %s" % (index + 1, total, name)
    bits = []
    if seconds:
        bits.append("took %s" % _fmt_hms(seconds))
    if layer.get("paths"):
        bits.append("%d paths" % layer["paths"])
    if next_layer is not None:
        nxt = next_layer.get("label") or next_layer.get("hex") or "the next one"
        bits.append("swap to %s" % nxt)
        if next_layer.get("estSec"):
            bits.append("~%s to go" % _fmt_hms(next_layer["estSec"]))
    else:
        bits.append("plot complete")
    return title, ", ".join(bits)


class Notifier:
    """Base: implement ``send``. ``layer_done`` is the call site."""

    def send(self, title, message, data=None):
        raise NotImplementedError

    def layer_done(self, layer, index, total, seconds=None, next_layer=None):
        title, message = layer_message(layer, index, total, seconds, next_layer)
        return self.send(title, message,
                         {"layer": index + 1, "layers": total,
                          "hex": layer.get("hex"), "seconds": seconds})

    def plot_done(self, layers, seconds=None):
        return self.send("Plot finished",
                         "%d layer%s in %s" % (len(layers),
                                               "" if len(layers) == 1 else "s",
                                               _fmt_hms(seconds)),
                         {"layers": len(layers), "seconds": seconds})


class HomeAssistantNotifier(Notifier):
    """POST to a Home Assistant notify service.

    ``service`` is the service path, e.g. ``notify/mobile_app_pixel``. The
    token may be the token itself or a path to a file holding it, which is how
    the GUI has always stored it.
    """

    def __init__(self, url, token, service, timeout=6, level=None):
        self.url = (url or "").rstrip("/")
        self.token = token or ""
        # HA's REST path is /api/services/<domain>/<service>, but the service
        # is written with a dot everywhere else in HA -- accept either.
        self.service = (service or "").strip().strip("/").replace(".", "/", 1)
        self.timeout = timeout
        # A script service (script/send_alert) takes its own fields; `level` is
        # the one that decides whether a phone actually buzzes.
        self.level = level
        self.last_error = None

    def configured(self):
        return bool(self.url and self.token and self.service)

    def _resolve_token(self):
        path = os.path.expanduser(self.token)
        if os.path.exists(path):
            with open(path) as fh:
                return fh.read().strip()
        return self.token

    def _payload_probe(self):
        """The payload shape this service gets -- so a gate can assert it
        without a live Home Assistant."""
        return self._payload("t", "m", {"x": 1})

    def _payload(self, title, message, data):
        payload = {"title": title, "message": message}
        if self.level and self.service.split("/")[0] == "script":
            # notify.* validates its schema and would reject a stray key; a
            # script takes whatever it is given and uses what it declares.
            payload["level"] = self.level
        elif data:
            payload["data"] = data
        return payload

    def send(self, title, message, data=None):
        if not self.configured():
            return False
        payload = self._payload(title, message, data)
        req = urllib.request.Request(
            "%s/api/services/%s" % (self.url, self.service),
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": "Bearer %s" % self._resolve_token(),
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp.read()
            self.last_error = None
            return True
        except Exception as exc:            # a phone is never worth a failed plot
            self.last_error = str(exc)
            return False


class MqttNotifier(Notifier):
    """Publish the alert as JSON on an MQTT topic.

    This is the transport for a machine that has no Home Assistant token: HA
    subscribes to the topic and turns the payload into an alert, so the LAN
    credential of a broker is all the plotter needs to reach a phone. It
    speaks MQTT 3.1.1 QoS 0 over a plain socket -- connect, publish,
    disconnect -- because one fire-and-forget publish per layer does not
    justify a dependency.

    ``level`` rides along in the payload; what a receiver does with it is the
    receiver's business (in this house: info is silent, warning and critical
    push to the phone).
    """

    def __init__(self, host, user="", password="", topic="alerts/raise",
                 port=1883, level="warning", timeout=6, client_id="busy"):
        self.host = (host or "").strip()
        self.port = int(port or 1883)
        self.user = user or ""
        self.password = password or ""
        self.topic = (topic or "").strip()
        self.level = level or "warning"
        self.timeout = timeout
        self.client_id = client_id
        self.last_error = None

    def configured(self):
        return bool(self.host and self.topic)

    @staticmethod
    def _remaining(n):
        """MQTT's variable-length integer."""
        out = bytearray()
        while True:
            b, n = n % 128, n // 128
            out.append(b | (0x80 if n else 0))
            if not n:
                return bytes(out)

    @staticmethod
    def _str(v):
        v = v.encode("utf-8")
        return struct.pack("!H", len(v)) + v

    def _packets(self, payload):
        # A fresh client id per connection. Two alerts can leave at the same
        # instant -- the last layer's "swap the nib" and the plot's "finished"
        # do exactly that -- and a broker drops the older session when a second
        # one connects under the same id, which silently ate one of them.
        client_id = "%s-%s" % (self.client_id, os.urandom(4).hex())
        flags = 0x02                                   # clean session
        if self.user:
            flags |= 0x80
            if self.password:
                flags |= 0x40
        body = (self._str("MQTT") + bytes([4, flags, 0, 30])
                + self._str(client_id))
        if self.user:
            body += self._str(self.user)
            if self.password:
                body += self._str(self.password)
        connect = bytes([0x10]) + self._remaining(len(body)) + body
        pub = self._str(self.topic) + payload.encode("utf-8")
        publish = bytes([0x30]) + self._remaining(len(pub)) + pub
        return connect, publish

    def send(self, title, message, data=None):
        if not self.configured():
            return False
        payload = json.dumps({"title": title, "message": message,
                              "level": self.level})
        connect, publish = self._packets(payload)
        try:
            with socket.create_connection((self.host, self.port),
                                          self.timeout) as sk:
                sk.settimeout(self.timeout)
                sk.sendall(connect)
                ack = sk.recv(4)
                if len(ack) < 4 or ack[0] != 0x20:
                    raise RuntimeError("no CONNACK from %s:%d" % (self.host, self.port))
                if ack[3]:
                    raise RuntimeError("broker refused the connection (rc=%d)" % ack[3])
                sk.sendall(publish)
                sk.sendall(bytes([0xE0, 0x00]))        # DISCONNECT
            self.last_error = None
            return True
        except Exception as exc:        # a phone is never worth a failed plot
            self.last_error = str(exc)
            return False


class WebhookNotifier(Notifier):
    """POST the payload as JSON to any URL -- ntfy, Discord, your own thing."""

    def __init__(self, url, timeout=6):
        self.url = url
        self.timeout = timeout
        self.last_error = None

    def configured(self):
        return bool(self.url)

    def send(self, title, message, data=None):
        if not self.url:
            return False
        body = json.dumps({"title": title, "message": message,
                           "data": data or {}}).encode("utf-8")
        req = urllib.request.Request(
            self.url, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp.read()
            self.last_error = None
            return True
        except Exception as exc:
            self.last_error = str(exc)
            return False


class CallableNotifier(Notifier):
    """Wraps any ``fn(title, message, data)`` -- a log line, a test recorder,
    a GUI status bar."""

    def __init__(self, fn):
        self.fn = fn

    def configured(self):
        return True

    def send(self, title, message, data=None):
        self.fn(title, message, data or {})
        return True


class MultiNotifier(Notifier):
    """Fan out. One transport failing does not stop the others."""

    def __init__(self, *notifiers):
        self.notifiers = [n for n in notifiers if n is not None]

    def configured(self):
        return any(getattr(n, "configured", lambda: True)() for n in self.notifiers)

    def send(self, title, message, data=None):
        ok = False
        for n in self.notifiers:
            try:
                ok = n.send(title, message, data) or ok
            except Exception:
                pass
        return ok


class Async(Notifier):
    """Send on a daemon thread, so a slow HTTP round trip never stalls the
    thing between two layers of a plot."""

    def __init__(self, inner):
        self.inner = inner

    def configured(self):
        return getattr(self.inner, "configured", lambda: True)()

    def send(self, title, message, data=None):
        threading.Thread(target=lambda: self.inner.send(title, message, data),
                         daemon=True).start()
        return True
