.. _qx_process_introduction:

Introduction
############

This page explains how the Qorix process description is built and how to read it. The
process areas themselves are listed in the :ref:`qx_organisation_level` and the
:ref:`qx_project_level`.

The process model
=================

Every process area uses the Eclipse S-CORE process model. Four kinds of element
describe a process:

* **Workflows** - what is done, as a sequence of activities, each performed by a role.
* **Work products** - what a workflow takes in and produces. Each one has a purpose, a
  concept that explains its content, and a template.
* **Roles** - who does the work. Every workflow names a responsible role, an approver
  who signs off, and optional supporting roles (responsible / approver / expertise).
* **Guidance** - templates and checklists that help a role produce a work product.

The full model, including how these elements link to each other, is in
:ref:`qx_workflow_model`.

Reading order within a process area
===================================

Each process area has the same pages, in this order:

#. **Overview** - purpose, level, maturity, owner, applicable standards and the
   area's concepts.
#. **Workflows** - a diagram of how workflows and work products connect, then each
   workflow with its activities.
#. **Work products** - what each workflow produces and why.
#. **Roles** - who is involved.
#. **Guidance** - the templates to use.

What guidance may contain
=========================

Guidance is solution-free: templates, checklists and examples. It does not prescribe
a tool. A project's choice of tools is documented on the project side.

How process requirements are enforced
=====================================

The process areas are authored as YAML in ``process/areas`` and rendered into these
pages by ``qpm render-process``. Rendering fails if a reference does not resolve, if a
workflow has no output, if responsible and approver are the same role, if a role is
unused, or if an area has no valid level or maturity. CI also fails when the rendered
pages are out of date with the YAML.

How the navigation is ordered
=============================

Introduction first, then the organisation level, then the project level. Within a
level, areas are listed alphabetically by file name.

Traceability and standards conformance
======================================

Every element is a Sphinx-needs object with a stable ID, so links between workflows,
work products, roles and guidance are checked when the documentation is built. Work
products list the standard clauses they comply with.

Verification of the process description itself
===============================================

The process description is checked on every change: catalog consistency and drift
checks in CI, metamodel validation in the documentation build, and the four-eyes rule
on every workflow.
