.. _qx_workflow_model:

Process Workflow Model
######################

Every process area is described with the SCORE process model (workflow -> work product ->
role, supported by guidance), authored as technology-neutral YAML in ``process/areas``.

.. code-block:: text

   IN (WP) --> [ WORKFLOW: activities ] --> OUT (WP)
                     ^        ^
             ROLES (RWE)   GUIDANCE (templates, checklists)
   R = responsible   W = approved_by (sign-off)   E = supported_by (expertise)

   WORK PRODUCT = PURPOSE (content) + CONCEPT (has -> doc_concept) + TEMPLATE (contains -> gd_temp)

Checks applied by ``qpm check-process``
=======================================

* every reference resolves to the catalog or to the SCORE process (ID snapshot);
* responsible != approver (four-eyes);
* each workflow has an output; each work product is produced by some workflow;
* each activity performer is one of the workflow's roles; each role is used;
* Qorix IDs never collide with SCORE IDs (``qx`` namespace).
