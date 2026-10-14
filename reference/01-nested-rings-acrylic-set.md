# 01 — The nested-ring toy: four elements, the bore set off-centre

![](01-nested-rings-acrylic-set.png)

Video frame (phone, portrait, mute button bottom right). Hand drives a pen through a hole; the set is laser-cut clear acrylic, blue- and orange-tinted, with tooth scales and spoke-rows of countersunk holes etched in.

## The four elements, outside in

| # | Element | Teeth (scaled to the 180 band) | Notes |
|---|---|---|---|
| 1 | Outer ring, fixed | 200+, label reads 250; runs off the frame | teeth on the inner surface only |
| 2 | Ring etched "XL-5 180" | 180 outside, about 168 bore | an annulus toothed on both edges; its bore is off its own centre |
| 3 | Blue annulus with the hole rows | about 142 outside, about 65 bore | same kind of piece, nested in ring 2's bore and meshed with it; the annulus is wide at the left and thin at the upper right, so its bore is off its centre too |
| 4 | The rider | about 40 | a toothed wheel rolling in ring 3's bore, pen in a hole near its rim |

- Rings 2 and 3 together are the carrier. Turning ring 3 inside ring 2 by some number of teeth adds their two offsets or cancels them, and the teeth hold the setting while drawing. That setting is how far the rider's bore sits from the carrier's centre: the toy's eccentricity knob.
- The carrier rolls round inside ring 1 as one piece, so the set offset is carried round and turned with the carrier's own spin.
- Every contact is stacked at the upper right under the hand; on the left and bottom all the gaps are open.

## The trace

- One red stroke so far: a tall narrow loop from the rider down through the bore and back up, pointed at the far end. With the bore-to-rider ratio near 65:40 the rider's loop is a lopsided ellipse.
- Purple smears at the top of the rider and at the bottom of the bore are pen starts from earlier attempts.

## For this project

- `ring_carrier.py`: a carriage step that carries everything before it, turned by its own spin, out to an off-centre bore, and round the fixed ring. The rider is whatever arm comes before it, and a carrier before a carrier is a ring in a ring in a ring.
- `reference/plots/01-nested-rings.ini` is this frame as a file: a 40-in-65 gear as the rider, a 144-in-180 carrier with the bore 6 units off centre.
- The rider's rate round its bore against the carrier's trip round ring 1 is set by the hand, not by teeth, so it is a free `cycles` on the rider.
