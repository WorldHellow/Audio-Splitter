# -*- coding: iso-8859-1 -*-

import codecs, gzip, sys
from tempfile import mkstemp

def zopen(fileName, mode = 'r'):
    """
    automatic detection for
    compressed file types : *.gz
    stdio                 : -, stdin, stdout, stderr
    /dev/null             : null, nil

    ATTENTION:
    When dealing with text files use uopen instead of zopen
    in order to support easy encoding transformations.
    Use zopen e.g. for reading binary data.
    """

    if fileName == '-':
	if mode == 'w' or mode == 'a':
	    return sys.stdout
	elif mode == 'r':
	    return sys.stdin
	else:
	    raise IOError('stdin/stdout do not support mode "%s"' % mode)
    elif fileName == 'stdin':
	if mode == 'r':
	    return sys.stdin
	else:
	    raise IOError('stdin does not support mode "%s"' % mode)
    elif fileName == 'stdout':
	if mode == 'w' or mode == 'a':
	    return sys.stdout
	else:
	    raise IOError('stdout does not support mode "%s"' % mode)
    elif fileName == 'stderr':
	if mode == 'w' or mode == 'a':
	    return sys.stderr
	else:
	    raise IOError('stderr does not support mode "%s"' % mode)
    elif fileName == 'null' or fileName == 'nil':
	return open('/dev/null', mode)
    elif fileName.endswith('.gz'):
	return gzip.open(fileName, mode)
    else:
	return open(fileName, mode)

def zclose(fd):
    if fd != sys.stdin and fd != sys.stdout and fd != sys.stderr:
	fd.close()


def uopen(fileName, encoding = 'utf-8', mode = 'r'):
    """
    universal unicode open:
    files are opened such that characters are encoded as unicode
    using the specified encoding and unicode is expected when
    characters are written (and decoded using the specified encoding);
    file type detection is supported (see zopen)
    """
    encoder, decoder, streamReader, streamWriter = codecs.lookup(encoding)

    fd = zopen(fileName, mode)

    if mode == 'w' or mode == 'a':
	return streamWriter(fd)
    elif mode == 'r':
	return streamReader(fd)
    else:
	return codecs.StreamReaderWriter(fd, streamReader, streamWriter)

def uread(fileName, encoding = 'utf-8'):
    return uopen(fileName, encoding, 'r')

def uappend(fileName, encoding = 'utf-8'):
    return uopen(fileName, encoding, 'a')

def uwrite(fileName, encoding = 'utf-8'):
    return uopen(fileName, encoding, 'w')

def uclose(fd):
    zclose(fd.stream)

#def utemp(encoding = 'utf-8'):
#    encoder, decoder, streamReader, streamWriter = codecs.lookup(encoding)
#    fd, fileName = mkstemp()
#    return codecs.StreamReaderWriter(fd, streamReader, streamWriter), fileName

def iterLines(filename, encoding = 'utf-8'):
    """
    iterate over lines in file
    empty lines or lines starting with '#' or ';;' are discarded
    """
    fd = uopen(filename, encoding, 'r')
    for line in fd:
	line = line.strip()
	if line and not line.startswith('#') and not line.startswith(';;'):
	    yield line
    uclose(fd)

