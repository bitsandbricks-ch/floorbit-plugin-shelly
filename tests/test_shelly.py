"""The Shelly agent plugin: reading meters in the hall. Only localhost. (Floorbit's own
tests cover handing the readings to Electrics.)"""
import http.server
import json
import threading

import pytest
from conftest import load
from floorbit.plugins.agent import MemoryContext


class Fake(http.server.BaseHTTPRequestHandler):
    routes = {}  # noqa: RUF012  # set per test

    def do_GET(self):
        status, body = self.routes.get(self.path, (404, {}))
        if status == 401 and self.headers.get("Authorization") == "Bearer good-token":
            status, body = self.routes.get("ok:" + self.path, (404, {}))
        data = json.dumps(body).encode()
        self.send_response(status)
        if status == 401:
            self.send_header("WWW-Authenticate", 'Basic realm="x"')
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture
def fake():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Fake)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    Fake.routes = {}
    yield f"127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def test_shelly_lines_and_both_generations():
    m = load("agent")
    assert m.parse_devices("db1-1 = 192.0.2.50\nbad line\ndb1-2=http://192.0.2.51/ em:0") == [
        ("db1-1", "192.0.2.50", None), ("db1-2", "192.0.2.51", "em:0")]
    status = {"switch:0": {"apower": 100.5}, "switch:1": {"apower": 20}, "em:0": {"total_act_power": 3000},
              "sys": {"apower": 9}}
    assert m.watts_from_rpc(status) == 3120.5 and m.watts_from_rpc(status, "switch:1") == 20
    assert m.watts_from_rpc({"sys": {}}) is None
    assert m.watts_from_status({"meters": [{"power": 40}, {"power": 2}]}) == 42
    assert m.watts_from_status({"emeters": [{"power": 900}]}, "0") == 900
    assert m.watts_from_status({"meters": []}, "3") is None


def test_shelly_reads_sends_and_stops_trying_a_refused_password(fake):
    m = load("agent")
    Fake.routes = {"/rpc/Shelly.GetStatus": (200, {"switch:0": {"apower": 230}}),
                   "/status": (200, {"meters": [{"power": 1}]})}
    settings = {"devices": f"db1-1 = {fake}\ndb1-2 = {fake} switch:3", "password": ""}
    ctx = MemoryContext("shelly", settings, {"sends": {"readings": {"privacy": "device", "latest": True}}})
    plugin = m.AgentPlugin(ctx)
    plugin.devices, plugin.rev = m.parse_devices(settings["devices"]), "r1"
    readings, failed = plugin.tick()
    assert readings == [{"meter": "db1-1", "watts": 230}] and "no power reading on switch:3" in failed[0]
    assert ctx.sent[-1] == ("readings", {"readings": [{"meter": "db1-1", "watts": 230}]})
    assert ctx.health_.report()["status"] == "warning"
    # A first-generation Shelly answers /status only.
    Fake.routes = {"/status": (200, {"meters": [{"power": 55}]})}
    assert plugin.tick()[0][0] == {"meter": "db1-1", "watts": 55}
    # A password it refuses: said once, not tried again.
    Fake.routes = {"/rpc/Shelly.GetStatus": (401, {})}
    plugin.tick()
    assert not ctx.may_login(fake, "shelly", "r1") and ctx.health_.report()["status"] == "error"
    assert any("refused the password" in e["error"] for e in ctx.health_.report()["errors"])
    Fake.routes = {"/rpc/Shelly.GetStatus": (200, {"switch:0": {"apower": 1}})}
    assert plugin.tick()[0] == []                       # still blocked
    plugin.rev = "r2"                                   # the password was changed
    assert plugin.tick()[0][0]["watts"] == 1
