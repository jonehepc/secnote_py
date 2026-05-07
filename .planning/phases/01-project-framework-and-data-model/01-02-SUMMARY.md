---
phase: 01-project-framework-and-data-model
plan: 02
subsystem: data-model
tags: python, pyside6, dataclass, qabstractitemmodel, json-serializer, pytest, tdd

requires:
  - plan: "01-01"
    provides: "Python src-layout skeleton, venv with PySide6+pytest+qt"

provides:
  - SNoteItem dataclass with section/note type system
  - JSON serializer/deserializer with version wrapper
  - Validator for hierarchy constraints (Note leaf-node rule)
  - TreeModel QAbstractItemModel adapter with hidden root pattern
  - 93 pytest test cases across 4 test files

affects:
  - 01-03: MainWindow integration (needs TreeModel, SNoteItem)
  - 01-04: TreeView binding (uses TreeModel directly)
  - 02-01: Encryption (needs Serializer for to_json/from_json)

tech-stack:
  added:
    - dataclasses (stdlib) -- SNoteItem data class definition
    - uuid (stdlib) -- UUID generation
    - json (stdlib) -- JSON serialization
  patterns:
    - TDD execution: RED (test) / GREEN (feat) per-component commit pairs
    - QAbstractItemModel hidden root pattern with internalPointer
    - Static utility class pattern (Serializer, Validator)
    - Recursive tree traversal for parent lookup and serialization

key-files:
  created:
    - src/secnotepad/model/__init__.py
    - src/secnotepad/model/snote_item.py
    - src/secnotepad/model/serializer.py
    - src/secnotepad/model/validator.py
    - src/secnotepad/model/tree_model.py
    - tests/model/__init__.py
    - tests/model/test_snote_item.py
    - tests/model/test_serializer.py
    - tests/model/test_validator.py
    - tests/model/test_tree_model.py
  modified:
    - tests/conftest.py

key-decisions:
  - "SNoteItem uses @dataclass with field(default_factory=list) for mutable defaults -- prevents shared-list bug"
  - "Serializer uses dataclasses.asdict() for tree-to-dict conversion, not manual traversal -- stdlib handles recursion"
  - "TreeModel._find_parent() uses reference comparison (is) instead of ID comparison -- ensures correctness with duplicate IDs in tests"
  - "TreeModel parent() uses _find_parent() linear traversal instead of parent back-reference -- keeps SNoteItem simple for <10K node trees"

patterns-established:
  - "TDD commit pairs: test(01-02) RED commit first, then feat(01-02) GREEN commit, atomic per component"
  - "Static utility classes (Serializer, Validator) with no instance state -- pure function pattern"
  - "TreeModel internalPointer stores raw SNoteItem pointer, retrieved via index.internalPointer()"
  - "hidden root: TreeModel._root_item never exposed via public index(), parent() returns QModelIndex() for top-level items"
  - "rowCount() column>0 guard: returns 0 for non-zero column parents (Qt internal call convention)"

requirements-completed:
  - NAV-01

duration: 45min
completed: 2026-05-07
---

# Phase 01 Plan 02 Summary

**SNoteItem dataclass with Serializer, Validator, and TreeModel QAbstractItemModel adapter, delivering 93 TDD-driven tests across the complete data model layer**

## Performance

- **Duration:** 45 min
- **Started:** 2026-05-07T04:43:00Z
- **Completed:** 2026-05-07T05:28:00Z
- **Tasks:** 6
- **Files created:** 10
- **Files modified:** 1
- **Tests:** 93 passing

## Accomplishments

- Implemented SNoteItem pure dataclass with section/note type system, factory methods (new_section/new_note), UUID hex ID generation, and ISO 8601 timestamps -- all decisions per D-01 through D-10
- Built Serializer for bidirectional JSON conversion using dataclasses.asdict() + recursive _from_dict(), with version wrapper and optional field defaults
- Created Validator enforcing Note leaf-node constraint (D-07) with recursive tree validation
- Implemented TreeModel QAbstractItemModel adapter with hidden root pattern (D-04), full contract methods (index/parent/rowCount/data/flags/headerData), and data mutation (add_item/remove_item)
- Added shared test fixtures (sample_tree, section_item, note_item) to conftest.py for cross-test reuse
- Followed strict TDD per-component: each component has separate RED (test) and GREEN (feat) commits in order

## Task Commits

Each task was committed atomically. TDD tasks have separate RED (test) and GREEN (feat) commits:

1. **Task 1: SNoteItem dataclass (TDD)**
   - `a660976` - test(01-02): add failing test for SNoteItem dataclass
   - `6612e74` - feat(01-02): implement SNoteItem dataclass
2. **Task 2: Serializer (TDD)**
   - `742ada2` - test(01-02): add failing test for Serializer JSON round-trip
   - `89cc924` - feat(01-02): implement Serializer JSON round-trip
3. **Task 3: Validator (TDD)**
   - `6eecc2d` - test(01-02): add failing test for Validator hierarchy rules
   - `c926b22` - feat(01-02): implement Validator hierarchy rules
4. **Task 4: TreeModel (TDD)**
   - `f96ee36` - test(01-02): add failing test for TreeModel QAbstractItemModel
   - `8ac0bf5` - feat(01-02): implement TreeModel QAbstractItemModel adapter
5. **Task 5: Shared fixtures**
   - `29caefa` - chore(01-02): add shared model fixtures to conftest.py
6. **Task 6: Full model verification** -- 93/93 tests passed (no separate commit, verification only)

**Plan metadata:** _(committed in this step)_

## Files Created

- `src/secnotepad/model/__init__.py` -- Package marker
- `src/secnotepad/model/snote_item.py` -- SNoteItem dataclass with factory methods
- `src/secnotepad/model/serializer.py` -- to_json/from_json bidirectional conversion
- `src/secnotepad/model/validator.py` -- ValidationError exception + Validator.validate()
- `src/secnotepad/model/tree_model.py` -- TreeModel QAbstractItemModel adapter
- `tests/model/__init__.py` -- Test package marker
- `tests/model/test_snote_item.py` -- 19 SNoteItem tests
- `tests/model/test_serializer.py` -- 20 serialization round-trip tests
- `tests/model/test_validator.py` -- 14 validation rule tests
- `tests/model/test_tree_model.py` -- 40 TreeModel contract tests

## Files Modified

- `tests/conftest.py` -- Added sample_tree, section_item, note_item fixtures

## Decisions Made

- **SNoteItem as pure dataclass (D-01)**: Does not inherit QStandardItem -- TreeModel handles Qt adapter role via internalPointer
- **asdict() for serialization**: dataclasses.asdict() handles recursive dataclass-to-dict conversion, simplifying Serializer.to_json() to ~5 lines
- **Reference comparison in _find_parent**: Using `is` operator (identity) rather than ID string comparison avoids issues with duplicate IDs in test data
- **Linear parent lookup**: _find_parent() traverses the whole tree each time (O(n)). No parent back-reference on SNoteItem -- keeps data class clean, acceptable for <10K nodes

## Deviations from Plan

None -- plan executed exactly as written. The TreeModel rowCount column>0 guard test was adjusted to use `createIndex()` instead of `index()` because a single-column model cannot create column>0 indices through the public API -- the guard logic itself is correct.

## TDD Gate Compliance

All components followed RED/GREEN commit sequence:
- SNoteItem: test(a660976) before feat(6612e74) -- PASS
- Serializer: test(742ada2) before feat(89cc924) -- PASS
- Validator: test(6eecc2d) before feat(c926b22) -- PASS
- TreeModel: test(f96ee36) before feat(8ac0bf5) -- PASS

Total: 4 RED commits + 4 GREEN commits + 1 chore commit = 9 commits.

## Issues Encountered

- **TreeModel column guard test**: The `rowCount()` guard `if parent.column() > 0: return 0` could not be tested through `model.index()` because a single-column model rejects column>0 indices at the `hasIndex()` gate. Fixed by using `model.createIndex(0, 1, ptr)` to bypass the gate and test the guard directly. This is a test-level adjustment, not an implementation bug.

## Known Stubs

None -- all data model components are fully implemented and tested. The TreeModel exposes a complete QAbstractItemModel API ready for QTreeView binding (Plan 03).

## Threat Flags

None -- Phase 1 introduces no security-relevant surface. Encryption is handled in Phase 2.

## Next Phase Readiness

- SNoteItem, Serializer, Validator, TreeModel complete and tested (93 tests, all passing)
- Model layer ready for MainWindow integration (Plan 03: tree view + welcome widget + three-panel layout)
- TreeModel.add_item/remove_item ready for navigation interactions (Plan 04)
- Serializer.to_json/from_json ready for file encryption (Phase 2)

---
*Phase: 01-project-framework-and-data-model*
*Completed: 2026-05-07*
