#!/usr/bin/env python 
# -*- coding: utf-8 -*-

"""
Recursively rename all the given files and folders so that their names only
consist of 'safe' ASCII characters.
"""

import os
import sys
from glob import glob

import logging

ALLOWED  = u"abcdefghijklmnopqrstuvwxyz"
ALLOWED += u"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ALLOWED += u"0123456789"
ALLOWED += u"_-[]*(){}.,;+^!&#$=@'~"
ALLOWED += u" %\r\n" # this are arguably ok

REPL = {} # global dict of replacements


def resolved(name):
    """ Return True if the given name contains no illegal characters anymore """
    result = True
    for char in list(name):
        if char not in ALLOWED:
            result = False
    return result


def enter_rule(orig_name, new_name):
    """ Ask the user for new replacement rule, and store it.
    """
    print ""
    print "Original  : %s" % orig_name
    print "Unresolved: %s" % new_name.encode('unicode-escape')
    print ""
    while True:
        orig = raw_input(u"Enter string to be replaced: ")
        repl = raw_input(u"Enter string to replace it with: ")
        try:
            orig = orig.decode('unicode-escape')
            if len(orig) == 0:
                print "Empty replacement string"
                continue
            break
        except UnicodeDecodeError, message:
            print message
            continue
    print ""
    REPL[orig] = repl


def get_new_filename(old_filename):
    """ Perform all necessary replacements in old_filename, and return the
        result
    """
    u_new_filename = unicode(old_filename, 'utf-8')
    # Replace what we can in first pass
    for orig, repl in REPL.items():
        u_new_filename = u_new_filename.replace(orig, repl)
    while not resolved(u_new_filename):
        # If the first pass didn't resolve all illegal characters, we have to
        # ask for additional replacement rules and apply those as well
        enter_rule(old_filename, u_new_filename)
        for orig, repl in REPL.items():
            u_new_filename = u_new_filename.replace(orig, repl)
    return u_new_filename.encode('ascii', 'replace')


def fix_non_ascii_name(name):
    """ Recursively rename the file or folder with the given name so that its
        name, and the name of all files it contains only consists of 'safe' ASCII
        characters
    """
    if os.path.isdir(name) and not os.path.islink(name):
        os.chdir(name)
        print "cd %s" % os.getcwd()
        logging.info("cd %s", os.getcwd())
        glob_list = glob('*')
        for item in glob_list:
            item = os.path.split(item)[-1] # strip './'
            fix_non_ascii_name(item)
        os.chdir('..')
        print "cd %s" % os.getcwd()
        logging.info("cd %s", os.getcwd())
    elif os.path.isfile(name) or os.path.islink(name):
        new_filename = get_new_filename(name)
        if new_filename != name:
            print "MOVE '%s' -> '%s'" % (name, new_filename)
            logging.info("mv '%s' -> '%s'", name, new_filename)
            #os.rename(name, new_filename)
    else:
        print "In %s, skipping %s" % (os.getcwd(), name)


def main(argv=None):
    """ Run program """
    if argv is None:
        argv = sys.argv
    cwd = os.getcwd()
    logging.basicConfig(filename='fix_filenames.log', format='%(message)s', 
                        filemode='w', level=logging.INFO)
    for arg in argv[1:]:
        path, name = os.path.split(arg)
        if path != '':
            os.chdir(path)
        fix_non_ascii_name(name)
        os.chdir(cwd)
    return 0


if __name__ == "__main__":
    sys.exit(main())
