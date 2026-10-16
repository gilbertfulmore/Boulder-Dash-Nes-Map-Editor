import os
import shutil
import json

class BoulderDashROM:
    def __init__(self, rom_path="Boulder Dash.nes", dump_json_path="levels_dump.json"):
        self.rom_path = rom_path
        self.backup_path = rom_path + ".original.bak"
        
        # Create backup if not exists
        if not os.path.exists(self.backup_path):
            shutil.copyfile(self.rom_path, self.backup_path)
            
        with open(dump_json_path, 'r') as f:
            dump = json.load(f)
            self.levels_meta = dump['levels']
            self.config = dump['config']
            
        with open(self.rom_path, 'rb') as f:
            self.rom_data = bytearray(f.read())
            
    def get_level(self, index):
        if 0 <= index < len(self.levels_meta):
            meta = self.levels_meta[index]
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
                
            return {
                'index': index,
                'name': meta['name'],
                'world': meta['world'],
                'cave': meta['cave'],
                'tileset': meta['tileset'],
                'diamonds_needed': diamonds,
                'time_limit': time_limit,
                'start_x': start_x,
                'start_y': start_y,
                'password': password,
                'grid': grid
            }
        return None

    def save_level(self, index, data):
        meta = self.levels_meta[index]
        # Update diamonds
        if 'diamonds_needed' in data:
            self.rom_data[meta['crystal_offset']] = max(0, min(255, int(data['diamonds_needed'])))
        # Update time
        if 'time_limit' in data:
            self.rom_data[meta['time_offset']] = max(0, min(255, int(data['time_limit'])))
        # Update start_x, start_y
        if 'start_x' in data:
            self.rom_data[meta['start_x_offset']] = max(0, min(39, int(data['start_x'])))
        if 'start_y' in data:
            self.rom_data[meta['start_y_offset']] = max(0, min(21, int(data['start_y'])))
        # Update password
        if 'password' in data and len(str(data['password'])) == 6:
            pw_off = 0x2938 + 8 * index + 1
            pw_str = str(data['password'])
            for d in range(6):
                digit = int(pw_str[d])
                self.rom_data[pw_off + d] = digit
        # Update grid
        if 'grid' in data:
            grid = data['grid']
            lvl_off = meta['level_offset']
            for r in range(22):
                for c_idx in range(20):
                    t0 = grid[r][c_idx * 2] & 0x0f
                    t1 = grid[r][c_idx * 2 + 1] & 0x0f
                    b = t0 | (t1 << 4)
                    self.rom_data[lvl_off + r * 20 + c_idx] = b

    def commit(self, output_path=None):
        out = output_path or self.rom_path
        with open(out, 'wb') as f:
            f.write(self.rom_data)
        return True

    def revert_to_backup(self):
        if os.path.exists(self.backup_path):
            with open(self.backup_path, 'rb') as f:
                self.rom_data = bytearray(f.read())
            self.commit()
            return True
        return False

# Test
if __name__ == "__main__":
    bd = BoulderDashROM()
    lvl0 = bd.get_level(0)
    print(f"Loaded Level 0: {lvl0['name']}, Diamonds: {lvl0['diamonds_needed']}, Time: {lvl0['time_limit']}, Start: ({lvl0['start_x']},{lvl0['start_y']}), PW: {lvl0['password']}")
