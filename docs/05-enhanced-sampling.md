# 5. Enhanced Sampling

In Chapter 2 we said there was a workaround for the timescale problem
and then walked away from it. This is that chapter.

The promise is a strange one, so it is worth stating plainly before we
start. Enhanced sampling does not make your computer faster, and it does
not make the simulation reach further in time. What it does is give up
on watching the event happen and extract the answer some other way. That
trade is the whole subject.

---

## 5.1 Why waiting does not work

Recall the lottery. Running for longer buys you more tickets, and more
tickets really do help — but only in proportion. Double the length of
the run and you double your chances, no more. What decides whether that
is worth anything is the odds printed on the ticket, and in molecular
terms those odds are set by the height of the barrier.

A protein sitting in one conformation is sitting in a free energy
minimum. To reach another minimum it has to climb over a barrier, and
thermal energy is what pays for the climb. At body temperature that
budget is small — k<sub>B</sub>T, about 0.6 kcal/mol — and the probability of finding
enough of it in the right place at the right moment falls off
*exponentially* with the height of the barrier.

Put a number on that exponential and the situation becomes clear. Every
extra **1.4 kcal/mol of barrier multiplies the waiting time by roughly
ten** — that is simply what an exponential with a 0.6 kcal/mol thermal
budget does.

Which means the whole problem is smaller than it feels. Chapter 2 left
us stranded between the hundreds of nanoseconds we can afford and the
milliseconds biology actually uses: a gap of about a million-fold in
time. In energy, a million-fold is six factors of ten, and six factors
of ten is **a little over 8 kcal/mol of barrier**. Everything we cannot
reach sits behind a wall about that tall — less than the energy of a
few hydrogen bonds.

{{INTERACTIVE: barrier-crossing}}

Now consider what buying more computer does for you. Doubling your GPU
budget doubles your simulated time, which moves the barrier height you
can reach by about 0.4 kcal/mol. A ten-fold larger machine buys you 1.4.
This is why the timescale gap has needed purpose-built hardware rather
than bigger clusters, and why the rest of us do not get to solve the
problem by waiting. **The cost of brute force scales exponentially in the
barrier; our resources scale linearly at best.**

There is one more thing hiding in this, and it is the thing beginners
most often miss. A simulation that never crosses a barrier does not look
broken. It looks beautifully converged. The RMSD plateaus, the
fluctuations are stable, everything is calm — because the system is
trapped in one basin and has stopped exploring. **A flat trajectory is
not evidence of equilibrium. It is equally consistent with being stuck.**

---

## 5.2 Two ways out

Almost everything in this field is one of two ideas, and they differ in
what they are willing to distort.

### 5.2.1 Add a bias potential

The first family adds an artificial potential on top of the real one,
and does it in one of two ways. You can **restrain**: pin the system at
chosen points along a coordinate — including points on top of a barrier
where it would never sit voluntarily — and measure how hard it fights
the restraint. Or you can **fill**: pour bias into whichever well the
system currently occupies until it overflows into the next, levelling
the landscape as you go. Umbrella sampling restrains; metadynamics and
AWH fill, though by different bookkeeping — metadynamics accumulates
what it has deposited, AWH maintains a running estimate of the free
energy itself. Either way the trajectory you get is fictitious, the bias you
added is known exactly, and subtracting it afterwards recovers the true
free energy. The dynamics are sacrificed; the thermodynamics survives.

#### 5.2.1.1 Umbrella sampling

Umbrella sampling (Torrie and Valleau, 1977) is the oldest and the
easiest to picture. You pick a coordinate — say the distance between a
ligand and its pocket — and run a series of separate simulations, each
with a harmonic spring holding the system near a different value of that
distance. Each window samples its own narrow slice thoroughly, including
slices the system would never visit on its own. The windows are then
stitched back together — classically with WHAM, now almost always with
MBAR, which needs no histogram binning — into one continuous free energy
profile. It is laborious and it requires you to guess the window
positions and spring strengths in advance, but it is robust and it is
easy to tell when it has gone wrong.

