# 1. What Is an MD Simulation: The Basics

The basic idea behind an MD simulation is straightforward. Given the
positions of all of the atoms in a biomolecular system (e.g., a protein
surrounded by water and perhaps a lipid bilayer), one can calculate the
force exerted on each atom by all of the other atoms. One can thus use
Newton’s laws of motion to predict the spatial position of each atom as
a function of time. In particular, one steps through time, repeatedly
calculating the forces on each atom and then using those forces to
update the position and velocity of each atom. The resulting trajectory
is, in essence, a three-dimensional movie that describes the
atomic-level configuration of the system at every point during the
simulated time interval.

{{VIDEO: md-simulations}}

---

[← Home](index.md) &nbsp;·&nbsp; [Scope and limitations →](02-scope-and-limitations.md)
