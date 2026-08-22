# Source data validation (balanced_10000_v1)

Rows: 40000

## Rows by model x condition
```
model         condition          
gpt-5.4       claim_only             10000
              claim_plus_evidence    10000
gpt-5.4-mini  claim_only             10000
              claim_plus_evidence    10000
```

## Gold label balance per model x condition
```
gold_label                        Refuted  Supported
model        condition                              
gpt-5.4      claim_only              5000       5000
             claim_plus_evidence     5000       5000
gpt-5.4-mini claim_only              5000       5000
             claim_plus_evidence     5000       5000
```

Unique claims: 10000
FEVER source rows: 10000

## Reproduced aggregate accuracy
```
model         condition          
gpt-5.4       claim_only             88.69
              claim_plus_evidence    96.04
gpt-5.4-mini  claim_only             84.67
              claim_plus_evidence    95.54
```

**Status: PASS**