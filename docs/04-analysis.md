# 4. Analysis

---

## 4.1 What came out, and getting it ready

### 4.1.1 The files on your disk

The run has finished. Let us see what we actually have.

**`md.xtc`** — the trajectory. This is the one that matters. It
holds the positions of your atoms at every point you asked to save, and
almost every analysis in this chapter reads from it.

**`md.gro`** — the very last frame, as a single structure. Useful
as a starting point if you want to continue the simulation, or if you
just want the final shape.

**`md.edr`** — the energies. Temperature, pressure, density and
all the rest, recorded through the run. We were already reading this
while the simulation was going.

**`md.log`** — the plain text record of what happened, including
the performance summary at the end.

**`md.cpt`** — the checkpoint, holding the complete state at the
moment it was written. Only needed for continuing a run.

**`md.trr`** — the full-precision trajectory. Ours is essentially
empty, because we set `nstxout` to zero and never asked for it. If you
did ask, this would be your largest file by far.

### 4.1.2 A peek inside the trajectory

You cannot open an `.xtc` in a text editor. It is binary, and there is
a good reason for that.

Think about what is in there. A modest system might have 50,000 atoms,
each with three coordinates, saved across a few hundred frames. That is
tens of millions of numbers. Written out as ordinary text, it would be
enormous and painfully slow to read. So the file is stored in a compact
binary form, with the coordinates rounded to a precision below anything
an atom could meaningfully move.

But you can still ask it about itself:

```bash

```

```bash
gmx check -f md.xtc
```


This tells you how many frames it contains, how much time separates
them, and how many atoms are in each. It is the first thing to run when
you sit down to analyse — partly to confirm you have what you expected,
and partly because you will need the frame count when planning anything.

It is also a quick way to catch a mistake. If you meant to save every 10
picoseconds and the file says 100, you know your `.mdp` did something
other than what you intended.

### 4.1.3 Fixing the trajectory before anything else

Here is something that surprises people: the raw trajectory is not ready
to analyse. Two things need correcting first, and neither of them is an
error.

**The molecule gets split across the box.** Remember the Snake game.
When a molecule drifts out through one face of the box, it comes back in from the opposite one — so your protein can end up drawn in two halves,
one at each edge. It looks shattered. It is not; it is simply being
displayed in pieces.

**The molecule tumbles.** It is floating freely in water, so it
drifts and rotates as it goes. For a movie this is distracting. For
measurements it is worse: if you measure how much your structure has
changed, you would mostly be measuring the tumbling rather than any real
change in shape.

So we fix both, once, and everything afterwards is built on solid
ground.

**Step one — put it back together and centre it**

```bash

```

```bash
echo -e "Protein\nProtein" | gmx trjconv -f md.xtc -s md.tpr -o pbc.xtc
\\
```

-pbc mol -center


`-pbc mol` keeps each molecule whole, so nothing is drawn split across
the boundary. `-center` places your chosen group in the middle of the
box and keeps it there, so the protein stops wandering off.

The two group names answer the two questions GROMACS asks: which group
to centre on, and which group to write out.

**Step two — stop the tumbling**

```bash

```

```bash
echo -e "Backbone\nProtein" | gmx trjconv -f pbc.xtc -s md.tpr -o
fitted.xtc \\
```

-fit rot+trans


This rotates and slides each frame so the molecule lines up as closely
as possible with its starting position. What remains is only the
internal motion — the parts genuinely changing shape — with the overall
spinning and drifting removed.

The two groups here answer: which part to line up on (Backbone, since it
is the stable framework), and which part to write out.

**Why two commands rather than one**

Because the order matters, and GROMACS will not let you do both at once.
The molecule has to be made whole first — trying to line up a structure
that is currently drawn in two halves would produce nonsense.

**Why this matters more than it looks**

This is not cosmetic. On a raw trajectory, two atoms sitting on opposite
sides of the box appear enormously far apart when they are actually
next-door neighbours. So anything involving distance — hydrogen bonds,
contacts, salt bridges, binding measurements — would quietly give you
the wrong answer.

Fix the trajectory once, here, and use the corrected file for everything
that follows.

**One caution:** keep the original `md.xtc`. The corrected file
has had information removed from it — the real positions in the box, and
the true orientation. A few analyses need those back, so never overwrite
your original.

### 4.1.4 Making a movie

Before measuring anything, watch it. A movie is the fastest way to catch
a disaster — a protein that came apart, a ligand that floated away — and
none of that is obvious from a graph.

The hard part is already done. Our `fitted.xtc` is exactly what a
movie needs: molecules kept whole, centred, and no longer tumbling.

**Thin it out first**

A movie does not need every frame. Aim for around a hundred:

```bash

```

```bash
echo "Protein" | gmx trjconv -f fitted.xtc -s md.tpr -o movie.xtc -skip
```
10


**Render the frames**

GROMACS prepares the trajectory but does not make video. For that we use
a molecular viewer. Save this as `movie.pml`:

```python

```bash
load frame_start.pdb, mol

load_traj movie.xtc, mol

bg_color white

hide everything

show cartoon, mol

color grey70, mol

color firebrick, ss H

color skyblue, ss S

orient

set ray_opaque_background, 1

mpng frame_, width=1200, height=900
```


Then run it and stitch the images into a video:

```bash

```

```bash
pymol -cq movie.pml

