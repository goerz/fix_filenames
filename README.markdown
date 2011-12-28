# fix_filenames

[http://github.com/goerz/LPBS](http://github.com/goerz/fix_filenames)

Author: [Michael Goerz](http://michaelgoerz.net)

Recursively rename all the given files and folders so that their names only
consist of 'safe' ASCII characters.


## Command Line Options ##


Usage: fix_filenames.py [options] FOLDER

 Recursively rename all the given files and folders so that their names only
consist of 'safe' ASCII characters.

    Options:
      -h, --help            show this help message and exit
      --logfile=LOGFILE     Name of logfile. Default: fix_filenames.log
      --encoding=ENCODING   Encoding of filesystem. Normally, this is detected
                            automatically.
      -n, --dry-run         Dry-run, don't rename any files
      -y                    Do not ask for confirmation before renaming files
      --replacements=REPLACEMENTS
                            Name of file containing replacements. File must
                            contain pairs of lines. Each first line must contain a
                            string to be replaced (with unicode escapes). Each
                            second line must contain a replacement string.
                            Interactively defined replacements will be added to
                            the file.
      --allowed=ALLOWED     String of characters to be added to the default set of
                            allowed characters (unicode-escaped). The default
                            character set consists of the english alphabet,
                            digits, space, and the characters
                            _-[]*(){}",;+^!&#$=@~. For example, --allowed='\n\r'
      --forbidden=FORBIDDEN
                            String of characters to be removed from the default
                            set of allowed characters. For example, to not allowed
                            spaces in filenames, use --forbidden=' '


## Recommended Usage ##

For safety, it is best to call the program with options `-n` and
`--replacements` to build a list of replacements without renaming anything.
Then -- after carefully examining the log file from the first run -- the program
should be run again, using the previously generated list of replacements to
perform all necessary replacements non-interactively.

You may set the set of allowed and forbidden characters depending on your
operating system and other requirements (e.g. no spaces in filenames).
See the [Filename Wikipedia entry][1]

Note that special care must be taken match the encoding to the one that is used
by your file system!

[1]: http://en.wikipedia.org/wiki/Filename
