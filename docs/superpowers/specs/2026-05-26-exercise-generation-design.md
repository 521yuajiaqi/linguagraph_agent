# Exercise Generation Design

## Goal

Optimize translation exercise generation so each generated exercise more reliably targets the learner's current weak area while keeping difficulty stable for the learner's level.

## Scope

This design only covers translation exercises.

Included:
- Weakness-driven exercise targeting
- Stable difficulty control for translation exercises
- Structured fallback behavior when the exercise bank cannot satisfy the target
- Internal explainability for why an exercise was selected

Excluded in this iteration:
- New exercise types such as error correction or fill-in-the-blank
- Multi-exercise training sequences
- Full curriculum planning
- Automatic LLM rewriting of selected bank exercises
- Major frontend interaction changes

## Current State

The current backend exercise generation flow is centered in `lingua_agent.nodes.generate_exercise`.

Today the system:
- Accepts `focus_areas`, `user_level`, `domain`, and language direction
- Calls the LLM to generate a translation exercise in JSON
- Falls back to a small hardcoded exercise bank when parsing fails
- Generates hints, diagnostics, and difficulty after the exercise text is decided

Current weaknesses:
- The system does not first formalize the pedagogical target of the exercise
- `focus_areas` influences prompting, but there is no durable representation of the intended teaching target
- Difficulty is estimated after generation rather than used as a stable constraint before generation
- The bank fallback cannot explicitly rank candidate exercises by pedagogical match
- There is little explainability for why the system chose a given exercise

## Design Overview

The generation pipeline should move from direct exercise generation to a two-stage design:

1. Build an `ExerciseBlueprint`
2. Select or generate an exercise that satisfies that blueprint

The key principle is:

> Decide what the system wants to teach first, then decide what the exercise should look like.

This makes the pedagogical target explicit, testable, and reusable for later enhancements.

## Core Objects

### ExerciseBlueprint

Represents the intended teaching target for the next exercise.

Required fields:
- `primary_focus`: one of `accuracy`, `fluency`, `terminology`, `grammar`, `strategy`
- `target_level`: learner target level such as `A1`, `A2`, `B1`, `B2`, `C1`
- `difficulty_band`: a narrow internal difficulty window relative to learner level
- `syntax_load`: qualitative target such as `low`, `medium`, `high`
- `terminology_load`: qualitative target such as `low`, `medium`, `high`
- `teaching_intent`: a short explicit intent string, for example `train concessive structure handling`
- `selection_reason`: a short machine-readable or human-readable explanation for why this focus was chosen

Optional fields may include:
- `preferred_domain`
- `avoid_overload_dimensions`
- `recent_error_tags`

### ExerciseCandidate

Represents a translation exercise that can be selected from the exercise bank.

Required fields:
- `source_text`
- `reference_translation`
- `language_pair`
- `level`
- `focus_tags`
- `syntax_load`
- `terminology_load`
- `teaching_points`
- `domain`

This object allows the system to reason about pedagogical fit before choosing an exercise.

### ExerciseSelectionResult

Represents the output of candidate ranking.

Required fields:
- `candidate`
- `score`
- `matched_focus`
- `matched_level`
- `match_reason`

This result is primarily for backend traceability and testing. It may later support user-facing explainability, but that is not required in this iteration.

## Input Signals

The first iteration should use only three signal groups:

1. Explicit weak areas
   - Source: `focus_areas`
   - Purpose: provide the clearest statement of what to train next

2. Historical learner performance
   - Source: session diagnosis, recent evaluation results, mistake history, and weak dimensions already tracked in state
   - Purpose: avoid overreacting to a single prompt and reinforce persistent weaknesses

3. Learner profile and direction
   - Source: `user_level`, `language_pair`, `domain`
   - Purpose: constrain exercise topic and difficulty

## Decision Order

The generation logic should use a fixed decision order.

### Step 1: Choose the primary focus

Only one primary focus should be selected for each exercise in this iteration.

Selection rules:
- If `focus_areas` is non-empty, choose the highest-priority weakness from `focus_areas`
- Otherwise choose the weakest persistent dimension from learner history
- Do not try to optimize multiple pedagogical goals equally in the same exercise

Reasoning:
- Single-focus targeting is easier to test
- Multi-focus generation would blur whether the exercise actually trains the intended weakness

### Step 2: Determine the difficulty band

The system should not treat target level as a loose suggestion. It should derive a narrow band from the learner's current level and recent performance.

Rules:
- Start from the learner's current level
- Allow only limited movement around that level
- If recent performance is unstable, reduce load instead of increasing it
- If the chosen weakness is already fragile, avoid stacking multiple forms of complexity in one exercise

