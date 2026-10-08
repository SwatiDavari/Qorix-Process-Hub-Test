.. _qx_missions:

Missions
########

One process hub for every Qorix project. The hub defines how Qorix works - workflows,
work products, roles and templates for each process - once, in a technology-neutral
model, and every project inherits it and narrows it in its own tailoring.

What the hub is built from
==========================

The repository follows the system-of-interest structure of ISO/IEC/IEEE 15288:

.. code-block:: text

   Qorix Process Hub                root = system of interest
   |-- needs/                       what the hub must satisfy: standards catalogue
   |-- prod/                        the system
   |   |-- missions/                why the hub exists (this page)
   |   |-- concepts/                process model, tiering, metamodel, tiers
   |   |-- realization/             qpm tool, docs build macro, regeneration
   |   '-- assemblies/
   |       '-- <cluster>/           cluster assembly
   |           '-- <process>/       process assembly
   |               |-- process/        identity, classification, getting started, concepts
   |               |-- workflows/      workflows (IN -> activities -> OUT, roles RWE)
   |               |-- work_products/  work products (purpose, concepts, template)
   |               |-- roles/          roles
   |               '-- templates/      templates and guidance
   '-- dist/                        distributions: one tailoring per project (#1, #2, ...)

Each assembly is classified by **enabler** (PRD, TST, BLD, DOC, SAF, SEC),
**scope** (GLOB, FEAT, COMP, UNIT) and **layer** (INT, REQ, ARC, DES, IMP).

Identifiers
===========

Every identifier follows ``<type>_qx_<assembly code>_<name>``, for example
``wf_qx_gc_tailor_project``, ``wp_qx_saf_safety_tailoring`` or
``rl_qx_qa_quality_office``. Identifiers never contain a double underscore; the
generator rejects any that do.
