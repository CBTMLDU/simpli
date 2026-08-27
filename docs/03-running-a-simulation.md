# 3. The Basic Steps of Running an MD Simulation

## 3.1 The primary software - Gromacs

Throughout this workshop we will be using GROMACS, which is one of the
most widely used molecular dynamics engines in biology.

There are several good alternatives — AMBER, NAMD, CHARMM, OpenMM — and
the concepts we cover here transfer to all of them. The specific
commands change, but the pipeline is the same everywhere: build the
system, minimise it, equilibrate it, then run.

We use GROMACS for a few practical reasons.

It is **free and open source**, which matters when you are learning and
when your lab is not flush with software budgets. Everything we do here
can be reproduced by anyone, anywhere, without a licence.

It is **fast**, and unusually well optimised for GPUs. A modern desktop
with a single consumer graphics card can now do work that once needed a
small cluster.

It is **very widely used**, so when something goes wrong — and it will —
someone has almost certainly hit the same error before. The GROMACS user
forum and mailing list archives are an enormous informal knowledge base.

And it is **actively developed**. Recent versions have added constant-pH
simulation, an interface for QM/MM through CP2K, and support for neural
network potentials, so the tool is keeping pace with where the field is
going.

The main thing to know before we start is that GROMACS is a
**command-line tool**. There is no graphical interface. Everything
happens by typing gmx followed by the name of a subcommand, and there
are many of them — for building systems, running simulations, and
analysing the results afterwards.

That feels unfriendly at first. But it is also what makes the work
reproducible: every step you take can be written into a script, saved,
shared, and run again months later to get exactly the same result. That
is worth a great deal more than a set of buttons.

## 3.2 The stage and the actors

### 3.2.1 PDB

A .pdb file is a standard text-based format used to store the 3D
structural data of large biological molecules, such as proteins and
nucleic acids. It simply lists the exact spatial coordinates (x, y, and
z) of all the atoms within the molecule.

Well, to be frank, there can be multiple molecules. More often than not,
we’re dealing with a complex of molecules, and we’re interested in the
interactions between the components of that complex — not to mention the
solvent, the ions, or the hundreds if not thousands of lipid bilayer
members if it's a membrane embedded system — despite the name standing
for “Protein Data Bank.” For very large systems, those with more than
99,999 atoms or more than 62 chains, we use the newer .cif file format.

Although RCSB is one of the primary repositories where we can find most
of these structure files, there are other data banks like PDBe (Protein
Data Bank in Europe) and PDBj (Protein Data Bank Japan) that share this
same archive and can be just as useful.

### 3.2.2 Finding and Downloading the PDB from RCSB

RCSB has a very nice advanced search filter, which you can use to find
your target structure's PDB. Once you find it, there are reports and
descriptions there regarding the methods used to obtain the structure,
its quality, and so on. If you scroll down, you will usually find the
paper that led to the structure, which you might look at for a more
detailed inspection.

The first thing to look at is resolution — the number that tells you how
much detail the experimental data actually supports, and therefore how
far you should trust any individual atom you are about to hand to
GROMACS. Roughly: below 2 Å side chains and ordered waters are well
determined; between 2 and 3 Å the backbone is reliable but side-chain
orientations are increasingly the crystallographer's interpretation;
beyond 3 Å treat individual positions with real caution. But resolution
is one global number, and quality is never uniform — a flexible loop, or
the ligand itself, can be poorly determined in an otherwise excellent
structure. So read everything the entry offers you: the validation
report, B-factors and occupancies for the region you actually care
about, the experimental details, and best of all the paper that produced
the structure. Watch too for missing residues, since disordered loops
are usually left out of the coordinate file rather than flagged.

I will make a hand-waving gesture here — say, for example, how the
structure was obtained could be relevant. If it was expressed in a
vector rather than extracted from its native source, then for a protein
that is heavily modified in its native host, we will most definitely
miss those modifications if it was expressed in a bacterial host. The
crystallization method used might also be relevant. So scrutinize the
context of the PDB structure before downloading it.

The method used to obtain the structure is another important factor.
While cryo-EM and NMR derive structures without crystallization, X-ray
structures come from crystallized molecules. Often the balance between
resolution and the quality of the region of interest — whether a
particular region, say the binding domain, was well defined or largely
modeled — must also be taken into account. If structures obtained by
multiple methods are available for the same molecule or complex, you
might even consider running independent simulations on both to see
whether they give similar results.

After choosing the right PDB structure, we can download it. For
complexes with fewer than 100,000 atoms, downloading the legacy PDB
format works pretty well.

### 3.2.3 Reading the PDB syntax

Tumor suppressor p53 complexed with DNA. Hover or tap any highlighted
field to see what it means and which columns it occupies. The PDB format
is fixed-width, so column position is the syntax.

{{INTERACTIVE: pdb-anatomy}}

### 3.2.4 Cleaning the PDB file

The next step is preparing and grooming the PDB file before we hand it
to our MD software Gromacs. A structure we download from RCSB often
carries things we don't want — crystallization ions, unwanted chains,
leftover buffer molecules — and it is also missing things we do need,
like absent residues, incomplete atoms and unfinished terminals. Both
have to be handled.

#### 3.2.4.1 Removing crystallization additives

Structures solved by crystallography often contain ions, water and small
molecules in the file. Many of these came from the crystallization
buffer, and some waters simply got trapped during crystallization. These
we remove, because we will add our own water and ions during solvation
later.

But we need to be careful too— not every ion or small molecule is an
artifact. Many are structural or catalytic and are genuinely part of the
molecule's biology. The zinc in 1TUP is exactly this case: it holds the
DNA-binding domain together, and removing it would ruin the structure.
So the rule is simple: remove the buffer leftovers, keep the functional
ones.

So how do we distinguish what to keep and what not to keep? By reviewing
the literature and inspecting the pdb structure visually using a pdb
viewing software.

Now, to remove the artifacts (crystallization ions and small molecules)
we look for lines containing HETATM, the identifier that marks anything
which is not a standard amino acid or nucleotide, and by reading the
residue name. Then we remove the lines we don't want — simply deleting
by hand, with bash, or with tools like PyMOL or UCSF ChimeraX.

#### 3.2.4.2 Resolving Alternate Locations

