import os
import re
import shutil
import argparse


def main():
    # init argparser
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='*.bib file to process')
    parser.add_argument('-l', '--length', type=int,
                        help='Maximum length of filename', default=100)
    parser.add_argument('-m', '--moveall', action='store_true',
                        help='Attached files will be moved/renamed if possible')
    parser.add_argument('-o', '--overwriteall', action='store_true',
                        help='If a destination file already exists, it will be '
                             'overwritten')
    args = parser.parse_args()

    # prepare regular expressions
    re_entrytype = re.compile('.+(?={)')
    re_attachedfile = re.compile('(?<={:).+(?=:[A-Za-z]{3}})')
    re_author = re.compile(' *author *= *.+')
    re_number = re.compile(' *number *= *.+')
    re_revision = re.compile(' *revision *= *.+')
    re_title = re.compile(' *title *= *.+')
    re_type = re.compile(' *type *= *.+')
    re_year = re.compile(' *year *= *.+')
    re_field = re.compile('(?<={).+(?=})')
    re_surname = re.compile('\w+(?=,)|(\w+)$')

    # define characters to replace
    replace_characters = {'/': '', '\\': '', '?': '', '%': '', '*': '',
                          ':': '',
                          '|': '', '"': '', '<': '', '>': ''}

    # open file and read file contents
    fh = open(args.filename)
    file_content = fh.read()
    fh.close()

    # split file-contents by blank lines
    entries = re.split('\n\n@', file_content, flags=re.MULTILINE)

    # store filePath
    filePath = os.path.split(args.filename)[0]

    # prepare list for modified entries
    new_entries = []

    # iterate entries
    for entry in entries:
        # check if file is attached to entry
        match = re_attachedfile.search(entry)
        if match is not None:
            # check if file exists
            if os.path.isfile(filePath + '/' + match.group(0)) or \
                    os.path.isfile(match.group(0)):
                entrytype = re_entrytype.search(entry).group(0)
                oldpath = match.group(0)
                extension = os.path.splitext(oldpath)[1]
                # switch types
                if entrytype == 'Standard':
                    standardtype = re_field.search(
                        re_type.search(entry).group(0)) \
                        .group(0)
                    number = re_field.search(re_number.search(entry).group(0)) \
                        .group(0)
                    revision = re_field.search(
                        re_revision.search(entry).group(0)) \
                        .group(0)
                    filename = standardtype + '_' + number + '_' + revision
                else:
                    author = re_field.search(re_author.search(entry).group(0)) \
                        .group(0)
                    authors = re.split(' and ', author)
                    title = re_field.search(re_title.search(entry).group(0)) \
                        .group(0)
                    year = re_field.search(re_year.search(entry).group(0)) \
                        .group(0)
                    # format authors
                    if len(authors) > 0:
                        # reduce author names to surname
                        for jj in range(len(authors)):
                            authors[jj] = re_surname.search(authors[jj]).group(
                                0)
                        # for authors with more than three, append "et al."
                        if len(authors) > 3:
                            author = ', '.join(authors[0: 3]) + ' et al.'
                        else:
                            author = ', '.join(authors)
                    filename = author + ' - ' + year + ' - ' + title
                # remove unallowed characters from filename
                for old, new in replace_characters.items():
                    filename = filename.replace(old, new)
                # check if subfolder type exists
                if not os.path.isdir(filePath + '/' + entrytype):
                    os.mkdir(filePath + '/' + entrytype)
                # add subfolder and file extension
                filename = entrytype + '/' + filename[
                                             0: args.length] + extension
                # ask for file change
                if filename != oldpath:
                    print('Found an attached file, which does not match file '
                          'naming convention:')
                    print(oldpath + ' -> ' + filename)
                    if args.moveall:
                        userInput = 'y'
                    else:
                        userInput = 'u'
                    while userInput not in ['y', 'n']:
                        userInput = input('Move and rename file? [y/n]: ')
                    # if "y" rename/move file and edit bibtex-entry
                    if userInput == 'y':
                        # check if destination file already exists
                        if os.path.isfile(filePath + '/' + filename):
                            if args.overwriteall:
                                userInput = 'y'
                            else:
                                userInput = 'u'
                            while userInput not in ['y', 'n']:
                                userInput = input(
                                    'Found a file at destination, '
                                    'overwrite? [y/n]: ')
                        else:
                            userInput = 'y'
                        if userInput == 'y':
                            entry = entry[0: match.start()] + filename + \
                                    entry[match.end():]
                            if os.path.isfile(filePath + '/' + oldpath):
                                shutil.move(filePath + '/' + oldpath,
                                            filePath +
                                            '/' + filename)
                            else:
                                shutil.move(oldpath, filePath + '/' + filename)
                        else:
                            print('Skipping file.')
            else:
                print('File ' + match.group(0) + ' does not exist.')

        # build new entries
        new_entries.append(entry)

    # reconstruct file contents
    file_content = '\n\n@'.join(new_entries)

    # write contents to file
    fh = open(args.filename, 'w')
    fh.write(file_content)
    fh.close()
