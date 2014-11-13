

"""HWRT (handwriting recognition toolkit) is a collection of tools which
   can be used for handwriting recognition. It offers much documentation.

   If any questions are not covered by the documentation or if difficulties
   with using HWRT occur, please contact info@martin-thoma.de"""

from pkg_resources import get_distribution, DistributionNotFound
import os.path

try:
    _dist = get_distribution('hwrt')
    # Normalize case for Windows systems
    dist_loc = os.path.normcase(_dist.location)
    here = os.path.normcase(__file__)
    if not here.startswith(os.path.join(dist_loc, 'hwrt')):
        # not installed, but there is another version that *is*
        raise DistributionNotFound
except DistributionNotFound:
    __version__ = 'Please install this project with setup.py'
else:
    __version__ = _dist.version