Note what the spring is not: it is not a rope dragging the system from
one well to the next. It pushes back from both sides, which is exactly
why each window samples a slice instead of sliding through it, and the
anchors never move — there is no journey, only a set of stationary
interrogations. The dragging version exists too: **steered MD** pulls
the system along the coordinate at constant velocity, and its usual
honest job is generating the starting structures for the windows. The
two are easy to conflate, not least because GROMACS runs both through
the pull code, but steered MD is a preparation step and umbrella
sampling is the measurement.

{{INTERACTIVE: umbrella-windows}}

#### 5.2.1.2 Choosing the coordinate

That word *coordinate* is carrying an enormous amount of weight, and
umbrella sampling is the right place to notice it, because here the
choice is made once, in advance, and everything afterwards is committed
to it. The window positions, the spring constants, the amount of
sampling each window needs — all of it follows from the coordinate. Get
it wrong and no amount of extra simulation will rescue the result.

In practice the candidates are drawn from a fairly small vocabulary, and
which one you reach for depends entirely on the process. For a ligand
leaving a pocket or two proteins separating, the usual choice is the
**distance between centres of mass**, sometimes restricted to a single
axis along the exit channel. For a molecule crossing a membrane, it is
the **depth along the bilayer normal**. For a rotameric flip or a sugar
pucker, a **dihedral angle**. For folding and unfolding, the **radius of
gyration**, the **end-to-end distance**, or a **count of native
contacts**. For a domain opening or a gate swinging, an **angle between
two rigid groups**. For an ion entering a site, its **coordination
number** with the surrounding oxygens. And when the mechanism is
genuinely a curved journey through several of these at once, there are
**path-based coordinates** that measure progress along a reference
pathway and distance away from it.

Two constraints narrow the list further. GROMACS has to be able to
restrain the thing, which in practice means it must be expressible
through the pull code — distances, angles, dihedrals between groups you
can define. And it has to be **single-valued along the process**: if two
genuinely different structures share the same value of your coordinate,
the windows covering that value will sample a mixture of both and the
profile you recover will be an average of two things you meant to keep
apart.

The deeper question — whether your coordinate captures the *slow* motion
rather than merely an obvious one — is the subject of Section 5.4, and
it is the reason that section is the longest in the chapter.

#### 5.2.1.3 Metadynamics

Metadynamics (Laio and Parrinello, 2002) automates the guessing. As
the simulation runs it periodically drops a small repulsive Gaussian at
wherever the system currently is. Sitting in a minimum becomes gradually
less comfortable; eventually the well fills up and the system spills
over into the next one. The deposited bias, once the landscape is
flooded, is an upside-down picture of the free energy surface. Plain
metadynamics never quite settles: the sampling is fine, but the free
energy *estimate* oscillates around the true value instead of converging
to it. **Well-tempered metadynamics** (Barducci et al., 2008) fixes this
by shrinking the Gaussians as a region fills, so deposition slows
asymptotically and the estimate converges. It is what people actually
use.

{{INTERACTIVE: metadynamics-filling}}

#### 5.2.1.4 Adaptive biasing force

Adaptive biasing force reaches the same levelled landscape as the
filling methods but by a different route: it estimates the average force
along the coordinate and applies its negative, cancelling the slope
directly rather than ever building the free energy surface.

#### 5.2.1.5 OPES

OPES, the newest of these, reframes the whole business: instead of
asking what bias to add, you specify the distribution you would *like*
to sample and construct the bias that produces it. That reframing is
more powerful than it sounds — with different target distributions it
reproduces well-tempered metadynamics, adaptive umbrella sampling, or a
multithermal ensemble, from one implementation.

#### 5.2.1.6 AWH

AWH — accelerated weight histogram — is GROMACS's own member of this
family, and the one you can run without installing anything. It is
closest in spirit to adaptive umbrella sampling: rather than piling up
Gaussians, it keeps an explicit estimate of the free energy along the
coordinate, refines it as data arrives, and sets the bias to whatever
that estimate says is needed to reach a target distribution — usually
flat. That framing puts it nearer to OPES than the shared word *fill*
suggests.

### 5.2.2 Run many short trajectories instead

The second family refuses to touch the forces. Every trajectory is
honest, unbiased Newtonian dynamics of exactly the sort Chapter 1
described. What changes is how you spend your compute: rather than one
long run, you start hundreds of short ones, and you are clever about
where you start them and which ones you keep.

