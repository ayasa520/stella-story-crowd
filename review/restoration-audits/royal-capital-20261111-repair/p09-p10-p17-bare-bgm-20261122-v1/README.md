# P09/P10/P17: source-identified BGM fields

Normal repair and install saved only three empty bg_music fields: P09 10020001/2 = bgm_adv_fuon01_cd2_03; P10 10020011/2 and P17 10020048/7 = bgm_adv_fuon02_cd2_14. Full old rows, IDs, branches and array order were checked; the other137 pairs and first22 protected files remained unchanged.

P09 has four coherent high-correlation source windows. P10 has three moderate coherent 65-track-library windows plus an independent8k refinement. P17 has a strong actual Julius-card window and source entry bracket. These support resource identity only. Original accepted packets contain historical wrapper constants; the new fields deliberately use bare IDs. No original CSV fade/reset, volume/loop, STOP, offset, command phase, audition, voice/SE, continuous saved playback or whole-scene acceptance is claimed. P09 historical Chinese sourceText and P10 previously unsigned UID are kept explicit in the new packet.

All original evidence transports map to byte hashes in archive-manifest.json. Gzip transports decompress to exact original bytes. Original videos and audio resources are referenced by their recorded hashes; the existing registered resources remain in assets.
