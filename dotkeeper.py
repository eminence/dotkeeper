#!/usr/bin/env python

import sys
import os
import os.path
from optparse import OptionParser
import subprocess
import re
import stat

HASH = 0x00
STR  = 0x01
FILE = 0x02

class GitException(Exception):
    "Generic exception for git-related failures"
    pass

def git_helper(args, git_dir=None, stdout=None, stdin=None):
    "Launces git subprocesses, taking care of error checking and stuff"

    if git_dir is None:
        global GIT_DIR
        git_dir = GIT_DIR

    sout = None
    if stdout in (HASH, STR):
        sout = subprocess.PIPE

    sin = None
    if isinstance(stdin, basestring):
        sin = subprocess.PIPE

    p = subprocess.Popen(["git", "--git-dir=" + git_dir] + args, stdout=sout, stdin=sin)

    (outdata, errdata) = p.communicate(stdin)

    p.wait()

    if p.returncode != 0:
        raise GitException("Failed to do something!")

    if stdout == HASH:
        # the output of this git command is expected to return a hash.  let's grab it and return it
        hash = outdata.strip()
        return hash
    if stdout == STR:
        return outdata


def hash_object(filename=None, contents=None, git_dir=None):
    """
    Accepts either a filename or a string, and hashed the object, adding it
    to the git object db, and returns the hash identified
    """

    if filename and contents is None:
        return git_helper(["hash-object", "-w", filename], stdout=HASH, git_dir=git_dir)
    elif filename is None and contents is not None:
        return git_helper(["hash-object", "-w", "--stdin"], stdout=HASH, stdin=contents, git_dir=git_dir)
    else:
        raise GitException("no filename, and no contents")


def read_tree(tree, git_dir=None):
    "Read the contents of a git tree and returns a dictionary (see mk_tree for a description)"
    data = git_helper(["ls-tree", tree], stdout=HASH, git_dir=git_dir)
    matcher = re.compile("^(\\S+) (\\S+) (\\S+)\t(\S+)$")
    d = dict()
    for line in data.splitlines():
        m = matcher.match(line)
        if not m: 
            raise GitException("no match in ls-tree output")
        d[m.group(4)] = dict(mode=m.group(1), type=m.group(2), hash=m.group(3), name=m.group(4))
    return d
        

def unpack_object(hash, git_dir=None):
    "Unpacks a blob into a temporary file, and returns that filename"
    filename = git_helper(["unpack-file", hash], stdout=HASH, git_dir=git_dir)
    return os.path.abspath(filename)

def cat_file(hash, git_dir=None):
    "Returns the contents of a blob, as a string"
    contents = git_helper(["cat-file", "blob", hash], stdout=HASH, git_dir=git_dir)
    return contents

def commit_tree(tree, msg, parent="HEAD", git_dir=None):
    "Commits a tree.  Does NOT update the HEAD ref"
    xtra_args = []
    if parent:
        xtra_args += ["-p", parent]
    commit_hash = git_helper(["commit-tree", tree] + xtra_args, stdin=msg, stdout=HASH, git_dir=git_dir)
    return commit_hash


def mk_tree(contents):
    """\
    Makes a tree based on the contents specified.  `contents` is a dictionary, with filenames
    for keys, and values that are dictionaries with the following keys:

    mode = a string, for example '100644', 
           or an int, which will be converted to 
    type = a string, either 'blob' or 'tree'
    hash = a string, the hash of the blob or tree
    name = string, the name of the file (without any directory parts)

    See also: http://www.kernel.org/pub/software/scm/git/docs/git-mktree.html
    """

    tree_string = ""
    for item in contents.itervalues():
        item_ = dict()
        item_.update(item)
        if isinstance(item_['mode'], int):
            item_['mode'] = oct(item_['mode'])
        tree_string += "{mode} {type} {hash}\t{name}".format(**item_)

    return git_helper(["mktree"], stdout=HASH, stdin=tree_string)

