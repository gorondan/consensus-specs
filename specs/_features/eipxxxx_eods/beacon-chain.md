# EIP-XXX_eODS -- The Beacon Chain

## Table of contents

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Introduction](#introduction)
- [Custom types](#custom-types)
- [Preset](#preset)
  - [Execution](#execution)
  - [State list lengths](#state-list-lengths)
- [Constants](#constants)
  - [Execution layer triggered requests](#execution-layer-triggered-requests)
  - [Execution layer triggered delegation requests](#execution-layer-triggered-delegation-requests)
  - [Domain types](#domain-types)
- [Configuration](#configuration)
  - [Time parameters](#time-parameters)
- [Containers](#containers)
  - [New containers](#new-containers)
    - [`Delegator`](#delegator)
    - [`DelegatedValidator`](#delegatedvalidator)
    - [`DelegationOperationRequest`](#delegationoperationrequest)
    - [`PendingActivateOperator`](#pendingactivateoperator)
    - [`PendingDepositToDelegate`](#pendingdeposittodelegate)
    - [`PendingDelegateRequest`](#pendingdelegaterequest)
    - [`PendingUndelegateRequest`](#pendingundelegaterequest)
    - [`PendingRedelegateRequest`](#pendingredelegaterequest)
    - [`PendingWithdrawFromDelegatorRequest`](#pendingwithdrawfromdelegatorrequest)
    - [`UndelegationExit`](#undelegationexit)
  - [Modified containers](#modified-containers)
    - [`ExecutionRequests`](#executionrequests)
    - [`Validator`](#validator)
    - [`BeaconState`](#beaconstate)
- [Beacon chain state transition function](#beacon-chain-state-transition-function)
  - [Block processing](#block-processing)
    - [New `process_delegation_operation_request`](#new-process_delegation_operation_request)
    - [Execution payload](#execution-payload)
      - [Modify `get_execution_requests_list`](#modify-get_execution_requests_list)
- [Helper functions](#helper-functions)
  - [Delegation helper functions](#delegation-helper-functions)
    - [New `register_new_delegator`](#new-register_new_delegator)
    - [New `get_delegated_validator`](#new-get_delegated_validator)
  - [Beacon state mutators](#beacon-state-mutators)
  - [Epoch processing](#epoch-processing)
    - [New `process_pending_deposits_to_delegate`](#new-process_pending_deposits_to_delegate)
    - [New `process_pending_activate_operators`](#new-process_pending_activate_operators)
    - [New `process_pending_delegations`](#new-process_pending_delegations)
    - [New `process_pending_undelegations`](#new-process_pending_undelegations)
    - [New `process_undelegations_exit_queue`](#new-process_undelegations_exit_queue)
    - [Modified process_rewards_and_penalties](#modified-process_rewards_and_penalties)
    - [Modified `process_slashings`](#modified-process_slashings)
    - [Modified `process_effective_balance_updates`](#modified-process_effective_balance_updates)
    - [New `is_validator_delegable`](#new-is_validator_delegable)
    - [Modified `process_epoch`](#modified-process_epoch)
    - [Operations](#operations)
      - [Modified `process_operations`](#modified-process_operations)
      - [Deposits](#deposits)
        - [New `is_valid_deposit_signature`](#new-is_valid_deposit_signature)
        - [New `is_withdrawable_from_delegator`](#new-is_withdrawable_from_delegator)

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

| Name                                 | Value            |
|--------------------------------------|------------------|
| `DELEGATION_OPERATIONS_REQUEST_TYPE` | `Bytes1('0x03')` |

### Delegation Operations Request Types

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
    validator: Validator
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
    execution_address: ExecutionAddress
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
  execution_address: ExecutionAddress
  validator_pubkey: BLSPubkey
  amount: Gwei
  slot: Slot
```

#### `PendingUndelegateRequest`

```python
class PendingUndelegateRequest(Container):
  execution_address: ExecutionAddress
  validator_pubkey: BLSPubkey
  amount: Gwei
```

#### `PendingRedelegateRequest`

```python
class PendingRedelegateRequest(Container):
  source_pubkey: BLSPubkey
  target_pubkey: BLSPubkey
  execution_address: ExecutionAddress
  amount: Gwei
```

#### `PendingWithdrawFromDelegatorRequest`

```python
class PendingWithdrawFromDelegatorRequest(Container):
  execution_address: ExecutionAddress
  amount: Gwei
```

#### `UndelegationExit`

```python
class UndelegationExit(Container):
  amount: Gwei
  total_delegated_at_withdrawal: Gwei
  execution_address: BLSPubkey
  validator_pubkey: BLSPubkey
  exit_queue_epoch: Epoch
  withdrawable_epoch: Epoch
  is_redelegation: boolean
  redelegate_to_validator_pubkey: BLSPubkey

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
    undelegations_exit_queue: List[UndelegationExit, PENDING_DELEGATION_OPERATIONS_LIMIT] # [New in EIPXXXX_eODS]
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
          execution_address=delegation_operation_request.execution_address,
          fee_quotient=delegation_operation_request.fee_quotient
      ))
    
    elif delegation_operation_request.type == DEPOSIT_TO_DELEGATE_REQUEST_TYPE:
        state.pending_deposits_to_delegate.append(PendingDepositToDelegate(
            execution_address=delegation_operation_request.execution_address,
            amount=delegation_operation_request.amount
        ))
        
    elif delegation_operation_request.type == DELEGATE_REQUEST_TYPE:
      state.pending_delegations.append(PendingDelegateRequest(
        validator_pubkey=delegation_operation_request.target_pubkey,
        execution_address=delegation_operation_request.execution_address,
        amount=delegation_operation_request.amount,
        slot=state.slot
      ))

    elif delegation_operation_request.type == UNDELEGATE_REQUEST_TYPE:
      state.pending_undelegations.append(PendingUndelegateRequest(
        validator_pubkey=delegation_operation_request.target_pubkey,
        execution_address = delegation_operation_request.execution_address,
        amount=delegation_operation_request.amount
      ))
        
    elif delegation_operation_request.type == REDELEGATE_REQUEST_TYPE:
      state.pending_redelegations.append(PendingRedelegateRequest(
        source_pubkey=delegation_operation_request.source_pubkey,
        target_pubkey=delegation_operation_request.target_pubkey,
        execution_address=delegation_operation_request.execution_address,  
        amount=delegation_operation_request.amount
      ))
        
    elif delegation_operation_request.type == WITHDRAW_FROM_DELEGATOR_REQUEST_TYPE:
      state.pending_withdraw_from_delegator.append(PendingWithdrawFromDelegatorRequest(
        execution_address=delegation_operation_request.execution_address,  
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
        (DELEGATION_OPERATIONS_REQUEST_TYPE, execution_requests.delegation_operations),
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
      # check if validator with given pubkey exists 
      validator_pubkeys = [v.pubkey for v in state.validators]
      request_pubkey = pending_activation.validator_pubkey
      if request_pubkey not in validator_pubkeys:
        break
          
      validator_index = ValidatorIndex(validator_pubkeys.index(request_pubkey))
      validator = state.validators[validator_index]

      # Ensure the validator is not already an operator
      if validator.is_operator:
        break
      
      # Verify withdrawal credentials
      has_correct_credential = has_compounding_withdrawal_credential(validator)
      is_correct_source_address = (
              validator.withdrawal_credentials[12:] == pending_activation.execution_address
      )
      if not (has_correct_credential and is_correct_source_address):
        break
          
      # Verify exit has not been initiated
      if validator.exit_epoch != FAR_FUTURE_EPOCH:
        break
          
      # Ensure the validator is not slashed
      if validator.slashed:
        break
   
      validator.is_operator = True
      
      delegated_validator =  DelegatedValidator(
        validator = validator,
        delegated_validator_quota = 1,
        delegators_quotas = [],
        delegated_balances = [],
        total_delegated_balance = 0,
        fee_quotient = pending_activation.fee_quotient
      ) 
    state.delegated_validators.append(delegated_validator)
    state.pending_activate_operator = []
```

#### New `process_pending_delegations`

```python
def process_pending_delegations(state: BeaconState) -> None:
    available_for_processing = get_activation_exit_churn_limit(state)
    processed_amount = 0
    delegations_to_postpone = []
    finalized_slot = compute_start_slot_at_epoch(state.finalized_checkpoint.epoch)
    
    delegators_execution_addresses = [d.execution_address for d in state.delegators]
    validator_pubkeys = [v.pubkey for v in state.validators]
        
    for delegation in state.pending_delegations:
        delegated_amount = 0
        requested_to_delegate = delegation.amount
        
        # check if the registry contains the delegator and validator
        delegator_index = delegators_execution_addresses.index(delegation.execution_address)
        if not delegator_index:
            break
        
        validator_index = validator_pubkeys.index(delegation.validator_pubkey)
        if not validator_index:
            break

        if state.delegators_balance[delegator_index] == 0:
          break
            
        if state.delegators_balance[delegator_index] < requested_to_delegate:
          requested_to_delegate = state.delegators_balance[delegator_index]

        validator = state.validators[validator_index]
        
        if not is_validator_delegable(validator):
          break
        
        if delegation.slot > finalized_slot:
            delegations_to_postpone.append(delegation)
            break
        
        # we can process the entire amount
        if available_for_processing >= processed_amount + requested_to_delegate:
          delegated_amount = delegation.amount
          
        # we can process a partial amount  
        elif available_for_processing < processed_amount:
          delegated_amount = available_for_processing - processed_amount 
          
        # nothing left in churn  
        else: 
            delegations_to_postpone.append(delegation)
            break

        # here beacon-chain-accounting is called to delegate amount to validator
        delegate_to_validator(state, delegator_index, validator.pubkey, delegated_amount)
        
        processed_amount += delegated_amount

    state.pending_delegations = delegations_to_postpone
```

#### New `process_pending_undelegations`

```python
def process_pending_undelegations(state: BeaconState) -> None:
  delegators_execution_addresses = [d.execution_address for d in state.delegators]

  for undelegate in state.pending_undelegations:
    delegator_index = delegators_execution_addresses.index(undelegate.execution_address)
    if not delegator_index:
      break
        
    delegated_validator = get_delegated_validator(state, undelegate.validator_pubkey)
    if not delegated_validator:
      break
    if not is_validator_delegable(delegated_validator.validator):
      break

    if len(delegated_validator.delegators_quotas) < delegator_index:
      break

    if delegated_validator.delegators_quotas[delegator_index] == 0:
      break
        
    # we cap the requested amount to avoid a malicious request which can fill up the churn    
    requested_to_undelegate = undelegate.amount  
    if delegated_validator.delegated_balances[delegator_index] < requested_to_undelegate:
      requested_to_undelegate = delegated_validator.delegated_balances[delegator_index]

    # Calculates the undelegation's exit and withdrawability epochs
    exit_queue_epoch = compute_exit_epoch_and_update_churn(state, requested_to_undelegate)
    withdrawable_epoch = Epoch(exit_queue_epoch + config.MIN_VALIDATOR_WITHDRAWABILITY_DELAY)

    # Appends the undelegation in the undelegation exit queue
    state.undelegations_exit_queue.append(
      UndelegationExit(
        amount=requested_to_undelegate,
        exit_queue_epoch=exit_queue_epoch,
        withdrawable_epoch=withdrawable_epoch,
        execution_address=undelegate.execution_address,
        validator_pubkey=undelegate.validator_pubkey))
        
  state.pending_undelegations = []
```

#### New `process_pending_redelegations`

*Note:* A redelegation is composed of one undelegation followed by one delegation.

```python
def process_pending_redelegations(state: BeaconState) -> None :
    delegators_execution_addresses = [d.execution_address for d in state.delegators]
    
    for redelegate in state.pending_redelegations:
        # we check if the target is valid
        target_delegated_validator = get_delegated_validator(state, redelegate.target_pubkey)
        if not target_delegated_validator:
          break
       
        # we check if the source is valid   
        source_delegated_validator = get_delegated_validator(state, redelegate.source_pubkey)
        if not source_delegated_validator:
          break
        
        delegator_index = delegators_execution_addresses.index(redelegate.execution_address)
        if not delegator_index:
            break
        
        # check if delegator has a delegation in the source delegated validator    
        if len(source_delegated_validator.delegators_quotas) < delegator_index:
            break  
        if source_delegated_validator.delegators_quotas[delegator_index] == 0:
            break
         
        # we cap the requested amount to avoid a malicious request which can fill up the churn    
        requested_to_redelegate = redelegate.amount  
        if source_delegated_validator.delegated_balances[delegator_index] < requested_to_redelegate:
            requested_to_redelegate = source_delegated_validator.delegated_balances[delegator_index]    
        
        # Calculates the redelegation's exit and withdrawability epochs before balance re-allocation to target validator
        exit_queue_epoch = compute_exit_epoch_and_update_churn(state, redelegate.amount)
        withdrawable_epoch = Epoch(exit_queue_epoch + config.MIN_VALIDATOR_WITHDRAWABILITY_DELAY)
        
        # Appends the redelegation in the undelegation exit queue
        state.undelegations_exit_queue.append(
          UndelegationExit(
            amount=requested_to_redelegate,             
            exit_queue_epoch=exit_queue_epoch, 
            withdrawable_epoch=withdrawable_epoch, 
            execution_address=redelegate.execution_address, 
            validator_pubkey=redelegate.source_pubkey,
            is_redelegation=True,
            redelegate_to_validator_pubkey=redelegate.target_pubkey
          ))
        
    state.pending_redelegations = []
```
#### New `process_undelegations_exit_queue`

```python
def process_undelegations_exit_queue(state: BeaconState) -> None :
    current_epoch = get_current_epoch(state)
    postponed = []
    
    for undelegation_exit in state.undelegations_exit_queue:
        if undelegation_exit.exit_queue_epoch != FAR_FUTURE_EPOCH:
            # the amount is undelegated
            if current_epoch >= undelegation_exit.exit_queue_epoch:
                # time to undelegate
                undelegation_exit.exit_queue_epoch = FAR_FUTURE_EPOCH
                undelegated_amount, total_delegated_at_withdrawal = undelegate_from_validator(undelegation_exit)
                undelegation_exit.amount = undelegated_amount
                undelegation_exit.total_delegated_at_withdrawal = total_delegated_at_withdrawal
               
                # we postpone it, so we can test it for withdrawability next epoch
                postponed.append(undelegation_exit)
                continue
            else:
              # not undelegated, we postpone the check for next epoch
              postponed.append(undelegation_exit)
              continue
                
        else:
            # the amount has been undelegated, we now check for withdrawability
            if current_epoch >= undelegation_exit.withdrawable_epoch:
                # beacon-chain-accounting is called to settle undelegation
                delegator_amount = settle_undelegation(undelegation_exit)
            
                if undelegation_exit.is_redelegation:
                    # Appends the redelegation in the delegations activation queue
                    state.pending_delegations.append(PendingDelegateRequest(
                      validator_pubkey=undelegation_exit.redelegate_to_validator_pubkey,
                      execution_address=undelegation_exit.execution_address,
                      amount=delegator_amount,
                      slot = state.slot
                    )) 
            
            else:
                # we can not withdraw, we postpone
                postponed.append(undelegation_exit)
              
    state.undelegations_exit_queue = postponed
```

#### New `process_pending_withdrawals_from_delegators`
```python
def process_pending_withdrawals_from_delegators(state: BeaconState) -> None:
  withdrawals_to_postpone = []
  
  delegators_execution_addresses = [d.execution_address for d in state.delegators]
  
  for withdraw_from_delegator in state.pending_withdrawals_from_delegators:
    delegator_index = delegators_execution_addresses.index(withdraw_from_delegator.execution_address)
    delegator = state.delegators[delegator_index]
    
    withdraw_amount = withdraw_from_delegator.amount
    
    if is_withdrawable_from_delegator(state, delegator):
       decrease_delegator_balance(state, delegator_index, withdraw_amount)
    else:
        withdrawals_to_postpone.append(withdraw_from_delegator)

    state.pending_withdrawals_from_delegators = withdrawals_to_postpone

```
#### Modified process_rewards_and_penalties

*Note*: The function `process_rewards_and_penalties` is modified to support delegation logic.

```python
def process_rewards_and_penalties(state: BeaconState) -> None:
    # No rewards are applied at the end of `GENESIS_EPOCH` because rewards are for work done in the previous epoch
    if get_current_epoch(state) == GENESIS_EPOCH:
        return

    flag_deltas = [get_flag_index_deltas(state, flag_index) for flag_index in range(len(PARTICIPATION_FLAG_WEIGHTS))]
    deltas = flag_deltas + [get_inactivity_penalty_deltas(state)]
    for (rewards, penalties) in deltas:    
        for index in range(len(state.validators)):
            validator = state.validators[index]
            if validator.is_operator:
              delegated_validator = get_delegated_validator(state, validator.pubkey)
              validator_quota = delegated_validator.delegated_validator_quota
              # Applies proportional rewards and penalties 
              apply_delegations_rewards(rewards[index] - rewards[index] * validator_quota, delegated_validator)
              apply_delegations_penalties(penalties[index] - penalties[index] * validator_quota, delegated_validator)
              
              increase_balance(state, ValidatorIndex(index), rewards[index] * validator_quota)
              decrease_balance(state, ValidatorIndex(index), penalties[index] * validator_quota)
            else:
              increase_balance(state, ValidatorIndex(index), rewards[index])
              decrease_balance(state, ValidatorIndex(index), penalties[index])
              
```

#### Modified `process_slashings`

*Note*: The function `process_slashings` is modified to support delegation logic.

```python
def process_slashings(state: BeaconState) -> None:
    epoch = get_current_epoch(state)
    total_balance = get_total_active_balance(state)
    adjusted_total_slashing_balance = min(
        sum(state.slashings) * PROPORTIONAL_SLASHING_MULTIPLIER_BELLATRIX,
        total_balance
    )
    increment = EFFECTIVE_BALANCE_INCREMENT  # Factored out from total balance to avoid uint64 overflow
    penalty_per_effective_balance_increment = adjusted_total_slashing_balance // (total_balance // increment)
    for index, validator in enumerate(state.validators):
        if validator.slashed and epoch + EPOCHS_PER_SLASHINGS_VECTOR // 2 == validator.withdrawable_epoch:
            effective_balance_increments = validator.effective_balance // increment
            penalty = penalty_per_effective_balance_increment * effective_balance_increments
            
            # [New in EIPXXXX_eODS]
            if validator.is_operator: 
                # slash the exit queue
                slashed_in_queue = slash_exit_queue(state, validator.pubkey, penalty)
                
                rest_to_slash = penalty - slashed_in_queue
                
                delegated_validator = get_delegated_validator(state, validator.pubkey)
              
                validator_penalty = delegated_validator.delegated_validator_quota * rest_to_slash
                delegators_penalty =  rest_to_slash - validator_slash

                # slash the validator
                decrease_balance(state, ValidatorIndex(index), validator_penalty)
                
                # slash the delegations
                apply_delegations_slashing(delegated_validator, delegators_penalty)
            else:
                decrease_balance(state, ValidatorIndex(index), penalty)
```

#### New `slash_exit_queue`

```python
def slash_exit_queue(state: BeaconState, validator_pubkey: BLSPubkey, penalty: Gwei) -> Gwei:
    current_epoch = get_current_epoch(state)
    list_to_slash = [item for item in state.exit_queue if item.validator_pubkey == validator_pubkey and item.exit_queue_epoch < current_epoch]
    total_slashed_in_queue = 0
    
    for index in range(len(list_to_slash)):
      exit_item = state.list_to_slash[index]
      
      delegated_quota = exit_item.amount / exit_item.total_delegated_at_withdrawal
      to_slash = delegated_quota * penalty
          
      total_slashed_in_queue += to_slash
      
      state.exit_queue[index].undelegated_amount -= to_slash
    
    return total_slashed_in_queue
```

#### Modified `process_effective_balance_updates`

*Note*: The function `process_effective_balance_updates` is modified to cumulate a validator's delegated balance into
it's effective balance calculation.

```python
def process_effective_balance_updates(state: BeaconState) -> None:
    # Update effective balances with hysteresis
    for index, validator in enumerate(state.validators):
        validator = state.validators[index]
        if validator.is_operator:
          balance = state.balances[index] + get_delegated_validator(state, validator.pubkey).total_delegated_balance  # [Modified in EIPXXXX_eODS]
        else:
          balance = state.balances[index]       
        HYSTERESIS_INCREMENT = uint64(EFFECTIVE_BALANCE_INCREMENT // HYSTERESIS_QUOTIENT)
        DOWNWARD_THRESHOLD = HYSTERESIS_INCREMENT * HYSTERESIS_DOWNWARD_MULTIPLIER
        UPWARD_THRESHOLD = HYSTERESIS_INCREMENT * HYSTERESIS_UPWARD_MULTIPLIER
        max_effective_balance = get_max_effective_balance(validator)
        if (
            balance + DOWNWARD_THRESHOLD < validator.effective_balance
            or validator.effective_balance + UPWARD_THRESHOLD < balance
        ):
            validator.effective_balance = min(balance - balance % EFFECTIVE_BALANCE_INCREMENT, max_effective_balance)
```

#### New `is_validator_delegable`

```python
def is_validator_delegable(validator: Validator) -> boolean:

    if not validator:
        return False
    if validator.is_operator:F
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
    process_pending_redelegations(state)  # [New in EIPXXXX_eODS]
    process_undelegations_exit_queue(state)  # [New in EIPXXXX_eODS]
    #process_undel(state)  # [New in EIPXXXX_eODS]
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