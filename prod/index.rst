Qorix Process Hub
#################

The Qorix Process Hub is the system of interest: one set of Qorix processes, defined once in a
technology-neutral model, that every Qorix project inherits and narrows in its own tailoring.

.. tab-set::

   .. tab-item:: Overview

      .. grid:: 1 2 3 3
         :gutter: 2

         .. grid-item-card:: Needs
            :link: qx_needs
            :link-type: ref

            What the hub must satisfy: the standard clauses Qorix work products comply with.

         .. grid-item-card:: Policies
            :link: qx_policies
            :link-type: ref

            Organisation level safety, quality and cybersecurity policies, and where each lives in the hub.

         .. grid-item-card:: Missions
            :link: qx_missions
            :link-type: ref

            Why the hub exists, how it is structured and how identifiers are formed.

         .. grid-item-card:: Concepts
            :link: qx_concepts
            :link-type: ref

            The process model, tiering, metamodel and workflow model.

         .. grid-item-card:: Realization
            :link: qx_realization
            :link-type: ref

            How the hub is built: the qpm tool, the docs build macro and the checks.

         .. grid-item-card:: Assemblies
            :link: qx_assemblies
            :link-type: ref

            The Qorix processes, grouped into cluster assemblies.

         .. grid-item-card:: Dist
            :link: qx_dist
            :link-type: ref

            One distribution per project: its composed process and tailoring report.

   .. tab-item:: Process Hub Guide

      Use this tab to find your way around the hub, change a process safely and look up the element types.

      .. tab-set::

         .. tab-item:: Use it

            **Where things live**

            .. list-table::
               :header-rows: 1
               :widths: 30 70

               * - What
                 - Where
               * - A process (outcomes, workflows, work products, roles, templates)
                 - ``prod/assemblies/<cluster>/<process>/`` as YAML, plus a generated ``index.rst``
               * - Organisation objectives and policies
                 - ``needs/objectives.yaml`` and ``needs/policies.yaml``; pages under *Missions* and *Policies*
               * - Standard clauses
                 - ``needs/standards.yaml``; the *Needs* page
               * - Artifact kinds
                 - ``needs/artifact_kinds.yaml``
               * - The metamodel (types, relations, rules)
                 - ``prod/concepts/tiers/``; the *Concepts* page
               * - A project's tailoring
                 - ``dist/<project>/tailoring.qpm.yaml``; the *Dist* page

            **Read a process**

            #. Open *Assemblies* and pick the cluster, then the process.
            #. Read the outcomes first: they state what the process must achieve and which standard clauses they meet.
            #. Follow a workflow from its entry gate through its activities to its outputs. Each step names its role and the capability it uses.
            #. Open a work product to see its purpose, kind, template and the clauses it complies with.

            **Reuse it in a project**

            #. Start from the hub as it is. Do not copy a process into your project.
            #. Narrow it in ``dist/<project>/tailoring.qpm.yaml``. A project may only narrow, and every narrowing needs a rationale.
            #. Run the compose step and read the tailoring report on the *Dist* page.

         .. tab-item:: Change it

            The hub holds organisation-level processes only. Technical processes of a product stay in the project repository.

            **Add or change a work product**

            #. Edit ``work_products/*.yaml`` of the process. Give it an ID ``wp_qx_<code>_<name>`` (lower case, single underscores, 45 characters at most), a title, a purpose and a ``kind``.
            #. Add ``complies`` with the standard clauses it meets, or ``internal: true`` if no clause applies.
            #. If a workflow produces it, add it to that workflow's outputs.

            **Add an outcome or capability**

            #. Add it to ``process/process.yaml`` of the process. An outcome carries ``complies``; a capability names the outcomes it realizes.
            #. Make a workflow ``achieves`` the outcome, and let its activities use the capability.

            **Add an objective or policy**

            #. Edit ``needs/objectives.yaml`` or ``needs/policies.yaml``. Every objective has an owner and a measure. Every policy is driven by at least one objective and drives outcomes.
            #. Keep the wording neutral: no standard, tool or technology names in objectives and policies.

            **Check and publish**

            #. Run ``python3 -m qpm check-process --assemblies prod/assemblies --standards needs/standards.yaml``. Fix every error.
            #. Run ``bash prod/realization/regen.sh`` to rebuild the generated pages, and commit them with the change.
            #. Run ``bash prod/realization/publish.sh`` or push to ``main``. CI rebuilds the site and fails on any drift.

            A process is complete when it has outcomes with clauses, capabilities, at least one workflow with an entry gate, work products linked to a clause (or internal), and roles with a responsible and an approver.

         .. tab-item:: Element types

            .. list-table::
               :header-rows: 1
               :widths: 14 11 31 44

               * - Type
                 - Prefix
                 - Purpose
                 - Links out
               * - ``objective``
                 - ``obj_``
                 - What the organisation wants, with a measure and an owner
                 - drives a policy; contributes to an objective
               * - ``policy``
                 - ``pol_``
                 - The why behind a discipline's rules
                 - complies with clauses; drives outcomes
               * - ``workflow``
                 - ``wf_``
                 - A defined way of working with steps, gates and roles
                 - achieves outcomes; input and output work products; responsible, approved by and supported by roles; contains guidance
               * - ``outcome``
                 - ``oc_``
                 - A result a process must achieve
                 - complies with clauses
               * - ``capability``
                 - ``cap_``
                 - A reusable ability that realises outcomes
                 - realizes outcomes
               * - ``role``
                 - ``rl_``
                 - Who is responsible, approves or supports
                 - contains roles
               * - ``workproduct``
                 - ``wp_``
                 - An input or output of a workflow, classified by kind
                 - complies with clauses
               * - ``gd_req``
                 - ``gd_req_``
                 - A process requirement
                 - satisfies a workflow; complies with clauses
               * - ``gd_temp``
                 - ``gd_temp_``
                 - A template
                 - complies with clauses
               * - ``gd_chklst``
                 - ``gd_chklst_``
                 - A checklist
                 - complies with clauses
               * - ``gd_guidl``
                 - ``gd_guidl_``
                 - A guideline
                 - complies with clauses
               * - ``gd_method``
                 - ``gd_meth_``
                 - A method
                 - complies with clauses
               * - ``std_req``
                 - ``std_req_``
                 - A requirement or clause of a standard
                 - any
               * - ``std_wp``
                 - ``std_wp_``
                 - A work product named by a standard
                 - none
               * - ``doc_concept``
                 - ``doc_concept_``
                 - The concept behind a process
                 - none
               * - ``doc_getstrt``
                 - ``doc_getstrt_``
                 - A getting-started page
                 - none
               * - ``document``
                 - ``doc_``
                 - A generic document
                 - realizes a work product
               * - ``dec_rec``
                 - ``dec_rec_``
                 - A decision record
                 - affects any item

         .. tab-item:: Relations and kinds

            .. list-table::
               :header-rows: 1
               :widths: 28 72

               * - Relation
                 - Meaning
               * - ``drives``
                 - objective to policy, and policy to outcome
               * - ``contributes_to``
                 - a project objective supports an organisation objective
               * - ``achieves``
                 - a workflow achieves an outcome
               * - ``realizes``
                 - a capability realises an outcome
               * - ``complies``
                 - the item conforms to a standard clause
               * - ``input``, ``output``
                 - a workflow reads or produces a work product
               * - ``responsible``, ``approved_by``, ``supported_by``
                 - the roles of a workflow
               * - ``contains``, ``has``, ``satisfies``, ``affects``
                 - structure, guidance and decision links

            Every work product has one **kind**, so a process reads the same under any lifecycle model or technology.

            .. list-table::
               :header-rows: 1
               :widths: 28 72

               * - Category
                 - Kinds
               * - Intent
                 - need
               * - Specification
                 - requirement
               * - Definition
                 - definition
               * - Analysis
                 - analysis
               * - Plan and control
                 - plan, request, baseline, report
               * - Evidence
                 - evidence
               * - Governance
                 - policy, rule, material
               * - Record
                 - record, register

.. toctree::
   :hidden:

   needs
   policies/index
   missions/index
   concepts/index
   realization/index
   assemblies/index
   dist/index
