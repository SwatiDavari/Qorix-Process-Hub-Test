.. _qx_common_processes:

Common Processes
################

.. note::

   Status: **concept, partly implemented**. The ``part_of`` composition, the Outcome and Capability
   element types and the gate are in the hub and checked by ``qpm check-process``. A pilot (Change
   Management at feature scope) uses them. Most of the common processes listed below are not yet
   assemblies. How to author them is in :ref:`qx_guide_layered_processes`.

Every software development, whatever the technology, domain or product, needs the same small set
of processes. They say nothing about languages, tools or platforms. They manage the work itself:
plan it, control it, keep it consistent, check it and release it. The hub defines each of them once
and every project inherits and narrows them in its tailoring.

The set follows ISO/IEC/IEEE 15288 (organisation-enabling and technical-management processes),
ISO/IEC/IEEE 12207 and the Automotive SPICE support and management groups. Safety and security
are domain overlays on top of this set. They are not part of it.

The common set
==============

.. list-table::
   :header-rows: 1
   :widths: 4 28 34 34

   * - #
     - Process
     - Reference
     - Hub status
   * - 1
     - Project planning and control
     - 15288 6.3.1-6.3.2, ASPICE MAN.3
     - not yet an assembly
   * - 2
     - Risk management
     - 15288 6.3.4, MAN.5
     - not yet an assembly
   * - 3
     - Decision management
     - 15288 6.3.3
     - not yet an assembly
   * - 4
     - Measurement
     - 15288 6.3.7, MAN.6
     - not yet an assembly
   * - 5
     - Requirements management and traceability
     - 15288 6.4.2-6.4.3, SYS / SWE.1
     - not yet an assembly
   * - 6
     - Configuration management
     - 15288 6.3.5, SUP.8
     - assembly ``cfg`` (draft)
   * - 7
     - Change request management
     - SUP.10, part of 15288 6.3.5
     - assembly ``cm`` (draft)
   * - 8
     - Problem resolution
     - SUP.9
     - not yet an assembly
   * - 9
     - Quality assurance
     - 15288 6.3.8, SUP.1
     - assembly ``qa`` (draft)
   * - 10
     - Verification and reviews
     - 15288 6.4.9, SUP.2
     - partly, in Validation
   * - 11
     - Information and documentation management
     - 15288 6.3.6, SUP.7
     - not yet an assembly
   * - 12
     - Release and transition
     - 15288 6.4.10, SPL.2
     - assembly ``rel`` (draft)
   * - 13
     - Supplier and acquisition management
     - 15288 Agreement group, ACQ.4
     - not yet an assembly
   * - 14
     - Infrastructure and tool management
     - 15288 6.2.2
     - assembly ``infra``
   * - 15
     - Training and competence
     - 15288 6.2.4
     - assembly ``trn``
   * - 16
     - Process improvement and tailoring
     - 15288 Annex A, ASPICE PIM.3
     - partly, in Governance & Compliance

Layered architecture, end to end
================================

The hub is built in layers. Each layer uses the same elements as the one above it, so a process
defined once can be repeated at a lower level or composed into a larger one.

.. code-block:: text

   Hub (system of interest)
     |
     +-- Cluster              grouping: compliance, engineering, build, testing, organisation, common
           |
           +-- Assembly       one process, classified by enabler / scope / layer
                 |
                 +-- Subcomponents (same five everywhere)
                       process | workflows | work products | roles | templates
                                   |
                                   +-- input / output links between work products

Two classification axes run through every assembly. They are independent and can be combined.

.. code-block:: text

   SCOPE  (how much of the product the process covers)
   GLOB  ->  FEAT  ->  COMP  ->  UNIT
   organisation   feature    component   unit

   LAYER  (which development step the process serves)
   REQ  ->  ARC  ->  DES  ->  IMP  ->  INT
   requirements  architecture  design  implementation  integration

Replication rule (implemented, pilot)
-------------------------------------

#. **Same shape at every scope.** A process at COMP scope has the same five subcomponents as the
   same process at GLOB scope.
