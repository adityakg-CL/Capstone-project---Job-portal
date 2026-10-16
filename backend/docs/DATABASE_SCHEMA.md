# Database Schema

Collections: `users`, `jobs`, `applications`, `referrals`, `referral_bonuses`, `interviews`, `notifications`, `audit_logs`, and `business_rules` (reserved for future configurable rules). Job documents use only `open` and `closed` statuses. At startup, legacy `active`/`published` jobs migrate to `open`; other noncanonical statuses migrate to `closed`. This updates status values without deleting jobs or their application/referral records.

Indexes are initialized idempotently in `models/indexes.py`: normalized email unique; job status/created and team/location; application owner and job/status plus unique employee/job; referrals by referrer and candidate/job; unique bonus per referral and bonus status; interviews by application/time; notifications by recipient/read/time; audit by actor/time and entity/time.

No data is deleted at startup. Before applying the unique application index to an existing database, check and resolve duplicate employee/job records. MongoDB transactions are not used by this first version; conditional atomic updates are used for status changes. For multi-document consistency guarantees, use a replica set and implement transactions/outbox or reconciliation as a follow-up.
