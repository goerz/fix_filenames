#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Recursively rename all the given files and folders so that their names only
consist of 'safe' ASCII characters.
"""

import os
import sys
from optparse import OptionParser
from glob import glob

import logging

ALLOWED  = u"abcdefghijklmnopqrstuvwxyz"
ALLOWED += u"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ALLOWED += u"0123456789"
ALLOWED += u"_-[]*(){}.,;+^!&#$=@'~"
ALLOWED += u" %\r\n" # this are arguably ok

REPL = {} # global dict of replacements


def write_replacements(filename):
    """ Write all replacements to a file, in pairs of lines, so that each first
        line defines a string to be replaced (unicode-escaped), and each second line
        defines a replacement
    """
    repl_fh = open(filename, 'w')
    for orig, repl in REPL.items():
        print >> repl_fh, orig.encode('unicode-escape')
        print >> repl_fh, repl
    repl_fh.close()


def resolved(name):
    """ Return True if the given name contains no illegal characters anymore """
    result = True
    for char in list(name):
        if char not in ALLOWED:
            result = False
    return result


def enter_rule(orig_name, new_name, replacements_file=None):
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
    if replacements_file is not None:
        write_replacements(replacements_file)


def get_new_filename(old_filename, encoding='utf-8', replacements_file=None):
    """ Perform all necessary replacements in old_filename, and return the
        result. Input and output are assumed to be byte-strings with the given
        encoding.
    """
    u_new_filename = unicode(old_filename, encoding)
    # Replace what we can in first pass
    for orig, repl in REPL.items():
        u_new_filename = u_new_filename.replace(orig, repl)
    while not resolved(u_new_filename):
        # If the first pass didn't resolve all illegal characters, we have to
        # ask for additional replacement rules and apply those as well
        enter_rule(old_filename, u_new_filename, replacements_file)
        for orig, repl in REPL.items():
            u_new_filename = u_new_filename.replace(orig, repl)
    return u_new_filename.encode(encoding, 'replace')


def fix_non_ascii_name(name, options):
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
            fix_non_ascii_name(item, options)
        os.chdir('..')
        print "cd %s" % os.getcwd()
        logging.info("cd %s", os.getcwd())
    elif os.path.isfile(name) or os.path.islink(name):
        new_filename = get_new_filename(name, options.encoding,
                                        options.replacements)
        if new_filename != name:
            print "MOVE '%s' -> '%s'" % (name, new_filename)
            logging.info("mv '%s' -> '%s'", name, new_filename)
            if not options.dry_run:
                os.rename(name, new_filename)
    else:
        print "In %s, skipping %s" % (os.getcwd(), name)


def main(argv=None):
    """ Run program """
    if argv is None:
        argv = sys.argv
        arg_parser = OptionParser(
        usage = "usage: %prog [options] FOLDER",
        description = __doc__)
        arg_parser.add_option(
          '--logfile', action='store', dest='logfile',
          default='fix_filenames.log', help="Name of logfile")
        arg_parser.add_option(
          '--encoding', action='store', dest='encoding',
          default='utf-8', help="Encoding of filesystem")
        arg_parser.add_option(
          '-n', '--dry-run', action='store_true', dest='dry_run',
          help="Dry-run, don't rename any files")
        arg_parser.add_option(
          '-y', action='store_true', dest='dont_ask',
          help="Do not ask for confirmation before renaming files")
        arg_parser.add_option(
          '--replacements', action='store', dest='replacements',
          help="Name of file containing replacements. File must contain pairs "
          "of lines. Each first line must contain a string to be replaced "
          "(with unicode escapes). Each second line must contain a replacement "
          "string. Interactively defined replacements will be added to the "
          "file.")
        options, args = arg_parser.parse_args(argv)
    cwd = os.getcwd()
    logging.basicConfig(filename=options.logfile, format='%(message)s',
                        filemode='w', level=logging.INFO)
    if len(args) <= 1:
        arg_parser.error("Nothing to operate on. Specify FOLDER.")
    if options.replacements is not None:
        options.replacements = os.path.abspath(options.replacements)
        try:
            repl_fh = open(options.replacements)
            print "Initial replacement rules: "
            while True:
                orig = repl_fh.readline()
                repl = repl_fh.readline()
                if (orig == '' or repl == ''):
                    break
                orig = orig[:-1].decode('unicode-escape')
                repl = repl[:-1]
                REPL[orig] = repl
                print "%s -> %s" % (orig.encode('unicode-escape'), repl)
            print ""
            repl_fh.close()
        except IOError:
            pass
    if options.dry_run:
        print "Dry Run. No files will be renamed"
        logging.info("Dry Run. No files will be renamed")
    if not options.dry_run and not options.dont_ask:
        answer = raw_input("This script will rename files on your hard drive. "
                "Are you sure you want to continue? yes/[no]: ")
        if answer != 'yes':
            return 0
    for arg in args[1:]:
        path, name = os.path.split(arg)
        if path != '':
            os.chdir(path)
        fix_non_ascii_name(name, options)
        os.chdir(cwd)
    return 0


if __name__ == "__main__":
    sys.exit(main())