#. **Composition.** A process at a lower scope declares ``part_of`` the same process one scope up
   (an assembly attribute).
   A UNIT process is part of a COMP process, a COMP process of a FEAT process, a FEAT process of a
   GLOB process.
#. **Interfaces.** A child's output work product satisfies an input of its parent. The chain of
   inputs and outputs stays unbroken from UNIT up to GLOB.
#. **Checks.** Every FEAT, COMP and UNIT process has a parent. The parent is exactly one scope up.
   At least one output of the child is an input of the parent. The composition graph has no cycle.
   Outcomes and capabilities are reused at the lower scope, not redefined.

Where each common process applies (proposed)
--------------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 15 15 15 15

   * - Process
     - GLOB
     - FEAT
     - COMP
     - UNIT
   * - Project planning and control
     - yes
     - yes
     - yes
     - -
   * - Risk management
     - yes
     - yes
     - yes
     - -
   * - Decision management
     - yes
     - yes
     - yes
     - yes
   * - Measurement
     - yes
     - yes
     - yes
     - yes
   * - Requirements management and traceability
     - policy
     - yes
     - yes
     - yes
   * - Configuration management
     - yes
     - yes
     - yes
     - yes
   * - Change request management
     - yes
     - yes
     - yes
     - yes
   * - Problem resolution
     - -
     - yes
     - yes
     - yes
   * - Quality assurance
     - yes
     - yes
     - yes
     - yes
   * - Verification and reviews
     - -
     - yes
     - yes
     - yes
   * - Information and documentation management
     - yes
     - yes
     - -
     - -
   * - Release and transition
     - yes
     - yes
     - yes
     - -
   * - Supplier and acquisition management
     - yes
     - yes
     - yes
     - -
   * - Infrastructure and tool management
     - yes
     - -
     - -
     - -
   * - Training and competence
     - yes
     - -
     - -
     - -
   * - Process improvement and tailoring
     - yes
     - -
     - -
     - -

Where each common process applies by layer (proposed)
-----------------------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 10 45 45

   * - Layer
     - Common processes that run here
     - Typical work products
   * - REQ
     - Requirements management and traceability, reviews, change requests
     - requirement set, trace matrix, review record
   * - ARC
     - Decision management, risk management, reviews
     - decision record, risk register entry
   * - DES
     - Reviews, change requests, configuration management
     - reviewed design, change package
   * - IMP
     - Configuration management, problem resolution, reviews
     - baseline record, problem report
   * - INT
     - Verification, problem resolution, release and transition
     - verification evidence, release notice

Dependencies between the common processes
=========================================

The dependencies follow from work product inputs and outputs. No separate dependency model is needed
for them.

.. code-block:: text

   Configuration Item List ---> Change Management ---> Change Package
            |                                                |
            v                                                v
   Configuration Management (baseline) <--------------------+
            |
            v
      Baseline Record ----+
                          +--> Release Management --> Release Notice
   Quality Assurance -----+
   (audit report)

A release needs three things first: a baseline that reflects approved changes, the change package
behind it and an audit report covering it. The rule "no release without all three" is a gate: entry criteria on the Release workflow. A workflow
cannot be approved until every gate work product has reached its minimum status. The dependency
between the processes is derived from the gate and the inputs, and is not stored a second time.

How this maps to ISO/IEC/IEEE 15288
===================================

15288 applies its processes recursively to each element of the system structure. The scope axis
above is how the hub expresses that recursion. The common set covers the organisation-enabling
processes (6.2) and the technical-management processes (6.3). The technical processes (6.4) are
covered only for verification, validation and transition. Conformance in 15288 is outcome-based. The
Outcome element type carries the claim: an outcome is written in Qorix's own neutral words and links
to clauses of any standard with ``complies``, so automotive clauses can be dropped for a project that
does not need them.

Open points
===========

* Write the missing common processes as assemblies, in the order given in the guide.
* Fill the cluster "Common" with the cross-cutting management processes (it exists and is empty).
* Replicate the pilot to COMP and UNIT scope where a process needs it.
* Confirm the applicability tables above with the process owners.
* Check the 15288 and ASPICE clause entries in ``needs/standards.yaml`` against your copy of each standard,
  and add the remaining clauses.