ffmpeg -framerate 15 -i frame_%04d.png -c:v libx264 -pix_fmt yuv420p
```
movie.mp4


Open-source PyMOL does all of this — no licence needed. The `-cq` flag
runs it without opening a window. For publication quality, add `set
ray_trace_frames, 1` before `mpng`, but expect it to take much
longer, so leave it off while you are still adjusting the view.

If the fiddly parts give you trouble, this is exactly the sort of task
an AI assistant handles well — ask it to adapt the script for your
system.

**What to look for**

Watch it once without trying to analyse anything. Does the protein hold
its shape or fall apart? Does the ligand stay in its pocket? Does
anything move in a way that looks physically wrong?

If the movie looks wrong, find out why before running a single
measurement. There is no point calculating anything from a broken
simulation. And if it looks fine, you now have a feel for what your
system did — which makes every number in the rest of this chapter easier
to interpret.

## 4.2 RMSD — how much has it changed?

RMSD is the first thing almost everyone plots, and it answers a simple
question: how different is the structure now compared to where it
started?

**How it works**

Take each atom. Measure how far it has moved from where it was in your
reference structure. Square all those distances, take the average, then
take the square root. That one number is your RMSD, usually given in
Ångströms.

Why square them? Because it makes RMSD notice when a few atoms go badly
wrong. One atom moving 4 Å counts for more than four atoms moving 1 Å
each. So if one part of your protein falls apart while the rest stays
fine, RMSD will tell you — which is usually what you want.

**The catch: you have to line things up first**

Here is what trips people up. Your molecule is floating in water, so it
drifts about and spins. If you just measure raw positions, a molecule
that has only turned around will show a big RMSD, even though its shape
has not changed at all.

So before measuring, we slide and rotate each frame until it sits on top
of the reference as neatly as possible. Whatever difference is left over
is real change in shape. This is the `-fit` step we already did to our
trajectory, and it is not optional — without it, RMSD tells you nothing
useful.

{{INTERACTIVE: rmsd-explainer}}

**Two separate choices: what to line up on, and what to measure**

GROMACS asks you two questions here, and people often answer both the
same way without thinking. They are different questions, and your
answers decide what the plot actually means.

**What to line up on** is your fixed point of view — the part you
are treating as "not moving." Usually the **backbone**, because it
is the stable framework of the protein. If you line up on a floppy loop
instead, the whole protein will appear to swing around it and your plot
will be nonsense.

**What to measure** is what you actually care about. Some useful
combinations:

*Backbone* — the standard choice. Tells you whether the overall fold
is holding together.

*All heavy atoms* — includes side chains, so numbers come out higher
and noisier. Side chains genuinely move a lot.

*One region only* — line up on the backbone, but measure just your
binding site, or just one domain. Now you are asking a focused question
instead of a general one.

*A ligand, lining up on the protein* — a very useful pairing. It tells
you whether the ligand stayed in its pocket, because you have made the
protein your fixed viewpoint and are watching the ligand move relative
to it.

**For complexes, run several**

If you have two molecules bound together — say a protein on DNA — no
single RMSD tells you enough. Run a few and compare:

*Line up on the DNA, measure the protein.* The DNA is now your fixed
viewpoint, so you are asking: has the protein stayed where it docked, or
slid along the groove?

*Line up on the protein, measure the DNA.* The reverse question: has
the DNA shifted or bent relative to the protein holding it?

*Each one against itself.* Line up on the protein and measure the
protein. Then do the same for the DNA. This asks whether each molecule
changed shape internally, ignoring the other completely.

*Everything together.* The overall picture, though it mixes internal
change and sliding into one number.

Put these side by side and you can work out what actually happened. Say
the whole-complex value is high. Is the protein deforming? Check the
protein against itself. Is the DNA bending? Check the DNA against
itself. Are they simply sliding apart while each stays rigid? Then both
individual values stay low while the cross-checked one climbs.

That last pattern is the interesting one, and you can only spot it by
comparing several curves. One line on its own leaves you knowing
something changed without knowing what.

```bash

```

```bash
gmx rms -s md.tpr -f fitted.xtc -o rmsd.xvg
```


It asks for the group to line up on first, then the group to measure.

**Reading the plot**

A typical curve climbs quickly at the start, then flattens out and
wanders around a steady value. That first climb is your structure
relaxing away from the crystal shape into something comfortable in
water. It is completely normal.

**The flattening is what you are looking for.** It suggests the
system has settled down and later frames are all sampling roughly the
same state. If the line is still climbing at the end of your run, the
simulation has not settled yet and you should not be drawing conclusions from it.

As a rough guide, a small protein often settles somewhere around 1–3 Å.
A large or floppy one will sit higher. There is no universal cut-off —
what counts as stable depends entirely on your system.

**Two things to keep in mind**

RMSD is one number summarising thousands of atoms, so it hides a lot. A
protein with one loop flailing about while everything else sits rock
solid can give the same value as one that is uniformly a bit loose. That
is exactly why RMSF comes next — it breaks the same information down
residue by residue.

And a low RMSD is not automatically good news. It means the structure
stayed close to where it started. That might mean it is stable, or it
might just mean nothing interesting happened in the time you ran for.

## 4.3 Radius of gyration — how compact is it?

RMSD asked “has it changed?” This one asks something different: “how
spread out is it?”

**How it works**

Find the centre of the molecule. Then measure how far every atom sits from that centre, and take the average — weighted by mass, so heavy
atoms count more. That average distance is the radius of gyration, or
Rg.

A tightly folded protein has all its atoms close to the centre, so Rg is
small. If it swells or comes apart, atoms spread out and Rg rises.

Think of it as the size of the ball the molecule fills.

{{INTERACTIVE: rg-explainer}}

**The nice thing: no lining up needed**

Unlike RMSD, Rg needs no reference and no superimposing. It only
measures distances *inside* the molecule, so it does not care where the
molecule sits in the box or which way it faces. Spin it, slide it across
the box — the number does not move at all.

That makes it a clean, independent measure. RMSD tells you how far you
have drifted from where you started. Rg tells you something about the
structure itself, frame by frame, with nothing to compare against.

**Running it**

```bash
echo "Protein" | gmx gyrate -s md.tpr -f fitted.xtc -o gyrate.xvg
```

Two things to know. gmx gyrate was rewritten in GROMACS 2024, so if you
are following an older tutorial and it behaves oddly, that is why — the
old version is still available as gmx gyrate-legacy. And GROMACS works
in nanometres, so expect values around 1–2 nm for a small protein rather
than 10–20 Ångströms.

**Reading the plot**

**A flat line** means the molecule is holding its shape. That is what
you want for a stable protein.

**A rising line** means it is expanding — unfolding, opening up, or
loosening. Watch the movie to see which.

**A falling line** means it is getting more compact. A small drop early
on is normal as the crystal structure settles into water.

You also get Rg separately along x, y and z. These say something about
*shape* rather than size. If all three are similar, the molecule is
roughly round. If one is much bigger, it is long and thin.

## 4.4 SASA — how much is exposed to water?

This one measures surface area: how much of the molecule is in contact
with the solvent around it.

**How it works**

Imagine rolling a ball the size of a water molecule over the surface of
your protein. The area that ball can reach is the solvent accessible
surface area, or SASA. Anything tucked away inside, where water cannot
get to it, does not count.

**Why it matters**

Proteins fold the way they do largely to hide their greasy parts.
Water-hating residues get buried in the core, water-loving ones face
outward. That arrangement is much of what holds a folded protein
together.

So SASA tells you whether that arrangement is holding. If buried parts
start becoming exposed, the structure is opening up.

The most useful trick is to split it. GROMACS can report the hydrophobic
and hydrophilic surface separately, and it is the **hydrophobic** number
you should watch. Total surface area going up is mildly interesting.
Greasy core becoming exposed to water is a real warning sign of
unfolding.

**Running it**

```bash
gmx sasa -s md.tpr -f fitted.xtc -o sasa.xvg -surface 'group "Protein"'
```

Add -or resarea.xvg to get a value per residue, which tells you *where*
the exposure is happening rather than just how much.

Values come out in square nanometres.

**The best use: measuring an interface**

For two molecules bound together, SASA gives you something genuinely
valuable — how large the contact area between them is.

The trick is to measure three times: the protein alone, the partner
alone, and the two together. Add the first two, subtract the third, and
what remains is the surface that got buried when they came together.

Buried area = SASA(protein) + SASA(DNA) − SASA(complex)

A large buried area means an extensive contact. And watching this number
over time tells you whether the interface is holding steady or quietly
coming apart — often more informative than RMSD for a binding study.

## 4.5 Hydrogen bonds — what is holding on to what?

Everything so far gave us one number for the whole molecule. Hydrogen
bonds are the first analysis that tells us about *specific* interactions
between *specific* atoms.

**What counts as a hydrogen bond**

A hydrogen bond forms when a hydrogen attached to nitrogen or oxygen
comes close to another nitrogen or oxygen. Each one is weak, but
proteins and DNA are held together by hundreds of them.

The important thing to understand is that the software calculates no
energy at all. It just applies two geometric rules: the donor and
acceptor must be closer than about 0.35 nm, and the angle must be
reasonably straight. If both hold, it counts as a bond.

This matters practically: **different programs use slightly different
rules**, so counts from GROMACS, VMD and MDAnalysis will not match.
Never compare a number from one tool with a number from another. Compare
within your own analysis only.

**Counting bonds between two molecules**

```bash
gmx hbond -s md.tpr -f fitted.xtc -num hbnum.xvg \\
```

-r 'group "Protein"' -t 'group "DNA"'

-r and -t are your two groups. Choosing two *different* groups is what
makes this intermolecular — you count only bonds between the partners,
ignoring what each makes internally.

Note that gmx hbond was rewritten in GROMACS 2024. It is easier to use
but dropped the ability to track individual bonds over time. The old one
is still there as gmx hbond-legacy.

**Reading the plot**

The count will jump around constantly, and that is correct. Hydrogen
bonds are weak and short-lived, breaking and reforming within
picoseconds. A flickering line is what real hydrogen bonding looks like.

So ignore individual spikes. Look at the **average** and whether it
holds steady. A stable average means the interface is intact. A count
drifting downward means the two molecules are letting go.

**The more useful question: which ones?**

The total count is the crude version. What you usually want is *which
residues* are doing the binding, and how reliably.

The measure for this is **occupancy** — the percentage of frames in
which a particular bond exists. A bond present in 90% of frames is a
real structural contact. One present in 5% is a passing brush.

That distinction turns a plot into a result. “The complex has about 12
hydrogen bonds” says little. “Arg248 holds the DNA backbone in 94% of
frames, while Lys120 only makes contact 20% of the time” says something
real about how the protein grips its target.

For this, MDAnalysis is the easier route:

```bash
import MDAnalysis as mda

