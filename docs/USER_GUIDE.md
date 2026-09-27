# Handoff User Guide

Handoff has two kinds of accounts:

- **Owners** capture procedures, review and approve them, and see the questions employees could not get answered.
- **Employees** ask questions and read approved procedures.

## Getting started

**The first account becomes the owner.** Open Handoff, choose to sign up, and enter your name, email, a password, and your business name.

**Employees join with an invite code.** The owner shares the code from the Team Access card on the owner dashboard. Employees enter it when they sign up.

Passwords need at least 12 characters, with uppercase and lowercase letters, a number, and a special character. The signup page shows a checklist that updates as you type. A sign-in lasts 8 hours (one work shift).

## For owners

### The owner dashboard

The dashboard shows three counts: **Procedures** (approved and searchable), **Pending Reviews** (drafts waiting for your approval), and **Knowledge Gaps** (open questions employees asked that Handoff could not answer). Below them are shortcuts to Capture a Procedure, Review Procedures, Knowledge Gaps, and Ask Handoff.

<!-- screenshot: owner dashboard (hide or blur the invite code) -->

### 1. Capture a procedure

Choose **Capture a Procedure** on the dashboard, or **+ Add Procedure** on the Procedures page. Give the procedure a title, then pick how to provide it:

- **Record Audio**: select **Start Recording**, explain the procedure in your own words, then **Stop Recording**. Use **Record Again** to start over.
- **Upload Audio**: select **Choose Audio File** and pick an existing recording (up to 10 MB).
- **Enter Manually**: type or paste written notes.

Select **Submit for AI Structuring →**. Handoff transcribes any audio, then organizes it into numbered steps and warnings.

**If something goes wrong after the recording was transcribed**, Handoff moves the transcript into the Enter Manually box and tells you so. Read it over, fix anything misheard, and submit again. The recording is not transcribed a second time.

### 2. Review the draft

The draft opens on the Procedure Review page. Nothing you capture is visible to employees until you approve it.

- Edit any step or warning directly. Use **+ Add Step** and **+ Add Warning** to add more, or **×** to remove one.
- **Handoff Noticed Possible Gaps** lists up to five questions about things the recording may have skipped, such as what to do if something goes wrong. For each question you can:
  - Type an answer, then select **Incorporate with AI** to have Handoff add it as new steps. **Undo AI Changes** reverses the last merge.
  - Select **I'll Add It Myself** and edit the steps yourself.
  - Select **Not Applicable** if the question does not apply. **Reopen** brings a question back.

**Handoff can add steps, but it can never change yours.** When it incorporates your answers, Handoff checks that every one of your original steps comes back word for word and in order. If the AI rewrote anything, the merge is cancelled and your procedure is left untouched.

<!-- screenshot: capture gap questions with Incorporate with AI -->

### 3. Approve

**Approve Procedure** becomes available once every gap question is handled. Approving makes the procedure searchable. If it answers questions employees had already asked, Handoff tells you how many knowledge gaps it resolved.

### 4. Update a procedure

Open it from the Procedures page with **Review**. The approve button reads **No Changes to Approve** until you edit something, then **Approve Changes (v2)** (or the next version number). Approving an update raises the version and updates the procedure's Last Confirmed date, which employees see with every answer.

<!-- screenshot: No Changes to Approve and Approve Changes side by side -->

### 5. Delete a procedure

On the Procedures page, select **Delete** and confirm. Deleting is permanent. Any knowledge gaps the procedure had resolved become open again, because nothing answers them anymore.

### 6. Knowledge gaps

When an employee asks something Handoff cannot answer, the question appears on the **Knowledge Gaps** page. This is your to-do list for what to document next.

Each card shows:

- **Asked N times**: questions with the same meaning are grouped, so the most-needed answers rise to the top.
- **Last asked**: when someone most recently asked it.
- **Closest match**: how close the best existing procedure came. A high percentage usually means a procedure covers the topic but not this exact question.

Select **Review** on a card to see its details, including **Also Asked As**: every different wording employees used. Grouping is automatic and can occasionally combine two different questions on the same topic, so each wording is kept for you to read.

A gap is:

- **Open** until something answers it.
- **Resolved** automatically when you approve a procedure that answers it. The card shows which procedure resolved it.
- **Dismissed** when you select **Dismiss** because it does not need an answer. If an employee asks it again later, it appears as a new open gap.

Use **Search questions** and **Show** (All, Open, Resolved, Dismissed) to filter the list. Search matches each gap's main question.

<!-- screenshot: knowledge gap with Asked N times and Also Asked As -->

### 7. Team access

On the dashboard's Team Access card, **Copy Code** copies the invite code to share with employees. **New Code** replaces it: the old code stops working immediately, which is useful if a code was shared by mistake. Existing accounts are not affected.

## For employees

### Ask Handoff

Select **Ask Handoff**, type a question in your own words, and select **Ask**. **Use Example** fills in a sample question, and **Clear** starts over.

You will see one of three results:

- **An answer**, with the name of the procedure it came from and the date the owner last confirmed it. Handoff answers only from procedures the owner approved.
- **"Not documented"**, when no approved procedure contains the answer. Handoff does not guess. Your question is sent to the owner as a knowledge gap, so it can be documented.
- **"Temporarily unavailable"**, when the AI service is busy or has reached its usage limit. Nothing was recorded; wait a moment and ask again.

<!-- screenshot: an answer with citation and last-confirmed date -->

### Tips for good results

- Ask one thing at a time: "What temperature should the milk fridge be?" works better than several questions in one.
- Be specific: name the equipment, task, or situation.
- If you get "not documented" for something you believe is written down, try different words. Handoff matches meaning, but a very different word can still miss. The owner also sees these questions and can add the words employees actually use.

### Read procedures

**Procedures** lists every approved procedure, so you can read one from start to finish. Drafts the owner has not approved are never shown to employees.

## Frequently asked questions

**Why didn't Handoff answer a question when the procedure clearly covers it?**
Usually the wording. In testing, "What time does the cafe open?" was answered, but "What time does the store open?" fell just short, because the procedure only said "cafe." The question appeared as a knowledge gap, the owner added "store" to the procedure, and approving it resolved the gap automatically.

**Why does Handoff sometimes say "not documented" instead of giving a close answer?**
On purpose. A wrong answer about a safety step or a refund rule is worse than no answer. Handoff answers only when an approved procedure actually contains the answer, and turns every other question into a gap the owner can fill.

**Can the AI change a procedure by itself?**
No. The AI drafts and suggests, but only the owner approves, and code blocks the AI from rewriting the owner's own steps.