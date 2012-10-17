#!/usr/bin/env python

from git_helper import *
import sys
import inspect
from optparse import OptionParser


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
        with open(config_file, "w") as f:
            f.write("[dotkeeper]\n")
            f.write("    base_dir=%s\n" % base_dir)
            f.write("\n")

    add_to_index(config_file, git_dir=GIT_DIR)

    root_tree = write_tree(git_dir=GIT_DIR)
    print "root_tree is %r" % root_tree

    commit_hash = commit_tree(root_tree, "Initial commit", parent=None, git_dir=GIT_DIR)
    print "commit_hash is %r" % commit_hash
    
    git_helper(["update-ref", "HEAD", commit_hash], git_dir=GIT_DIR)
    print "Done!"

def cmd_log():
    "Outputs a git log"
    git_helper(["log"], git_dir="/home/achin/.dotkeeper/repo")

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
    
    func = locals().get("cmd_" + cmd)
    if func is None:
        print "Sorry, I don't know about", cmd
        sys.exit(1)

    spec = inspect.getargspec(func)
    args = spec[0]
    varargs = spec[1]
    kwargs = spec[2]
    defaults = spec[3]
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

    (options, _) = parser.parse_args()
    d = {}
    for x in range(len(args)):
        thing = args[x]
        parsed = getattr(options, thing)
        if (x-offset < 0) and parsed is None:
            parser.print_help()
            print "\nError: --%s is required" % thing
            sys.exit(1)
        d[thing] = parsed

    func(**d)


