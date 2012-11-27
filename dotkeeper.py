#!/usr/bin/env python

from git_helper import *
import sys
import inspect
from argparse import ArgumentParser
from configparser import ConfigParser
from pprint import pprint
import subprocess

class Command(object):
    """Manages the glue that connects the command line parser to individual functions"""
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

    def call_with(self, from_cmd):
        d = {}
        for thing in self.args:
            parsed = getattr(from_cmd, thing)
            d[thing] = parsed

        args = []
        for thing in self.args:
            args.append(getattr(from_cmd, thing))
        if self.varargs is not None:
            args += getattr(from_cmd, self.varargs)
        self.func(*args)



    def setup(self):

        parser = ArgumentParser(prog=sys.argv[0] + " " + self.name,  description=self.func.__doc__)

        offset = len(self.args) - len(self.defaults)
        for x in range(len(self.args)):
            thing = self.args[x]
            d = {}

            d['help'] = self.annotations[thing]
            prefix=''
            if (x-offset) >= 0:
                default = self.defaults[x-offset]
                d['default'] = default
                d['dest'] = thing
                prefix='--'
                if type(default) == bool:
                    d['action'] = 'store_true'
        
            #print(prefix+thing, d)
            parser.add_argument(prefix+thing,**d)
        if self.varargs:
            parser.add_argument(self.varargs,nargs='+', help=self.annotations[self.varargs])
        return parser

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
        cp = ConfigParser()
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

@Command.register("log")
def cmd_log():
    "Outputs a git log"
    global GIT_DIR
    git_helper(["log"], git_dir=GIT_DIR)

@Command.register("add")
def cmd_add(verbose:"Be verbose"=False, *file:"File to add"):
    "Adds a file to the index"
    global GIT_DIR

    for f in file:
        if verbose:
            print("Added", f)
        if not os.path.exists(f):
            print("File does not exist")
        add_to_index(f, git_dir=GIT_DIR)

@Command.register("status")
def cmd_status(verbose:"Be verbose"=False):
    "Shows the status of the index and the file system"
    global GIT_DIR
    r = diff_index(git_dir=GIT_DIR)
    for item in r.values():
        if item['treeHash'] == '0000000000000000000000000000000000000000':
            print("%s - add" % fix_git_to_path(item['name']))
    index_files = ls_files(git_dir=GIT_DIR)
    for file in index_files.values():
        #compare this hash to the work hash
        fspath = fix_git_to_path(file['name'])
        workhash = hash_object(filename=fspath, write=False, git_dir=GIT_DIR)
        if workhash != file['hash']:
            print("%s - modified" % fspath)

@Command.register("diff")
def cmd_diff(verbose:"Be verbose"=False, *file:"File to diff"):
    "Diffs the file system with the index"
    index_files = ls_files(git_dir=GIT_DIR)
    for item in file:
        gitpath = fix_path_to_git(item)
        blob = index_files[gitpath]['hash']
        index_file = unpack_file(blob, git_dir=GIT_DIR)
        p = subprocess.Popen(["vimdiff", index_file, item])
        p.wait()
        os.unlink(index_file)

@Command.register("commit")
def cmd_commit(msg:"Commit message"=None, verbose:"Be verbose"=False):
    "Commits the index"
    tree = write_tree(git_dir=GIT_DIR)
    if verbose:
        print("New tree is", tree)
    commit = commit_tree(tree, msg, git_dir=GIT_DIR)
    if verbose:
        print("New commit is", commit)

    git_helper(["update-ref", "HEAD", commit], git_dir=GIT_DIR)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        Command.print_usage()
        sys.exit(1)
    cmd_s = sys.argv[1]

    cp = ConfigParser()
    cp.read(os.path.expanduser('~/.dotkeeper/config'))
    global GIT_DIR
    GIT_DIR = os.path.expanduser(os.path.join(cp.get("dotkeeper", "base_dir", fallback="~/.dotkeeper/repo"), "repo"))
  
    cmd = Command.get_command(cmd_s)
    if cmd is None:
        Command.print_usage()
        sys.exit(0)
    parser = cmd.setup()
    _args = parser.parse_args(sys.argv[2:])
    cmd.call_with(_args)