#### 5.2.2.1 Adaptive sampling

Adaptive sampling is the simple version of the idea. Run a batch of
short simulations, look at where they went, and launch the next batch
from the least-explored places. Repeat. The frontier of what you know
expands outward instead of the trajectory circling one basin.

#### 5.2.2.2 Markov state models

Markov state models are how the pieces get put back together. If you
chop configuration space into discrete states and count how often short
trajectories hop between neighbouring ones, you can assemble a transition
matrix — and that matrix will tell you about transitions far slower than
any individual simulation you ran. This is the trick Chapter 2 alluded
to: a millisecond process reconstructed from microsecond fragments,
including rate constants and mean first passage times. It works because
the hops are local even when the journey is long — but only if the model
is genuinely Markovian at the lag time you chose, which is an assumption
you have to test rather than hope for.

#### 5.2.2.3 Weighted ensemble

Weighted ensemble is the most rigorous version, and the one worth
understanding properly. You run many walkers in parallel, each carrying
a numerical weight. When a walker makes progress into a poorly populated
region, it is split into copies whose weights sum to the parent's; when
walkers crowd together, they are merged. No force is ever added and no
walker is ever pushed. The dynamics stay exactly correct, and because
they do, **weighted ensemble gives you rate constants without assuming
anything about Markovianity** — which is what separates it from the MSM
route to the same quantities. Biased methods, by contrast, recover
thermodynamics cleanly and kinetics only with extra work and extra
assumptions.

{{INTERACTIVE: weighted-ensemble-walkers}}

### 5.2.3 Choosing between the two

The trade between the families is fairly clean. Biasing gets
you an answer with less bookkeeping but distorts the dynamics, and the
distortion has to be undone correctly. Many-trajectory methods keep the
physics untouched and pay for it in infrastructure — job management,
storage, and analysis machinery that is often more work than the
simulation itself.

---

## 5.3 A third route: change the ensemble

There is a family that fits neither description, and it is worth its own
short section because you will meet it constantly in the literature.
These methods do not bias a coordinate and do not manage swarms of
walkers. They change the thermodynamic conditions instead.

### 5.3.1 Replica exchange

Replica exchange (parallel tempering) runs many copies of your system
at a ladder of temperatures. The hot copies cross barriers easily; the
cold one is the one you care about. Periodically, neighbouring replicas
attempt to swap configurations, with the swap accepted or rejected by a
criterion that preserves the correct distribution at every rung. Good
structures discovered at high temperature filter down to the bottom of
the ladder.

Its great virtue is that it needs no collective variable at all — you do
not have to know what the interesting motion is. Its great vice is cost.
The number of rungs needed to keep neighbouring temperatures overlapping
grows with the size of the system, and most of your system is water,
which you had no interest in heating. A solvated protein can need
dozens of replicas before it works at all.

### 5.3.2 REST2

REST2 is the repair. Instead of heating everything, it scales only
the solute's interactions, so the protein feels hot while the water
stays cold. The replica count then depends on the size of the part you
care about rather than the size of the box, which brings the method back
into range for ordinary systems.

### 5.3.3 Accelerated MD and GaMD

These take a different angle again: they add a
boost potential that raises the low regions of the *potential energy*
surface wherever it dips below a threshold, smoothing barriers
everywhere at once without naming a coordinate. GaMD makes the boost
harmonic, which allows the reweighting to be done through a cumulant
expansion. The catch is that reweighting is where these methods hurt —
the boost applies to a global quantity, the reweighting factors have
large variance, and recovering an accurate free energy surface can be
much harder than generating the trajectory was.

---

## 5.4 The collective variable problem

Everything in 5.2.1, and a good deal of what is built on top of 5.2.2,
depends on choosing a coordinate. This is the hardest idea in the
chapter and the place where most real failures originate, so it deserves
more care than the methods themselves.

### 5.4.1 What a collective variable is

A collective variable is a function that maps the full configuration —
tens of thousands of coordinates — down to one or two numbers you can
bias along. A distance. An angle. A count of contacts. A radius of
gyration. The bias acts in that reduced space, and the reduced space is
therefore the lens through which the method sees your system.