Sometimes a side chain sits in one arrangement in some copies of the
crystal and a different one in others, so the file includes both
(marked as A and B in column 17). This is static disorder across the
many molecules in the crystal, not a single atom moving back and forth.
You must resolve it before building, or pdb2gmx will stop with a
duplicate-atom error. Keep the conformer with the higher occupancy —
listed in columns 55–60 — and delete the other. That is usually the 'A'
version, but check rather than assume, since the occupancies are
sometimes close to equal.

#### 3.2.4.3 Disordered and missing regions

Crystallography cannot see everything. Regions that were too floppy to
resolve simply have no coordinates in the file, and they are listed
under REMARK 465. So these are not things we delete — they are gaps we
have to decide about.

There are two situations. If the gap is in the middle of a chain, we
must fill it in, because a simulation cannot have a hole in the middle
of a molecule. If the missing part is at the end of a chain, we can
usually just leave it out and cap that terminal properly.

A word of warning: do not delete loops just because they look like loose
noodles on screen. Loops and turns are normal, well-ordered parts of a
protein — they simply are not helices or sheets. Cutting one out breaks
the chain and creates artificial ends in the middle of your molecule.
When in doubt, keep it.

#### 3.2.4.4 Filling in missing residues and atoms

Now we fill the gaps. Along with missing residues, structures often have
residues that are present but incomplete, with a few side-chain atoms
missing — these are listed under REMARK 470.

It is best to leave this job to expert tools rather than doing it by
hand. CHARMM-GUI, MODELLER and PDBFixer can all rebuild missing atoms,
and MODELLER in particular is the standard choice for rebuilding missing
loops.

#### 3.2.4.5 Fixing the terminals

Every chain has two ends, and the software needs to know what to put
there. If the chain ends where the real protein ends, we simply leave
the natural charged ends in place — a positive NH₃⁺ at the start and a
negative COO⁻ at the finish. That is chemically correct.

But often the chain ends only because the crystallographer could not see
any further, or because we trimmed something off. In that case the real
protein carries on, and leaving a charge there would be wrong — we would
be putting a charged end in the middle of a molecule that has none. So
instead we cap it with a small neutral group (ACE at the start, NME at
the end) to tidy the cut. Tools like CHARMM-GUI let you choose this for
each chain.

DNA has the same issue at its 5′ and 3′ ends, which is where those
dangling ends we mentioned earlier need attention.

#### 3.2.4.6 CHARMM-GUI

One nice thing to point out is that CHARMM-GUI is a web interface — you
upload a PDB and click through all of the above steps, which makes it
very beginner friendly.

### 3.2.5 Docking

When we are studying how two or more molecules bind, we do not simply
drop them into a box and hope they find each other. If we did, it could
take an unimaginably long time for random motion to bring them together
in the right position with the right pose — far beyond what we can
simulate, and that is before we even think about running replicas.
Biologically that would be the ideal experiment, but computationally it
is out of reach.

So instead we start the simulation with the two molecules already placed
together in a sensible binding pose. Getting that starting pose is what
docking does.

Docking is not manual placement. It is an automated search: the program
generates a very large number of candidate poses, scores each one, and
ranks them. We then choose the pose to carry forward.

#### 3.2.5.1 How docking tools work — and where the biology comes from

Docking programs have no built-in knowledge of biology. They see atoms
with coordinates and charges, not a protein with a function. Everything
they know about your system, you have to tell them. Tools like AutoDock
Vina search through a large number of possible poses and score them on
physical criteria — shape fit, hydrogen bonds, hydrophobic contacts —
and rank the results. Nothing in that process knows whether the pocket
it is searching is the real binding site or an irrelevant crevice.

That is why the way you set up the run matters so much. When you draw a
search box around a known binding site, you are already feeding the
program biology from the literature. You can also choose which side
chains stay flexible and set the protonation states, and these too are
chemical judgements you are making, not things the program works out for
itself. Other tools accept richer input. HADDOCK is the main one: you
feed in what you learned from the literature or from experiments, such
as residues known from mutagenesis to sit at the interface, and it
drives the docking toward poses consistent with that evidence.

Co-folding models are a different case, and increasingly the default
first move. AlphaFold3, Boltz, and Chai-1 do not search a pocket you
define — you give them a sequence and a ligand, and they generate the
complex directly, with the protein free to rearrange as the prediction
forms, something a rigid-receptor tool like Vina simply cannot do. On
standard benchmarks they recover native poses considerably more often
than classical docking, and they handle DNA, RNA, and ions as partners
too. But they are trained on the PDB and lean heavily on that memory:
accuracy falls off for ligands and pockets unlike anything in the
training set, and allosteric sites fare worse than orthosteric ones. The
predicted ligand geometry is also not always physically clean — slightly
wrong bond lengths and angles, non-planar rings — which is survivable in
a figure but not as input to a force field, so check the geometry and
minimise carefully before building. Read the confidence scores seriously
rather than as decoration; they tell you when the model is guessing.

So the practical order is simple. Look up the literature first. If a
structure of your exact complex exists, use it — a real experimental
complex beats any prediction. If not, look for a related protein bound
to the same kind of partner and use it as a template, which most
co-folding tools will accept as an input restraint. If nothing suitable
exists, then fall back on co-folding or blind docking, and treat the
result with appropriate caution either way.

And whichever route your pose came from — literature or a docking tool —
if you have the computing power, do not rely on a single starting
structure. Run several replicas, and include variants where the two
molecules are placed slightly offset from the original pose.

The reason is simple. If the pose is right, the complex should settle
back into it from several nearby starting points. If it only holds
together from the one exact position docking gave you, that is a warning
sign. After all, real binding partners approach from many orientations
rather than one. This also protects you from a docking artifact quietly
becoming the foundation of everything you conclude afterwards.

### 3.2.6 Mutating

Often what we want from MD is a comparison: how does a mutated version
of a biomolecule behave differently from the wild type, in terms of
structural stability or binding? So we introduce the mutation into our
system, run the simulation, and look for differences that might carry
biological meaning.

There are several tools for introducing mutations, each with its own
strengths and weaknesses, which we should weigh before choosing one.

But there is something that often goes unmentioned. Almost all of these
tools take the existing wild-type structure and simply swap the mutated
residue, then let the simulation show how the conformation changes from
there. What this quietly assumes is that the mutant protein reaches the
same folded structure as the wild type in the first place.

