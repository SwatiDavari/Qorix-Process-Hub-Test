.. _qx_objectives:

Business Objectives
###################

The objectives every Qorix process, policy and project exists to serve. They sit at the top of
the chain: objective, policy, process, outcome, capability, work product. They state what the
organisation wants, in terms that name no standard, integrity level, tool or product domain.
Standards bind one layer down, through the policies and the ``complies`` links.

Ownership
=========

ISO/IEC/IEEE 15288 keeps processes consistent with "the organization's objectives" in Life
Cycle Model Management (6.2.1). The hub's Governance and Compliance assembly
(``compliance/governance_compliance``) carries that process, so it owns the objectives. The
Head of G&C (``rl_qx_gc_head``) is the owner of every objective. Another assembly may deliver an
objective, but it does not own it.

Fields
======

Every objective has an identifier, a title, a statement, one measure, a target, a scope, an owner
role, the policies it drives, and the assembly that delivers it. They are kept in ``needs/objectives.yaml``. The scope is ``GLOB`` for the
organisation. A project may state its own objectives at project scope, and each one must
``contribute to`` a GLOB objective. This mirrors how a project-scope process is part of its
organisation-scope process.

Targets are set by Qorix, not by the hub. They stay ``TBD`` here until the Head of G&C approves
them.

Objectives
==========

The objectives are listed in the :ref:`qx_objective_register`, generated from ``needs/objectives.yaml``.
Each one is a model element (``objective``) that drives one or more policies.

Neutrality rule
===============

No standard name, integrity level, tool, language or product-domain term appears in an
objective's title, statement or measure. Such names appear only in the policy that the objective
drives and in that policy's ``complies`` links. Integrity ceilings and capability targets live in
the project tailoring record.

Conformance claim
=================

The hub claims tailored conformance to ISO/IEC/IEEE 15288, not full conformance. Annex A states
that tailoring is not permitted when full conformance is claimed. Objective
``obj_qx_gc_tailor_not_fork`` therefore also protects the claim: each tailoring is recorded with
its rationale.

Out of scope
============

Portfolio Management (15288 6.2.3), meaning investment, resourcing and project viability, has no
assembly in the hub. Objectives on those topics have nowhere to attach and are not defined here.

What the checker enforces
=========================

``qpm check-process`` fails the build when an objective:

* lacks a title, statement, measure, target, scope, owner or delivering assembly;
* names an owner role or assembly that does not exist, or a policy that does not exist;
* names a standard, integrity level, tool or product-domain term in its title, statement or measure;
* has scope ``PROJECT`` without a ``contributes_to`` GLOB objective, or scope ``GLOB`` with one.

It also fails when a policy is driven by no objective. An objective that drives no policy is a
warning, which today flags ``obj_qx_gc_process_shareable``.