### 5.4.2 How it fails

Here is the failure mode. Suppose you bias a ligand's distance from the
pocket, and the real bottleneck to unbinding is a gate loop that has to
swing open first. Your bias will happily drag the ligand outward while
the loop stays shut, forcing the system through configurations that are
physically absurd and enormously strained. The simulation will not
crash. It will produce a free energy profile. That profile will be
wrong, and nothing in the output announces it.

**A bad collective variable does not fail loudly. It converges
confidently to the wrong answer.** This is the single most important
sentence in the chapter.

### 5.4.3 Hysteresis, the symptom you can check

The usual symptom, when you look for it, is **hysteresis**: push the
system forward along your coordinate and then back, and if the two
profiles do not lie on top of each other, some slow degree of freedom
you did not include is lagging behind. Always run both directions.
Always look.

{{INTERACTIVE: hidden-cv-hysteresis}}

### 5.4.4 The committor

What makes a coordinate good, in principle, is well understood. The
gold standard is the **committor** — the probability that a trajectory
started from a given configuration reaches the product basin before
returning to the reactant. A perfect reaction coordinate is one that the
committor depends on and nothing else, with the transition state sitting
at a committor of one half. That is not an aesthetic preference: the
committor's isosurfaces are the true dividing surfaces of the
transition, so rates computed across them are exact, and any coordinate
that disagrees with it is hiding a slow mode. The trouble is that
computing the committor
requires launching swarms of trajectories from candidate structures,
which is expensive enough that it has traditionally been used to
*validate* a coordinate rather than to find one.

### 5.4.5 Learned coordinates

This is precisely where machine learning entered the field, and it is
the reason the review sitting in this project is organised the way it
is (Zhu, Trizio et al., *arXiv:2509.04291*). If a good coordinate is a
low-dimensional function of the configuration that captures the slow
motion, then finding one is a learning problem. Approaches split roughly
into those that learn to *discriminate* known metastable states from one
another, those that learn the *slowest* modes from trajectory data —
tICA and its deep relatives, VAMPnets, DeepTICA — and those that go
after the committor directly. We will not work through them here; that
is the next chapter's job.

### 5.4.6 In practice

For this chapter, the practical advice is smaller and more useful:
choose coordinates from the mechanism you believe in, not from
convenience; include the degrees of freedom you suspect are slow even
when they are awkward to define; and treat every free energy surface as
provisional until you have checked it does not depend on the direction
you approached it from.

---

## 5.5 Alchemical free energy

The methods above all try to move the system along a physical path.
Alchemical methods do something stranger and, for drug discovery, far
more useful: they change the molecule instead.

### 5.5.1 The thermodynamic cycle

The idea rests on free energy being a state function. If you want to
know whether ligand B binds your target more tightly than ligand A, you
do not have to simulate either one binding. You can instead mutate A
into B — atom by atom, through a series of unphysical intermediate
states — twice: once with the ligand bound in the pocket, and once with
it floating in water. The difference between those two transformation
costs is the difference in binding affinity. The two legs, drawn with
the two binding processes you never simulated, close into a
thermodynamic cycle.

Nothing in that path is physical. The intermediates are molecules that
do not exist, with atoms partly switched off. It does not matter,
because the endpoints are real and free energy does not care how you got
between them. This is the industry workhorse referred to in the
instructor's note, and the source of the roughly 1 kcal/mol accuracies
now being reported.

### 5.5.2 λ is a collective variable

Unphysical is not the same as unfamiliar, and it is worth seeing that
this is the same machinery as 5.2.1, not a different subject. The
transformation runs along a coordinate called λ,
and λ behaves exactly like a collective variable — you place
windows along it, you need neighbouring windows to overlap, and there
can be barriers between them that trap the system just as a spatial
barrier would.

### 5.5.3 How alike is alike enough?

**This is also where Chapter 2's argument about error cancellation
finally earns its keep.** We said there that comparisons survive
because both simulations are wrong in the same way. Alchemical
calculations are that principle made quantitative — and they make the
hidden condition visible. The errors cancel only to the extent that the
two end states are *alike*. So the real question, the one Chapter 2
could only gesture at, becomes concrete: **how alike is alike enough?**

