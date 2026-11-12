P30 ruined shop background

Only node10450056:28.bg_picture changes, from empty to bg/bg046c_stealshop. Node29 retains its sparse empty field and inherits the same ruined scenery in ordinary saved-data playback27→28→29. The existing native background resource is used.

The delegated image reviewer accepted both screenshots against the original recording/native046c. Node29 currently has no actor; this remains a separate pending character issue. Motion, facial expressions, CG26/27, effects and exact original script timing are not accepted by this change.

The capture driver exited1 after both required screenshots because its final assertion called a stored URL string as a function. Retained ready/phase/background logs and the actual background HTTP200 establish the playback result. The original driver, corrected unexecuted driver and recovery note are included; no replay or second import was performed. Chrome/CLI/recorder and owned server were closed before image review.
