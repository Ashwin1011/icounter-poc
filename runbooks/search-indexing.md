# Runbook — Search Indexing Lag

Use this runbook when search queue age or indexing lag exceeds the operational threshold.

### Response
1. Verify source-event ingestion from Data Platform.
2. Check indexing-worker processing time and error rate.
3. Determine whether the issue is source-data delay or indexing-worker regression.
4. Roll back recent indexing changes when evidence indicates a deployment regression.
5. Monitor queue age until backlog returns to normal.

Search indexing is eventually consistent. Stale results do not automatically mean data loss.