def init(base_dir="~/.dotkeeper"):
    "Gets things going"

    base_dir = os.path.expanduser(base_dir)
    repo_dir = os.path.join(base_dir, "repo")
    global GIT_DIR
    GIT_DIR = repo_dir

    if not os.path.exists(repo_dir):
        os.makedirs(repo_dir)
    git_helper(["init"])

    # create new, empty config file.  this will be the first commit into the repo
    config_file = os.path.join(base_dir, "config")
    with open(config_file, "w") as f:
        f.write("# empty config file")

    config_hash = hash_object(config_file)

    # create tree for the .dotkeeper directory
    tree = dict(config=dict(
        name="config", 
        hash=config_hash,
        mode=stat.S_IFREG | stat.S_IRUSR | stat.S_IWUSR,
        type="blob"))

    dotkeeper_hash = mk_tree(tree)
   
    # tree for the /home directory, just contains .dotkeeper tree
    tree = {".dotkeeper": dict(
        name=".dotkeeper",
        type="tree",
        mode=stat.S_IFDIR,
        hash = dotkeeper_hash
        )}

    home_hash = mk_tree(tree)

    # tree for the root (/) directory.  just contains the home tree
    tree = {"home": dict(
        name="home",
        type="tree",
        mode=stat.S_IFDIR,
        hash=home_hash
        )}
    
    root_tree = mk_tree(tree)
    print "root_tree is:", root_tree

    commit_hash = commit_tree(root_tree, "Initial commit")
    print "commit hash is:", commit_hash
    
    git_helper(["update-ref", "HEAD", commit_hash])

def find_file(file, tree, git_dir=None):
    "recurses through the given tree, trying to find the blob hash for the given filepath"

    r = read_tree(tree, git_dir=git_dir)

    if not isinstance(file, list):
        file = filter(bool, file.split("/"))
    if len(file) == 1:
        if file[0] in r:
            return r[file[0]]
        else:
            return None

    if file[0] in r:
        x = r[file[0]]
        if x['type'] == 'tree':
            return find_file(file[1:], x['hash'], git_dir=git_dir)

def add_to_index(path, git_dir=None):
    """Adds the specified path to the index
    The path should be a real filesystem path"""

    # first add the object to the database
    hash = hash_object(filename=path, git_dir=git_dir)

    path_g = fix_path_to_git(path)

    # then add to index 
    git_helper(["update-index", "--add", "--cacheinfo", "100600",hash, path_g])


def diff_index(tree="HEAD", git_dir=None):
    """Show the differences between the index and the repo
    Returns a dictionary, with paths are keys, and values are dictionaries:
     * treeMode
     * treeHash
     * indexMode
     * indexHash
     * state
     * path
    """

    d = {}
    output = git_helper(["diff-index", tree, "--cached"], stdout=STR, git_dir=git_dir)
    matcher = re.compile("^:(\\d+) (\\d+) (\\S+) (\\S+) (\\S+)\t(\\S+)$")
    for line in output.splitlines():
        m = matcher.match(line)
        if not m: 
            raise GitException("no match in diff-index output")
        d[m.group(6)] = dict(treeMode=m.group(1),
                treeHash=m.group(3),
                indexMode=m.group(2),
                indexHash=m.group(4),
                state=m.group(5),
                name=m.group(6))


    return d

def diff_work(file=None, git_dir=None):
    """Shows the difference between the index and the filesystem
    SInce we're operating without a real-work tree, we have to diff manually by:
    unpacking the file from the object database, and diffing it with the filesystem
    """
    files = ls_files(file=file, git_dir=git_dir)


def fix_path_to_git(path):
    "Takes a file-system path and turns it into a path in the git tree"
    p = os.path.abspath(path)
    home = os.environ['HOME']
    user = os.environ['USER']
    if p.startswith(home):
        if not home.endswith(user):
            raise Exception("bad home/user")
        homeroot = home[1:-1-len(user)]
        return homeroot + p[len(home):]

    return p[1:]

def write_tree(git_dir=None):
    hash = git_helper(["write-tree"], stdout=HASH, git_dir=git_dir)
    return hash


def ls_files(file=None, git_dir=None):
    "show information about the index"
    # first, get a list of the files in the index
    args = ["ls-files", "--stage"]
    if file:
        args += ["--", file]
    output = git_helper(args, stdout=STR, git_dir=git_dir)
    matcher = re.compile("^(\\d+) (\\S+) (\\S+)\t(\\S+)$")
    d={}
    for line in output.splitlines():
        m = matcher.match(line)
        if not m:
            raise GitException("no match in ls-files output")
        d[m.group(4)] = dict(mode=m.group(1), hash=m.group(2), state=m.group(3), name=m.group(4))
    
    
    return d

def status(git_dir=None):
    "Prints out a git-like status"
    pass

GIT_DIR="/home/achin/.dotkeeper/repo"
from pprint import pprint
