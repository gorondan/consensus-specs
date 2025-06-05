from remerkleable.basic import uint64

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
This specification defines the integration of eODS (Enshrined Operator-Delegator Separation) into Ethereum’s Beacon
Chain. It introduces protocol-level delegation tracking, enshrined accounting logic, and a minimal delegation lifecycle
without dynamic validator selection or delegator governance.

## Custom types

| Name             | SSZ equivalent | Description                |
|------------------|----------------|----------------------------|
| `DelegatorIndex` | `uint64`       | a delegator registry index | 
| `Quota`          | `uint64`       | a quota                    |

## Preset

### Execution

| Name                                           | Value                     | Description                                                                                           |
|------------------------------------------------|---------------------------|-------------------------------------------------------------------------------------------------------|
| `MAX_DEPOSIT_TO_DELEGATE_REQUESTS_PER_PAYLOAD` | `uint64(2**13)` (= 8,192) | *[New in EIPXXXX_eODS* Maximum number of execution layer deposit_to_delegate requests in each payload |

### State list lengths

| Name                                 | Value                                 | Unit                         |
|--------------------------------------|---------------------------------------|------------------------------|
| `DELEGATOR_REGISTRY_LIMIT`           | `uint64(2**40)` (= 1,099,511,627,776) | delegators                   |
| `PENDING_DEPOSITS_TO_DELEGATE_LIMIT` | `uint64(2**27)` (= 134,217,728)       | pending deposits_to_delegate |

## Constants

### Misc

### Gwei values

### Domain types

| Name                         | Value                      |
|------------------------------|----------------------------|
| `DOMAIN_DEPOSIT_TO_DELEGATE` | `DomainType('0x07000000')` |

## Configuration

### Time parameters

| Name                                  | Value                    |  Unit  |  Duration  |
|---------------------------------------|--------------------------|:------:|:----------:|
| `MIN_DELEGATOR_WITHDRAWABILITY_DELAY` | `uint64(2**11)` (= 2048) | epochs | ~218 hours |

## Containers

### Misc dependencies

### New containers

#### `Delegator`

```python
class Delegator(Container):
    pubkey: BLSPubkey
    withdrawal_credentials: Bytes32
    delegator_entry_epoch: Epoch
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
    fee_quotient: uint64
```

#### `DepositToDelegateRequest`

```python
class DepositToDelegateRequest(Container):
    pubkey: BLSPubkey
    withdrawal_credentials: Bytes32
    amount: Gwei
    signature: BLSSignature
    index: uint64
```

#### `PendingDepositToDelegate`

```python
class PendingDepositToDelegate(Container):
    pubkey: BLSPubkey
    withdrawal_credentials: Bytes32
    amount: Gwei
    signature: BLSSignature
```

### Modified containers

#### `ExecutionRequests`

```python
class ExecutionRequests(Container):
    deposits: List[DepositRequest, MAX_DEPOSIT_REQUESTS_PER_PAYLOAD]
    withdrawals: List[WithdrawalRequest, MAX_WITHDRAWAL_REQUESTS_PER_PAYLOAD]
    consolidations: List[ConsolidationRequest, MAX_CONSOLIDATION_REQUESTS_PER_PAYLOAD]
    deposits_to_delegate: List[DepositToDelegateRequest, MAX_DEPOSIT_TO_DELEGATE_REQUESTS_PER_PAYLOAD]  # [New in EIPXXXX_eODS]
```

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
    is_operator: boolean # [New in EIPXXXX_eODS]
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
    delegators: List[Delegator, DELEGATOR_REGISTRY_LIMIT] #[New in EIPXXXX_eODS]
    delegators_balances: List[Gwei, DELEGATOR_REGISTRY_LIMIT] #[New in EIPXXXX_eODS]
    delegated_validators: List[DelegatedValidator, VALIDATOR_REGISTRY_LIMIT] #[New in EIPXXXX_eODS]
    pending_deposits_to_delegate: List[PendingDepositToDelegate, PENDING_DEPOSITS_TO_DELEGATE_LIMIT] #[New in EIPXXXX_eODS]
```

## Beacon chain state transition function

### Block processing

```python
def process_deposit_to_delegate_request(state: BeaconState,
                                        deposit_to_delegate_request: DepositToDelegateRequest) -> None:
    # Create pending deposit
    state.pending_deposits_to_delegate.append(PendingDepositToDelegate(
        pubkey=deposit_to_delegate_request.pubkey,
        withdrawal_credentials=deposit_to_delegate_request.withdrawal_credentials,
        amount=deposit_to_delegate_request.amount,
        signature=deposit_to_delegate_request.signature
    ))
```

## Helper functions

### Beacon state mutators

#### New `increase_delegator_balance`

```python
def increase_delegator_balance(state: BeaconState, delegator_index: DelegatorIndex, delta: Gwei) -> None:
    """
    Increase the delegator balance at index ``delegator_index`` by ``delta``.
    """
    state.delegators_balances[delegator_index] += delta
```

### Epoch processing

#### New `process_pending_deposits_to_delegate`

```python
def process_pending_deposits_to_delegate(state: BeaconState) -> None:
    for deposit_to_delegate in state.pending_deposits_to_delegate:
        apply_deposit_to_delegate(state, deposit_to_delegate)
    state.pending_deposits_to_delegate = []

```
#### New `apply_pending_deposit`

```python
def apply_deposit_to_delegate(state: BeaconState, deposit_to_delegate: PendingDepositToDelegate) -> None:
  if not is_valid_deposit_to_delegate_signature(
          deposit_to_delegate.pubkey,
          deposit_to_delegate.withdrawal_credentials,
          deposit_to_delegate.amount,
          deposit_to_delegate.signature
  ):
    return

  delegators_pubkeys = [d.pubkey for d in state.delegators]
  if deposit_to_delegate.pubkey not in delegators_pubkeys:
    delegator_index = register_new_delegator(state, deposit_to_delegate.pubkey, deposit_to_delegate.withdrawal_credentials)
  else:
    delegator_index = DelegatorIndex(delegators_pubkeys.index(deposit_to_delegate.pubkey))
  increase_delegator_balance(state, delegator_index, deposit_to_delegate.amount)
```

#### Modified `process_epoch`

```python
def process_epoch(state: BeaconState) -> None:
    process_justification_and_finalization(state)
    process_inactivity_updates(state)
    process_rewards_and_penalties(state)
    process_registry_updates(state)  # [Modified in Electra:EIP7251]
    process_slashings(state)  # [Modified in Electra:EIP7251]
    process_eth1_data_reset(state)
    process_pending_deposits(state)  # [New in Electra:EIP7251]
    process_pending_consolidations(state)  # [New in Electra:EIP7251]
    process_pending_deposits_to_delegate(state)  # [New in EIPXXXX_eODS]
    process_effective_balance_updates(state)  # [Modified in Electra:EIP7251]
    process_slashings_reset(state)
    process_randao_mixes_reset(state)
    process_historical_summaries_update(state)
    process_participation_flag_updates(state)
    process_sync_committee_updates(state)
```

#### Operations

##### Modified `process_operations`

```python
def process_operations(state: BeaconState, body: BeaconBlockBody) -> None:
    # [Modified in Electra:EIP6110]
    # Disable former deposit mechanism once all prior deposits are processed
    eth1_deposit_index_limit = min(state.eth1_data.deposit_count, state.deposit_requests_start_index)
    if state.eth1_deposit_index < eth1_deposit_index_limit:
        assert len(body.deposits) == min(MAX_DEPOSITS, eth1_deposit_index_limit - state.eth1_deposit_index)
    else:
        assert len(body.deposits) == 0

    def for_ops(operations: Sequence[Any], fn: Callable[[BeaconState, Any], None]) -> None:
        for operation in operations:
            fn(state, operation)

    for_ops(body.proposer_slashings, process_proposer_slashing)
    for_ops(body.attester_slashings, process_attester_slashing)
    for_ops(body.attestations, process_attestation)  # [Modified in Electra:EIP7549]
    for_ops(body.deposits, process_deposit)
    for_ops(body.voluntary_exits, process_voluntary_exit)  # [Modified in Electra:EIP7251]
    for_ops(body.bls_to_execution_changes, process_bls_to_execution_change)
    for_ops(body.execution_requests.deposits, process_deposit_request)  # [New in Electra:EIP6110]
    for_ops(body.execution_requests.withdrawals, process_withdrawal_request)  # [New in Electra:EIP7002:EIP7251]
    for_ops(body.execution_requests.consolidations, process_consolidation_request)  # [New in Electra:EIP7251]
    for_ops(body.execution_requests.deposits_to_delegate, process_deposit_to_delegate_request)  # [New in EIPXXXX_eODS]
```

##### Deposits


###### New `is_valid_deposit_signature`

```python
def is_valid_deposit_to_delegate_signature(pubkey: BLSPubkey,
                                           withdrawal_credentials: Bytes32,
                                           amount: uint64,
                                           signature: BLSSignature) -> bool:
    deposit_to_delegate_message = DepositToDelegateMessage(
        pubkey=pubkey,
        withdrawal_credentials=withdrawal_credentials,
        amount=amount,
    )
    domain = compute_domain(
        DOMAIN_DEPOSIT_TO_DELEGATE)  # Fork-agnostic domain since delegation deposits are valid across forks
    signing_root = compute_signing_root(deposit_to_delegate_message, domain)
    return bls.Verify(pubkey, signing_root, signature)
```

###### New `is_withdrawable_from_delegator`

```python
def is_withdrawable_from_delegator(state: BeaconState, delegator: Delegator) -> bool:
    return state.epoch > delegator.delegator_entry_epoch + MIN_DELEGATOR_WITHDRAWABILITY_DELAY
```