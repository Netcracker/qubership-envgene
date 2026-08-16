# Prose and text style

General English style for any text this repository ships: documentation, README prose, issue and
change-request bodies, and pull-request descriptions. Read this file whenever you write or edit prose.

- [Prose and text style](#prose-and-text-style)
  - [Dialect](#dialect)
  - [Dashes](#dashes)
  - [Semicolons](#semicolons)
  - [Oxford comma](#oxford-comma)
  - [Heading case](#heading-case)
  - [Compound modifiers](#compound-modifiers)
  - [Vocabulary](#vocabulary)
  - [Sentence craft](#sentence-craft)
  - [Pronouns and modifiers](#pronouns-and-modifiers)
  - [Voice and tense](#voice-and-tense)
  - [Hedging](#hedging)
  - [Avoid AI tells](#avoid-ai-tells)

## Dialect

**Default to American English. Yield to an existing dialect when a repository already uses British
spelling consistently.**

- **Spelling.** Use `-ize` endings (`organize`, `organization`), `-or` endings (`color`,
  `behavior`), `-er` endings (`center`, `meter`), and a single consonant in the past tense
  (`traveled`, `signaled`).
- **Quotation marks.** Use double quotation marks in body prose. Either is fine in code or inline
  literals where the syntax requires.
- **Date format.** Use `Month DD, YYYY` (`March 15, 2026`). Avoid all-numeric `mm/dd/yyyy` because
  it is ambiguous with `dd/mm/yyyy`.
- **Word choices.** Use `while`, not `whilst`, and `among`, not `amongst`. Contractions (`don't`,
  `it's`, `you'll`) are fine.
- **Yield rule.** If a repository's existing prose is mostly British-spelled, treat it as `en-GB`
  and match. Never mix dialects within a file. A pinned dialect in `CONTRIBUTING.md` or a Vale
  config wins.

The Oxford serial comma stays in both dialects - see [Oxford comma](#oxford-comma).

**Scope:** Applies to **new and modified content only**.

**Why:** Consistent dialect within a file removes friction. Defaulting to one dialect prevents docs
from drifting into mixed spelling.

---

## Dashes

**CRITICAL: Always use a regular hyphen-minus (`-`) as a dash in prose. Never use em dashes (`—`) or en dashes (`–`).**

❌ **INCORRECT:**

```markdown
EnvGene searches these locations — from bottom to top — and uses the first match.
```

✅ **CORRECT:**

```markdown
EnvGene searches these locations - from bottom to top - and uses the first match.
```

**Why:** Em dashes are a typographic convention that varies by locale and style guide. A plain hyphen-minus is universally readable, renders consistently across all Markdown renderers, and avoids accidental character encoding issues.

## Semicolons

**Avoid semicolons in prose. Split into separate sentences instead.**

❌ **AVOID:**

```markdown
Native callouts render with icons; bold-text variants are plain blockquotes.
```

✅ **PREFER:**

```markdown
Native callouts render with icons. Bold-text variants are plain blockquotes.
```

**Scope:** Applies to **new and modified content only**. Existing content using semicolons is
not affected by this rule and does not need rewriting unless the surrounding lines are being
edited for other reasons.

**Why:** Two short sentences read more naturally on screen than one compound sentence linked by
a semicolon. Also reduces AI-stylized rhythm in generated text.

---

## Oxford comma

**Use a serial (Oxford) comma in lists of three or more items.**

❌ **INCORRECT:**

```markdown
The pipeline reads `A`, `B` and `C`.
```

✅ **CORRECT:**

```markdown
The pipeline reads `A`, `B`, and `C`.
```

**Scope:** Applies to **new and modified content only**.

**Why:** The serial comma removes parsing ambiguity in lists with conjunctions inside list items
and matches the OUP, Google, and Microsoft style guides.

---

## Heading case

**Use sentence case for all headings: capitalize the first word and proper nouns only.**

Proper nouns include product names, feature names, brand names, and code identifiers
(`envgeneNullValue`, `ParameterSet`, `Cloud Passport`, `EnvGene`).

❌ **INCORRECT:**

```markdown
## How to Resolve Credentials
### Verification Step (Required)
#### Generated `credentials.yml` (Username/Password)
```

✅ **CORRECT:**

```markdown
## How to resolve credentials
### Verification step (required)
#### Generated `credentials.yml` (username/password)
```

**Scope:** Applies to **new and modified content only**. Existing headings in Title Case are not
affected by this rule and do not need rewriting unless the surrounding lines are being edited
for other reasons.

**Recommended (not required):** When editing a Markdown file for any other reason, consider
bringing its remaining Title Case headings to sentence case in the same PR. For large files
(many headings, large TOC), a separate dedicated migration PR is preferred to keep the original
change reviewable. Reviewers may suggest opportunistic migration but must not block merge over it.

**Why:** Aligns with the GitHub Docs convention and modern dev-doc style guides (Google,
Microsoft, Mozilla, GitHub). Sentence case has fewer rules (no debate about which prepositions
or conjunctions to capitalize), keeps proper nouns visually distinct from generic words,
translates more cleanly to non-English locales, and is the established convention across modern
technical documentation.

---

## Compound modifiers

**Hyphenate compound modifiers when they appear before the noun they qualify.**

❌ **INCORRECT:**

```markdown
A well known parameter.
```

✅ **CORRECT:**

```markdown
A well-known parameter.
```

Compound modifiers that appear **after** the noun do not need a hyphen: "The parameter is well
known."

**Scope:** Applies to **new and modified content only**.

**Why:** Hyphenation signals "treat these words as one unit". Without it, readers parse
adjective-noun-noun and stumble on the boundary.

---

## Vocabulary

**Choose common words. Define unfamiliar ones. Pick one term per concept.**

The rule covers vocabulary choices that hurt non-native readers most:

- **Common verbs over Latinate ones.** "use" not "utilize", "help" not "facilitate", "do" not
  "perform", "let" not "permit", "set" not "establish", "try" not "endeavor", "happen" not
  "transpire", "spread" not "proliferate", "outline" not "delineate", "above" not
  "aforementioned". Domain Latinate verbs that name a concept of art (`orchestrate`,
  `instantiate`, `obfuscate`) stay.
- **English over Latin abbreviations.** "for example" not "e.g.", "that is" not "i.e.", "and so
  on" not "etc.".
- **One term per concept.** Pick one and stick with it across the document.
- **Use specific verbs.** Avoid vague `be`, `have`, `do`, `make` when a specific verb names the
  action. "The pipeline validates the inputs", not "The pipeline does the validation".
- **Define acronyms on first use, and prefer full names.** Spell out the acronym at first mention
  with the short form in parentheses. Bare acronyms are fine after that.
- **Avoid metaphorical phrasal verbs.** Drop spatial metaphors (`wired into`, `tied into`,
  `bolted on`, `plugged into`), causality metaphors (`ends up`, `winds up`, `boils down to`,
  `comes out to`), and activity metaphors (`kicks in`, `picks up`, `falls through`). Replace
  with a direct verb: `wired into` → `uses`, or `ends up X` → `becomes X` (or just `is X`). Operational
  phrasals stay - they are the canonical term: `set up`, `look up`, `roll back`, `fall back`,
  `back up`, `log in`/`log out`, `sign up`.

❌ **INCORRECT:**

```markdown
The CR includes acceptance criteria from UC steps.
```

✅ **CORRECT:**

```markdown
The change-request (CR) issue includes acceptance criteria from use-case (UC) steps.
```

**Scope:** Applies to **new and modified content only**. Established repository acronyms used in
filenames (`AGENTS.md`, `CLAUDE.md`) need no expansion.

**Why:** Common and specific vocabulary reads faster across language backgrounds. Acronyms
expanded on first use spare readers a hunt for the definition.

---

## Sentence craft

**One main idea per sentence, active voice, no noun stacks, and parallel construction in lists.**

- **One main idea per sentence.** Split long compound sentences into two. Target no more than 25
  words.
- **One main idea per paragraph.** The first sentence carries the point. The rest supports it.
- **Active voice for behavior statements.** "The calculator emits X" not "X is emitted by the
  calculator".
- **No idioms, metaphors, or office-speak.** "Out of the box", "low-hanging fruit", "hands
  down", "moving the needle", "circle back", "touch base", "deep dive", "drill down", "boil
  the ocean", "stakeholder buy-in", "take this offline" - drop them. They do not translate
  and read awkwardly to non-native English speakers.
- **No noun stacks.** Long chains of nouns ("application instance environment configuration
  file") force readers to parse syntactic structure on the fly. Split into a possessive or
  prepositional phrase.
- **No adjective stacks.** Three or more adjectives before a noun (`a robust scalable cloud-native
  message broker`) is a rewrite signal. Pick the one adjective that earns the spot or drop them
  all.
- **Parallel structure in lists and headings.** Every bullet starts with the same part of
  speech. Every step uses the same imperative form.

❌ **INCORRECT** (mixed forms):

```markdown
- Configure replicas
- Setting retention
- Restart node
```

✅ **CORRECT** (parallel imperatives):

```markdown
- Configure replicas
- Set retention
- Restart node
```

**Scope:** Applies to **new and modified content only**.

**Why:** Short, active, parallel sentences read at a steady pace. Parsing speed matters most
when the reader's first language is not English.

---

## Pronouns and modifiers

**Pronoun references and modifier placement carry weight in technical prose. Keep them
unambiguous.**

- **Avoid ambiguous pronouns. Repeat the noun if there is any doubt.** With multiple actors in a
  paragraph, `it` and `this` lose their referent fast.
- **Place modifiers next to what they modify.** `only`, `just`, `also`, `even`, `not` belong
  immediately before the word they qualify.
- **Avoid gerund subordinate clauses. Use `you` or `to`.** Replace `When configuring the
  cluster...` with `When you configure the cluster...` or `To configure the cluster...`.

❌ **INCORRECT** (ambiguous pronoun, then ambiguous `only`, then gerund clause):

```markdown
The validator reads the config. It applies the rules. It then reports findings.
The hook only runs on changed files.
When configuring the cluster, set the region.
```

✅ **CORRECT:**

```markdown
The validator reads the config, applies the rules, and reports findings.
The hook runs only on changed files.
When you configure the cluster, set the region.
```

**Scope:** Applies to **new and modified content only**.

**Why:** Ambiguous pronouns, misplaced modifiers, and headless gerund clauses are translation
traps. They force re-reading even when each word is familiar.

---

## Voice and tense

**Speak directly to the reader. Describe the system in the present.**

- **Use second person (`you`, `your`). Reserve `we` for an actual team decision.** Imperatives
  address the reader directly: "Set the region" not "We set the region".
- **Lead with the answer (Bottom Line Up Front).** Put the verb the reader runs, or the
  conclusion they need, in the first clause. Detail follows.
- **Specific, not promotional.** Say what the thing does, not that it is `powerful`,
  `seamless`, `robust`, `next-generation`, `industry-leading`, `best-in-class`, or
  `cutting-edge`. Skip release-note verbs: `revolutionize`, `unlock`, `transform`, `empower`,
  `accelerate`, `streamline`. Drop words that do not pay rent.
- **No throat-clearing or page-topic self-description.** Skip filler openers - `It's worth
  noting that...`, `It's important to remember...`, `Let's explore...`, `This guide explains
  how to...`, `In this section, we will cover...`. Start with the thing.
- **Present tense for system behavior.** "The handler retries three times" not "The handler
  will retry three times".
- **Reserve `will` for the actual future.** "The build fails if the secret is missing" describes
  a property. "The build will fail when we update X next quarter" describes a future event.
- **Avoid `currently`.** It dates the sentence the moment it is written. Either give a version
  or drop it.

❌ **INCORRECT:**

```markdown
We recommend that you should set replicas to 3.
Currently the validator will support YAML.
```

✅ **CORRECT:**

```markdown
Set replicas to 3.
The validator supports YAML.
```

**Scope:** Applies to **new and modified content only**.

**Why:** Second person and BLUF cut reading time. Present tense names the system's behavior as
observable now. Future tense describes change events. Mixing them confuses readers.

---

## Hedging

**One hedge per sentence at most. State the rule, then add a caveat only when a real one
exists.**

Avoid weasel words like `can`, `may`, `should` when clarity matters. "X happens" is stronger
than "X may happen" when X always happens.

❌ **INCORRECT:**

```markdown
It may possibly sometimes fail under unusual conditions.
```

✅ **CORRECT:**

```markdown
It fails when the input exceeds 256 MB.
```

**Scope:** Applies to **new and modified content only**.

**Why:** Stacked hedges make rules sound suggestive when they are mandatory. Readers cannot tell
from "may possibly sometimes" whether an action is required, optional, or unreliable.

---

## Avoid AI tells

**Documentation is written for humans, not stylized like AI output.**

Common AI tells to avoid:

- Em dashes (`—`) and en dashes (`–`). See [Dashes](#dashes).
- Semicolons. See [Semicolons](#semicolons).
- Filler intensifiers: `simply`, `just`, `easily`, `truly`, `incredibly`, `seamlessly`,
  `robust`, `comprehensive`, `cutting-edge`, `leverage`, `delve`, `tapestry`, `landscape`.
- `Not only X, but also Y` and `Not just X, but Y` patterns.
- Empty closings: `In conclusion`, `To summarize`, `As we've seen`.
- Vague attributions: `widely regarded as`, `has been described as`, `experts agree`. Cite a
  source or delete the claim.
- Tail `-ing` significance clauses: `...enabling teams to deliver value at scale`. The phrase
  almost never carries information. Cut it.
- Rigid section scaffolding lifted onto a technical page: `Introduction / Challenges / Future
  Prospects`. Use the section headings the content actually needs.
- Bullet lists where every item starts with a bold inline header plus colon used to format
  ordinary prose. Fine for genuine term-definition pairs. An AI tell when applied to all
  bullets by default.

**Scope:** Applies to **new and modified content only**.

**Why:** AI-generated text leans on these patterns heavily. Their absence makes documentation
feel more direct and trustworthy. Read sentences aloud. If it sounds like a press release or a
chatbot, rewrite.