In reality, a mutation acts much earlier than the folded state. It is
present during translation, during folding, and during
chaperone-assisted folding, and it may affect any of those. A
destabilizing mutation may cause the protein to become trapped in a
partly folded or misfolded state instead of reaching the native fold at
all — which for p53 is not hypothetical but a well-documented mechanism
of inactivation. Our simulation never sees any of this, because we
handed it a correctly folded mutant to begin with.

So we are starting from a biased point, and we should be careful about
what we claim. The honest way to put it is this: our simulation tells us
what the mutation does to the folded structure, not whether that
structure is ever reached. That is still a useful and legitimate
question. It is simply a narrower one than "what does this mutation do
in the cell."

#### 3.2.6.1 Tools for introducing mutations

As for the tools, PyMOL has a simple mutagenesis wizard where you click
the residue, pick the replacement and choose a rotamer from a ranked
list — quick, visual and ideal for a one-off change. CHARMM-GUI lets you
specify the mutation during preparation and hands back a system ready to
simulate. FoldX goes a step further by repacking the neighbouring side
chains and giving you a fast rough estimate of how much the mutation
destabilizes the protein, which makes it the usual choice when scanning
many mutations at once. Rosetta is the most thorough, since it can also
relax the local backbone, and is worth the extra effort when the new
residue is much larger or smaller than the old one. For insertions and
deletions rather than substitutions, MODELLER is the tool, because the
backbone itself has to be rebuilt. One tool to avoid here is AlphaFold —
it usually returns almost the same structure for wild type and point
mutant, so it cannot show you the effect of your mutation, though it is
perfectly good for building a starting structure when none exists.

### 3.2.7 Membrane bound molecules

There are a handful of membrane building tools, but CHARMM-GUI Membrane
Builder is the default recommendation unless you need something
scriptable, in which case PACKMOL-Memgen is the usual alternative.

The key biological consideration here is the lipid composition — which
membrane your protein actually lives in. A bacterial inner membrane, a
mitochondrial membrane and a mammalian plasma membrane are chemically
very different, and that difference changes how the bilayer behaves. So
again, know your context. Two other things worth checking: some lipids
are genuine structural partners of the protein rather than background,
and if the experimental structure resolved them, they should stay. And
the protein has to be placed in the bilayer at the right orientation and
depth — don't eyeball this; use OPM, which CHARMM-GUI can pull from
directly.

## 3.3 The orchestrator: GROMACS

Once our actor — the PDB — is ready, the orchestrator - GROMACS comes
in.

### 3.3.1 The first handshake

Here the orchestrator meets the actor. We hand our cleaned PDB to
GROMACS with pdb2gmx:

```bash
gmx pdb2gmx -f protein.pdb -o processed.gro -water tip3p -ignh -ter
```

This step is where all our parameter decisions get written down. We
choose the force field, and we declare which water model we will be
using. It may seem odd to name the solvent before we have even built a
box, but nothing is being added yet — we are only telling GROMACS what a
water molecule is, so that when we pour thousands of them in later, it
already has the parameters ready.

The -ignh flag tells it to ignore any hydrogens in our file and add its
own, for the reasons we discussed earlier.

The -ter flag is worth using every time. Our PDB is often truncated, and
the terminals may or may not be properly defined. This option lets us
actively choose what goes on each end of each chain, rather than
accepting whatever GROMACS would apply on its own. It costs two
keystrokes when the terminals are genuinely fine, and it saves you from
a silent mistake when they are not.

There are many more options like this, for handling chain separation,
disulfide bonds, protonation states and so on. For the full list, look
up the official GROMACS documentation:
https://manual.gromacs.org/current/onlinehelp/gmx-pdb2gmx.html

What comes out is a .gro file — GROMACS's own coordinate format — along
with a topology file describing every atom, bond and charge in the
system, and a third file called posre.itp which we will come to shortly.
From here on, the .gro file is what the rest of the commands work with.

#### 3.3.1.1 What GROMACS hands back — .gro, .top and posre.itp

After pdb2gmx you have three files instead of one.

The .gro file holds the where. It is a list of every atom in the system
with its position in space, and later on its velocity as well. That is
all it contains. It does not know that one atom is a carbon and another
is a nitrogen, or which atoms are bonded together, or what any of them
weigh. It is a snapshot of positions, nothing more. If you took a
photograph of the system at one instant, this is what you would be
writing down.

{{INTERACTIVE: gro-top-anatomy}}

The .top file holds the how. This is where the physics lives. For every
atom it records the mass, the electric charge and the atom type. It
records which atoms are bonded to which, how stiff each bond is, what
angle each set of three atoms prefers, and how each set of four atoms
likes to twist. In short, it contains everything needed to work out what
force acts on an atom once you know where all the atoms are. Notice that
it contains no positions at all — it describes what the system is, never
where it happens to be.


You need both, and neither is any use alone. Positions with no
parameters give you a picture but no way to make it move. Parameters
with no positions give you rules but nothing to apply them to. Put them
together and you can compute a force on every atom, which is the one
thing molecular dynamics actually does, over and over again.

The third file, posre.itp, holds a set of springs we can switch on
later. More on that in a moment.

##### 3.3.1.1.1 Why they are kept separate

GROMACS separates the coordinates from the topology because they answer
two different questions. The .gro file says where every atom is. The
.top file says how every atom behaves — its charge, its mass, what it is
bonded to, and every parameter needed to compute a force on it.

Keeping them apart is what makes the setup flexible. The topology can be
rebuilt with a different force field while the structure stays the same,
and it can be edited — adding water, adding ions, adding position
restraints — without ever touching the coordinates. Notice this is
exactly what happens later: gmx solvate and gmx genion add molecules to
the box and simply update the count in the topology's [ molecules ]
list.

##### 3.3.1.1.2 Position restraints (posre.itp) explained

What it does:

It attaches an imaginary spring to each heavy atom in your molecule —
heavy meaning everything except hydrogen. The atoms can still jiggle a
little, but the springs stop them from drifting away from their starting
positions.

Why we need it:

When you first add water to your simulation box, the water molecules are
placed artificially and need time to settle around the protein. The
springs hold your protein steady so the moving water doesn't push it out
of shape while it packs itself in.

​**How it is controlled:**

