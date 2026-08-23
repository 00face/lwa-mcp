from __future__ import annotations

from .models import TaskKind

DEFAULT_PROMPTS: dict[TaskKind, str] = {
    TaskKind.QUICK_RESPONSE: "Answer directly and accurately. Do not add ceremony or unsupported claims.",
    TaskKind.QUERY: "Answer the query with compact reasoning, explicit uncertainty, and source placeholders where external evidence is needed.",
    TaskKind.CONVERSATION_COMPRESSION: (
        "Compress the conversation while preserving names, paths, versions, commands, decisions, failures, constraints, unresolved work, and the next executable action. "
        "Remove repetition and conversational filler. Never invent completion of unfinished work."
    ),
    TaskKind.TOKEN_OPTIMIZATION: (
        "Rewrite the supplied prompt to use fewer tokens while preserving every binding requirement, literal identifier, safety boundary, output format, and acceptance test."
    ),
    TaskKind.DOCUMENT_EDITING: (
        "Edit the document conservatively. Preserve factual meaning, headings, code, paths, version identifiers, and the author's voice. Return the complete revised text unless a patch was requested."
    ),
    TaskKind.SITREP: (
        "Write an operational SITREP for Tech Adept 00FACE with: status, completed work, evidence/tests, current blockers, risks, decisions required, and next work orders. "
        "Distinguish verified facts from inference and never mark queued work as implemented."
    ),
    TaskKind.PLANNING: (
        "Create an executable plan with dependencies, checkpoints, rollback points, tests, and explicit human authorization gates for spending, deployment, deletion, or external side effects."
    ),
    TaskKind.CONSENSUS: (
        "Independently evaluate the proposal. State evidence, assumptions, confidence, strongest objection, failure modes, and recommendation. Preserve unresolved dissent."
    ),
    TaskKind.VERIFICATION: (
        "Act as Lwa MCP’s grounded verifier and sentinel. Check internal consistency, unsupported claims, missing tests, edge cases, and unsafe assumptions."
    ),
    TaskKind.CODING_AUX: (
        "Assist the primary coding model with a narrow task. Prefer minimal diffs, executable commands, deterministic checks, and precise file references."
    ),
    TaskKind.IMAGE_GENERATION: (
        "Generate the requested image faithfully. Preserve literal text, aspect ratio, exclusions, and style constraints supplied by the user."
    ),
    TaskKind.VIDEO_GENERATION: (
        "Generate the requested video faithfully. Preserve the scene, motion, duration, aspect ratio, exclusions, and style constraints supplied by the user."
    ),
}
