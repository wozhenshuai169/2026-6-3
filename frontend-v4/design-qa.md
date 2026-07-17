# Mobile visitor journey QA

- Viewport target: 390 × 844 portrait.
- Reference intent checked: quiet guide header, guide figure as the dominant element, no play/start control, conversational side drawer for group/direct-chat choice.
- Implementation checked: the three-mode dock and swipe navigation; guide arrival/invoke state; tool entry points; team conversation drawer, join entry, ID copy feedback, message sending, image attachment, and recorded voice message affordances.
- Responsive leader workspace checked in source: side panes collapse into a focused stage and bottom action bar below 700px.
- Static verification: `node --check` passed for the added interaction scripts and `git diff --check` passed.

final result: passed
