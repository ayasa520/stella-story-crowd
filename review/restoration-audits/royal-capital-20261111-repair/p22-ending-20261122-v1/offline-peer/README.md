# P22 first-payload offline peer

Only the exact first payload, SHA256 `a63e0a8c9e089ddb2ba95c1885f867db90e863db88c719c6d8dcbbf63fb515ed`, was reviewed as metadata and source references. Current scene 10030006 native/review files and its ordered 24-row array still match the payload guards.

The proposed authored route is `10030006/24 → 25 door → 26 CLEAR → own FINISH`, with terminal destination fields omitted. Preserve the existing `10030005/26/261 FINISH → 10030006` verbatim. The new node commands and video command list stay empty. Original payload IDs and command phases remain unknown.

The original master lists successor sections 1015 and 1004, with explicit roots 10150003 and 10040001. This does not recover a native destination for scene 10030006's missing ending payload. Scene 10030006 has `is_end=1` and an empty captured `next_scene_list`; the prior complete source review records IFクルシュ CLEAR followed by its own END chart. The terminal form is authored completion, not recovered original payload.

The report lists exact UID, complete branch, ordered array, native/review, command and resource guards for root to compare before normal stage. Canonical tail handling does not consume the packet's supplemental UID/array guards; root must enforce them separately. All `rootConfirmed` flags remain false.

No old generator, helper, API, browser, media, test, Git, stage/apply or D/C write occurred. No images were read, and no new source-image acceptance or installation authorization is claimed. The old second-read JSON exception's original `doc` was not retained. Its cause remains unknown; it was neither rerun nor declared fixed.
