import sys, os
from UI.MainWindow import display_gui
from filesystem.iterator import recursivecopy

if __name__ == "__main__":
    print("\n\n\n\n\nSTARTING ITERATION: \n")
    p = os.path.abspath("/home/jonathan")
    count = 0
    for entry in recursivecopy(p):
        count += 1
        if os.path.isfile(entry):
            print("File: " + entry)
        elif os.path.isdir(entry):
            print("directory: " + entry)
        else:
            print("UNIDENTIFIED: " + entry)
    print("\n\nDone iterating over " + str(count) + " paths under " + p)
    #sys.exit(display_gui(sys.argv))
    sys.exit(0)