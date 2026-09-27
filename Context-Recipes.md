# Context recipes

For any trading question, retrieve `system.authority` and `system.retrieval` first. Search the relevant term, open the returned note, follow its relations, and inspect the linked retained source. Keep the note's `status`, `authority`, validity flags, warning, and `sync_review_state` in the answer. Distinguish normative knowledge from executable source evidence and from inference.

For an unresolved or disputed entity, request it explicitly or use diagnostic search flags. Report its metadata; do not use it as an approved regression baseline. For an Order or audit question, determine the entity's presence and status from the current Vault index rather than its name.

For a fixture, read its case note and linked dataset or window. Check source fixture anchors and use full-data verification before a RAW integrity claim. A recorded expected output is not proof of a fresh calculation.

For an algorithm-reference quotation, obtain the reference ID from the Vault registry and configure `TRADINGBOT_ENGINE_ROOT`. Use the reference tool only after its hash check passes. The excerpt remains external evidence.

For a post-sync answer, inspect `_INDEX/sync-status.json`, run the Vault's index builder in check mode, verify this plugin in both modes, and compare the relevant production checkout separately. A new source hash does not approve a semantic change.
