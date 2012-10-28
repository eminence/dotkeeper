#!/usr/bin/env python

from git_helper import *
import sys
import inspect
from optparse import OptionParser
from ConfigParser import SafeConfigParser


def cmd_init(base_dir="~/.dotkeeper/"):
    """Initializes the dot keeper repo

    --base_dir=<dir>  
    """

    base_dir = os.path.expanduser(base_dir)
    repo_dir = os.path.join(base_dir, "repo")
    GIT_DIR = repo_dir

    if not os.path.exists(repo_dir):
        os.makedirs(repo_dir)
    git_helper(["init"], git_dir=GIT_DIR)

    config_file = os.path.join(base_dir, "config")
    if os.path.exists(config_file):
        print "Config file already exists!"
    else:
        # create new, empty config file.  this will be the first commit into the repo
        cp = SafeConfigParser()
        cp.add_section("dotkeeper")
        cp.set("dotkeeper", "base_dir", base_dir)
        with open(config_file, "w") as f:
            cp.write(f)

    add_to_index(config_file, git_dir=GIT_DIR)

    root_tree = write_tree(git_dir=GIT_DIR)
    print "root_tree is %r" % root_tree

    commit_hash = commit_tree(root_tree, "Initial commit", parent=None, git_dir=GIT_DIR)
    print "commit_hash is %r" % commit_hash
    
    git_helper(["update-ref", "HEAD", commit_hash], git_dir=GIT_DIR)
    print "Done!"

def cmd_log():
    "Outputs a git log"
    global GIT_DIR
    git_helper(["log"], git_dir=GIT_DIR)

def cmd_add(verbose=False, *args):
    "Adds a file to the index"
    global GIT_DIR

    for file in args:
        print "Added", file
        if not os.path.exists(file):
            print "File does not exist"
            return
        add_to_index(file, git_dir=GIT_DIR)

def cmd_status():
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
    print "Usage info goes here"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print usage()
        sys.exit(1)
    cmd = sys.argv[1]

    cp = SafeConfigParser()
    cp.read(os.path.expanduser('~/.dotkeeper/config'))
    global GIT_DIR
    GIT_DIR = os.path.join(cp.get("dotkeeper", "base_dir"), "repo")
    
    func = locals().get("cmd_" + cmd)
    if func is None:
        print "Sorry, I don't know about", cmd
        sys.exit(1)

    spec = inspect.getargspec(func)
    args = spec[0]
    varargs = spec[1]
    kwargs = spec[2]
    defaults = spec[3]
    #print args, varargs, kwargs, defaults
    if defaults is None: defaults = []

    parser = OptionParser()
    parser.set_usage("%%prog %s [options]" % cmd)

    offset = len(args) - len(defaults)
    for x in range(len(args)):
        thing = args[x]
        d = {"dest": thing}

        if (x-offset) >= 0:
            default = defaults[x-offset]
            d['default'] = default
            if type(default) == bool:
                d['action'] = 'store_true'
    
        parser.add_option("--"+thing, **d)

    (options, _args) = parser.parse_args()
    d = {}
    for x in range(len(args)):
        thing = args[x]
        parsed = getattr(options, thing)
        if (x-offset < 0) and parsed is None:
            parser.print_help()
            print "\nError: --%s is required" % thing
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


