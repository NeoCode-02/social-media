## 2025-05-15 - Icon-only buttons need ARIA labels
**Learning:** In a chat-heavy interface, many actions (Reply, Edit, Delete, Attach) are often represented by icons only. While they have `title` attributes for tooltips, screen readers rely on `aria-label` or `aria-labelledby` to convey purpose.
**Action:** Always pair `title` with an identical `aria-label` for icon-only buttons to ensure parity between mouse and screen reader users.

## 2025-05-15 - Asynchronous feedback on mobile-style buttons
**Learning:** For primary actions like "Send" that may have slight network latency, a loading spinner within the button prevents double-submissions and provides immediate visual confirmation that the action is in progress.
**Action:** Implement `loading` states for primary buttons, ensuring the spinner uses `border-current` to match the button's text color automatically.
