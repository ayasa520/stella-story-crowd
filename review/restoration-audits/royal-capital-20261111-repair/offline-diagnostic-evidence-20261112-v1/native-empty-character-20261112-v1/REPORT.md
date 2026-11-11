The inspected original ADV2 path does not support a blanket claim that an empty
actor-resource string inherits the previous actor. This is a conditional static
finding, not proof of which producer/path the recording used.

Fresh original-byte resolution binds ScenarioUtil.HasLive2DChara to
0x17179f4..0x1717a24 through its own Assembly-CSharp method table. The 48-byte
function returns false for a null scenario. Otherwise it reads the string at
scenario+0x58, calls the independently resolved System.String.IsNullOrEmpty at
0x1eefbb0, and negates the result.

The preserved original View.ShowLive2D disassembly in
../native-motion-entry-20261111/entry-order-native-capstone.txt:569 shows:

- A null scenario returns without calling the actor helper.
- HasLive2DChara false, or IsMovie true, leads to ADVUtil.HideAllLive2D at
  0x16892b0.
- A present actor in a non-movie scenario passes the same scenario+0x58 string
  and scenario+0x68 value to ADVUtil.SetLive2D at0x16892d8.

This supports the shown path's empty-string hide branch. It does not establish
the recording's dynamic call path, an original lost CSV, hide animation timing,
all native/script producers, or a change to current runtime behavior. Background
script_background inheritance is a separate compiler contract and must not be
used to infer actor inheritance.

For the planned Reinhard reference, only node7 has a character memory override.
Node8 remains an unaccepted empty-character story field. Natural traversal to8
does not sign the original image or prove actor inheritance. No extra override
or production change follows from this report.

Only new evidence files were written. Original library/metadata sources match
the existing entry-order witnesses. No browser, image inspection, game execution,
test, registry, production source or data/Git mutation occurred.
