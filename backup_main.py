import sys, os
from UI.MainWindow import display_gui
from filesystem.iterators import CopyIterator

if __name__ == "__main__":
    print("\n\n\n\nSTARTING ITERATION: \n\n\n\n")
    for entry in CopyIterator(os.path.abspath("..")):
        print(entry)
    print("Done iterating over " + os.path.abspath(".."))
    #sys.exit(display_gui(sys.argv))
    sys.exit(0)