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

| Name             | SSZ equivalent | Description |
|------------------| - |---------|
| `DelegatorIndex` | `uint64` | a delegator registry index | 
| `Quota` | `uint64` | a quota |

## Preset

## Constants

### Misc

### Domain types

### State list lengths

| Name                       | Value                                 |    Unit    |
|----------------------------|---------------------------------------|:----------:|
| `DELEGATOR_REGISTRY_LIMIT` | `uint64(2**40)` (= 1,099,511,627,776) | delegators |

---

## Containers

### New containers

#### `Delegator`

```python
class Delegator(Container):
    pubkey: BLSPubkey
    withdrawal_credentials: Bytes32
    effective_delegated_balance: Gwei
    delegation_entry_epoch: Epoch
```

#### `DelegatedValidator`

```python
class DelegatedValidator(Container):
    delegated_validator: Validator
    delegated_validator_initial_balance: Gwei
    delegated_validator_quota: uint64
    delegators_quotas: List[Quota, DELEGATOR_REGISTRY_LIMIT]
    delegated_balances: List[Gwei, DELEGATOR_REGISTRY_LIMIT]
    total_delegated_balance: Gwei
```

### Modified containers

#### `Validator`

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
    delegated: boolean
    fee_quotient: uint64
```

#### `BeaconState`

```python
class BeaconState(Container):
    # Versioning
    genesis_time: uint64
    genesis_validators_root: Root
    slot: Slot
    fork: Fork
    # History
    latest_block_header: BeaconBlockHeader
    block_roots: Vector[Root, SLOTS_PER_HISTORICAL_ROOT]
    state_roots: Vector[Root, SLOTS_PER_HISTORICAL_ROOT]
    historical_roots: List[Root, HISTORICAL_ROOTS_LIMIT]
    # Eth1
    eth1_data: Eth1Data
    eth1_data_votes: List[Eth1Data, EPOCHS_PER_ETH1_VOTING_PERIOD * SLOTS_PER_EPOCH]
    eth1_deposit_index: uint64
    # Registry
    validators: List[Validator, VALIDATOR_REGISTRY_LIMIT]
    balances: List[Gwei, VALIDATOR_REGISTRY_LIMIT]
    # Randomness
    randao_mixes: Vector[Bytes32, EPOCHS_PER_HISTORICAL_VECTOR]
    # Slashings
    slashings: Vector[Gwei, EPOCHS_PER_SLASHINGS_VECTOR]  # Per-epoch sums of slashed effective balances
    # Participation
    previous_epoch_participation: List[ParticipationFlags, VALIDATOR_REGISTRY_LIMIT]
    current_epoch_participation: List[ParticipationFlags, VALIDATOR_REGISTRY_LIMIT]
    # Finality
    justification_bits: Bitvector[JUSTIFICATION_BITS_LENGTH]  # Bit set for every recent justified epoch
    previous_justified_checkpoint: Checkpoint
    current_justified_checkpoint: Checkpoint
    finalized_checkpoint: Checkpoint
    # Inactivity
    inactivity_scores: List[uint64, VALIDATOR_REGISTRY_LIMIT]
    # Sync
    current_sync_committee: SyncCommittee
    next_sync_committee: SyncCommittee
    # Execution
    latest_execution_payload_header: ExecutionPayloadHeader
    # Withdrawals
    next_withdrawal_index: WithdrawalIndex
    next_withdrawal_validator_index: ValidatorIndex
    # Deep history valid from Capella onwards
    historical_summaries: List[HistoricalSummary, HISTORICAL_ROOTS_LIMIT]
    deposit_requests_start_index: uint64  # [New in Electra:EIP6110]
    deposit_balance_to_consume: Gwei  # [New in Electra:EIP7251]
    exit_balance_to_consume: Gwei  # [New in Electra:EIP7251]
    earliest_exit_epoch: Epoch  # [New in Electra:EIP7251]
    consolidation_balance_to_consume: Gwei  # [New in Electra:EIP7251]
    earliest_consolidation_epoch: Epoch  # [New in Electra:EIP7251]
    pending_deposits: List[PendingDeposit, PENDING_DEPOSITS_LIMIT]  # [New in Electra:EIP7251]
    # [New in Electra:EIP7251]
    pending_partial_withdrawals: List[PendingPartialWithdrawal, PENDING_PARTIAL_WITHDRAWALS_LIMIT]
    pending_consolidations: List[PendingConsolidation, PENDING_CONSOLIDATIONS_LIMIT]  # [New in Electra:EIP7251]
    # Delegation additions
    delegators: List[Delegator, DELEGATOR_REGISTRY_LIMIT]
    delegators_balances: List[Gwei, DELEGATOR_REGISTRY_LIMIT]
    delegated_validators: List[DelegatedValidator, VALIDATOR_REGISTRY_LIMIT]
```