We turn position restraints **ON** only for the equilibration (settling)
phase. Once the water is settled, we switch the restraints **OFF** for
the actual production run so the protein can move naturally.

​**Note on multiple chains:**

If your protein has multiple chains, GROMACS creates a separate
restraint file for each one. Having a stack of these files is completely
normal.

### 3.3.2 Defining the box

Now that our molecule has proper coordinates and a topology, we confine
it inside a box.

We do this because we are about to fill the surroundings with water, and
without a boundary we would need an infinite amount of it. So we define
a box and apply what is called a periodic boundary condition: if a
molecule drifts out through one face of the box, it re-enters from the
opposite face. If you have played Snake on an old Nokia button phone,
you already know exactly what we are talking about.

The box tiles infinitely in every direction, so our small system behaves
as though it were part of something much larger, with no artificial
walls to bump into. With one limited box, we simulate an effectively
infinite system.

The shape and size of the box matter. Think of it like a gift box —
depending on the size and shape of what you are packing, you choose an
appropriate one. We do the same here, leaving some breathing room around
the molecule.

That breathing room is not decoration. The molecule must never come
close enough to interact with its own periodic image — it would be like
the snake biting its own tail as it comes back around from the other
side of the screen. If that happens, we are no longer simulating a
molecule in solution; we are effectively simulating a crystal of them. A
minimum distance of around 1.0 to 1.2 nanometres from the molecule to
the box edge is the usual starting point, and it should comfortably
exceed the cutoff distance used for non-bonded interactions.

As for shape, a cube is the obvious choice but a wasteful one, because
most of the corners end up filled with water we are paying to simulate.
A rhombic dodecahedron encloses the same clearance in roughly 70% of the
volume, which is a substantial saving in computing time, and it is the
usual recommendation for a globular molecule in solution. A cube still
makes sense for a very elongated molecule, and membrane systems are a
separate case, where the box is built around the bilayer rather than
chosen freely.


```bash
gmx editconf -f processed.gro -o boxed.gro -c -d 1.2 -bt dodecahedron
```

This centres the molecule in the box, sets the minimum distance to the
edge, and chooses the box type.

Two things change in the .gro:

The last line — the box vectors. It was empty or zeros before; now it
holds the real dimensions. Three numbers for a rectangular box, nine for
a dodecahedron, since that shape is slanted.

All the coordinates — because -c centres the molecule, every atom is
shifted. The molecule is moved as a whole, so its internal structure is
untouched.

The .top file is not touched at all. Moving a molecule does not change
what it is made of.

### 3.3.3 Solvation

Once we have defined the container, we want it to mimic in vivo
conditions. Most molecules do not float in a vacuum — they live
submerged in solution. So that is what we do next: we fill the empty
space of the box with solvent molecules, usually water.

```bash
gmx solvate -cp boxed.gro -cs spc216.gro -o solvated.gro -p topol.top
```

This takes our boxed structure — the .gro file — fills every gap around
it with water, and writes out a new .gro containing both the molecule
and the thousands of water molecules now surrounding it. Importantly, it
also updates the topology at the same time, adding a line to [
molecules ] recording how many water molecules went in. This is one of
the few commands that touches both files, because it is genuinely adding
matter to the system.

Choosing the water model

You may notice we already named a water model back at pdb2gmx. That was
the declaration; this is the delivery. The parameters were loaded then,
and now the molecules themselves arrive.

Water is not one thing in simulation. There are several models, and they
differ in how many points they use to represent a single molecule. TIP3P
and SPC/E are three-point models — one oxygen, two hydrogens — and they
are the fastest and by far the most common. TIP4P adds a fourth dummy
point carrying charge, which improves the description of water's
structure at some cost. There are more elaborate models still, but they
are rarely worth it for routine work.

The rule here is simple: use the water model your force field was
parameterised with. CHARMM36 expects a modified TIP3P; AMBER ff19SB was
designed around OPC. Mixing a force field with a water model it was not
built for is a quiet way to get wrong answers, because the two were
tuned together.

Why explicit water, and what it costs

The water is not scenery. It is doing real work in your simulation —
screening charges, forming and breaking hydrogen bonds with the surface,
mediating contacts, and holding the hydrophobic core together by staying
out of it. A protein simulated in a vacuum behaves nothing like a
protein in solution.

The price is that most of your atoms end up being water. In a typical
box, water accounts for the large majority of the system, which means
most of your computing time is spent simulating solvent rather than the
molecule you actually care about. That is the main reason box size
matters so much, and why the wasteful corners of a cubic box are worth
avoiding.

There is a cheaper alternative called implicit solvent, which replaces
the water molecules with a continuum that mimics their average effect.
It is much faster, but it loses the individual water molecules — and
since specific waters often sit in binding sites and bridge
interactions, that loss matters for exactly the questions we usually
care about. For most work, explicit water is the right choice.

Other solvents

Water is the default, but not the only option. You can solvate in other
liquids if your question calls for it — mixed solvents, membrane-mimetic
environments, or higher concentrations of small molecules such as urea,
which is used deliberately in unfolding studies. These need their own
parameters and are more work to set up, but the machinery is the same.

### 3.3.4 Adding ions

After solvating our system, we add ions. There are two reasons for this.

The first is to make the system electrically neutral. Most biomolecules
carry a net charge — a protein might be +5 or −8 overall, and DNA is
strongly negative because of its phosphate backbone. A box with leftover
charge causes problems for the way GROMACS handles long-range
electrostatics, so we cancel it out.

The second reason is biological. Cells are not distilled water. There is
roughly 150 mM of salt inside a cell, and that salt does real work — it
screens charges, it gathers around DNA, and it affects how strongly
molecules stick to each other. So we usually add salt to a realistic
concentration, not just the bare minimum needed for neutrality.

**Why genion needs grompp first**


```bash
gmx grompp -f ions.mdp -c solvated.gro -p topol.top -o ions.tpr

gmx genion -s ions.tpr -o solvated_ions.gro -p topol.top \
           -pname NA -nname CL -neutral -conc 0.15
```


Notice that `genion` takes a `.tpr` file, not a `.gro`. That is
because it has to work out how many ions are needed, and for that it
needs to know the total charge of the system. Charges are not in the
coordinate file — they live in the topology. So it needs both at once,
and a `.tpr` is exactly that: the two combined into a single package.

