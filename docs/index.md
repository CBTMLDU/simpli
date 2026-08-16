# 0. Simulating Bits and Pieces of Life in GROMACS

## Instructor's Note

Let me start with an uncomfortable question: how much molecular dynamics work ever reaches a patient?

Very little. And it is worth understanding why before you spend a year of your life on a simulation.

The COVID period made this impossible to ignore. Software became easy to get and everyone rushed in, producing a surge of rapidly performed docking studies nominating drug candidate after drug candidate on computational arguments alone — most of which, though well intentioned, ignored the best practices the field had spent years building (Tropsha et al., *Chem. Soc. Rev.* 2023, 52, 872). Thousands of papers. Essentially no medicines. This is not a failure of ability so much as a habit: hurrying toward a publishable figure without pausing to ask what claim the evidence can actually support.

But it would be wrong to conclude that MD cannot deliver. It can, and it has. [D. E. Shaw Research](https://www.deshawresearch.com/drug-discovery.html) has taken several simulation-driven compounds into clinical trials, their lead one — zovegalisib — now in Phase 3 for metastatic breast cancer. They are, by most accounts, the only clear success story for a purely simulation-led approach to drug discovery.

It is worth looking closely at *how* they did it, though, because the answer is instructive. They built their own supercomputer. Their signature results come from simply running long enough — in one of their studies, a drug molecule placed at random in a box found its own binding site with no bias applied at all. They did not outsmart the sampling problem. They out-spent it.

That is not a path open to us. We lack the computing power that kind of work demands, and no amount of care substitutes for a machine we do not have.

So the realistic answer is the one everybody without an Anton uses: **enhanced sampling**. Umbrella sampling, AWH, alchemical free energy methods. These do not wait for a rare event to happen by itself; they extract the answer directly. And for drug discovery in particular, alchemical free energy calculations have been the industry workhorse for decades, now reaching accuracies near 1 kcal/mol. A well-designed calculation on a modest workstation can answer a question that a brute-force run a hundred times longer could not.

The field is also moving quickly toward AI. Neural network potentials now run inside GROMACS itself, generative models produce protein ensembles in minutes rather than months, and design loops let an AI propose molecules while simulations score them and feed the results back. Used well, this is a genuine multiplier for a small group: it lets modest computing power be aimed where it matters rather than spent uniformly.

Further ahead sits quantum computing, and real progress is being made — a 12,635-atom protein was modelled on quantum hardware in May 2026 ([IBM news release](https://newsroom.ibm.com/2026-05-05-cleveland-clinic,-riken,-and-ibm-model-a-12,635-atom-protein-the-largest-known-to-be-simulated-with-quantum-computers)). What it promises is not longer simulations but *truer* ones. Quantum computers calculate electronic structure directly, which could eventually give us force fields far beyond the fixed charges we work with today, and a proper treatment of active sites and metal centres. That is a different improvement from the one we most need — but it is a real one, and it may be where this field ends up.

The caution, through all of it, is simply that sophistication is not impact. What decides whether work translates is not how advanced the method is, but whether it ends up reflecting actual *in vivo* biology.

Let this work be a nudge in that direction. It will not teach you how to run the experiments — but it will teach you to simulate carefully enough that the results are worth taking to someone who can.

---

[What is an MD simulation →](01-basics.md)
