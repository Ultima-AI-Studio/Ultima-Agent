# Caller review output clarification

The review brief's shorthand `held_closed9IDs` refers to canonical machine field `held_closed`: an array of exactly RC-01 through RC-09, as in the existing harness/review metadata. ROOT's code-only sealer consumes that canonical name. Optional `held_closed_ids` and literal `held_closed9IDs` aliases may be present only if equal. The reviewer was notified before final output.

This corrects ROOT's output-schema ambiguity. No author source/manifest/test changes, no finding waiver or preselected verdict, and no runtime authorization. Spec/quality and their equal aliases, exact candidate/caller hash, execution_released=false and T2=NOT_PASSED remain as specified. All earlier input artifact hashes remain unchanged.
