import os
import threading

os.system("mkdir -p container")

def update_container(i):
    os.system(f"rm -rf container/{i}/container")
    os.system(f"mkdir -p container/{i}/container")
    os.system(f"cp default_container.zip container/{i}/")
    os.system(f"cd container/{i}/container;"
              f"unzip -o ../default_container.zip")
    os.system(f"cd container/{i}/; docker build --no-cache --force-rm -t compiler_{i} .")

thList = []
for i in range(1, 13):
    th = threading.Thread(target=update_container, args=(i,))
    th.start()
    thList.append(th)

for th in thList:
    th.join()
