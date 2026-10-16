import os
import sys
import json
import base64
import subprocess
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(APP_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")
WEB_DIR = os.path.join(ROOT_DIR, "web")

if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from boulder_rom import BoulderDashROM

PORT = 8080
ROM_FILE = os.path.join(DATA_DIR, "Boulder Dash.nes")
DUMP_FILE = os.path.join(DATA_DIR, "levels_dump.json")
TILES_FILE = os.path.join(DATA_DIR, "tiles_library.json")

rom_handler = BoulderDashROM(ROM_FILE, DUMP_FILE)

class MapEditorHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/levels":
            levels = [rom_handler.get_level(i) for i in range(24)]
            self.send_json_response({"levels": levels, "has_rom": rom_handler.has_rom()})
            return

        elif path == "/api/tiles":
            with open(TILES_FILE, "r") as f:
                fresh_tiles = json.load(f)
            self.send_json_response({"tiles": fresh_tiles})
            return

        elif path.startswith("/api/level/"):
            try:
                lvl_idx = int(path.split("/")[-1])
                lvl_data = rom_handler.get_level(lvl_idx)
                if lvl_data:
                    self.send_json_response({"level": lvl_data, "has_rom": rom_handler.has_rom()})
                    return
                else:
                    self.send_error_response(404, "Level not found")
                    return
            except ValueError:
                self.send_error_response(400, "Invalid level index")
                return

        elif path == "/api/rom":
            if rom_handler.has_rom():
                rom_bytes = bytes(rom_handler.rom_data)
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Length", str(len(rom_bytes)))
                self.end_headers()
                self.wfile.write(rom_bytes)
                return
            else:
                self.send_error_response(404, "No base ROM loaded yet")
                return

        elif path == "/api/export":
            if rom_handler.has_rom():
                rom_bytes = bytes(rom_handler.rom_data)
                self.send_response(200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Content-Disposition", 'attachment; filename="Boulder Dash (Edited).nes"')
                self.send_header("Content-Length", str(len(rom_bytes)))
                self.end_headers()
                self.wfile.write(rom_bytes)
                return
            else:
                self.send_error_response(404, "Base ROM file not loaded. Please load your Boulder Dash.nes ROM first.")
                return

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            body = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            body = {}

        if path == "/api/upload_rom":
            rom_b64 = body.get("rom_base64")
            if not rom_b64:
                self.send_error_response(400, "Missing rom_base64 payload")
                return
            try:
                raw_bytes = base64.b64decode(rom_b64)
                sync_edits = body.get("sync_existing_edits", True)
                rom_handler.load_rom_bytes(raw_bytes, sync_existing_edits=sync_edits)
                levels = [rom_handler.get_level(i) for i in range(24)]
                self.send_json_response({
                    "status": "success",
                    "has_rom": True,
                    "levels": levels
                })
            except Exception as e:
                self.send_error_response(400, f"Invalid ROM file: {e}")
            return

        elif path == "/api/save":
            lvl_idx = body.get("index")
            if lvl_idx is not None and 0 <= lvl_idx < 24:
                rom_handler.save_level(lvl_idx, body)
                committed = rom_handler.commit()
                updated = rom_handler.get_level(lvl_idx)
                self.send_json_response({"status": "success", "level": updated, "has_rom": committed})
                return
            elif "levels" in body:
                for lvl in body["levels"]:
                    rom_handler.save_level(lvl["index"], lvl)
                committed = rom_handler.commit()
                self.send_json_response({"status": "success", "message": "All levels saved successfully", "has_rom": committed})
                return
            else:
                self.send_error_response(400, "Missing level index or data")
                return

        elif path == "/api/revert":
            success = rom_handler.revert_to_backup()
            if success:
                levels = [rom_handler.get_level(i) for i in range(24)]
                self.send_json_response({"status": "success", "message": "Reverted to original backup", "levels": levels, "has_rom": rom_handler.has_rom()})
            else:
                self.send_error_response(500, "Failed to revert")
            return

        elif path == "/api/launch":
            if not os.path.exists(ROM_FILE):
                self.send_error_response(404, "No ROM file on disk to launch")
                return
            try:
                subprocess.Popen(["open", ROM_FILE])
                self.send_json_response({"status": "success", "message": f"Launched {os.path.basename(ROM_FILE)} in system emulator"})
            except Exception as e:
                self.send_error_response(500, f"Failed to launch emulator: {e}")
            return

        self.send_error_response(404, "Not found")

    def send_json_response(self, data, code=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_error_response(self, code, message):
        self.send_json_response({"status": "error", "error": message}, code=code)

def run():
    port = PORT
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    server = HTTPServer(("0.0.0.0", port), MapEditorHandler)
    print("==================================================")
    print("  BOULDER DASH NES MAP EDITOR SERVER")
    print(f"  Running on: http://localhost:{port}")
    print("==================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()

if __name__ == "__main__":
    run()