The tool that does the combining is `grompp`. But it does not take
just those two files. It needs a third.

**What is an .mdp file?**

The `.gro` says **where** the atoms are. The `.top` says
**how** they behave. The `.mdp` is the third piece: it says
**what we want done to them**.

It is a plain text file, just a list of settings written one per line.
How long to run, at what temperature, what kind of calculation to
perform, how to handle the forces. Nothing complicated — but this is
where every decision about the actual simulation gets made.

`grompp` needs all three. It takes the coordinates, the topology and
the settings, checks that they agree with one another, and packs them
into a single `.tpr` file.

**Why we need one here**

This is the odd part: we are not running a simulation at this stage.
`genion` only needs a `.tpr` so it can read the system's charges.
But `grompp` will not build a `.tpr` without a settings file, so we
hand it one.

The result is that `ions.mdp` is close to a formality. The settings
inside it describe a short energy minimisation that never actually
happens. What matters is simply that the file exists and is valid.

Still, it is worth looking at, because the same format — with different
values — drives every stage that follows.

{{INTERACTIVE: mdp-anatomy}}

**A bonus: grompp checks your work**

`grompp` is a strict checker. If your topology and coordinates
disagree — the atom counts do not match, or a molecule is missing from
the `[ molecules ]` list — it stops and tells you. That is a good
thing. Far better to be caught here than after a week of computing.

We will meet `grompp` again before every stage that follows, always
doing the same job.

**How the ions get placed**

`genion` does not scatter ions randomly. It replaces existing water
molecules with ions, picking spots where the charge balance is most
favourable. This is why we solvate first and add ions afterwards. When
it runs, it will ask which group to take water from — choose the solvent
group, usually called SOL.

Sodium and chloride are the usual default. But potassium is actually the
main cation inside cells, so for an intracellular protein it may be the
better choice. Worth a moment's thought rather than accepting the
default blindly.

**Structural and catalytic ions are a separate matter**

Everything above is about background salt. The functional ions in your
molecule are a completely different case, and they are not added here.

Think back to the zinc in 1TUP. That zinc is part of the protein — it
holds the DNA-binding domain together. It should have been kept during
cleaning and carried through `pdb2gmx`. `genion` places ions by
electrostatics alone and has no idea that a particular zinc belongs in a
particular pocket, so it cannot help you here.

If such an ion is genuinely missing from your structure, you place it
during the PDB preparation step, not now. The usual method is to borrow
it: find a related structure where the ion is resolved, superimpose it
onto yours, and copy the ion's coordinates across. Because the
surrounding residues are usually well conserved, the borrowed position
is normally very good. Never guess a position by eye.

The harder part is not placement but parameters. A tightly held metal
often needs special treatment so it stays properly coordinated during
the run, and organic cofactors like heme or NAD need small-molecule
parameters of their own. Many common ones already ship with the force
fields, so check first. This is fiddly work, and it is the main reason
people route systems with cofactors through CHARMM-GUI, which assembles
the topology for you.

So the rule is simple: **background salt goes in here; functional ions
belong to the molecule and should already be there.**

### 3.3.5 Energy minimisation

The solvated, electroneutral system is now assembled. But before we can
begin dynamics, we have to make sure there are no steric clashes or
awkward geometry anywhere in it. We fix that through a process called
energy minimisation.

Why it is needed

Think about what we have just built. Hydrogens were added by a program.
Missing side chains were rebuilt by a tool that guessed a rotamer.
Thousands of water molecules were dropped in on a regular grid, and some
ions replaced a few of them. Nothing about this arrangement is
physically relaxed. Somewhere in that box there will be atoms sitting
far too close to one another.

That matters because force grows steeply as atoms approach. Two atoms
overlapping slightly can produce an enormous force between them. If we
started dynamics straight away, that force would fling an atom across
the box in a single step, and the simulation would fail — usually with
an error about the system blowing up, or particles moving more than a
cell in one step.

So minimisation comes first. It walks the system downhill in energy,
nudging atoms apart until nothing is badly strained.

What it is not

Minimisation is not a simulation. There is no time, no temperature and
no motion in the physical sense — atoms have no velocities here. It
simply slides everything toward the nearest low-energy arrangement, one
small step at a time, and stops when nothing is being pushed too hard.

It also does not find the best structure. It finds the nearest
comfortable one. Minimisation only goes downhill, so it settles into
whichever local minimum happens to be closest to where you started. That
is exactly what we want here — we are removing clashes, not searching
for a better fold.

**Running it**

```bash
gmx grompp -f minim.mdp -c solvated_ions.gro -p topol.top -o em.tpr
gmx mdrun -v -deffnm em
```

The pattern is the one we have already seen: grompp gathers the
coordinates, the topology and the settings into a .tpr, and then the
engine runs it.

This is our first proper meeting with mdrun, which is the part of
GROMACS that does the actual computing. The -deffnm em flag simply tells
it to name everything it produces em.something, which saves typing out
each output file.

**What mdrun leaves behind**

It is worth noting what comes out, because every run from here on writes
the same small family of files, sharing the name we gave with -deffnm:

em.gro — the final coordinates. This is what we hand to the next step.

em.log — a plain text log of what happened. Worth opening when something
goes wrong.

em.edr — the energy file, recording values like energy, temperature and
pressure through the run. It is binary, so we use gmx energy to pull
numbers out of it.

em.trr — the trajectory file. Here it is nearly empty, because our
settings file never asked for frames to be saved.

That last point is worth remembering: trajectories are only written if
you ask for them. Our minim.mdp said nothing about saving coordinates,
so nothing was saved. From the equilibration stage onward we will start
asking.

Note also that none of these appeared during the earlier steps. grompp
and genion only shuffle files around — nothing was simulated, so there
was nothing to record.

The settings file, minim.mdp, looks much like the ions.mdp we already
examined — but this time the settings are real, and the calculation
actually runs. The key lines are integrator = steep, which walks
downhill, and emtol, which sets how relaxed is relaxed enough.

{{INTERACTIVE: minim-mdp-anatomy}}

Checking that it worked

Do not skip this. Two numbers tell you almost everything:

The potential energy should be large and negative, and it should have
fallen steadily during the run. For a typical solvated protein you would
expect something in the order of 10⁵ to 10⁶ kJ/mol negative — the exact
figure depends on system size, so what matters is that it decreased and
then levelled off.

The maximum force should have dropped below your emtol. If it did not,
and the run stopped because it hit the step limit instead, something is
wrong upstream — often a badly rebuilt residue, an overlapping ligand,
or a structural problem you carried in from preparation.

You can extract both with:

```bash
gmx energy -f em.edr -o potential.xvg
```

And plot the results.

A common misunderstanding

Minimisation removing clashes does not mean the structure is now
correct. It means the structure is no longer physically impossible.
Those are different things. The water is still sitting in an artificial
arrangement, nothing has any thermal motion yet, and the protein has not
had a chance to relax in a realistic way.

That is what equilibration is for, and it comes next.

### 3.3.6 Equilibration part one: temperature (NVT)

Minimisation left us with a system that is no longer physically
impossible — but it is also completely still. Every atom sits exactly
where it was placed, with no motion at all. Real molecules are not like
that. At body temperature everything is vibrating, jostling and drifting
constantly.

So the next job is to warm the system up to the temperature we want to
study, and let it settle there.

**What NVT means**

NVT is simply a label for what we are holding fixed. **N** is the
number of particles, **V** the volume of the box, and **T** the
temperature. So during this stage the box stays exactly the size we made
it, no atoms come or go, and we control the temperature. Pressure is
left alone for now — we will deal with that in the next step.

The reason for doing temperature first is practical. Warming the system
and letting the box resize at the same time would mean two things
changing at once, and if something went wrong we would not know which
was responsible. Doing one at a time is simply easier to control and
easier to diagnose.

**How temperature is controlled**

Temperature in a simulation is just a measure of how fast the atoms are
moving. To warm the system, GROMACS gives every atom a random starting
velocity drawn from the distribution appropriate to our target
temperature — this is the velocity seed we discussed much earlier, the
one that makes replicas independent.

From then on a **thermostat** keeps the temperature steady, gently
speeding atoms up or slowing them down as needed. This matters because
the system will heat itself as it relaxes: as atoms settle into more
comfortable positions, that released energy turns into motion. Without a
thermostat the temperature would simply drift upward.

The choice of thermostat is worth one sentence. The older
**Berendsen** method holds temperature well but does not reproduce a
correct distribution of energies, so it should not be used for anything
you intend to analyse. Use **velocity-rescale (v-rescale)** or
**Nosé-Hoover** instead.

#### 3.3.6.1 Position restraints

This is where those springs from `posre.itp` finally get used.

Remember the problem: our water was placed on an artificial grid and has
not yet found its natural arrangement. As it settles, it will push and
pull on the protein. If the protein is free to move at the same time,
the solvent can shove it out of shape before it has settled down.

So we switch the restraints on for this stage. The heavy atoms of the
protein are tethered to their starting positions — they can still
vibrate, but they cannot wander. The water is left completely free to
move, which is exactly what we want, because the water is what needs to
reorganise.

Switching them on takes one line in the settings file:


```bash
define = -DPOSRES
```


Note also the `-r` flag in the command below. It tells GROMACS which
structure the springs should pull *towards* — the reference positions.
Here we use our minimised structure, so everything is tethered to where
minimisation left it.

**The settings file**

This is the first file that actually moves atoms through time, so it is
considerably longer than the ones before it.

{{INTERACTIVE: nvt-mdp-anatomy}}

**Running it**


```bash
gmx grompp -f nvt.mdp -c em.gro -r em.gro -p topol.top -o nvt.tpr

gmx mdrun -v -deffnm nvt
```


A hundred picoseconds is a common length for this stage — long enough
for the temperature to settle, short enough to finish quickly.

**Checking that it worked**

One number matters here: the temperature.


```bash
gmx energy -f nvt.edr -o temperature.xvg
```


Plot it, and you should see the temperature climb rapidly to your target
— 300 K, or whatever you chose — and then stay there, fluctuating around
it. Those fluctuations are normal and expected; a small system genuinely
does wobble in temperature. What you are looking for is a flat average,
not a flat line.

If the temperature is still climbing at the end, run longer. If it never
settles, something is wrong upstream.

### 3.3.7 Equilibration part two: pressure (NPT)

The previous step stabilised the temperature. Now we do the same for
pressure — and with it, the density.

Why this stage is needed

Think about what we built. We drew a box, filled it with water, and
swapped a few waters for ions. Nothing about that guaranteed the right
amount of water in that space. The system might be slightly too crowded
or slightly too sparse.

So now we let the box itself adjust. If the system is too dense, the box
expands a little; if too sparse, it shrinks. It settles until the
pressure inside matches the pressure we asked for, and the density
arrives at a realistic value on its own.

What NPT means

Same naming logic as before. N is the number of particles, P the
pressure, T the temperature — all held constant. The volume is now free
to change, which is exactly the difference from NVT.

This is called the isothermal-isobaric ensemble, and it is the one that
most closely resembles a real experiment. A test tube on a bench is at
constant temperature and constant atmospheric pressure, with the liquid
free to occupy whatever volume it likes.

**Choosing a barostat**

The same caution we gave for thermostats applies here. The
**Berendsen** barostat brings the volume to the right value quickly
and robustly, which makes it a reasonable choice for equilibration, but
it does not produce a correct ensemble, so it should not be used for a
production run you intend to analyse. For that, use **C-rescale**,
which is the modern recommendation and is stable enough to use from the
start, or **Parrinello-Rahman**, which is well established but can
oscillate badly if it is switched on before the system is already close
to the right density.

Handing over from the previous run

This is the first time we continue from an earlier simulation rather
than starting fresh, and three things change to make that work.

In the settings file, continuation = yes tells GROMACS this is not a
fresh start, and gen_vel = no tells it not to generate new velocities —
we want to keep the motion the system already has.

In the command, the -t flag supplies the checkpoint file from NVT. That
file holds the complete state of the system: velocities, thermostat
variables, everything. Without it we would be throwing away the
temperature equilibration we just paid for.

**The settings file**

Nearly the same file as the one before it. Only four things changed.

{{INTERACTIVE: npt-mdp-anatomy}}

**Running it**

```bash
gmx grompp -f npt.mdp -c nvt.gro -r nvt.gro -t nvt.cpt -p topol.top -o npt.tpr
gmx mdrun -v -deffnm npt
```