from MDAnalysis.analysis.hydrogenbonds import HydrogenBondAnalysis

u = mda.Universe('md.tpr', 'fitted.xtc')

hb = HydrogenBondAnalysis(u, between=['protein', 'nucleic'])
```

hb.run() for donor, hyd, acceptor, count in hb.count_by_ids():

d, a = u.atoms[donor], u.atoms[acceptor]

print(f"{d.resname}{d.resid} — {a.resname}{a.resid}
{100*count/hb.n_frames:.0f}%")

Sort that list by percentage and the top of it *is* your result.

**Splitting the count — worth doing for protein–DNA**

Look at *what* is being contacted. Bonds to the phosphate backbone are
electrostatic grip — they hold on, but they would hold on to any
sequence. Bonds to the bases, especially in the major groove, are what
give **sequence specificity**. That is how a transcription factor
recognises its own site rather than random DNA.

To split them, make two index groups with gmx make_ndx — backbone atoms
(P, OP1, OP2, the sugar carbons) in one, base ring atoms (N1, C2, N3,
N7, O6) in the other — then run gmx hbond once against each.

Two curves, and comparing them answers the specificity question. A
protein making many backbone contacts and few base contacts is holding
tightly but reading nothing.

## 4.6 RMSF — which parts are moving?

RMSD gave us one number per frame. RMSF flips that around: one number
per residue.

Instead of asking “how much has the structure changed over time?”, it
asks “how much does each individual residue wobble?” So where RMSD
produces a line against time, RMSF produces a profile along the
sequence.

**How it works**

For each atom, work out its average position across the whole
trajectory. Then measure how far it strays from that average, frame by
frame, and take the root mean square. A residue that sits still has a
low value. One that swings about has a high one.

Note this needs the same superimposing as RMSD. If the molecule is
tumbling, every residue looks like it is moving. Our fitted.xtc already
handles that.

**Running it**

```bash
echo "Protein" | gmx rmsf -s md.tpr -f fitted.xtc -o rmsf.xvg -res -b
```
1000

-res averages over each residue rather than reporting every atom, which
is almost always what you want.

-b 1000 skips the first part of the run. This matters more here than
elsewhere — if you include the early relaxation, that settling motion
inflates every value. Only measure the equilibrated portion.

**A very useful extra:**

```bash
echo "Protein" | gmx rmsf -s md.tpr -f fitted.xtc -oq bfactors.pdb -res
```

This writes a structure file with the flexibility values stored in the
B-factor column. Open it in PyMOL and colour by B-factor, and you get
your protein painted by how much each part moves. It is far more
intuitive than a graph, and it makes a good figure.

**Reading the plot**

You are looking at peaks and valleys along the sequence.

**Peaks** are flexible regions — loops, exposed turns, and above all the
chain ends. The two termini are almost always the highest points on the
plot, because they are only attached at one side. That is expected and
rarely interesting.

**Valleys** are rigid regions — the hydrophobic core, helices and
sheets, and anything locked in place by a metal or a binding partner.

So the first thing to check is simply whether the profile makes sense.
If your helices are rigid and your loops are floppy, the simulation is
behaving. If a helix shows up as a peak, something has gone wrong there
— go and look at it.

**Comparing against the experiment**

Here is something worth knowing. Crystal structures carry a B-factor for
every atom, which measures how poorly localised that atom was in the
experiment. That is a rough experimental measure of flexibility, and it
is directly related to RMSF.

So you can plot your RMSF against the crystal B-factors and see whether
they agree. If the same regions are flexible in both, that is genuine
evidence your simulation is behaving realistically. It is one of the few
easy validation checks available, and worth doing.

**One caution**

RMSF measures how much something moves, not whether that movement
matters. A floppy surface loop with no function will dominate your plot
while contributing nothing biologically. Always read the profile
alongside what you know about the structure — the interesting result is
usually a change in flexibility somewhere that *should* be rigid.

For the index groups, gmx select is easier and more reliable than
make_ndx here, so I’ve led with it. Here’s the whole section.

## 4.7 Focusing on a specific part or domain of a molecule

Everything so far has treated the molecule as a whole. But most
questions are not about the whole molecule. What if we want to fix our
attention on one particular region or domain?

To do that, we first define the region as a group:

```bash

