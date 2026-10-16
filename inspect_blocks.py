import subprocess

out = subprocess.check_output(['python3', 'decrypt_all.py']).decode('latin1')

for b in range(6):
    sec = f"[WorldBlocks{b}]"
    idx = out.find(sec)
    idx2 = out.find("[", idx + len(sec))
    print(out[idx:idx2 if idx2 != -1 else len(out)])
