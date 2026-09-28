Immutable baseline inventories, not regeneration outputs.

`historical_inputs.json` pins the 774 historical files inventoried by reviewed
commit 0cc36f04ce8bbfd2a62848760c71550242be78c4, excluding correction outputs.
Content identity is obtained from Git blobs at source baseline 776d09b;
original recorded raw-byte hashes are retained from the reviewed inventory.
The scientific artifact tag points to 29102c3. These are different identities.

`page_snapshot.json` pins the page snapshot exported in the reviewed correction
commit. `../inputs/` holds its LF-serialized copy and original acquisition
provenance (recorded hashes unchanged). No local wiki cache is needed for the
documented reproduction path.

No runtime command refreshes these baselines. Substantive source changes fail
before outputs are written. The sole historical text equivalence is replacing
CRLF with LF; raw-match and EOL-only statuses remain separate. Binary files
require their recorded raw SHA-256. Inventory files never hash themselves.