```

```bash
gmx select -s md.tpr -on domains.ndx -select \\
```

'domain_A = resid 96 to 180;

domain_B = resid 200 to 290'


That writes an index file with two named groups. From now on, add `-n
domains.ndx` to any analysis and it will offer them as choices. `gmx
rms`, `gmx rmsf`, `gmx gyrate`, `gmx sasa` and `gmx covar` all
work this way.

You can select by residue number, by chain, or even by proximity to
something else — `chain A`, or `within 0.5 of group "Ligand"`.

**What you fit on changes the question**

This is the same idea from the RMSD section, now applied inside a single
molecule. Two runs, two very different questions:

**Fit on domain A, measure domain A.** Did this domain change shape
internally?

**Fit on domain A, measure domain B.** Did domain B move relative to
domain A?

Run both and compare. If the first is low and the second is high, your
domains kept their shapes but swung against each other on a hinge. If
both are high, the domains themselves are deforming. That distinction is
invisible in a whole-protein RMSD, and it is often the entire answer.

**Measuring the hinge directly**

If two domains open and close, the clearest measure is the angle between
them:

```bash

```

```bash
gmx gangle -s md.tpr -f fitted.xtc -oav angle.xvg \\
```

-g1 vector -g2 vector \\

-group1 'com of resid 96 to 140 plus com of resid 141 to 180' \\

-group2 'com of resid 200 to 245 plus com of resid 246 to 290'


Each domain gets a vector running through its two halves, and we track
the angle between them.

Plot it as a histogram as well as against time. One peak means one
state. **Two peaks mean the protein is opening and closing between two
positions** — usually the result you were hoping for.

## 4.8 Hydrophobic contacts — what is packing against what?

Hydrogen bonds were one half of the interaction story. This is the other
half.

**What we are counting**

Some side chains are greasy — Ala, Val, Leu, Ile, Met, Phe, Trp — and
they avoid water. Left in solution they huddle together, not because
they attract each other strongly, but because water pushes them out of
its way.

This is the main force that folds a protein in the first place, and a
large part of what holds two molecules together when they bind.

Unlike a hydrogen bond, there is nothing directional here. No donor, no
acceptor, no angle. Two greasy groups near each other is the whole idea.
So the measurement is simply: how many pairs of nonpolar atoms are close
enough to count?

**The awkward part: no fixed definition**

There is no standard cutoff. People use anywhere from 0.4 to 0.6 nm, and
the count you get depends heavily on which you pick. There is also no
fixed list of which residues count as hydrophobic — some people include
Pro, Cys or Tyr, some do not.

That makes the absolute number fairly meaningless on its own. What
matters is comparison — the same cutoff and the same residue list
applied to your wild type and your mutant. Pick your definitions, state
them in your methods, and stick to them.

**Making the index groups**

GROMACS has no dedicated hydrophobic contact tool, so we build the
groups ourselves. The easiest way is gmx select:

```bash
gmx select -s md.tpr -on hydrophobic.ndx -select \\
```

'nonpolar_1 = chain A and resname ALA VAL LEU ILE MET PHE TRP and not
backbone;

nonpolar_2 = chain B and resname ALA VAL LEU ILE MET PHE TRP and not
backbone'

Read that selection in plain English: take the greasy residues from one
chain, keep only their side chains and not the backbone, and call the
result nonpolar_1. Then do the same for the other partner. Change chain
A and chain B to match whatever your two partners actually are.

You can do the same thing with the older gmx make_ndx, which is
interactive:

```bash
gmx make_ndx -f md.tpr -o hydrophobic.ndx
```

At the prompt:

\> r ALA VAL LEU ILE MET PHE TRP

\> "SideChain" & 19

\> name 20 Nonpolar

\> q

The first line picks the greasy residues, the second keeps only their
side chains, and the third gives the result a sensible name. One
warning: those group numbers depend on your system, so read what
make_ndx prints rather than copying 19 and 20 blindly.

**Counting the contacts**

```bash
gmx mindist -f fitted.xtc -s md.tpr -n hydrophobic.ndx \\
```

-on numcont.xvg -d 0.6

-on gives the number of contacts within your cutoff, frame by frame. -d
sets that cutoff.

The same command with -od gives the minimum distance between the two
groups instead, which is a simple way to check whether they stay in
touch at all.

**Reading it**

Like hydrogen bonds, the count fluctuates. Read the average and the
trend, not individual frames.

A stable count means the packing is holding. A falling count means the
surfaces are separating — and it often falls *before* the hydrogen bond
count does, since the greasy contact tends to loosen first.

**Where this really pays off**

Pair it with the hydrophobic SASA from earlier. The two are telling you
the same thing from opposite directions: contacts count what is
touching, buried surface measures how much got hidden from water. If
both move together, you can trust the result.

For a binding study, this is often the more informative of the two
interaction analyses. Hydrogen bonds give specificity — *which* partner
is recognised. Hydrophobic packing gives much of the strength — *how
tightly* it is held.

**A shortcut worth knowing**

If you mainly want a clear picture of which residues are involved rather
than a curve over time, tools like **PLIP** or **LigPlot+** take a
single structure and produce a labelled diagram of every interaction at
once — hydrogen bonds, hydrophobic contacts, salt bridges.

Extract a representative frame from the middle of your run and feed it
to one of these. You get a publication-ready interaction map in seconds,
which complements the time-series analysis nicely.

## 4.9 Specific distances — asking a direct question

Everything so far has been exploratory. This one is the opposite: you
already have a hypothesis, and you want to test it.

**What it does**

You pick two atoms, or two groups, and simply track the distance between
them over the whole run. Nothing more.

**When to use it**

When you can name the thing you want to know. Is this channel gate open
or shut? Does the ligand stay in reach of the catalytic residue? Do
these two domains close on each other? How wide is the binding pocket?

**Running it**

For two specific atoms:

```bash

