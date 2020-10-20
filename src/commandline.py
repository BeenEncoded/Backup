import argparse, logging, tqdm, sys, math, os

from data import BackupProfile
from algorithms import Backup, ProcessStatus, prune_backup
from globaldata import PDATA, CONFIG
from iterator import recursivecopy

logger = logging.getLogger(__name__)


class ProgressState:
    def __init__(self, total=1):
        self.prevpercent = 0.0
        self.count = total
        self.progressbar = None
        self.errors = []

    def __del__(self):
        if self.progressbar is not None:
            self.progressbar.close()
            self.progressbar = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.deleteProgressbar()

    def deleteProgressbar(self) -> None:
        if self.progressbar is not None:
            self.progressbar.close()
            self.progressbar = None

    def printProgress(self, status: ProcessStatus = ProcessStatus(0.0, "")) -> None:
        self.getProgressbar().update(float(math.floor(status.percent)) - self.prevpercent)
        if float(math.floor(status.percent)) != self.prevpercent:
            self.prevpercent = float(math.floor(status.percent))

    def listError(self, error) -> None:
        self.errors.append(error)

    def getProgressbar(self) -> tqdm.tqdm:
        if self.progressbar is None:
            self.progressbar = tqdm.tqdm(total=100 * self.count)
        return self.progressbar

    def reset(self):
        self.prevpercent = 0.0

    def setProgressbar(self, newbar: tqdm.tqdm = None) -> None:
        if newbar is not None:
            if self.progressbar is not None:
                self.deleteProgressbar()
            self.progressbar = newbar


def run_backup(backup: BackupProfile = None) -> None:
    destinations = [d for d in backup.destinations if os.path.isdir(d)]

    if len(destinations) == 0:
        logger.error("No destinations could be found.  Aborting procedure.")
        print("No destinations are accessible.  Aborting.")
        return
    if destinations != backup.destinations:
        answer = input("Not all destination folders could be found.  Continue anyway? Y/N: ")
        if "n" in str(answer).lower():
            print("ABORTED")
            return

    sources = [s for s in backup.sources if os.path.isdir(s)]
    mapping = backup.find_mapping(CONFIG)
    with ProgressState(total=len(sources)) as state:
        for d in destinations:
            print(f"DESTINATION: {d}")

        backups = [Backup(data={"source": source, "destinations": destinations, "newdest": mapping[source]},
                          com={"progressupdate": state.printProgress, "reporterror": state.listError, "finished": None})
                   for source in sources]

        if len(backups) == 0:
            print("Error: sources don't exist or could not be found.  Aborting procedure.")
            return

        if len(backups) != len(backup.sources):
            logger.error(f"Could not find all the sources.  (found {repr(sources)})  Asking user what to do.")
            print("Error: could not find all sources, however there were some I could find.")
            answer = input("Do you want to procede with the ones I found?  Y/N: ")
            if "n" in str(answer).lower():
                print("ABORTING")
                logger.error("User chose to abort.")
                return

        # execute all the backups:
        for b in backups:
            state.getProgressbar().set_description(os.path.basename(b.source))
            b.execute()
            state.reset()
        sys.stdout.flush()

        # check for errors.  If there were any, then tell the user:
        if len(state.errors) > 0:
            print()
            print(f"There were {len(state.errors)} errors! during the backup.")
            for error in state.errors:
                print(str(error))
            print()
            answer = input("Would you like to continue with the pruning process?  Y/N: ")
            if "n" in str(answer).lower():
                print("ABORTED")
                return

    # finally prune destinations that the user may have removed from their backup.
    with ProgressState() as state:
        state.getProgressbar().set_description("Pruning the backup sources")
        prune_backup(backup, mapping, state.printProgress)

    print(f"{backup.name} COMPLETED")


def load_named_profile(name: str = "") -> BackupProfile:
    for p in PDATA.profiles:
        if p.name == name:
            return p
    return None


def handle_queries(args) -> None:
    """
    Handles queries from the user.  If a query argument is passed
    it will spit out the relevant information.  If non-query arguments
    are passed they are ignored and the program will terminate after the
    queried information is provided.
    """
    if args.list:
        print("Backup Profiles available:")
        for p in PDATA.profiles:
            print(f"\t{p.name}")
        sys.exit(0)
    elif args.listerrortypes:
        print("Error types:")
        for name in recursivecopy.ERROR_TYPES.keys():
            print(f"\t{name}")
        sys.exit(0)


def run_commandline(args: argparse.Namespace = None) -> int:
    handle_queries(args)
    if args.loglevel is not None:
        if args.loglevel in ["critical", "error", "warning", "info", "debug"]:
            logging.getLogger().setLevel({
                                             "critical": logging.CRITICAL,
                                             "error": logging.ERROR,
                                             "warning": logging.WARNING,
                                             "info": logging.INFO,
                                             "debug": logging.DEBUG}[args.loglevel])
    if args.profile:
        profile = load_named_profile(args.profile)
        if profile is not None:
            run_backup(profile)
            return 0
    return 1
