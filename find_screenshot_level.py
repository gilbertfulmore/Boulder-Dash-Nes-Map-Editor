import json

with open('levels_dump.json', 'r') as f:
    dump = json.load(f)

levels = dump['levels']

# Look for level with triangle of diamonds (8) and two boulders (7)
for lvl in levels:
    grid = lvl['grid']
    found = False
    for r in range(len(grid)-3):
        for c in range(len(grid[r])-3):
            # Check for two boulders side by side: [7, ..., 7] or [7, 7]
            if grid[r][c] == 7 and (grid[r][c+1] == 7 or (c+2 < 40 and grid[r][c+2] == 7)):
                # Check if underneath are blocks or dirt
                # And check if there are diamonds nearby
                diamonds_nearby = sum(grid[r+dr][c+dc] == 8 for dr in range(-2, 5) for dc in range(-2, 10) if 0 <= r+dr < 22 and 0 <= c+dc < 40)
                if diamonds_nearby >= 5:
                    print(f"Level {lvl['index']} ({lvl['name']}): match at row {r}, col {c} with {diamonds_nearby} diamonds nearby!")
                    found = True
                    break
        if found:
            break