```

```bash
gmx distance -s md.tpr -f fitted.xtc \\
```

-select 'resid 248 and name CZ plus resid 15 and name P' \\

-oav dist.xvg


For the closest approach between two groups:

```bash

```

```bash
gmx mindist -s md.tpr -f fitted.xtc -n groups.ndx -od mindist.xvg
```


**Reading it**

Plot it, and also plot it as a histogram. The histogram is often the
more revealing of the two.

A single peak means one stable state. **Two peaks means the system is
switching between two states** — open and closed, bound and released.
That is a genuinely interesting result, and it is invisible on a plot
against time if the switching is fast.

**Why it is worth doing**

It is the simplest analysis in this chapter and often the most
convincing. One clear distance answering one clear question beats a
dozen summary plots.

It is also the easiest to compare against experiment. FRET measures
distances. Crosslinking tells you two residues came close. Those are
directly checkable against a number like this.

## 4.10 MM-PBSA / MM-GBSA — estimating binding strength

This one attempts to put a number on how tightly two molecules bind, in
kcal/mol.

**How it works**

Take frames from your trajectory. For each one, calculate the
interaction energy between the two partners, then subtract the cost of
pushing water out of the way to let them touch. Average over all frames.

**The honest caveat, up front**

Recall what we said earlier about junk MD papers. "Docking, 100 ns,
MM-GBSA, promising lead" is exactly that template.

These methods are cheap and popular, but unreliable. They ignore
entropy, they depend on a dielectric constant nobody can pin down, and
their correlation with measured affinity is often no better than docking
scores. **The absolute number is not a binding free energy**,
whatever the units suggest.

Where they are defensible: **ranking closely related things** — the
same complex with different mutations, or a series of similar ligands.
Errors partly cancel across similar systems, so the ordering can be
informative even when the values are not.

**Running it**

Use `gmx_MMPBSA`, which is actively maintained and works directly with
GROMACS files:

```bash

```

```bash
gmx_MMPBSA -O -i mmpbsa.in -cs md.tpr -ci index.ndx \\
```

-cg 1 13 -ct fitted.xtc -o results.dat


`-cg` gives the two group numbers for your partners.

**The genuinely useful output**

Ask for **per-residue decomposition**. This breaks the total down
residue by residue, showing which ones contribute most to binding.

That is the part worth having. It is a hypothesis generator: the
residues at the top of the list are your candidates for mutagenesis, and
you can test them at the bench.

**How to report it**

Never as an affinity. Report it as a relative ranking, state the method,
and treat it as suggestive. If binding strength is central to your
paper, use a rigorous alchemical calculation instead — the pmx route we
discussed earlier.

## 4.11 Binding pocket volume — does the site open and close?

Pockets are not fixed holes. They breathe — widening, narrowing,
sometimes closing entirely. Tracking that over a trajectory tells you
something a static structure never can.

**Why it matters**

Two reasons. First, if you are docking into a pocket, you should know
whether that pocket is reliably there or only exists in the crystal
structure.

Second, and more interesting, is the reverse case: **cryptic
pockets**. These are sites that are closed in the experimental
structure but open transiently during the simulation. Recall the
raltegravir story from earlier — an MD-revealed trench that no crystal
structure showed, which led to an approved drug. Watching pocket volume
is how you find those.

**Running it**

The usual tool is **mdpocket**, part of the fpocket package and
built for trajectories:

```bash

```

```bash
mdpocket --trajectory_file fitted.xtc --trajectory_format xtc -f
```
frame_start.pdb


It scans the whole surface and reports where pockets appear, how often,
and how big. Run it once to find pockets, then again focused on one you
care about to get its volume frame by frame.

**POVME** is the alternative if you already know exactly which site
you want measured.

**Reading it**

A steady volume means a well-defined, reliable pocket. Large
fluctuations mean a flexible site — worth knowing before you trust a
single docked pose. A volume that starts near zero and opens up part way
through is your cryptic pocket.

**The caveat**

"Volume" depends entirely on where you decide the pocket ends, and that
boundary is set by the probe size and the algorithm. Different tools
give different numbers for the same cavity.

So use it comparatively — the same settings, wild type against mutant,
or across your own trajectory — rather than quoting an absolute volume
as if it were measured.

## 4.12 PCA — what are the big movements?

Also called essential dynamics. This is the first analysis that tries to
find *patterns* rather than measure a quantity.

**The problem it solves**

Your trajectory has thousands of atoms moving over thousands of frames.
Most of that is meaningless jiggling. Buried in it are a few large,
coordinated movements — a domain swinging, a loop closing over a site —
and those are what you actually care about.

PCA sorts through the noise and pulls out those dominant motions, ranked
by how much of the total movement each one accounts for. Usually the
first two or three explain most of it.

**Running it**

Two steps. First build and analyse the fluctuations:

```bash
echo -e "Backbone\nBackbone" | gmx covar -s md.tpr -f fitted.xtc \\
```

-o eigenval.xvg -v eigenvec.trr

Then project your trajectory onto the top two motions:

```bash
echo -e "Backbone\nBackbone" | gmx anaeig -s md.tpr -f fitted.xtc \\
```

-v eigenvec.trr -2d 2dproj.xvg -first 1 -last 2

Superimposing beforehand is essential here. If the molecule is still
tumbling, PCA will helpfully identify tumbling as your biggest motion.

**The output worth looking at**

Numbers are less useful here than pictures. Generate the extreme
structures along the first motion:

```bash
echo "Backbone" | gmx anaeig -s md.tpr -f fitted.xtc -v eigenvec.trr \\
```

-extr extreme.pdb -first 1 -last 1 -nframes 20

Open that in PyMOL and you get a short animation showing the single
largest movement in your simulation, exaggerated so you can see it. That
is usually the moment things click — you can watch the domain actually
open and close.

The 2D projection is the other key output: each frame plotted as a point
on the first two motions. Points clustered in one blob means one state.
Two blobs means the protein is switching between two conformations.

**The main caution**

PCA needs good sampling. On a short trajectory it will still confidently
report a “dominant motion” — but that may just be one random event that
happened to be large, not a real feature of the system.

Check it by running PCA on the first and second halves separately. If
they give similar motions, trust the result. If not, you have not
sampled enough.

This also sets up the next analysis: the free energy landscape is
usually built directly on these first two components.

## 4.13 DCCM — which parts move together?

PCA found the big motions. This asks a different question: which
residues move *in step* with each other?

**How it works**

For every pair of residues, compare how they move. If they consistently
move in the same direction, they are correlated. If one goes up whenever
the other goes down, they are anti-correlated.

The result is a value between +1 and −1 for every pair, displayed as a
heatmap with the sequence along both axes.

**Reading the map**

**Red blocks along the diagonal** are regions moving as one rigid unit —
typically a domain or a helix.

**Off-diagonal blocks** are the interesting ones. Two regions far apart
in sequence moving together means they are mechanically linked, even if
nothing obvious connects them.

**Blue patches** are anti-correlated motion — two parts moving in
opposite directions. This is the signature of a hinge, or two domains
opening and closing on each other.

**Why it matters: allostery**

This is the main reason to run it. Allostery means something happening
at one site affects a distant site — and DCCM is how you look for the
mechanical route between them.

If your binding site is correlated with a region 40 Å away, that is a
candidate pathway for the signal to travel.

**Running it**

GROMACS gives you the raw covariance matrix:

```bash
echo -e "C-alpha\nC-alpha" | gmx covar -s md.tpr -f fitted.xtc -ascii
```
covar.dat

But the usual tool is **Bio3D**, an R package built for this:

library(bio3d)

dcm \<- dccm(xyz)

plot(dcm)

It handles the normalisation and produces the heatmap directly.

**Two cautions**

Correlated motion is not proof of communication. Two things can move
together because a third thing moves them both.

And it needs good sampling. On a short trajectory you will see
correlations that are really just one large event happening to affect
two regions at once. Check the first and second halves separately before
believing anything.

## 4.14 Free energy landscape — how many states are there?

This builds directly on PCA. Instead of watching the motions, we ask:
where does the system actually spend its time?

**How it works**

Take two coordinates — usually the first two principal components,
sometimes RMSD and Rg. Divide that space into a grid and count how many
frames land in each square.

Then flip the counting into energy. Places the system visits often are
comfortable, so we call them low energy. Places it rarely visits are
unfavourable, so they are high. The result is a map with valleys and
hills.

**Reading it**

**Valleys** are stable states — conformations the protein genuinely
settles into.

**One deep valley** means a single stable structure. That is the usual
result for a well-behaved folded protein.

**Two or more valleys** is the interesting outcome. Your protein is
switching between distinct conformations, and you have caught both.

**Ridges** between valleys are barriers separating those states.

**Running it**

```bash
gmx sham -f 2dproj.xvg -ls gibbs.xpm -notime