The position restraints stay on for this stage. The protein is still
being held while its surroundings settle.

**Checking that it worked — and a warning**

Here is where people get worried unnecessarily. Plot the pressure:

```bash
gmx energy -f npt.edr -o pressure.xvg
```

It will look terrible. The pressure jumps around wildly, swinging by
hundreds of bar, when we asked for 1 bar. This is completely normal.
Pressure in a small box is a genuinely noisy quantity, and those
fluctuations are real physics, not a mistake. What matters is that the
average sits in the right region, not that the line looks flat.

Density is the far more useful check:

```bash
gmx energy -f npt.edr -o density.xvg
```

This should settle quickly and stay steady. For a protein in TIP3P
water, expect something a little above 1000 kg/m³ — water itself is
about 1000, and the protein makes it slightly denser. A stable density
line is your real evidence that the system has equilibrated.

One caution: pressure-related properties converge slowly. A hundred
picoseconds suffices for a small system like ours, but larger or more
complex systems may need considerably longer.

### 3.3.8 The production run

Both equilibration stages are done. The system sits at the temperature
and pressure we want, the water has arranged itself properly, and the
density has settled. Everything up to this point was preparation — none
of it was data.

Now we take the springs off and let the system go.

**Releasing the restraints**

This is the moment the protein is finally free. Up to now it has been
tethered near its starting positions while its surroundings sorted
themselves out. We remove that by simply leaving out the `define =
-DPOSRES` line. The `posre.itp` file is still sitting there and is
still included in the topology, but nothing switches it on, so it does
nothing.

**Deciding how much to save**

This is the one genuinely new decision at this stage, and it deserves a
moment's thought before writing the settings file.

Every simulation writes out snapshots as it runs, and you choose how
often. Save too frequently and you get enormous files and a slower run,
for detail nobody will ever look at. Save too rarely and the motion you
were trying to observe simply is not in your trajectory.

So think about your analysis first. If you are measuring how a large
domain drifts over a nanosecond, saving once every 10 picoseconds is
plenty. If you are watching a fast local rearrangement, you will want
finer spacing.

Remember also the difference between the two trajectory files. The
compressed `.xtc` holds positions only, at reduced precision, and is
what you want for almost all analysis. The full-precision `.trr` can
also hold velocities and forces, which makes it far bigger, and you only
need it for the specific analyses that require them. Most people write
the `.xtc` frequently and the `.trr` rarely or never.

**How long would you run?**

The example below sets 1 nanosecond. That is a convenient number for
showing the workflow, but it is not a serious production length. Recall
what we said much earlier about timescales — published work typically
runs hundreds of nanoseconds to microseconds, and even that only reaches
the faster end of biological motion.

The useful point is that length is a single number. `nsteps`
multiplied by `dt` is your total simulated time, and nothing else in
the file needs to change to run longer. What does change is how long you
wait, and how much disk space you need.

**The settings file**

With those decisions made, here is what the production `.mdp` looks
like.

{{INTERACTIVE: md-mdp-anatomy}}

**Running it**

Now the familiar pair of commands.


```bash
gmx grompp -f md.mdp -c npt.gro -t npt.cpt -p topol.top -o md.tpr

gmx mdrun -v -deffnm md
```


As before, `-t` carries over the full state from the previous run, so
the motion we equilibrated is preserved rather than thrown away. Notice
the command has also lost its `-r` flag — that existed only to tell
the restraints where to pull toward, and with no restraints there is
nothing to point at.

You may see `grompp` print an estimate of how much data the run will
generate, along with something called the PME load. That second number
tells you what fraction of the effort goes into the long-range
electrostatics, which is useful when tuning performance on larger
machines.

**A note on GPUs**

The commands above are written plainly, to keep the logic clear. In
practice, on a machine with a GPU, you will want to tell `mdrun` to
use it properly:


```bash
gmx mdrun -deffnm md -nb gpu -pme gpu -bonded gpu -update gpu \
          -ntmpi 1 -ntomp 8 -pin on
```


Each flag moves a different part of the calculation onto the graphics
card. `-nb` is the non-bonded forces, `-pme` the long-range
electrostatics, `-bonded` the bonds and angles, and `-update` the
actual integration step. Moving all four across means the data stays on
the GPU instead of being shuttled back and forth every step, which is
where most of the speed-up comes from. `-pin on` keeps the threads
tied to fixed processor cores rather than being moved around.

Two things to know. First, the thread numbers depend entirely on your
hardware — `-ntomp 8` suits an eight-core machine, and it is worth
testing a few values to see what runs fastest on yours. Second,
`-update gpu` does not work with every feature; if your run uses
something incompatible, GROMACS will simply tell you and fall back to
the processor. It is not something you can break by trying.

## 3.4 Keeping an eye on the run

Your simulation is now running, and it may run for hours or days. You do
not have to sit and wait blindly. Almost everything you might want to
know is available while it is still going.

This matters for a practical reason. If something has gone wrong, you
want to find out in the first ten minutes, not after three days of
wasted computing.

How fast is it going, and when will it finish?

If you started mdrun with the -v flag, it prints its progress directly
to the screen — which step it is on, how far through it is, and an
estimate of how much longer it will take. That estimate becomes reliable
after the first minute or so, once the program has settled into a steady
rhythm.

The number people quote to each other is nanoseconds per day — how much
simulated time you get for one day of real time. It is the honest
measure of your machine's speed, and it lets you work out in advance
whether the run you are planning is realistic. If you are getting 20
ns/day and you want a 500 ns simulation, that is twenty-five days.
Better to know now.

Reading the log file while it runs

The .log file is being written as the simulation goes, so you can read
it at any time. On Linux the useful command is:

```bash
tail -f md.log
```

This shows the end of the file and keeps updating as new lines appear.
Press Ctrl+C to stop watching — it does not affect the simulation.

The log prints a block of numbers at intervals, showing the current
energies, temperature and pressure. It is the simplest way to see
whether things look sensible.

Checking the numbers properly

You do not have to wait for the run to finish. gmx energy works
perfectly well on a partially written .edr file:

```bash
gmx energy -f md.edr -o check.xvg
```

