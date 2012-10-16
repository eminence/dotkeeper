#!/usr/bin/env python

from git_helper import *


def init(base_dir="~/.dotkeeper"):
    "Gets things going"

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
            f.write("# empty config file\n")

    add_to_index(config_file, git_dir=GIT_DIR)

    root_tree = write_tree(git_dir=GIT_DIR)
    print "root_tree is %r" % root_tree

    commit_hash = commit_tree(root_tree, "Initial commit", parent=None, git_dir=GIT_DIR)
    print "commit_hash is %r" % commit_hash
    
    git_helper(["update-ref", "HEAD", commit_hash], git_dir=GIT_DIR)
    print "Done!"

def status(git_dir=None):
    "Prints out a git-like status"
    pass

def usage():
    "Prints out usage"

GIT_DIR="/home/achin/.dotkeeper/repo"
from pprint import pprint