Difficulty should be constrained before final exercise generation or selection, not merely reported afterwards.

### Step 3: Translate focus into pedagogical constraints

The abstract focus must become operational constraints.

Examples:
- `grammar`
  - Increase grammatical decision pressure such as word order, case governance, clause structure, or connectors
  - Keep terminology load controlled
- `terminology`
  - Increase term density or term precision requirements
  - Keep syntax load moderate
- `accuracy`
  - Use sentences with multiple information units or logical relations that must all be preserved
- `fluency`
  - Favor natural expression, collocation, and idiomatic flow
  - Avoid overloading the sentence with dense terminology
- `strategy`
  - Favor sentences that require restructuring, splitting, merging, or explicit handling of implied meaning

### Step 4: Select the exercise

The first iteration should prefer bank selection over free-form LLM generation.

Order:
1. Build blueprint
2. Filter exercise candidates by language pair and level compatibility
3. Rank candidates by focus match and overload avoidance
4. Choose the best candidate
5. Only if no candidate is acceptable, use constrained LLM fallback

## Exercise Bank Strategy

The existing fallback bank should evolve into a tagged translation exercise bank.

Requirements:
- Each exercise in the bank must carry pedagogical metadata
- Metadata must support ranking by focus and difficulty
- The bank can remain small in the first iteration, but the schema must support later expansion

Minimal tagging required in iteration one:
- Level
- Focus tags
- Syntax load
- Terminology load
- Teaching points
- Domain

This bank can remain code-local initially. A database or external content system is unnecessary for this round.

## LLM Fallback Strategy

The LLM remains a fallback, not the default generator.

Fallback rules:
- The LLM must receive the fully constructed `ExerciseBlueprint`
- The prompt must instruct the model to produce exactly one translation exercise satisfying the blueprint
- The output must still be parsed and normalized
- The result must be validated against the blueprint at a lightweight level before acceptance

Validation examples:
- Does the output contain only exercise text and reference translation
- Does the difficulty appear consistent with the blueprint
- Does the output avoid obvious format drift or explanation leakage

If validation fails, the system should fall back again to the safest bank candidate available rather than return a malformed pedagogical target.

## Backend Flow Changes

The revised backend flow for `generate_exercise` should be:

1. Initialize learner context
2. Build `ExerciseBlueprint`
3. Select the best `ExerciseCandidate` from the bank
4. If selection succeeds, use that exercise
5. If selection fails, run constrained LLM fallback using the blueprint
6. Normalize output text
7. Generate hints, diagnostics, and difficulty metadata
8. Return trace data including blueprint and selection reasoning where useful

This keeps the pedagogical decision explicit and traceable.

## Verification Strategy

The implementation must be judged against concrete pedagogical behaviors, not only code-level success.

### 1. Weakness targeting

Given `focus_areas=["grammar"]`, the chosen exercise should show grammar-oriented tags and structure load rather than unrelated term-heavy content.

### 2. Difficulty stability

For the same learner level and similar history, repeated generation should stay within a narrow difficulty profile instead of oscillating between very easy and overloaded prompts.

### 3. Controlled fallback

When the bank has no acceptable candidate, the fallback LLM path must still return a translation exercise that fits the blueprint and preserves output structure.

## Non-Goals and Guardrails

To keep this iteration focused:
- Do not redesign frontend learning flow
- Do not add multi-step teaching plans
- Do not introduce many new abstractions outside the generation path
- Do not build a full authoring system for exercises
- Do not attempt automatic pedagogical perfection from the first bank version

The goal is narrower: make the next exercise noticeably more intentional and stable.

## Implementation Consequences

This design implies:
- New typed structures for blueprint and candidate metadata
- Refactoring of the current `generate_exercise` flow
- Expansion of the local exercise bank schema
- New ranking and validation logic
- Tests focused on pedagogical targeting and fallback behavior

## Recommended Rollout Order

1. Define blueprint and candidate schemas
2. Tag the local exercise bank with pedagogical metadata
3. Build blueprint generation from learner signals
4. Implement candidate filtering and ranking
5. Add constrained LLM fallback
6. Add tests for focus targeting, difficulty stability, and fallback correctness

## Open Decisions Resolved For This Iteration

Resolved:
- Only translation exercises are in scope
- Only one primary pedagogical focus is targeted per exercise
- Bank selection is preferred over free-form generation
- The LLM is a constrained fallback
- Frontend changes are minimal

Deferred:
- Richer exercise types
- Multi-exercise training sequences
- Rewrite-based diversification of selected bank content
- Deep user-facing explanations for exercise choice
