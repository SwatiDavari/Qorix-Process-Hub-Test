.. _qx_guide_layered_processes:

Guide: Layered Common Processes
###############################

How to define a common process once and repeat it at lower scopes, with outcomes, capabilities and
gates. The concept is in :ref:`qx_common_processes`. The pilot used as the example is Change
Management at feature scope, ``change_management_feat``, which is part of ``change_management``.

When to use what
================

.. list-table::
   :header-rows: 1
   :widths: 18 40 42

   * - Element
     - Use it when
     - Do not use it for
   * - Outcome
     - You must claim conformance to a standard clause, or say what the process achieves.
     - Describing steps. That is the workflow.
   * - Capability
     - An ability is used by more than one workflow or at more than one scope (for example impact
       analysis).
     - An ability used once. Name the activity instead.
   * - Gate
     - A workflow must not be approved before its inputs have reached a status.
     - Ordering workflows. The order comes from inputs and outputs.
   * - ``part_of``
     - The same process is repeated one scope down.
     - Grouping processes. That is the cluster.

Steps
=====

Follow them in this order. Run ``qpm check-process`` after each step.

#. **Define the process at the highest scope first (GLOB).** Write the workflows, work products,
   roles and templates as in any assembly. Link work products by ``input`` and ``output``; that is
   how dependencies between processes are stated. A work product produced in another assembly is a
   plain input. Mark it ``origin: external`` only when no Qorix workflow produces it.

#. **Add the outcomes.** In ``process/process.yaml``::

      outcomes:
      - id: oc_qx_cm_changes_authorised
        title: Changes are analysed and authorised before they are applied
        statement: Every change to an organisation level work product is analysed ... before it is applied.
        complies: [std_req_aspice_40_sup_10, std_req_iso15288_635]

   Write the statement without a tool, a language or a domain. Add the clause to
   ``needs/standards.yaml`` before you link it. Link as many standards as apply. A project that
   does not need a standard drops it in its tailoring, and the outcome stays.

#. **Add the capabilities that realize them.** Also in ``process/process.yaml``::

      capabilities:
      - id: cap_qx_cm_impact_analysis
        title: Impact analysis
        description: Establish which work products, projects and disciplines a change reaches ...
        realizes: [oc_qx_cm_changes_authorised]

#. **Tie the workflow to them.** In ``workflows/workflows.yaml``::

      achieves:
      - oc_qx_cm_changes_authorised
      activities:
      - step: Analyse the impact across all projects
        by: rl_qx_qa_quality_office
        capability: cap_qx_cm_impact_analysis

   The ``by`` role must be responsible, approver or supporter of the workflow. An activity may omit
   ``capability``.

#. **Add a gate where a workflow has entry criteria.** Only for work products that are already inputs::

      gate:
      - wp: wp_qx_cm_change_package
        min_status: approved

   ``min_status`` is one of ``draft``, ``proposed``, ``approved``, ``released``. Once the workflow is
   ``approved`` or ``released``, the check fails if a gate work product has a lower status or is
   ``deprecated`` or ``retired``. The workflow page shows the gate as a table with the producing workflow
   for each work product.

#. **Repeat the process one scope down.** Create a new assembly folder, for example
   ``prod/assemblies/engineering/change_management_feat/``, with the five subcomponents. In its
   ``process.yaml`` set::

      scope: FEAT
      part_of: change_management

   Rules for the child:

   * Reuse the parent's outcomes and capabilities. Do not copy them. The pilot's workflow
     ``achieves`` ``oc_qx_cm_changes_authorised`` and exercises ``cap_qx_cm_impact_analysis``.
   * Use its own assembly code in the ids (``cmf`` here) and its own roles where the performer differs.
   * Make at least one output work product an input of a workflow in the parent. In the pilot,
     ``wp_qx_cmf_feature_change_package`` is an input of ``wf_qx_cm_manage_org_change``.
   * The parent is exactly one scope above: FEAT under GLOB, COMP under FEAT, UNIT under COMP.

#. **Regenerate and test.** Run ``bash prod/realization/regen.sh`` and
   ``python -m pytest prod/realization/qpm/tests``. Commit the generated pages with the YAML.

Reading a check failure
=======================

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - Message contains
     - Fix
   * - ``must be part_of an assembly one scope up``
     - Set ``part_of`` on the FEAT, COMP or UNIT assembly.
   * - ``exactly one scope above``
     - The parent is at the wrong scope. Check ``scope`` on both assemblies.
   * - ``broken interface``
     - No output of the child is an input of the parent. Add the work product to a parent workflow input.
   * - ``no workflow achieves this outcome``
     - Add ``achieves`` to the workflow that delivers the outcome.
   * - ``no capability realizes this outcome``
     - Add a capability with ``realizes``, or remove the outcome.
   * - ``no workflow activity exercises this capability``
     - Add ``capability:`` to an activity, or remove the capability.
   * - ``unresolved standard clause``
     - Add the clause to ``needs/standards.yaml``.
   * - ``gate work product ... must be an input``
     - Add the work product to the workflow ``input`` list.
   * - ``gate not met``
     - Raise the work product status, or lower the workflow status. A workflow cannot be approved first.

Order for the missing common processes
======================================

Write them in this order, because later ones depend on earlier ones:

#. Risk management, Decision management and Problem resolution.
#. Project planning and control, Requirements management and traceability, Measurement.
#. Information management, Supplier management, Process improvement.
#. Verification and reviews, split out of Validation.

Put the cross-cutting management processes in the cluster ``common``. Keep Configuration, Change,
Quality and Release in Engineering.

What is still open
==================

* The 15288 and ASPICE clauses in ``needs/standards.yaml`` come from the authors' knowledge of the
  standards. Check them against your copy before you rely on them.
* The pilot repeats Change Management at feature scope. The getting-started text of the
  organisation level process says a project's own change management is out of its scope. Decide
  whether feature level change belongs in the hub, then amend one of the two texts.
* COMP and UNIT scope are supported by the checks but not yet used by any assembly.
