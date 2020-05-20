import argparse, logging, tqdm, sys, math, os

from data import BackupProfile
from algorithms import Backup, ProcessStatus
from globaldata import PDATA

logger = logging.getLogger(__name__)

class BackupState:
    def __init__(self):
        self.prevpercent = 0.0
        self.progressbar = None
    
    def setDesc(self, d: str="") -> None:
        if self.progressbar is None: self.progressbar = tqdm.tqdm(total=100)
        self.progressbar.set_description(d)

    def printProgress(self, status: ProcessStatus=ProcessStatus(0.0, "DEFAULT STATUS"))->None:
        if self.progressbar is None: self.progressbar = tqdm.tqdm(total=100)
        self.progressbar.update(float(math.floor(status.percent)) - self.prevpercent)
        if float(math.floor(status.percent)) != self.prevpercent:
            self.prevpercent = float(math.floor(status.percent))
    
    def finishedCallback(self)->None:
        print("BACKUP COMPLETE.")

def run_backup(backup: BackupProfile=None) -> None:
    state = BackupState()
    backups = [Backup({"source": source, "destinations": backup.destinations}, 
        {"progressupdate": state.printProgress, "reporterror": None, "finished": None})
        for source in backup.sources]
    
    for d in backup.destinations: print(f"DESTINATION: {d}")
    for b in backups:
        print()
        state.setDesc(os.path.basename(b.source))
        b.execute()
    state.progressbar.close()

def load_named_profile(name: str="") -> BackupProfile:
    for p in PDATA.profiles:
        if p.name == name: return p
    return None

def handle_queries(args) -> None:
    '''
    Handles queries from the user.  If a query argument is passed
    it will spit out the relevant information.  If non-query arguments
    are passed they are ignored and the program will terminate after the
    queried information is provided.
    '''
    if args.list:
        print("Backup Profiles available:")
        for p in PDATA.profiles: print(f"\t{p.name}")
        sys.exit(0)

def run_commandline(args: argparse.ArgumentParser=None) -> int:
    handle_queries(args)
    if args.loglevel is not None:
        if args.loglevel in ["critical", "error", "warning", "info", "debug"]:
            logging.getLogger().setLevel({
                "critical": logging.CRITICAL,
                "error":    logging.ERROR,
                "warning":  logging.WARNING,
                "info":     logging.INFO,
                "debug":    logging.DEBUG}[args.loglevel])
    if args.profile is not None:
        profile = load_named_profile(args.profile)
        if profile is not None:
            run_backup(profile)
            return 0
    elif (args.source is not None) and (args.destination is not None):
        print("Source and destination arguments not implimented yet!")
    return 1