gmx xpm2ps -f gibbs.xpm -o gibbs.eps
```

The input is the 2D projection from the PCA step. Many people prefer to
```bash
load the raw values into Python and plot the map themselves, which gives
```
much better-looking figures.

**The most useful part: pulling out structures**

A map is nice, but what you really want is to *see* the states. Find
which frames sit at the bottom of each valley, then extract those
structures:

```bash
echo "Protein" | gmx trjconv -f fitted.xtc -s md.tpr -o basin1.pdb
```
-dump 4200

Now you have a representative structure for each state, and you can
compare them directly — what actually differs between the open and
closed forms.

**The caveat, and it is a big one**

This is not really a free energy landscape unless your sampling was
thorough.

From a short unbiased run, all you have mapped is *where your simulation
happened to go*. If a state exists but your run never reached it, it
simply will not appear — and the map will confidently show a single tidy
basin as though that were the whole story. The barrier heights are
especially unreliable, because you rarely observe enough crossings to
measure them.

So call it what it is: a population map of your trajectory. A genuine
free energy landscape needs the enhanced sampling methods we mentioned
earlier, which is precisely what those methods were built for.

Check it the same way as PCA — build the map from each half of your run
separately. If the two look alike, you can believe it.

## 4.15 Chi angles — how are the side chains sitting?

Everything so far treated residues as whole units. This looks inside
them, at how the side chains are oriented.

**What a chi angle is**

A side chain can rotate about each of its single bonds. Those rotations
are the chi angles: χ1 is the rotation about the first bond out from the
backbone, χ2 the next one, and so on.

Side chains do not sit at arbitrary angles. Because of how the atoms
bump into each other, they settle into a few preferred positions,
usually near −60°, +60° or 180°. These preferred positions are called
**rotamers**, and a side chain typically sits in one and occasionally
flips to another.

**Why it matters**

For most residues it does not. But for a few it matters enormously.

A catalytic residue has to point the right way to do its job. A residue
lining a binding site can swing in or out and open or block the pocket.
In a channel, a single side chain flipping can be the difference between
open and shut.

So this is a focused analysis — you run it when you already suspect a
particular residue matters.

**Running it**

```bash
gmx chi -s md.tpr -f fitted.xtc -all -rt rotamer_transitions.xvg
```

This produces a file for every chi angle in the structure, plus a count
of how often each side chain switched rotamer.

Add -oh for histograms, which are usually easier to read than the raw
time series.

**Reading it**

Plot the angle against time for the residue you care about.

**A flat line** means the side chain is locked in one orientation. If
that orientation is the functional one, good.

**Sudden jumps between levels** mean it is flipping between rotamers.
How often it flips, and how long it spends in each, is the real result.

The histogram tells you the same thing more compactly: one peak means
locked, several peaks means it visits several positions, and the
relative heights tell you how much time it spends in each.

**One caution**

Not all side chain motions are equally well sampled. χ1 flips are fast
and you will see plenty of them. But large aromatic rings flipping, or
buried side chains rearranging, can be slow enough that a short run
shows you only whichever position it started in.

So a flat line means “it did not move in this run”, which is not the
same as “it cannot move.”

## 4.16 Contact maps — the whole interaction pattern at once

A contact map is a simple idea: for every pair of residues, is it in
contact or not? Draw that as a grid with the sequence on both axes, and
you get a picture of the entire structure’s internal contacts in one
image.

**Reading it**

The **diagonal** is always filled, because every residue touches its
sequence neighbours. That is not informative.

The **off-diagonal** patterns are the structure:

A **thick band hugging the diagonal** is a helix — each residue
contacting the one three or four places along.

A **stripe running perpendicular to the diagonal** is an antiparallel
sheet — two strands running opposite ways.

A **stripe running parallel to the diagonal** is a parallel sheet.

**Isolated blobs far from the diagonal** are long-range contacts — two
parts of the chain that are distant in sequence but touching in space.
These are what hold the fold together.

**Running it**

```bash
echo "C-alpha" | gmx mdmat -f fitted.xtc -s md.tpr -mean dm.xpm -frames
```
dmf.xpm

-mean gives the average over the whole run; -frames gives individual
snapshots.

For anything more flexible, MDAnalysis or Bio3D lets you build a
**contact frequency map** instead — where each square shows the
percentage of frames that contact existed. That is more useful, because
it separates permanent contacts from occasional ones.

**The real payoff: difference maps**

Compute a contact map for wild type and one for your mutant, then
subtract.

What is left shows only what changed — contacts lost in red, contacts
gained in blue. Everything shared cancels out and disappears.

This is a genuinely powerful figure for mutation work, because it
answers “what did this mutation actually break?” in a single image.
Often you find lost contacts nowhere near the mutation site, which tells
you the effect propagated through the structure.

**For complexes**

Restrict it to one partner against the other and you get an **interface
contact map** — every residue pair across the binding surface, and how
reliably each one holds. That is the complete picture of an interface,
and it complements the hydrogen bond and hydrophobic analyses by showing
everything at once rather than one interaction type at a time.

## 4.17 DNA shape — bending, twisting and grooves

DNA is not a rigid rod. It bends, unwinds, and its grooves widen and
narrow — and proteins care about all of that.

**Why it matters**

Many transcription factors bend their target DNA sharply when they bind.
That bending is often part of the recognition: some sequences bend more
easily than others, so a protein can effectively read a sequence by how
it deforms, without touching the bases directly.

The grooves matter too. The **major groove** is where sequence-specific
reading happens, because the bases present distinguishable chemical
patterns there. If a protein widens or narrows that groove, it changes
what can be read.

**What gets measured**

A handful of numbers describe how each pair of stacked bases sits
relative to the next:

**Twist** — how far the helix rotates per step. Around 34° in normal
B-DNA. Lower means the helix is unwinding.

**Roll** — how much two base pairs open up like a book. This is the main
driver of bending, so it is usually the one to watch.

**Rise** — how far apart the stacked pairs sit, normally around 3.4 Å.

Plus **groove widths** and an overall **bend angle** for the whole
duplex.

**Running it**

The standard tool is **Curves+**, with its companion **Canal** for
handling trajectories:

```bash
Cur+ \< curves.in

