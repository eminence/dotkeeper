#!/usr/bin/env python

from git_helper import *
import sys
import inspect
from optparse import OptionParser
from configparser import SafeConfigParser

class Command(object):
    registered = []
    def __init__(self, func, name):
        (self.args, self.varargs, self.varkw, self.defaults, self.kwonlyargs, self.kwonlydefaults, self.annotations) = \
                inspect.getfullargspec(func)
        #print args, varargs, kwargs, defaults
        if self.defaults is None: self.defaults = []
        self.name = name
        self.func = func

    def print_usage():
        for cmd in Command.registered:
            print("%-20s %s" % (cmd.name, cmd.func.__doc__))

      
    def get_command(name):
        for cmd in Command.registered:
            if cmd.name == name: return cmd
        return None



    def setup(self, parser):

        parser.set_usage("%%prog %s [options]" % cmd)

        offset = len(self.args) - len(self.defaults)
        for x in range(len(self.args)):
            thing = self.args[x]
            d = {"dest": thing}

            if (x-offset) >= 0:
                default = self.defaults[x-offset]
                d['default'] = default
                d['help'] = self.annotations[thing]
                if type(default) == bool:
                    d['action'] = 'store_true'
        
            parser.add_option("--"+thing, **d)

    def register(name):
        "A decorator maker"
        def deco(func):
            "A decorator"
            Command.registered.append(Command(func, name))
            return func
        return deco


@Command.register("init")
def cmd_init(base_dir:"Path to dotkeeper base directory"="~/.dotkeeper/"):
    """Initializes the dot keeper repo"""

    base_dir = os.path.expanduser(base_dir)
    repo_dir = os.path.join(base_dir, "repo")
    GIT_DIR = repo_dir

    if not os.path.exists(repo_dir):
        os.makedirs(repo_dir)
    git_helper(["init"], git_dir=GIT_DIR)

    config_file = os.path.join(base_dir, "config")
    if os.path.exists(config_file):
        print("Config file already exists!")
    else:
        # create new, empty config file.  this will be the first commit into the repo
        cp = SafeConfigParser()
        cp.add_section("dotkeeper")
        cp.set("dotkeeper", "base_dir", base_dir)
        with open(config_file, "w") as f:
            cp.write(f)

    add_to_index(config_file, git_dir=GIT_DIR)

    root_tree = write_tree(git_dir=GIT_DIR)
    print("root_tree is %r" % root_tree)

    commit_hash = commit_tree(root_tree, "Initial commit", parent=None, git_dir=GIT_DIR)
    print("commit_hash is %r" % commit_hash)
    
    git_helper(["update-ref", "HEAD", commit_hash], git_dir=GIT_DIR)
    print("Done!")

def cmd_log():
    "Outputs a git log"
    global GIT_DIR
    git_helper(["log"], git_dir=GIT_DIR)

def cmd_add(verbose=False, *args:"One or more paths"):
    "Adds a file to the index"
    global GIT_DIR

    for file in args:
        print("Added", file)
        if not os.path.exists(file):
            print("File does not exist")
            return
        add_to_index(file, git_dir=GIT_DIR)

@Command.register("status")
def cmd_status(verbose:"Be more verbose"=False):
    "Shows the status of the index and the file system"
    global GIT_DIR
    r = diff_index(git_dir=GIT_DIR)
    if r == {}:
        # check LF
        pass

def status(git_dir=None):
    "Prints out a git-like status"
    pass

def usage():
    "Prints out usage"
    print("Usage info goes here")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        Command.print_usage()
        sys.exit(1)
    cmd_s = sys.argv[1]

    cp = SafeConfigParser()
    cp.read(os.path.expanduser('~/.dotkeeper/config'))
    global GIT_DIR
    GIT_DIR = os.path.join(cp.get("dotkeeper", "base_dir"), "repo")
  
    cmd = Command.get_command(cmd_s)
    print(cmd)
    if cmd is None:
        Command.print_usage()
    parser = OptionParser()
    cmd.setup(parser)
    (options, _args) = parser.parse_args()
    sys.exit(0)


    d = {}
    for x in range(len(args)):
        thing = args[x]
        parsed = getattr(options, thing)
        if (x-offset < 0) and parsed is None:
            parser.print_help()
            print("\nError: --%s is required" % thing)
            sys.exit(1)
        d[thing] = parsed

    #print "d is", d
    if varargs is None:
        func(**d)
    else:
        #print "_args is", repr(_args)
        f_args = [d[x] for x in args]
        f_args += _args[1:]
        func(*f_args)


