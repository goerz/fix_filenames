#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Recursively rename all the given files and folders so that their names only
consist of 'safe' ASCII characters.
"""

import os
import sys
import shutil
import filecmp
import unicodedata
from optparse import OptionParser
from glob import glob

import logging

ALLOWED  = u"abcdefghijklmnopqrstuvwxyz"
ALLOWED += u"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ALLOWED += u"0123456789"
ALLOWED += u"_-[]*(){}.,;+^!&#$=@'~"
ALLOWED += u'"'
ALLOWED += u" "

REPL = {} # global dict of replacements


def file_folder_cmp(f1, f2):
    """ Compare given files or folders """
    if os.path.isfile(f1) and os.path.isfile(f2):
        return filecmp.cmp(f1, f2)
    if os.path.isdir(f1) and os.path.isdir(f2):
        diff = filecmp.dircmp(f1, f2)
        if len(diff.diff_files) > 0:
            return False
        if len(diff.funny_files) > 0:
            return False
        if len(diff.left_only) > 0:
            return False
        if len(diff.right_only) > 0:
            return False
        for directory in diff.common_dirs:
            if not file_folder_cmp(os.path.join(f1, directory),
                                   os.path.join(f2, directory)):
                return False
        return True
    return False


def safe_chdir(folder):
    """ Change the current directory to the given folders, print/log where we
        are, and return True. If folder cannot be changed, stay where we are and
        return False.
    """
    try:
        os.chdir(folder)
        success = True
    except OSError, message:
        print "ERROR: Can't change to %s: %s" % (folder, message)
        logging.error("ERROR: Can't change to %s: %s", folder, message)
        success = False
    print "cd %s" % os.getcwd()
    logging.info("cd %s", os.getcwd())
    return success


def write_replacements(filename):
    """ Write all replacements to a file, in pairs of lines, so that each first
        line defines a string to be replaced (unicode-escaped), and each second
        line defines a replacement
    """
    repl_fh = open(filename, 'w')
    for orig, repl in REPL.items():
        print >> repl_fh, orig.encode('unicode-escape')
        print >> repl_fh, repl
    repl_fh.close()


def resolved(name, allowed=ALLOWED):
    """ Return True if the given name contains no illegal characters anymore """
    result = True
    for char in list(name):
        if char not in allowed:
            result = False
    return result


def enter_rule(orig_name, new_name, allowed=ALLOWED, replacements_file=None):
    """ Ask the user for new replacement rule, and store it.
    """
    print ""
    print "Original  : %s" % orig_name.encode('unicode-escape')
    print "Unresolved: %s" % new_name.encode('unicode-escape')
    print "Illegal characters:"
    for letter in new_name:
        if letter not in allowed:
            letter_escaped = letter.encode('unicode-escape')
            try:
                letter_name = unicodedata.name(letter)
            except ValueError:
                letter_name = 'n/a'
            print "%s: %s" % (letter_escaped, letter_name)
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


def get_new_filename(old_filename, allowed=ALLOWED,
    encoding=sys.getfilesystemencoding(), replacements_file=None):
    """ Perform all necessary replacements in old_filename, and return the
        result. Input and output are assumed to be byte-strings with the given
        encoding.
    """
    u_old_filename = unicode(old_filename, encoding)
    u_new_filename = unicode(old_filename, encoding)
    # Replace what we can in first pass
    for orig, repl in REPL.items():
        u_new_filename = u_new_filename.replace(orig, repl)
    while not resolved(u_new_filename, allowed):
        # If the first pass didn't resolve all illegal characters, we have to
        # ask for additional replacement rules and apply those as well
        enter_rule(u_old_filename, u_new_filename, allowed, replacements_file)
        for orig, repl in REPL.items():
            u_new_filename = u_new_filename.replace(orig, repl)
    return u_new_filename.encode(encoding, 'replace')


def safe_file_rename(from_name, to_name):
    """ Rename file from_name to to_name, making sure not to overwrite anything
    """
    if from_name == to_name:
        return
    if os.path.islink(to_name):
        os.unlink(to_name)
        # unlinking should be safe, because the data exists elsewhere
        print "WARN: Removed existing link %s"  % to_name
        logging.warn("WARN: Removed existing link %s", to_name)
    if os.path.isfile(to_name):
        # If to_name already exists and the file is identical to the source
        # file, we can simply delete the source file
        try:
            if file_folder_cmp(from_name, to_name):
                logging.info("rm '%s'", from_name)
                os.unlink(from_name)
            else:
                print "ERROR: Non-identical files %s and %s exist already" \
                      % (from_name, to_name)
                logging.error("ERROR: Non-identical files %s and %s "
                             "exist already", from_name, to_name)
        except (IOError, OSError) as message:
            print "ERROR: Could not delete %s: %s" % ( from_name, message)
            logging.error("ERROR: Could not delete %s: %s", from_name, message)
    elif os.path.isdir(to_name):
        message = "%s is an existing folder" % to_name
        print "ERROR: Could not rename %s to %s: %s" \
                % (from_name, to_name, message)
        logging.error("ERROR: Could not rename %s to %s: %s",
                     from_name, to_name, message)
    else:
        try:
            shutil.move(from_name, to_name)
        except (IOError, OSError) as message:
            print "ERROR: Could not rename %s to %s: %s" \
                % (from_name, to_name, message)
            logging.error("ERROR: Could not rename %s to %s: %s",
                        from_name, to_name, message)


def safe_dir_rename(from_name, to_name):
    """ Rename folder from_name to to_name, making sure not to overwrite
        anything
    """
    if from_name == to_name:
        return
    if os.path.islink(to_name):
        os.unlink(to_name)
        # unlinking should be safe, because the data exists elsewhere
        print "WARN: Removed existing link %s"  % to_name
        logging.warn("WARN: Removed existing link %s", to_name)
    if os.path.isfile(to_name):
        message = "%s is an existing file" % to_name
        print "ERROR: Could not rename %s to %s: %s" \
                % (from_name, to_name, message)
        logging.error("ERROR: Could not rename %s to %s: %s",
                        from_name, to_name, message)
    if os.path.isdir(to_name):
        # If to_name already exists and directory and its contents is identical
        # to the source directory, we can simply delete the source directory
        try:
            if file_folder_cmp(from_name, to_name):
                logging.info("rm -r '%s'", from_name)
                shutil.rmtree(from_name)
            else:
                print "ERROR: Non-identical folders %s and %s exist already" \
                      % (from_name, to_name)
                logging.error("ERROR: Non-identical folders %s and %s "
                             "exist already", from_name, to_name)
        except (IOError, OSError) as message:
            print "ERROR: Could not delete folder %s: %s" \
                  % ( from_name, message)
            logging.error("ERROR: Could not delete folder %s: %s",
                         from_name, message)
    else:
        try:
            shutil.move(from_name, to_name)
        except (IOError, OSError) as message:
            print "ERROR: Could not rename folder %s to %s: %s" \
                % (from_name, to_name, message)
            logging.error("ERROR: Could not rename folder %s to %s: %s",
                        from_name, to_name, message)


def fix_non_ascii_name(name, options):
    """ Recursively rename the file or folder with the given name so that its
        name, and the name of all files it contains only consists of 'safe'
        ASCII characters
    """
    if os.path.isdir(name) and not os.path.islink(name):
        success = safe_chdir(name)
        if not success:
            return
        glob_list = glob('*')
        for item in glob_list:
            item = os.path.split(item)[-1] # strip './'
            fix_non_ascii_name(item, options)
        safe_chdir('..')
        new_dirname = get_new_filename(name, options.allowed, options.encoding,
                                        options.replacements)
        if new_dirname != name:
            print "MOVE DIR '%s' -> '%s'" % (name, new_dirname)
            logging.info("mv '%s' -> '%s'", name, new_dirname)
            if not options.dry_run:
                safe_dir_rename(name, new_dirname)
    elif os.path.isfile(name) or os.path.islink(name):
        new_filename = get_new_filename(name, options.allowed, options.encoding,
                                        options.replacements)
        if new_filename != name:
            print "MOVE '%s' -> '%s'" % (name, new_filename)
            logging.info("mv '%s' -> '%s'", name, new_filename)
            if not options.dry_run:
                safe_file_rename(name, new_filename)
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
        default='fix_filenames.log', help="Name of logfile. "
        "Default: fix_filenames.log")
    arg_parser.add_option(
        '--encoding', action='store', dest='encoding',
        default=sys.getfilesystemencoding(), help="Encoding of filesystem. "
        "Normally, this is detected automatically.")
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
    arg_parser.add_option(
        '--allowed', action='store', dest='allowed', default='',
        help="String of characters to be added to the default set of "
        "allowed characters (unicode-escaped). The default character set "
        "consists of the english alphabet, digits, space, and the characters "
        "_-[]*(){}\",;+^!&#$=@~. For example, --allowed='\\n\\r'")
    arg_parser.add_option(
        '--forbidden', action='store', dest='forbidden', default='',
        help="String of characters to be removed from the default set of "
        "allowed characters. For example, to not allowed spaces in filenames, "
        "use --forbidden=' '")
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
            # file doesn't exist yet, but that's okay
            pass
    print "Using filesystem encoding %s" % options.encoding
    logging.info("Using filesystem encoding %s", options.encoding)
    if options.dry_run:
        print "Dry Run. No files will be renamed"
        logging.info("Dry Run. No files will be renamed")
    if not options.dry_run and not options.dont_ask:
        answer = raw_input("This script will rename files on your hard drive. "
                "Are you sure you want to continue? yes/[no]: ")
        if answer != 'yes':
            return 0
    try:
        options.allowed = options.allowed.decode('unicode-escape')
    except UnicodeDecodeError, message:
        arg_parser.error("allowed options: %s" % message)
    options.allowed += ALLOWED
    try:
        options.forbidden = options.forbidden.decode('unicode-escape')
    except UnicodeDecodeError, message:
        arg_parser.error("allowed options: %s" % message)
    for char in options.forbidden:
        options.allowed = options.allowed.replace(char, '')
    print "Allowed characters: %s" % options.allowed.encode('unicode-escape')
    for arg in args[1:]:
        path, name = os.path.split(arg)
        success = True
        if path != '':
            success = safe_chdir(path)
        if success:
            fix_non_ascii_name(name, options)
        safe_chdir(cwd)
    return 0


if __name__ == "__main__":
    sys.exit(main())
