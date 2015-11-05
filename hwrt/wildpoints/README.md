I want to write an algorithm which detects all WILDPOINTs. The problem is
that there are other points like the dots in "i" and "j". Those should not
be falsely detected as WILDPOINTs.

## What is a WILDPOINT?
A WILDPOINT is a stroke which was not inteded to be written by the user.
Typically, it is only a single dot. It can savely be removed. Removing it does
either not affect the classification accuracy or even improve it.

## How the WILDPOINT detection algorithm can work
It is a classification problem. The classifier takes features of a stroke. Then
it has to decide between two classes: (1) IS_WILDPOINT (2) NO_WILDPOINT.

Possible features:

* length of the stroke
* minimum of temporal distance to previous stroke and next stroke
* minimum of spacial distance to previous stroke and next stroke


## TODO

- [x] Get dataset with
      - recordings with WILDPOINTs
      - recordings which have the tag "has-dot"
- [ ] Split set of recordings into training and test set of features
- [ ] Train classifier
- [ ] Test classifier
- [ ] Run over real data to annotate WILDPOINTs on a stroke-basis in recordings