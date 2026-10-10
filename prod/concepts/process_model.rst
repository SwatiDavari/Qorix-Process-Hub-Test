.. _qx_process_model:

Process Model
#############

A process takes the system of interest from **A to B**. It says **how, who, when, by what
means and what**: which workflows run, which roles perform them, and which work products go in
and come out.

.. code-block:: text

   Idea / System of Interest  <------>  Evidence of Compliance

A process is described by:

* **Workflows (WF)** - what is done;
* **Work Products (WP)** - what is used and produced;
* **Roles (RWE)** - who does it;
* **Dependencies of WPs** - implicit: they follow from the inputs and outputs of the workflows.

Workflow
========

.. code-block:: text

           +-------------------- <WORKFLOW> --------------------+
           |                                                    |
           |   IN (WP)  -->  ACTIVITIES (TASKS)  -->  OUT (WP)  |
           |                        ^                           |
           |                  ROLES (RWE)                       |
           +----------------------------------------------------+
                  ^                                    |
                  +---------  WPs (repository)  <------+

   R = responsible   W = approved_by (sign-off)   E = supported_by (expertise)

Work product
============

Every work product has three parts:

* **Purpose** - what it is for;
* **Concepts** - what it contains and why (``has`` link to a concept);
* **Template** - the form it takes (``typed_by`` link to a template).

Test policy and test systems are work products of the Validation assembly; every assembly
that verifies something uses them.

Reading an assembly
===================

Every assembly has the same five pages, in this order:

#. **Process** - purpose, classification (enabler / scope / layer), status, owner, standards,
   getting started and concepts.
#. **Workflows** - how workflows and work products connect, then each workflow with its
   activities.
#. **Work Products** - what each workflow produces and why.
#. **Roles** - who is involved.
#. **Templates** - the templates and guidance to use.

Templates are solution-free: they do not prescribe a tool. A project's choice of tools is
documented on the project side.

Outcomes, capabilities, gates and scope
=======================================

* **Outcome** - what a process must achieve, in Qorix's neutral words. A workflow ``achieves`` it;
  clauses of any standard attach to it with ``complies``.
* **Capability** - a reusable ability that ``realizes`` outcomes. Workflow activities exercise it, at
  any scope.
* **Gate** - entry criteria on a workflow: work products and the status each must have before the
  workflow can be approved.
* **Scope composition** - a process at FEAT, COMP or UNIT scope is ``part_of`` the same process one
  scope up.

How to author them: :ref:`qx_guide_layered_processes`.

Lifecycle
=========

Assemblies and their elements move through ``draft -> proposed -> approved -> released ->
deprecated -> retired``.

Traceability
============

Every element is a traceable need with a stable identifier ``<type>_qx_<assembly code>_<name>``,
so links between workflows, work products, roles and templates are checked when the
documentation is built. Work products link the standard clauses they comply with
(:ref:`qx_needs`).
