import sys, os
from UI.MainWindow import display_gui
from filesystem.iterator import recursive, split_path, ischild

if __name__ == "__main__":
    print("\n\n\n\n\nSTARTING ITERATION: \n")
    p = os.path.abspath("../../..")
    count = 0
    errors = list()
    for entry in recursive(p):
        count += 1
        print(split_path(p, entry))
        if p != entry:
            ic = ischild(p, os.path.join(split_path(p, entry)[0], split_path(p, entry)[1]))
            print("second is child: " + str(ic))
            if ic != True:
                errors.append([entry, split_path(p, entry)])
    if len(errors) > 0:
        print("\n\n\n\nErrors: " + str(len(errors)))
    else:
        print("\n\n\n\nNo errors")
    for e in errors:
        print("Path: " + e[0])
        print("split_path: " + e[1])
    print("\n\nDone iterating over " + str(count) + " paths under " + p)
    sys.exit(0)
    #sys.exit(display_gui(sys.argv))