import hashlib
from uuid import uuid1, uuid4


def uuid():
    '''
    Return a new universally unique id as a unicode string consisting of
    only ASCII characters.

    The returned string can be expected to be highly unlikely to be generated
    twice.

    There is no format restriction on the returned strings, so this algorithm
    can change in the future.
    The returned string can not be expected to follow the format of RFC 4122.

    One important property needs to be preserved when the algorithm changes:
    The uuids returned by the new algorithm should be highly unlikely to ever
    collide with previously generated uuids.

    E.g, it can be achieved by returning progressively longer strings with
    each change, or adding a constant (but algorithm specific) prefix to all
    uuids generated.
    '''
    # uuid1 by itself has privacy/security concerns, so hash it
    # + add a random uuid to remain collision free
    scrambled_uuid1 = hashlib.sha256(uuid1().bytes).hexdigest()[:32]
    unicode = ''.__class__
    return unicode(scrambled_uuid1) + '-' + unicode(uuid4())