Canal \< canal.in
```

**3DNA** and its newer version **DSSR** do the same job and are often
easier to script. For GROMACS trajectories specifically, do_x3dna wraps
3DNA and handles the frame-by-frame analysis for you.

You will need to convert your trajectory to PDB frames first, since none
of these read .xtc directly.

**Reading it**

Plot the parameter against base-pair position rather than against time.
That shows you *where* along the DNA the deformation is happening —
usually right where the protein sits.

Then compare the bound DNA against free DNA simulated on its own. The
difference is what the protein did to it.

**For your wild type against mutant question**

This is the direct measurement. If your mutation weakens the protein’s
grip, the DNA may bend less, or the bend may shift position. That is a
much more specific result than “binding got weaker” — it tells you the
protein is failing to deform its target properly.

Plot bend angle over time for both, and compare the distributions rather
than single values.

**Two cautions**

The ends of a DNA duplex fray. The last base pair or two will look
distorted no matter what, so exclude them from your analysis.

And DNA shape is sensitive to the force field. Use a modern one —
parmbsc1 or OL21 for AMBER, CHARMM36 for CHARMM — because older ones
produce well-documented artefacts in exactly these parameters.

## 4.18 Ion binding — where do the ions go?

We added ions as background salt. But ions do not stay evenly spread out
— they gather in specific places, and sometimes those places matter.

**Why it is worth looking at**

For DNA, the phosphate backbone is strongly negative, so positive ions
crowd around it. This is not incidental — that cloud of counterions
screens the charge and affects how easily the DNA bends and how tightly
a protein can bind. If your mutation changes the charge at an interface,
the ion distribution will change too.

For channels, ions are the whole point. Which ions sit in the
selectivity filter, and how they move through, is the function you are
trying to understand.

And some ions sit in defined pockets as genuine cofactors — a magnesium
in an enzyme active site, for example.

**Where the ions gather**

The standard measure is a **radial distribution function**: how ion
density varies with distance from something.

```bash
gmx rdf -f fitted.xtc -s md.tpr -o rdf.xvg \\
```

-ref 'group "DNA"' -sel 'name NA'

Peaks show shells where ions accumulate. A sharp peak close in means
ions binding directly; a broader one further out means a loosely held
cloud.

**Counting ions at a site over time**

This uses a dynamic selection — one that re-evaluates every frame:

```bash
gmx select -f fitted.xtc -s md.tpr -os numions.xvg \\
```

-select 'name NA and within 0.5 of group "DNA"'

That gives you how many sodium ions were within 0.5 nm of the DNA in
each frame. Swap the reference for a specific residue or pocket to watch
one site.

**The useful question: how long do they stay?**

An ion drifting past is not the same as an ion bound. What separates
them is **residence time** — how long a given ion stays in place before
leaving.

Milliseconds of contact means a real binding site. Picoseconds means
passing traffic. GROMACS does not calculate this directly, so it is
usually done in MDAnalysis by tracking individual ion identities over
time.

**Two cautions, and they are serious**

**Ions converge slowly.** The ion atmosphere around DNA can take tens of
nanoseconds to settle. If your run is short, what you are seeing may
just reflect where genion happened to place them at the start. Check
that the distribution is stable across the second half of your run
before believing it.

**Ion parameters are imperfect**, particularly for divalent ions like
magnesium and calcium. Known problems include over-binding and
artificial clustering. If ions are central to your conclusion rather
than background, check which parameter set your force field uses and
whether it has a better alternative.

## 4.19 Secondary structure over time

RMSF told us which parts move. This tells us whether they are still
helix, sheet or coil — and when that changes.

**What it does**

For every frame, every residue is classified based on its hydrogen
bonding pattern: alpha helix, beta sheet, turn, bend, or coil. Plot that
as a grid — residues down one axis, time across the other, coloured by
type — and you can see the structure holding or falling apart at a
glance.

**Running it**

```bash
echo "Protein" | gmx dssp -s md.tpr -f fitted.xtc -o dssp.dat -num
```
ss_count.xvg

```bash
gmx dssp is built into GROMACS since version 2023, so there is nothing
```
extra to install. Older tutorials use do_dssp, which needed a separate
DSSP program — that is no longer necessary.

-num gives you a simple count of how many residues are in each structure
type over time, which is often easier to read than the full map.

**Reading it**

**Solid horizontal bands** mean a helix or sheet that held throughout.
That is what a stable protein looks like.

**A band that stops partway** means that element melted at that point.
Note where and when — then go and look at that region in your movie.

**Flickering at the edges** of a helix is normal. Helix ends fray
constantly; that is not unfolding.

**A band appearing** where there was none means new structure formed,
which is less common but interesting when it happens.

**Where it is most useful**

**Thermal unfolding.** This is the clearest way to show a protein coming
apart as it heats — you watch the bands disappear one by one, and you
can see which elements go first.

**Wild type against mutant.** If your mutation destabilises a specific
helix, this shows exactly which one and how quickly. That is far more
specific than a raised RMSD.

**One caution**

The classification depends purely on hydrogen bond geometry, so it can
flicker between two labels frame to frame when a residue sits near a
boundary. Do not read anything into a single frame’s classification —
look at whether a region holds its assignment over time.

## 4.20 Clustering — what did it actually look like?

Your trajectory holds hundreds of structures, most of them nearly
identical. Clustering sorts them into groups of similar shapes and hands
you one representative structure for each.

**Why you want this**

Sooner or later someone asks for a picture of your protein. Which frame
do you show? The first one is just your starting structure. The last one
is arbitrary. A random middle frame might be unrepresentative.

Clustering answers this properly: it gives you the structure that best
represents where the system spent its time.

**How it works**

Compare every frame against every other by RMSD. Any frames within a
chosen cutoff of each other get grouped together. The frame sitting
closest to the middle of each group becomes its representative.

**Running it**

```bash
echo -e "Backbone\nProtein" | gmx cluster -s md.tpr -f fitted.xtc \\
```

-cl clusters.pdb -o rmsd-clust.xpm -g cluster.log -cutoff 0.15 -method
gromos

-cutoff is in nanometres and is the one setting that matters. Too large
and everything collapses into one cluster; too small and you get
hundreds of tiny ones. Start at 0.15 and adjust until you get a handful
of meaningful groups.

-cl writes the representative structures, one per cluster, in order of
size.

**Reading the output**

The log file lists how many frames fell into each cluster. That
distribution is your result.

**One dominant cluster** holding most frames means a single stable
conformation.

**Two or three substantial clusters** means the protein visited
genuinely distinct states, and you now have a structure for each to
compare.

**Many small clusters** usually means the system never settled, or your
cutoff is too tight.

The log also tells you *when* each cluster was occupied. If cluster 1
covers the first half and cluster 2 the second half, that is not two
states in equilibrium — that is a transition, and probably a sign your
run had not equilibrated.

**How it relates to what came before**

Clustering and the free energy landscape answer the same question by
different routes. The landscape shows you *where* the states sit in a
continuous space; clustering hands you *structures* for them directly.

In practice, people use both — the map for the figure, the clustered
structures for anything you want to look at, measure or dock into.

**A caution**

Clustering will always produce clusters, even from meaningless noise. It
cannot tell you whether the states it found are real or just the
wandering of a run that never settled.

So check against everything else. If your RMSD had levelled off and your
landscape showed distinct valleys, believe the clusters. If RMSD was
still climbing, they are probably just stages of a drift.

## 4.21 Did you sample enough? — checking convergence

Every analysis in this chapter carries the same silent assumption: that
your trajectory is long enough to mean something. This section is about
testing that assumption, and it belongs at the end because it applies to
everything before it.

**The problem**

Simulations always produce output. Run 5 nanoseconds and you will still
get an RMSD curve, a free energy landscape and a set of clusters. They
will look perfectly presentable. They may also be completely
meaningless.

Nothing in the software warns you about this. The only protection is
checking deliberately.

**Check one: split the run in half**

The simplest test, and the most useful. Run your analysis on the first
half, then on the second half, and compare.

```bash
gmx rms -s md.tpr -f fitted.xtc -o rmsd_first.xvg -b 0 -e 500

