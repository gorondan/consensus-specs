# EIP-XXX_eODS -- The Beacon Chain

## Table of contents

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Introduction](#introduction)
- [Preset](#preset)
  - [Domain types](#domain-types)
  - [State list lengths](#state-list-lengths)
- [Containers](#containers)
  - [New containers](#new-containers)
  - [Modified containers](#modified-containers)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

---

## Introduction

*Note:* This specification is built upon [Electra](../../electra/beacon_chain.md) and is under active development.
This specification defines the integration of eODS (Enshrined Operator-Delegator Separation) into Ethereum’s Beacon Chain. It introduces protocol-level delegation tracking, enshrined accounting logic, and a minimal delegation lifecycle without dynamic validator selection or delegator governance.

## Custom types

| Name | SSZ equivalent | Description |
| - | - | - |
| `DelegatorIndex` | `uint64` | a delegator registry index |

## Preset

### Misc

| Name                      | Value |
|---------------------------| - |
| `DELEGDATOR_FEE_QUOTIENT` | `uint64(4)` |
| `DELEGDATOR_QUOTA`        | `uint64(4)` |

### Domain types

### State list lengths

| Name                       | Value                                 |    Unit    |
|----------------------------|---------------------------------------|:----------:|
| `DELEGATOR_REGISTRY_LIMIT` | `uint64(2**40)` (= 1,099,511,627,776) | delegators |

---

## Containers

### New containers

```python
class Delegator(Container):
    pubkey: BLSPubkey
    withdrawal_credentials: Bytes32
    effective_delegated_balance: Gwei
    delegation_entry_epoch: Epoch
```

```python
class DelegatedValidator(Container):
    delegated_validator: Validator
    delegated_validator_initial_balance: Gwei
    delegated_validator_quota: Quota
    delegators_quotas: List[Quota]
    delegated_balances: List[Gwei]
    total_delegated_balance: Gwei
```

### Modified containers

```python
class Validator(Container):
    pubkey: BLSPubkey
    withdrawal_credentials: Bytes32
    effective_balance: Gwei
    slashed: boolean
    activation_eligibility_epoch: Epoch
    activation_epoch: Epoch
    exit_epoch: Epoch
    withdrawable_epoch: Epoch
    delegated: bool
    fee_percentage: Fee
```

```python
class BeaconState(Container):
    # Core fields omitted for brevity...

    # Delegation additions
    delegators: List[Delegator, DELEGATOR_REGISTRY_LIMIT]
    delegators_balances: List[Gwei, DELEGATOR_REGISTRY_LIMIT]
    delegated_validators: List[DelegatedValidator, VALIDATOR_REGISTRY_LIMIT]
```