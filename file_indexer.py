# Python standard libraries
import os

def get_next_index_file(folder, prefix, ext=".json"):
    existing = [f for f in os.listdir(folder) if f.startswith(prefix) and f.endswith(ext)]
    indices = []
    for f in existing:
        try:
            index = int(f[len(prefix):-len(ext)])
            indices.append(index)
        except:
            pass
    next_index = max(indices) + 1 if indices else 1
    return os.path.join(folder, f"{prefix}{next_index}{ext}")