"""Where "layer 2 of 3 is done, swap to red" goes.

A plot is a sequence of unattended stretches separated by moments that need a
person. This panel configures who gets told about those moments and builds the
:mod:`axiplot.notify` notifier that does the telling. The transports are
axiplot's; all this adds is somewhere to type the URL and a button that proves
it works before a two-hour plot depends on it.

Home Assistant wants a long-lived token. Typing one into a settings field
leaves it in QSettings in the clear, so the field also accepts a *path* — put
the token in a file with sane permissions and point at it, which is what
axiplot's HomeAssistantNotifier already resolves.
"""

import configparser
import os

from PySide6.QtCore import QSettings, Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QGroupBox, QLabel,
                               QLineEdit, QPushButton, QVBoxLayout, QWidget)

from axiplot import notify
from spiro.ui import theme
from spiro.ui.widgets import row


# The BUSY plotter GUI on this machine keeps the same three transports under
# an [ha] section here. Importing beats retyping a broker password.
BUSY_CONF = "~/.config/busy-python/plotter.conf"


class NotifyPanel(QWidget):
    """Home Assistant, MQTT, a webhook — any or all of them."""

    statusMessage = Signal(str)

    def __init__(self, settings=None, parent=None):
        super().__init__(parent)
        self.settings = settings or QSettings("spirograph-2", "notify")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        layout.addWidget(theme.h2("Alerts"))
        layout.addWidget(theme.muted(
            "A message when each layer finishes — which pen to put in next — "
            "and one when the plot is done.", wrap=True))

        self.enabled = QCheckBox("Send alerts")
        self.enabled.setChecked(self._get("enabled", "false") == "true")
        layout.addWidget(self.enabled)

        # -- Home Assistant -------------------------------------------------- #
        box = QGroupBox("Home Assistant")
        inner = QVBoxLayout(box)
        inner.setContentsMargins(8, 4, 8, 6)
        inner.setSpacing(4)
        self.ha_enabled = QCheckBox("Use Home Assistant")
        self.ha_enabled.setChecked(self._get("ha_enabled", "false") == "true")
        inner.addWidget(self.ha_enabled)
        self.ha_url = self._field(inner, "Base URL", "ha_url",
                                  "http://homeassistant.local:8123")
        self.ha_token = self._field(
            inner, "Token or token file", "ha_token", "~/.config/spiro/ha-token",
            tip="A long-lived access token, or the path to a file holding one. "
                "A path keeps the token out of the settings store.")
        self.ha_service = self._field(inner, "Service", "ha_service",
                                      "notify.mobile_app_phone",
                                      tip="notify.<your app>, or script.<name>")
        self.ha_level = QComboBox()
        self.ha_level.addItems(["", "info", "warning", "critical"])
        self.ha_level.setCurrentText(self._get("ha_level", ""))
        self.ha_level.setToolTip(
            "Only sent to a script.* service — notify.* rejects unknown keys.")
        inner.addWidget(row(QLabel("Level"), 1, self.ha_level))
        layout.addWidget(box)

        # -- MQTT ----------------------------------------------------------------- #
        box = QGroupBox("MQTT")
        inner = QVBoxLayout(box)
        inner.setContentsMargins(8, 4, 8, 6)
        inner.setSpacing(4)
        self.mqtt_enabled = QCheckBox("Publish to a broker")
        self.mqtt_enabled.setChecked(self._get("mqtt_enabled", "false") == "true")
        inner.addWidget(self.mqtt_enabled)
        inner.addWidget(theme.muted(
            "For a machine with no Home Assistant token: publish on a topic "
            "and let HA turn it into an alert.", wrap=True))
        self.mqtt_host = self._field(inner, "Broker", "mqtt_host", "10.0.0.2")
        self.mqtt_topic = self._field(inner, "Topic", "mqtt_topic", "alerts/raise")
        self.mqtt_user = self._field(inner, "User", "mqtt_user", "")
        self.mqtt_pass = self._field(inner, "Password", "mqtt_pass", "",
                                     password=True)
        self.mqtt_level = QComboBox()
        self.mqtt_level.addItems(["info", "warning", "critical"])
        self.mqtt_level.setCurrentText(self._get("mqtt_level", "warning"))
        inner.addWidget(row(QLabel("Level"), 1, self.mqtt_level))
        layout.addWidget(box)

        # -- webhook ------------------------------------------------------------------ #
        box = QGroupBox("Webhook")
        inner = QVBoxLayout(box)
        inner.setContentsMargins(8, 4, 8, 6)
        inner.setSpacing(4)
        self.hook_enabled = QCheckBox("POST to a URL")
        self.hook_enabled.setChecked(self._get("hook_enabled", "false") == "true")
        inner.addWidget(self.hook_enabled)
        self.hook_url = self._field(inner, "URL", "hook_url", "https://ntfy.sh/...")
        layout.addWidget(box)

        self.import_button = QPushButton("Import from the BUSY plotter")
        self.import_button.setToolTip(
            "Copy the broker, topic and service already configured in "
            + BUSY_CONF)
        self.import_button.setEnabled(os.path.exists(os.path.expanduser(BUSY_CONF)))
        self.import_button.clicked.connect(self.import_busy_settings)
        layout.addWidget(self.import_button)

        test = QPushButton("Send a test alert")
        test.clicked.connect(self.send_test)
        layout.addWidget(test)
        self.result = theme.muted("", wrap=True)
        layout.addWidget(self.result)
        layout.addStretch(1)

    # -- settings ------------------------------------------------------------------- #

    def _get(self, key, default=""):
        return str(self.settings.value(key, default))

    def _field(self, layout, label, key, placeholder, tip=None, password=False):
        edit = QLineEdit(self._get(key, ""))
        edit.setPlaceholderText(placeholder)
        if password:
            edit.setEchoMode(QLineEdit.Password)
        if tip:
            edit.setToolTip(tip)
        holder = QLabel(label)
        holder.setMinimumWidth(96)
        layout.addWidget(row(holder, edit, stretch_last=True))
        edit._settings_key = key
        return edit

    def save_settings(self):
        for widget in self.findChildren(QLineEdit):
            key = getattr(widget, "_settings_key", None)
            if key:
                self.settings.setValue(key, widget.text())
        self.settings.setValue("enabled", "true" if self.enabled.isChecked() else "false")
        for name, box in (("ha_enabled", self.ha_enabled),
                          ("mqtt_enabled", self.mqtt_enabled),
                          ("hook_enabled", self.hook_enabled)):
            self.settings.setValue(name, "true" if box.isChecked() else "false")
        self.settings.setValue("ha_level", self.ha_level.currentText())
        self.settings.setValue("mqtt_level", self.mqtt_level.currentText())

    def import_busy_settings(self):
        """Seed the fields from the BUSY plotter's own configuration.

        Explicit, and only on the button: copying someone's broker password
        into a second settings store is not something to do behind their back.
        """
        path = os.path.expanduser(BUSY_CONF)
        config = configparser.ConfigParser()
        try:
            config.read(path)
            section = dict(config.items("ha"))
        except Exception as exc:
            self._report("Could not read %s: %s" % (BUSY_CONF, exc), theme.ERR)
            return

        moved = []
        pairs = ((self.mqtt_host, "mqtthost"), (self.mqtt_user, "mqttuser"),
                 (self.mqtt_pass, "mqttpass"), (self.mqtt_topic, "mqtttopic"),
                 (self.ha_url, "url"), (self.ha_service, "service"),
                 (self.ha_token, "token"))
        for widget, key in pairs:
            value = (section.get(key) or "").strip()
            if value:
                widget.setText(value)
                moved.append(key)
        if section.get("level"):
            self.mqtt_level.setCurrentText(section["level"])
            self.ha_level.setCurrentText(section["level"])

        transport = (section.get("transport") or "").strip()
        self.mqtt_enabled.setChecked(transport == "mqtt"
                                     or bool(section.get("mqtthost")))
        self.ha_enabled.setChecked(transport == "rest" and bool(section.get("url")))
        self.enabled.setChecked(section.get("enabled") in ("1", "true", "True"))
        self.save_settings()
        self._report("Imported %d setting%s from the BUSY plotter."
                     % (len(moved), "" if len(moved) == 1 else "s"),
                     theme.OK if moved else theme.WARN)

    # -- the notifier ------------------------------------------------------------------- #

    def notifier(self, log=None):
        """The notifier a plot should use, or None when alerts are off.

        Wrapped in :class:`axiplot.notify.Async` so a slow HTTP round trip
        between two layers never holds up the machine, and fanned out through
        MultiNotifier so one dead transport does not silence the others.
        """
        if not self.enabled.isChecked():
            return None
        transports = []
        if self.ha_enabled.isChecked():
            transports.append(notify.HomeAssistantNotifier(
                self.ha_url.text().strip(), self.ha_token.text().strip(),
                self.ha_service.text().strip(),
                level=self.ha_level.currentText() or None))
        if self.mqtt_enabled.isChecked():
            transports.append(notify.MqttNotifier(
                self.mqtt_host.text().strip(), self.mqtt_user.text(),
                self.mqtt_pass.text(), self.mqtt_topic.text().strip(),
                level=self.mqtt_level.currentText()))
        if self.hook_enabled.isChecked():
            transports.append(notify.WebhookNotifier(self.hook_url.text().strip()))
        if log is not None:
            transports.append(notify.CallableNotifier(log))
        if not transports:
            return None
        return notify.Async(notify.MultiNotifier(*transports))

    def send_test(self):
        """Send synchronously, so the button can say what happened."""
        transports = []
        if self.ha_enabled.isChecked():
            transports.append(("Home Assistant", notify.HomeAssistantNotifier(
                self.ha_url.text().strip(), self.ha_token.text().strip(),
                self.ha_service.text().strip(),
                level=self.ha_level.currentText() or None)))
        if self.mqtt_enabled.isChecked():
            transports.append(("MQTT", notify.MqttNotifier(
                self.mqtt_host.text().strip(), self.mqtt_user.text(),
                self.mqtt_pass.text(), self.mqtt_topic.text().strip(),
                level=self.mqtt_level.currentText())))
        if self.hook_enabled.isChecked():
            transports.append(("Webhook",
                               notify.WebhookNotifier(self.hook_url.text().strip())))
        if not transports:
            self._report("Nothing is switched on to send to.", theme.WARN)
            return

        lines, worst = [], theme.OK
        for name, transport in transports:
            if not transport.configured():
                lines.append("%s: not configured" % name)
                worst = theme.WARN
                continue
            ok = transport.send("Spirograph test",
                                "If this reached you, plot alerts will too.",
                                {"source": "spirograph-2"})
            lines.append("%s: %s" % (name, "sent" if ok else
                                     (transport.last_error or "failed")))
            if not ok:
                worst = theme.ERR
        self._report("   ".join(lines), worst)

    def _report(self, text, color):
        self.result.setText(text)
        self.result.setStyleSheet("color: %s;" % color)
        self.statusMessage.emit(text)
