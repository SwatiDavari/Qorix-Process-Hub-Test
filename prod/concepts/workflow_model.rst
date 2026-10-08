.. _qx_workflow_model:

Process Workflow Model
######################

Every process area is described with the Qorix process model (workflow -> work product ->
role, supported by guidance), authored as technology-neutral YAML in its assembly folder
``prod/assemblies/<cluster>/<process>/`` (subfolders ``process``, ``workflows``, ``work_products``,
``roles``, ``templates``).

.. code-block:: text

   IN (WP) --> [ WORKFLOW: activities ] --> OUT (WP)
                     ^        ^
             ROLES (RWE)   GUIDANCE (templates, checklists)
   R = responsible   W = approved_by (sign-off)   E = supported_by (expertise)

   WORK PRODUCT = PURPOSE (content) + CONCEPT (has -> doc_concept) + TEMPLATE (contains -> gd_temp)

Checks applied by ``qpm check-process``
=======================================

* every reference resolves to the catalog or to the Qorix standards catalogue (``needs/standards.yaml``);
* responsible != approver (four-eyes);
* each workflow has an output; each work product is produced by some workflow;
* each activity performer is one of the workflow's roles; each role is used;
* every ID is unique and follows ``<type>_qx_<assembly code>_<name>`` with no double
  underscore; work products marked ``origin: external`` are
  inputs produced outside these areas and must not be output by a Qorix workflow.