It responds with a numbered list of everything it has recorded —
potential energy, temperature, pressure, density, box dimensions and so
on. You type the number of what you want, press Enter, and then Enter
again on a blank line to finish. You can pick several at once by typing
their numbers separated by spaces.

One thing worth knowing: those numbers are not fixed. Which term sits at
15 or 16 depends on your system and your settings, so do not memorise
them — read the list each time. If you want something you can script
reliably, use the name instead:

```bash
echo "Temperature" | gmx energy -f md.edr
```

**What it prints back**

For each term you selected, you get four numbers straight in the terminal.

**Average** is the mean value over the period analysed. This is usually
what you actually wanted.

**Err. Est.** is an estimate of how uncertain that average is.

**RMSD** is how much the value fluctuates around the average. For pressure
this will be large, in the hundreds of bar, and that is entirely normal.

**Tot-Drift** is how much the value moved from the start of the run to the
end. This is the useful one for checking health. A drift close to zero
means the property is stable. A steady drift in temperature, density or
the conserved energy term means something is wrong.

**Skipping the early part**

The beginning of a run often includes some settling that would distort your
averages. The -b flag tells it to start from a given time in picoseconds:

```bash
echo "Density" | gmx energy -f md.edr -b 100
```

Add -o only when you want to plot the curve rather than just read the
summary. For a quick check, the terminal output is enough.

**Looking at the structure so far**

Numbers do not tell you everything. Pull out a recent frame and look at it:

```bash
echo "Protein" | gmx trjconv -f md.xtc -s md.tpr -o snapshot.pdb -dump 500
```

Open it in PyMOL or ChimeraX. Is the protein still folded? Is the ligand
still in its pocket? Is anything obviously broken? Thirty seconds of
looking can save you days.

**Warning signs to watch for**

A few things in the log mean trouble.

**LINCS warnings** say a constrained bond could not be held at its proper
length. One or two at the very start can be harmless. A stream of them
means the system is unstable and heading for a crash.

**"Water molecule cannot be settled"** is the same problem for water, and
usually means something is badly wrong upstream.

**Energies becoming enormous or showing as nan** means the simulation has
blown up. There is no recovering from this — you go back and find the
setup problem.

Almost always, these trace back to something before the run: a bad
structure, a clash minimisation did not fix, or a mistake in preparation.

**Is your hardware actually being used?**

If you have a GPU, check it is working rather than sitting idle:

```bash
nvidia-smi
```

This shows how busy the graphics card is. If it is near zero while your
simulation is supposedly running on it, your flags are not doing what you
think.

At the end of every run GROMACS also prints a performance summary in the
log, showing where the time went. It is worth reading once, because it
tells you what is limiting your speed.

**If the run stops unexpectedly**

Power cuts happen. So do accidental closures and full disks. GROMACS writes
a checkpoint file periodically, holding the complete state of the system.
If a run is interrupted, you resume from it rather than starting over:

```bash
gmx mdrun -deffnm md -cpi md.cpt
```

It picks up where it left off and continues writing to the same output
files. This is one of those features you will not think about until the day
you desperately need it.

## 3.5 Checkpoint files

As it runs, GROMACS periodically saves a .cpt file holding the complete
state of the system — positions, velocities, and the thermostat and
barostat settings — so a run can be resumed exactly where it stopped. It
writes one every fifteen minutes by default, and keeps a backup copy of
the previous one in case the newest gets corrupted mid-write. Note this
is a different thing from the trajectory: the .xtc is for looking at
afterwards, the .cpt is purely for continuing.

## 3.6 Beyond the standard run: advanced controls

So far our system has just been sitting there. We set a temperature, set
a pressure, and left it alone to do whatever it does. That is the
standard experiment, and it answers a lot of questions.

But we do not have to be so passive. GROMACS lets us change the
conditions while the simulation is running, and even push and pull on
the molecule directly. We will not go into how to set any of this up —
that is a workshop on its own — but it is worth knowing these things
exist, because one day your question will need them.

Changing the conditions as you go

The temperature does not have to stay the same throughout. You can give
GROMACS a schedule instead: hold at 300 K for a while, then warm up
slowly to 400 K, then hold again.

This is the natural way to study how heat breaks a protein apart.
Instead of running several separate simulations at several temperatures
and comparing them, you heat one system gradually and watch where it
gives way.

The same trick works for pressure. You can change the target as the run
goes along, and push the system through a change rather than waiting for
it to happen by itself.

There is one thing to be careful about, and it is the same warning we
met with pH earlier. If you change conditions slowly, the system keeps
up. If you change them quickly, it falls behind. Sometimes that lag is
exactly what you want to see. Sometimes it is just an artefact. Either
way, you have to think about the speed and be able to defend it.

Pushing and pulling

You can also apply force directly to your molecules.

You can pull two molecules apart at a steady speed, hold one at a fixed
distance from another, or push in a chosen direction with a set amount
of force. This is how people study how a drug leaves its binding site,
how a protein unfolds when stretched, and how molecules squeeze through
channels.

There is a related option that stretches the box itself, slowly changing
its shape over time. That is useful when the thing you want to squeeze
or stretch is the whole system rather than one molecule inside it.

Stretching a membrane

This one deserves a mention on its own, because it is how mechanically
activated channels are studied.

Normally the box is squeezed equally from all sides. But you can ask
GROMACS to treat the membrane differently: pull outward in the plane of
the membrane, while keeping normal pressure in the direction across it.
This stretches the bilayer, thinning it and spreading the lipids apart.

Then you simply watch what the protein does. A channel that opens when
its membrane is stretched should open here too — and that is exactly how
stretch activation is thought to work in a real cell.

It is not easy to get right. Stretch too hard and you tear the membrane
apart before anything interesting happens, and researchers are still
developing better ways of applying the pull gently and locally.

One more thing: you can change GROMACS itself

Worth knowing, especially if you ever hit a wall with what the program
offers. GROMACS is free and open source, so the entire code is available
to read, modify and build yourself. If a feature you need does not
exist, you can add it, and other groups do exactly that — several
well-known tools are add-ons written by outside researchers rather than
by the GROMACS team.

You are unlikely to need this early on. But it means the ceiling is much
higher than the list of options in the manual suggests.

---

[← Scope and limitations](02-scope-and-limitations.md) &nbsp;·&nbsp; [Analysis →](04-analysis.md)
