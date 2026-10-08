.. _qx_metamodel:

Technology-neutral Metamodel (QPM)
##################################

The single source of truth is the QPM tier files (``prod/concepts/tiers``, ``dist/*``),
schema ``prod/concepts/schema/qpm-tier.schema.json``. Sphinx-needs is one adapter.

.. code-block:: text

   tier files (YAML) --qpm compose--> resolved model (JSON)
                                         |-- adapters/sphinx_needs  -> metamodel.yaml (docs build engine)
                                         |-- reports                -> tailoring report
                                         |-- lint-needs             -> rules no adapter can express
                                         '-- (future) jira / codebeamer / polarion adapters

Neutral concepts
================

=================  ===============================================  =====================
QPM concept        Meaning                                          Sphinx-needs mapping
=================  ===============================================  =====================
element type       kind of traceable item (requirement, WP, ...)    need type
attribute          typed field, ``enum`` or ``pattern``, required   (mandatory|optional)_options
relation           typed link with allowed target types             (mandatory|optional)_links
relation type      forward / reverse names                          needs_extra_links
rule (graph)       condition on linked items                        graph_checks
rule (attr-if)     conditional attribute                            not expressible -> qpm lint-needs
lint               forbidden words per field                        prohibited_words_checks
=================  ===============================================  =====================

The Sphinx-needs adapter is complete: the test suite checks that every element type and
every rule of the base model is either emitted or handed to ``qpm lint-needs``.

Writing a new adapter
=====================

An adapter is a function ``emit(model) -> (artifact, unsupported_rules)``. It must not
change semantics: anything it cannot express is returned as ``unsupported`` and is then
enforced by ``qpm lint-needs`` on exported data.
