.. _qx_realization:

Realization
###########

How the hub is built from its sources.

* ``prod/realization/qpm/`` - the ``qpm`` tool: composes the tiers into one model, checks and
  renders the assemblies, writes the tailoring reports and lints exported needs.
* ``prod/realization/bzl/qorix_docs.bzl`` - the ``qorix_docs()`` Bazel macro every Qorix repo
  calls to get a tailored documentation build.
* ``prod/realization/regen.sh`` - regenerates every generated page (assemblies, Needs, Dist).
  CI runs it and fails when the committed pages differ.

Checks that block a merge
=========================

* every reference resolves to an assembly or to the standards in :ref:`qx_needs`;
* responsible and approver of a workflow differ (four-eyes);
* every work product is output by a workflow, unless it is marked ``origin: external``;
* every role is used by a workflow or owns an assembly;
* every activity is performed by one of the workflow's roles;
* every identifier follows ``<type>_qx_<assembly code>_<name>`` and never contains a double
  underscore;
* every assembly has a valid cluster, status and enabler / scope / layer classification.