The practical answer is that alchemical methods are at their best on
small, local modifications — adding a methyl, swapping a halogen,
changing a substituent on a ring — where the two ligands share a
scaffold and a binding mode, and the environments they perturb are
nearly identical. They degrade as the change gets larger, and they can
fail outright when the modification changes the binding pose, changes
the net charge, or displaces a structurally important water. In those
cases you are no longer comparing near-identical systems and there is
nothing left to cancel.

### 5.5.4 The sampling problem has not gone away

And note what has *not* gone away. The sampling problem from 5.1 is
still there; it has simply moved somewhere less visible. If a side chain
in the pocket needs to reorganise to accommodate ligand B, that
reorganisation has to actually happen during your run, or your free
energy is the free energy of a strained pocket. Alchemical methods
sidestep the barrier between bound and unbound. They do not sidestep the
barriers *within* the bound state — which is why serious protocols often
run enhanced sampling on top of the alchemical machinery rather than
instead of it.

### 5.5.5 Where to read the mechanics

For the mechanics — soft-core potentials, lambda schedules, how many
intermediate windows, BAR versus MBAR estimators — the standard
references are better than anything we could compress into this chapter.
Start with the GROMACS free energy documentation, and with the community
material collected at [alchemistry.org](http://www.alchemistry.org).

---

## 5.6 What you can actually run

A short orientation, since the practical distance between these methods
varies enormously.

### 5.6.1 AWH — native

AWH is configured through the `.mdp` file
like anything else, needs no external software, and is the natural first
enhanced sampling method for anyone already comfortable with the
workflow in Chapter 3. If you want a free energy profile along a
coordinate you can define with a pull group, this is the shortest path
from here to there.

### 5.6.2 Alchemical free energy — native

GROMACS has free energy
settings built in; the analysis is usually done afterwards with `alchemlyb`
or `pymbar`. No patching, but a good deal of protocol design.

### 5.6.3 Metadynamics and OPES — requires PLUMED

PLUMED is a separate library
that drives the biasing through its own input file. Since GROMACS 2025 a
basic PLUMED interface is bundled in — `gmx mdrun -plumed plumed.dat`,
no patching — though it is not yet feature-complete, and older GROMACS
versions still need the patch. It is very widely used, well documented,
and comes with an extensive tutorial series, but it is its own small
language to learn.

### 5.6.4 Weighted ensemble — requires WESTPA

WESTPA is a Python framework that
sits above the simulation engine, orchestrating the walkers, the
splitting and merging, and the bookkeeping. GROMACS runs underneath it
essentially unchanged. The payoff is kinetics; the cost is operational.
A native AWH run that dies can simply be restarted from its checkpoint.
A weighted ensemble run that dies leaves the framework's own bookkeeping
and the simulation files in disagreement, and reconciling them is its
own skill. Budget for that before you commit to it.

### 5.6.5 Where to get the commands

Rather than reproduce commands that will be out of date before the next
GROMACS release, work from the GROMACS manual for AWH and free energy,
the PLUMED masterclass tutorials for metadynamics and OPES, and the
WESTPA documentation for weighted ensemble. All three are actively
maintained and all three are better than a snapshot in a workshop page.

---

## 5.7 Where this is going

Every method in this chapter has the same shape: something has to be
specified in advance by a human who does not yet know the answer. Which
coordinate to bias. Where to place the windows. Which states matter.
Which mutation is small enough to trust.

That is the seam machine learning is prying open, and it is doing it in
several places at once — learning collective variables from data instead
of guessing them, learning bias potentials in more dimensions than a
human can reason about, and, most radically, learning to generate
equilibrium structures directly, which would replace the sampling
problem rather than accelerate it.

That is the next chapter.

But carry one thing forward into it. Nothing in this chapter changed
what a free energy surface *means*, and nothing in the next chapter will
either. A method that produces a landscape faster is not a method that
produces a truer one, and a confidently wrong answer arrives just as
quickly from a neural network as from a badly chosen distance.

---

[← Analysis](04-analysis.md) &nbsp;·&nbsp; [Machine learning →](06-machine-learning.md)
