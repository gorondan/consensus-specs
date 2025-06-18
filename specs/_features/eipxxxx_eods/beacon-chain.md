from mypy.state import state

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

| Name                                             | Value                     | Description                                                                                             |
|--------------------------------------------------|---------------------------|---------------------------------------------------------------------------------------------------------|
| `MAX_DELEGATION_OPERATIONS_REQUESTS_PER_PAYLOAD` | `uint64(2**13)` (= 8,192) | *[New in EIPXXXX_eODS* Maximum number of execution layer delegation operations requests in each payload |

### State list lengths

| Name                                  | Value                                 | Unit                                |
|---------------------------------------|---------------------------------------|-------------------------------------|
| `DELEGATOR_REGISTRY_LIMIT`            | `uint64(2**40)` (= 1,099,511,627,776) | delegators                          |
| `PENDING_DELEGATION_OPERATIONS_LIMIT` | `uint64(2**27)` (= 134,217,728)       | pending delegation operations limit |

## Constants

### Execution layer triggered requests

| Name                                | Value            |
|-------------------------------------|------------------|
| `DELEGATION_OPERATION_REQUEST_TYPE` | `Bytes1('0x03')` |

### Execution layer triggered delegation requests

| Name                                   | Value            |
|----------------------------------------|------------------|
| `ACTIVATE_OPERATOR_REQUEST_TYPE`       | `Bytes1('0x00')` |
| `DEPOSIT_TO_DELEGATE_REQUEST_TYPE`     | `Bytes1('0x01')` |
| `DELEGATE_REQUEST_TYPE`                | `Bytes1('0x02')` |
| `UNDELEGATE_REQUEST_TYPE`              | `Bytes1('0x03')` |
| `REDELEGATE_REQUEST_TYPE`              | `Bytes1('0x04')` |
| `WITHDRAW_FROM_DELEGATOR_REQUEST_TYPE` | `Bytes1('0x05')` |
| `EARLY_LIQUIDITY_REQUEST_TYPE`         | `Bytes1('0x06')` |
| `EXIT_REQUEST_TYPE`                    | `Bytes1('0x07')` |

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

### New containers

#### `Delegator`

```python
class Delegator(Container):
    execution_address: ExecutionAddress
    delegator_entry_epoch: Epoch
```

#### `DelegatedValidator`

```python
class DelegatedValidator(Container):
    delegated_validator: Validator
    delegated_validator_quota: uint64
    delegators_quotas: List[Quota, DELEGATOR_REGISTRY_LIMIT]
    delegated_balances: List[Gwei, DELEGATOR_REGISTRY_LIMIT]
    total_delegated_balance: Gwei
    fee_quotient: uint64
```
#### `DelegationOperationRequest`

```python
class DelegationOperationRequest(Container):
    type: Bytes1
    source_pubkey: BLSPubkey
    target_pubkey: BLSPubkey
    withdraw_credentials: Bytes32
    signature: BLSSignature
    amount: Gwei
    source_address: ExecutionAddress
```

#### `PendingActivateOperator`

```python
class PendingActivateOperator(Container):
    validator_pubkey: BLSPubkey
    fee_quotient: uint64
    source_address: ExecutionAddress
```
#### `PendingDepositToDelegate`

```python
class PendingDepositToDelegate(Container):
    execution_address:ExecutionAddress
    amount: Gwei
```

#### `PendingDelegateRequest`

```python
class PendingDelegateRequest(Container):
  execution_address:ExecutionAddress
  validator_pubkey: BLSPubkey
  amount: Gwei
  slot: Slot
```

#### `PendingUndelegateRequest`

```python
class PendingUndelegateRequest(Container):
  pubkey: BLSPubkey
  signature: BLSSignature
  amount: Gwei
```

#### `PendingRedelegateRequest`

```python
class PendingRedelegateRequest(Container):
  source_pubkey: BLSPubkey
  target_pubkey: BLSPubkey
  signature: BLSSignature
  amount: Gwei
```

#### `PendingWithdrawFromDelegatorRequest`

```python
class PendingWithdrawFromDelegatorRequest(Container):
  pubkey: BLSPubkey
  signature: BLSSignature
  amount: Gwei
```

### Modified containers

#### `ExecutionRequests`

```python
class ExecutionRequests(Container):
    deposits: List[DepositRequest, MAX_DEPOSIT_REQUESTS_PER_PAYLOAD]
    withdrawals: List[WithdrawalRequest, MAX_WITHDRAWAL_REQUESTS_PER_PAYLOAD]
    consolidations: List[ConsolidationRequest, MAX_CONSOLIDATION_REQUESTS_PER_PAYLOAD]
    delegation_operations: List[DelegationOperationRequest, MAX_DELEGATION_OPERATIONS_REQUESTS_PER_PAYLOAD]  # [New in EIPXXXX_eODS]
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
    is_operator: boolean  # [New in EIPXXXX_eODS]
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
    earliest_consolidationavailable_epoch: Epoch  # [New in Electra:EIP7251]
    pending_deposits: List[PendingDeposit, PENDING_DEPOSITS_LIMIT]  # [New in Electra:EIP7251]
    # [New in Electra:EIP7251]
    pending_partial_withdrawals: List[PendingPartialWithdrawal, PENDING_PARTIAL_WITHDRAWALS_LIMIT]
    pending_consolidations: List[PendingConsolidation, PENDING_CONSOLIDATIONS_LIMIT]  # [New in Electra:EIP7251]
    # Delegation additions
    delegators: List[Delegator, DELEGATOR_REGISTRY_LIMIT]  # [New in EIPXXXX_eODS]
    delegators_balances: List[Gwei, DELEGATOR_REGISTRY_LIMIT]  # [New in EIPXXXX_eODS]
    delegated_validators: List[DelegatedValidator, VALIDATOR_REGISTRY_LIMIT]  # [New in EIPXXXX_eODS]
    pending_operator_activations: List[PendingActivateOperator, PENDING_DELEGATION_OPERATIONS_LIMIT]  # [New in EIPXXXX_eODS]
    pending_deposits_to_delegate: List[PendingDepositToDelegate, PENDING_DELEGATION_OPERATIONS_LIMIT]  # [New in EIPXXXX_eODS]
    pending_delegations: List[PendingDelegateRequest, PENDING_DELEGATION_OPERATIONS_LIMIT]  # [New in EIPXXXX_eODS]
    pending_undelegations: List[PendingUndelegateRequest, PENDING_DELEGATION_OPERATIONS_LIMIT]  # [New in EIPXXXX_eODS]
    pending_redelegations: List[PendingRedelegateRequest, PENDING_DELEGATION_OPERATIONS_LIMIT]  # [New in EIPXXXX_eODS]
    pending_withdrawals_from_delegators: List[PendingWithdrawFromDelegatorRequest, PENDING_DELEGATION_OPERATIONS_LIMIT]  # [New in EIPXXXX_eODS]
```

## Beacon chain state transition function

### Block processing

#### New `process_delegation_operation_request`

```python
def process_delegation_operation_request(state: BeaconState,
                                         delegation_operation_request: DelegationOperationRequest) -> None:
   
    if delegation_operation_request.type == ACTIVATE_OPERATOR_REQUEST_TYPE:
      state.pending_activate_operator.append(PendingActivateOperator(
          validator_pubkey=delegation_operation_request.target_pubkey,
          source_address=delegation_operation_request.source_address,
          fee_quotient=delegation_operation_request.fee_quotient
      ))
    
    elif delegation_operation_request.type == DEPOSIT_TO_DELEGATE_REQUEST_TYPE:
        state.pending_deposits_to_delegate.append(PendingDepositToDelegate(
            execution_address = delegation_operation_request.execution_address,
            amount=delegation_operation_request.amount
        ))
        
    elif delegation_operation_request.type == DELEGATE_REQUEST_TYPE:
      state.pending_delegations.append(PendingDelegateRequest(
        validator_pubkey=delegation_operation_request.target_pubkey,
        execution_address = delegation_operation_request.execution_address,
        amount=delegation_operation_request.amount,
        slot=state.slot
      ))

    elif delegation_operation_request.type == UNDELEGATE_REQUEST_TYPE:
      state.pending_undelegate.append(PendingUndelegateRequest(
        pubkey=delegation_operation_request.pubkey,
        signature=delegation_operation_request.signature,
        amount=delegation_operation_request.amount
      ))
        
    elif delegation_operation_request.type == REDELEGATE_REQUEST_TYPE:
      state.pending_redelegate.append(PendingRedelegateRequest(
        source_pubkey=delegation_operation_request.source_pubkey,
        target_pubkey=delegation_operation_request.target_pubkey,
        signature=delegation_operation_request.signature,
        amount=delegation_operation_request.amount
      ))
        
    elif delegation_operation_request.type == WITHDRAW_FROM_DELEGATOR_REQUEST_TYPE:
      state.pending_withdraw_from_delegator.append(PendingWithdrawFromDelegatorRequest(
        source_pubkey=delegation_operation_request.source_pubkey,
        target_pubkey=delegation_operation_request.target_pubkey,
        signature=delegation_operation_request.signature,
        amount=delegation_operation_request.amount
      )) 
```

#### Execution payload

##### Modify `get_execution_requests_list`

*Note*: Encodes execution requests as defined by [EIP-7685](https://eips.ethereum.org/EIPS/eip-7685).

```python
def get_execution_requests_list(execution_requests: ExecutionRequests) -> Sequence[bytes]:
    requests = [
        (DEPOSIT_REQUEST_TYPE, execution_requests.deposits),
        (WITHDRAWAL_REQUEST_TYPE, execution_requests.withdrawals),
        (CONSOLIDATION_REQUEST_TYPE, execution_requests.consolidations),
        (DELEGATION_OPERATION_REQUEST_TYPE, execution_requests.delegation_operations),
    ]

    return [
        request_type + ssz_serialize(request_data)
        for request_type, request_data in requests
        if len(request_data) != 0
    ]
```

## Helper functions

### Delegation helper functions

#### New `register_new_delegator`

```python
def register_new_delegator(state: BeaconState, execution_address: ExecutionAddress) -> DelegatorIndex:
    delegator = Delegator(
        execution_address=execution_address,
        delegator_entry_epoch=compute_epoch_at_slot(state.slot),
    )
    state.delegators.append(delegator)
    state.delegators_balances.append(Gwei(0))
    return DelegatorIndex(len(state.delegators) - 1)
```

#### New `get_delegated_validator`

```python
def get_delegated_validator(state: BeaconState, validator_pubkey: BLSPubkey) -> DelegatedValidator:
  for i, dv in enumerate(state.delegated_validators):
    if dv.delegated_validator.pubkey == validator_pubkey:
      return dv
```

### Beacon state mutators

### Epoch processing

#### New `process_pending_deposits_to_delegate`

```python
def process_pending_deposits_to_delegate(state: BeaconState) -> None:
    for deposit_to_delegate in state.pending_deposits_to_delegate:
      delegators_execution_addresses = [d.execution_address for d in state.delegators]
      if deposit_to_delegate.execution_address not in delegators_execution_addresses:
        delegator_index = register_new_delegator(state, deposit_to_delegate.execution_address)
      else:
        delegator_index = DelegatorIndex(delegators_execution_addresses.index(deposit_to_delegate.execution_address))
      increase_delegator_balance(state, delegator_index, deposit_to_delegate.amount)
    state.pending_deposits_to_delegate = []
```

#### New `process_pending_activate_operators`

```python
def process_pending_activate_operators(state: BeaconState) -> None:
    for pending_activation in state.pending_activate_operator:
      validator_pubkeys = [v.pubkey for v in state.validators]
      # Verify pubkey exists
      request_pubkey = pending_activation.validator_pubkey
      if request_pubkey not in validator_pubkeys:
        return
      validator_index = ValidatorIndex(validator_pubkeys.index(request_pubkey))
      validator = state.validators[validator_index]

      # Ensure the validator is not already an operator
      if validator.is_operator:
        return
      
      # Verify withdrawal credentials
      has_correct_credential = has_compounding_withdrawal_credential(validator)
      is_correct_source_address = (
              validator.withdrawal_credentials[12:] == pending_activation.source_address
      )
      if not (has_correct_credential and is_correct_source_address):
        return
      # Verify the validator is active
      if not is_active_validator(validator, get_current_epoch(state)):
        return
      # Verify exit has not been initiated
      if validator.exit_epoch != FAR_FUTURE_EPOCH:
        return
      # Ensure the validator is not slashed
      if validator.slashed:
        return
   
      validator.is_operator = True
      
      delegated_validator =  DelegatedValidator(
      validator = validator,
      delegated_validator_quota = 1,
      delegators_quotas = [],
      delegated_balances = [],
      total_delegated_balance = 0,
      fee_quotient = pending_activation.fee_quotient
    ) 
     
    state.pending_activate_operator = []
```

#### New `process_pending_delegations`

```python
def process_pending_delegations(state: BeaconState) -> None:
    next_epoch = Epoch(get_current_epoch(state) + 1)
    available_for_processing = get_activation_exit_churn_limit(state)
    processed_amount = 0
    delegations_to_postpone = []
    finalized_slot = compute_start_slot_at_epoch(state.finalized_checkpoint.epoch)
    
    delegators_execution_addresses = [d.execution_address for d in state.delegators]
    validator_pubkeys = [v.pubkey for v in state.validators]
        
    for delegation in state.pending_delegations:
        delegated_amount = 0
        has_delegator = False
        has_validator = False

        delegator_index = delegators_execution_addresses.index(delegation.execution_address)

        if delegator_index:
          has_delegator = True

        validator_index = validator_pubkeys.index(delegation.validator_pubkey)
           
        if validator_index:
          has_validator = True

        if not has_delegator or not has_validator:
          break  
            
        # here we have delegator and validator

        if state.delegators_balance[delegator_index] < delegation.amount:
          break

        validator = state.validators[validator_index]
        
        if not is_validator_delegable(validator):
          break
        
        if delegation.slot > finalized_slot:
            delegations_to_postpone.append(delegation)
            break
        
        # we can process the entire amount
        if available_for_processing >= processed_amount + delegation.amount:
          delegated_amount = delegation.amount
          
        # we can process a partial amount  
        elif available_for_processing < processed_amount:
          delegated_amount = available_for_processing - processed_amount 
          
        # nothing left in churn  
        else: 
            delegations_to_postpone.append(delegation)
            break

        # here we decrement the delegators available balance
        delegate_to_validator(state, delegator_index, validator.pubkey, delegated_amount)
        
        processed_amount += delegated_amount

    state.pending_delegations = delegations_to_postpone

```
#### New `process_pending_undelegations`

```python
def process_pending_undelegations(state: BeaconState) -> None:
    # NEW:
        # - add undelegation_exit_queue in state
            # here we must hold all undelegation requests until Weak Subjectivity and churn are settled 
    # PREREQ:
        # - withdrawal must fit in churn
        # - validator must be active
    # STEPS: 
        # Queue undelegation exit request
          # - check if delegator can undelegate the given amount (if there is enough quota in DV)
          # - calculate the validator's fee
              # this we need to hold in the undelegation_exit_queue 
          # - calculate the undelegation exit epoch
          # - create an UndelegationExitRequest:
                          # - amount
                          # - fee
                          # - delegator (to transfer funds after WS)
                          # - validator (to transfer fee after WS)
                          # - exit epoch
          # - add the UndelegationExitRequest to the state
          # - remove the amount from the DV's delegated balances
          # - recalculate quotas in DV
        
        # Process undelegation exit request queue:
            # - for each request, we check if the withdrawable_epoch is here
            # - we transfer the required funds to delegator
            # - we transfer the required funds to validator (the fee)
        
        # Modify the slashing logic:    
            # slash validator - as is now
            # slash delegated values
            # slash queued for exit values

```

#### New `is_validator_delegable`

```python
def is_validator_delegable(validator: Validator) -> boolean:
    next_epoch = Epoch(get_current_epoch(state) + 1)
    
    if not validator:
        return False
    if validator.is_operator:
        return False
    if validator.exit_epoch < FAR_FUTURE_EPOCH:
      return False
    if validator.withdrawable_epoch < next_epoch:
      return False
    if validator.slashed:
      return False
    if validator.effective_balance > MAX_EFFECTIVE_BALANCE:
      return False
    
    return True
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
    process_pending_activate_operators(state)
    process_pending_deposits_to_delegate(state)  # [New in EIPXXXX_eODS]
    process_pending_delegations(state)  # [New in EIPXXXX_eODS]
    process_pending_undelegations(state)  # [New in EIPXXXX_eODS]
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
    for_ops(body.execution_requests.delegation_operations,
            process_delegation_operation_request)  # [New in EIPXXXX_eODS]
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