# TR-043 - Persistent Operator Pipeline Marks Rite

**Entry:** WO-041 marks exist only in process memory.
**Action:** Add a versioned local ledger record and read/write validation.
**Check:** Mark, restart, read, export, migrate, and reject malformed or
secret-bearing records.
**Promote when:** blocked/maintenance marks survive restart and gate execution
without changing provider credentials or prompt handling.
**Rollback:** quarantine invalid records and use computed status only.
