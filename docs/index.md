# 0. Simulating Bits and Pieces of Life in GROMACS

Let me start with an uncomfortable question: how much molecular dynamics
work ever reaches a patient?

Very little. And it is worth understanding why before you spend a year
of your life on a simulation.

The COVID period made this impossible to ignore. Software became easy to
get and everyone rushed in, producing a surge of rapidly performed
docking studies nominating drug candidate after drug candidate on
computational arguments alone — most of which, though well intentioned,
ignored the best practices the field had spent years building (Tropsha
et al., Chem. Soc. Rev. 2023, 52, 872). Thousands of papers. Essentially
no medicines. This is not a failure of ability so much as a habit:
hurrying toward a publishable figure without pausing to ask what claim
the evidence can actually support.

But it would be wrong to conclude that MD cannot deliver. It can, and it
has. D. E. Shaw Research has taken several simulation-driven compounds
into clinical trials, and groups like Peter Coveney's at UCL have built
free energy methods now used alongside commercial tools in industry.
What these efforts share is not better software. It is that their
predictions get tested. One approach ends in an experiment; the other
ends in a figure.

Beyond that cultural problem, we face a plain infrastructural one. We
largely lack the computing power that genuinely impactful MD demands.

Quantum computing is often raised as the eventual answer, and real
advances are being made (IBM news release). But let’s be clear about
what it promises. Quantum computers aim at calculating electronic
structure more accurately, not at making our simulations longer. Better
energies could eventually give us better force fields and a proper
treatment of active sites and metal centres. What they will not do is
hand us the microseconds we are short of. So we cannot simply wait for
that day.

Right now, if we want our work to carry practical value, we need to
pivot toward advanced enhanced sampling: umbrella sampling,
metadynamics, AWH, alchemical free energy methods. These offer an
elegant workaround for the microsecond-scale simulations we cannot
afford to replicate.

The field is also moving quickly toward AI. Neural network potentials
now run inside GROMACS itself, generative models produce protein
ensembles in minutes rather than months, and design loops let an AI
propose molecules while simulations score them and feed the results back
— an approach known as generative active learning. Used well, this is a
genuine multiplier for a small group: it lets modest computing power be
aimed where it matters rather than spent uniformly.

The caution is the same one as before. Sophistication is not impact.
What decides whether work translates is not how advanced the method is,
but whether it ends up reflecting actual in vivo biology.

Let this work be a nudge in that direction: not a guide to translation,
but to doing the simulation well enough to deserve it.

---

[What is an MD simulation →](01-basics.md)
