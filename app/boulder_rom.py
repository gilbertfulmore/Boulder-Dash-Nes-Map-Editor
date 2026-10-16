import os
import copy
import shutil
import json

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
DEFAULT_ROM_PATH = os.path.join(DATA_DIR, "Boulder Dash.nes")
DEFAULT_DUMP_PATH = os.path.join(DATA_DIR, "levels_dump.json")

class BoulderDashROM:
    def __init__(self, rom_path=DEFAULT_ROM_PATH, dump_json_path=DEFAULT_DUMP_PATH):
        self.rom_path = rom_path
        self.backup_path = rom_path + ".original.bak"
        self.rom_data = None

        with open(dump_json_path, 'r') as f:
            dump = json.load(f)
            self.original_levels_meta = copy.deepcopy(dump['levels'])
            self.levels_meta = copy.deepcopy(dump['levels'])
            self.config = dump['config']

        if self.rom_path and os.path.exists(self.rom_path):
            if not os.path.exists(self.backup_path):
                shutil.copyfile(self.rom_path, self.backup_path)
            with open(self.rom_path, 'rb') as f:
                self.rom_data = bytearray(f.read())

    def has_rom(self):
        return self.rom_data is not None

    def load_rom_bytes(self, raw_bytes, sync_existing_edits=True):
        if len(raw_bytes) < 16 or raw_bytes[:4] != b"NES\x1a":
            raise ValueError("Invalid NES ROM file (missing iNES 'NES\\x1a' header)")
        self.rom_data = bytearray(raw_bytes)
        if self.rom_path:
            # Save backup of unmodified uploaded ROM before applying any edits
            with open(self.backup_path, 'wb') as f:
                f.write(raw_bytes)
            if sync_existing_edits:
                for idx, meta in enumerate(self.levels_meta):
                    self._write_level_to_rom_data(idx, meta)
            self.commit()
        elif sync_existing_edits:
            for idx, meta in enumerate(self.levels_meta):
                self._write_level_to_rom_data(idx, meta)
        return True

    def get_level(self, index):
        if 0 <= index < len(self.levels_meta):
            meta = self.levels_meta[index]
            if self.rom_data is not None:
                # Read current values from rom_data
                diamonds = self.rom_data[meta['crystal_offset']]
                time_limit = self.rom_data[meta['time_offset']]
                start_x = self.rom_data[meta['start_x_offset']]
                start_y = self.rom_data[meta['start_y_offset']]

                # Read password (from 0x2938 + 8*index + 1 .. + 6)
                pw_off = 0x2938 + 8 * index + 1
                raw_pw = [self.rom_data[pw_off + d] for d in range(6)]
                if all(0 <= d <= 9 for d in raw_pw):
                    password = "".join(str(d) for d in raw_pw)
                else:
                    password = "FINAL"

                # Read 440 bytes of grid
                lvl_off = meta['level_offset']
                cave_bytes = self.rom_data[lvl_off : lvl_off + 440]
                grid = []
                for r in range(22):
                    row = []
                    for c_idx in range(20):
                        b = cave_bytes[r * 20 + c_idx]
                        row.append(b & 0x0f)
                        row.append((b >> 4) & 0x0f)
                    grid.append(row)
            else:
                diamonds = meta['diamonds_needed']
                time_limit = meta['time_limit']
                start_x = meta['start_x']
                start_y = meta['start_y']
                password = meta.get('password', 'FINAL' if index == 23 else '000000')
                grid = [row[:] for row in meta['grid']]

            return {
                'index': index,
                'name': meta['name'],
                'world': meta['world'],
                'cave': meta['cave'],
                'tileset': meta['tileset'],
                'level_offset': meta['level_offset'],
                'crystal_offset': meta['crystal_offset'],
                'time_offset': meta['time_offset'],
                'start_x_offset': meta['start_x_offset'],
                'start_y_offset': meta['start_y_offset'],
                'scroll_offset': meta.get('scroll_offset', 0),
                'diamonds_needed': diamonds,
                'time_limit': time_limit,
                'start_x': start_x,
                'start_y': start_y,
                'password': password,
                'grid': grid
            }
        return None

    def _write_level_to_rom_data(self, index, data):
        if self.rom_data is None:
            return
        meta = self.levels_meta[index]
        if 'diamonds_needed' in data:
            self.rom_data[meta['crystal_offset']] = max(0, min(255, int(data['diamonds_needed'])))
        if 'time_limit' in data:
            self.rom_data[meta['time_offset']] = max(0, min(255, int(data['time_limit'])))
        if 'start_x' in data:
            self.rom_data[meta['start_x_offset']] = max(0, min(39, int(data['start_x'])))
        if 'start_y' in data:
            self.rom_data[meta['start_y_offset']] = max(0, min(21, int(data['start_y'])))
        if 'password' in data and len(str(data['password'])) == 6 and str(data['password']).isdigit():
            pw_off = 0x2938 + 8 * index + 1
            pw_str = str(data['password'])
            for d in range(6):
                self.rom_data[pw_off + d] = int(pw_str[d])
        if 'grid' in data:
            grid = data['grid']
            lvl_off = meta['level_offset']
            for r in range(22):
                for c_idx in range(20):
                    t0 = grid[r][c_idx * 2] & 0x0f
                    t1 = grid[r][c_idx * 2 + 1] & 0x0f
                    b = t0 | (t1 << 4)
                    self.rom_data[lvl_off + r * 20 + c_idx] = b

    def save_level(self, index, data):
        meta = self.levels_meta[index]
        if 'diamonds_needed' in data:
            meta['diamonds_needed'] = max(0, min(255, int(data['diamonds_needed'])))
        if 'time_limit' in data:
            meta['time_limit'] = max(0, min(255, int(data['time_limit'])))
        if 'start_x' in data:
            meta['start_x'] = max(0, min(39, int(data['start_x'])))
        if 'start_y' in data:
            meta['start_y'] = max(0, min(21, int(data['start_y'])))
        if 'password' in data and len(str(data['password'])) == 6 and str(data['password']).isdigit():
            meta['password'] = str(data['password'])
        if 'grid' in data:
            meta['grid'] = [row[:] for row in data['grid']]

        self._write_level_to_rom_data(index, data)

    def commit(self, output_path=None):
        if self.rom_data is None:
            return False
        out = output_path or self.rom_path
        if not out:
            return False
        with open(out, 'wb') as f:
            f.write(self.rom_data)
        return True

    def revert_to_backup(self):
        self.levels_meta = copy.deepcopy(self.original_levels_meta)
        if os.path.exists(self.backup_path):
            with open(self.backup_path, 'rb') as f:
                self.rom_data = bytearray(f.read())
            self.commit()
            return True
        return True

if __name__ == "__main__":
    bd = BoulderDashROM()
    lvl0 = bd.get_level(0)
    print(f"Loaded Level 0 ({'ROM loaded' if bd.has_rom() else 'Metadata mode'}): {lvl0['name']}, Diamonds: {lvl0['diamonds_needed']}, Time: {lvl0['time_limit']}, Start: ({lvl0['start_x']},{lvl0['start_y']}), PW: {lvl0['password']}")

