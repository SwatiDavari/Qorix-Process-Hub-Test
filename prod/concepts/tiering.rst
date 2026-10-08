.. _qx_tiering:

Tiering: Base -> Qorix -> Project
#################################

.. code-block:: text

   Qorix base process model (ASIL B, CAL TBD, ASPICE L3)     tier 0  kind=base
        |
        v
   Qorix processes (ASIL B + ASIL D, CAL 3, ASPICE L3)       tier 1  kind=overlay  (add / widen only)
   + G&C, Infrastructure, Validation, Training
        |
        v
   Project tailoring (Performance: ASIL B | Products CP: ASIL D, CAL 3 | BL | QD | CPM)
                                                             tier 2  kind=project  (narrow only + rationale)

Rules enforced by ``qpm compose``
=================================

* **Superset rule (overlay).** Only ``add_element_type``, ``extend_element_type`` (optional
  attributes/relations), ``extend_enum``, ``add_relation_type``, ``add_rule``,
  ``add_forbidden_words``. Anything valid against the base stays valid against Qorix.
* **Narrowing rule (project).** Only ``restrict_enum``, ``require_attribute``,
  ``exclude_element_type``, ``add_rule``; each needs a ``rationale``. Integrity ceilings
  (``asil_max``, ``cal_max``) are translated into enum restrictions automatically.
* **Chain rule.** One base, each tier extends the previous one, project tier last.
* **Integrity.** Every relation/target/prefix resolves in the composed model.

The composed model and the tailoring report are generated; they are never edited by hand.
