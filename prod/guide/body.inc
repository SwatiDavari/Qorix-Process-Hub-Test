Use this guide to find your way around the hub, change a process safely and look up the element types.

.. tab-set::
   :class: qx-tabs

   .. tab-item:: Use it

      **Where things live**

      .. list-table::
         :header-rows: 1
         :class: qx-reg
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
         :class: qx-reg
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
         :class: qx-reg
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
         :class: qx-reg
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

   .. tab-item:: Abbreviations

      **Terms and abbreviations**

      .. list-table::
         :header-rows: 1
         :class: qx-reg
         :widths: 18 24 58

         * - Abbreviation
           - Full form
           - Details
         * - 15288
           - ISO/IEC/IEEE 15288
           - International standard for system life cycle processes. The hub's outcomes and clauses refer to it; Qorix claims tailored, not full, conformance.
         * - ASPICE
           - Automotive SPICE
           - Process assessment model for automotive software. The hub links work products to its process outcomes and information item characteristics.
         * - IIC
           - Information item characteristics
           - ASPICE description of what an information item (work product) should contain. Written as IIC and a number, for example IIC 13-55.
         * - ISO 26262
           - ISO 26262
           - Functional safety standard for road vehicles.
         * - ISO/SAE 21434
           - ISO/SAE 21434
           - Cybersecurity engineering standard for road vehicles.
         * - ASIL
           - Automotive Safety Integrity Level
           - Safety integrity level from ISO 26262, from QM and ASIL A up to ASIL D.
         * - CAL
           - Cybersecurity Assurance Level
           - Assurance level from ISO/SAE 21434, CAL1 to CAL4.
         * - QMS
           - Quality management system
           - The system through which Qorix plans, runs and improves the quality of its processes.
         * - QA
           - Quality assurance
           - The assurance of conformance to the QMS and to the process definitions.
         * - QPM
           - Qorix process metamodel tool
           - The command-line tool in the repository that composes, checks and renders the process definitions. See Realization.
         * - Tier
           - Metamodel tier
           - A layer of the composed metamodel: Qorix base, Qorix overlay, then a project's tailoring. A project may only narrow.
         * - GLOB, FEAT, COMP, UNIT
           - Global, feature, component, unit
           - Scope levels at which a process definition is replicated. The hub holds the organisation (global) level only.
         * - Assembly
           - Process assembly
           - A folder of YAML that defines one process: process, workflows, work products, roles and templates.
         * - Cluster
           - Assembly cluster
           - A group of assemblies shown together, for example Engineering or Compliance.
         * - Gate
           - Entry gate
           - A condition on a workflow: a work product that must reach a minimum status (draft, proposed, approved, released) before work starts.
         * - R, A, S roles
           - responsible, approved_by, supported_by
           - The three roles a workflow names: who does the work, who approves it and who supports it.
         * - SoI
           - System of interest
           - The thing being defined. For this repository it is the Process Hub itself.
         * - WP
           - Work product
           - An input or output of a workflow. IDs start with ``wp_``.
         * - CI
           - Continuous integration
           - The automated build that rebuilds the site and fails when a generated page differs from its source.
         * - RST, YAML
           - reStructuredText, YAML
           - The page format and the definition format used in the repository.
         * - TBD
           - To be determined
           - A value not yet set. All objective targets are TBD until the owner sets them.

      **Assembly codes**

      The code appears in every ID of the assembly, for example ``wp_qx_qa_qms_plan``.

      .. list-table::
         :header-rows: 1
         :class: qx-reg
         :widths: 18 42 40

         * - Code
           - Assembly
           - Cluster
         * - ``infra``
           - infrastructure
           - Build
         * - ``gc``
           - governance_compliance
           - Compliance
         * - ``saf``
           - safety
           - Compliance
         * - ``sec``
           - security
           - Compliance
         * - ``cm``
           - change_management
           - Engineering
         * - ``cfg``
           - configuration_management
           - Engineering
         * - ``dec``
           - decision_management
           - Engineering
         * - ``info``
           - information_management
           - Engineering
         * - ``meas``
           - measurement
           - Engineering
         * - ``prb``
           - problem_resolution
           - Engineering
         * - ``pim``
           - process_improvement
           - Engineering
         * - ``plan``
           - project_planning
           - Engineering
         * - ``qa``
           - quality_assurance
           - Engineering
         * - ``rel``
           - release_management
           - Engineering
         * - ``req``
           - requirements_management
           - Engineering
         * - ``risk``
           - risk_management
           - Engineering
         * - ``sup``
           - supplier_management
           - Engineering
         * - ``vnr``
           - verification_reviews
           - Engineering
         * - ``trn``
           - training
           - Organisation
         * - ``val``
           - validation
           - Testing
