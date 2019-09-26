'''
I am providing the content hash functions.
'''

import hashlib

READ_BLOCK_SIZE = 1024 ** 2

# hashes are created from {length of content}:content;
# similarity to http://cr.yp.to/proto/netstrings.txt are not accidental:
# length is hashed with content AND there is a known suffix


def _add_prefix(hash, size):
    hash.update(f'{size}:'.encode('ascii'))


def _add_suffix(hash, size):
    hash.update(f';{size}'.encode('ascii'))


def file(file, file_size):
    '''
    Read file and return sha512 hash for its content.

    Closes the file.
    Can process BIG files.
    '''

    hash = hashlib.sha512()
    _add_prefix(hash, file_size)

    bytes_read = 0

    with file:
        while True:
            block = file.read(READ_BLOCK_SIZE)
            if not block:
                break
            bytes_read += len(block)
            hash.update(block)

    assert bytes_read == file_size

    _add_suffix(hash, file_size)
    return ''.__class__(hash.hexdigest())


def bytes(bytes):
    '''
    Return sha512 hash for bytes.
    '''
    hash = hashlib.sha512()
    _add_prefix(hash, len(bytes))
    hash.update(bytes)
    _add_suffix(hash, len(bytes))
    return ''.__class__(hash.hexdigest())
