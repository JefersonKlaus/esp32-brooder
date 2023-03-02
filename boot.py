#!/opt/bin/lv_micropython


import os

files = os.listdir()

if len(files) >= 2:
    print("The device have %d files" % len(files))

    for i in range(len(files)):
        if ".py" not in files[i]:
            sub_files = os.listdir("./" + files[i])

            for x in range(len(sub_files)):
                print("Running file: ./" + files[i] + "/" + sub_files[x])
                try:
                    exec(open("./" + files[i] + "/" + sub_files[x]).read(), globals())
                except Exception as error:
                    print(error)

        elif files[i] != "boot.py":
            print("Running file:", files[i])
            try:
                exec(open(files[i]).read(), globals())
            except Exception as error:
                print(error)


else:
    print("MicroPython has no files!")