gmx rms -s md.tpr -f fitted.xtc -o rmsd_second.xvg -b 500 -e 1000
```

If the two halves agree, your result is reproducible within your own
run. If they disagree, you are still watching the system change and have
no business drawing conclusions.

Do this for whatever your main result is — PCA, the landscape,
clustering, contact maps. It costs nothing and catches most problems.

**Check two: the RMSD matrix**

This is the single most informative convergence picture, and it is
underused.

```bash
echo -e "Backbone\nBackbone" | gmx rms -s md.tpr -f fitted.xtc \\
```

-f2 fitted.xtc -m rmsd_matrix.xpm

It compares every frame against every other frame and draws the result
as a heatmap.

**Uniform colour throughout** means the system stayed in one state the
whole time. Good.

**Square blocks along the diagonal** mean distinct periods where the
structure was one thing, then another. Each block is a state, and the
boundaries are transitions.

**A gradient getting steadily darker away from the diagonal** is the bad
one. It means the structure kept drifting further from where it started
and never settled. Your run is too short.

**Check three: error bars, not just averages**

When you quote an average — hydrogen bond count, radius of gyration — it
needs an uncertainty. But consecutive frames are not independent, so the
ordinary standard deviation is far too optimistic.

The proper approach is block averaging: chop the run into blocks,
average each, and look at the spread between blocks.

```bash
gmx analyze -f hbnum.xvg -ee errest.xvg
```

-ee does this for you and reports a realistic error estimate.

**Check four: run replicas**

The strongest test, and the one no single trajectory can substitute for.

Recall the replica discussion from earlier: same structure, different
velocity seeds, ideally different equilibration. If three independent
runs give the same answer, you have a result. If they disagree, you have
learned something equally important — that one run was never enough.

This matters most for comparisons. A difference between wild type and
mutant is only believable if it is larger than the difference between
replicas of the same system.

## 4.22 A closing note on analysis

This chapter covers what you will use most often, but it is nowhere near
everything.

Depending on your system you might also want diffusion rates, backbone
dihedral analysis, native contact counts, water residence times, or any
number of tools built for one particular question. Membrane systems have
a whole family of their own — area per lipid, bilayer thickness, lipid
order parameters, protein tilt and insertion depth.

```bash
gmx help commands lists everything GROMACS offers, and it is worth
```
reading through once simply to know what exists. Beyond GROMACS,
MDAnalysis and Bio3D let you compute essentially anything you can
define, and PLUMED brings its own large collection.

But the more important point is this: **the analysis should follow from
your question, not the other way round.**

It is easy to run every tool you have and produce twenty plots that say
nothing in particular. That is the pattern we described right at the
start — the papers that report an RMSD that levelled off, call the
compound promising, and never touch a bench. The problem there was never
the software. It was that no question was ever asked.

So when you sit down with a finished trajectory, start by writing out
what you actually want to know. Then find the analysis that answers it.

One well-chosen measurement, compared between wild type and mutant, run
in replicate and honestly reported, is worth more than a folder full of
curves. That is the whole difference between description and evidence.

---

[← Running a simulation](03-running-a-simulation.md)
