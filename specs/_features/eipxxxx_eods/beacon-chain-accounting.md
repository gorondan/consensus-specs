<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [EIP-XXX_eODS -- Beacon Chain Accounting](#eip-xxx_eods----beacon-chain-accounting)
  - [Introduction](#introduction)
  - [Delegation Lifecycle Functions](#delegation-lifecycle-functions)
    - [delegate_to_validator](#delegate_to_validator)
    - [Accounting helper functions](#accounting-helper-functions)
      - [New `recalculate_delegators_quotas`](#new-recalculate_delegators_quotas)
      - [New `apply_delegations_rewards`](#new-apply_delegations_rewards)
      - [New `apply_delegations_penalties`](#new-apply_delegations_penalties)
      - [New `apply_delegations_slashing`](#new-apply_delegations_slashing)
  - [Advanced Delegation Lifecycle](#advanced-delegation-lifecycle)
    - [Beacon state mutators](#beacon-state-mutators)
      - [New `decrease_delegator_balance`](#new-decrease_delegator_balance)
      - [New `increase_delegator_balance`](#new-increase_delegator_balance)
      - [New `undelegate_from_validator`](#new-undelegate_from_validator)
      - [New `settle_undelegation`](#new-settle_undelegation)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

from bla2 import UndelegationExitfrom build.lib.eth2spec.test.helpers.state import get_validator_index_by_pubkeyfrom build.lib.eth2spec.eipxxxx_eods.mainnet import decrease_balancefrom build.lib.eth2spec.fulu.mainnet import BLSPubkeyfrom eth2spec.eipxxxx_eods.mainnet import DelegatorIndex

# EIP-XXX_eODS -- Beacon Chain Accounting

## Introduction

*Note:* This specification is built upon [Electra](../../electra/beacon_chain.md) and is under active development.  
This specification defines the accounting logic for eODS (Enshrined Operator-Delegator Separation), responsible for 
enshrined delegation balances, withdrawal processing, and reward preview computation in the Beacon Chain.

## Delegation Lifecycle Functions

### delegate_to_validator

```python
def delegate_to_validator(state: BeaconState, delegator_index: DelegatorIndex, validator_pubkey: BLSPubkey, delegated_amount: Gwei) -> None:
    # here we decrement the delegators available balance
    decrease_delegator_balance(state, delegator_index, delegated_amount)
    
    delegated_validator = get_delegated_validator(state, validator_pubkey)

    num_delegated_balances = len(delegated_validator.delegated_balances)

    # ensure we have enough indexes inside the delegated validator to keep them parallel with delegator_index 
    if(delegator_index > num_delegated_balances):
        for _ in range(delegator_index - num_delegated_balances):
            delegated_validator.delegated_balances.append(0)
            delegated_validator.delegated_quotas.append(0)
    
    # here we increase the delegated balance from this specific delegator, under this delegated validator, with delegated amount
    delegated_validator.delegated_balances[delegator_index] += delegated_amount
    
    # here we increase the delegated validator's total delegated balance with delegated amount
    delegated_validator.total_delegated_balance += delegated_amount
    
    # here we recalculate delegators' quotas under this delegated validator  
    recalculate_delegators_quotas(state, delegated_validator)
```

### Accounting helper functions

#### New `recalculate_delegators_quotas`
```python
def recalculate_delegators_quotas(state: BeaconState, delegated_validator: DelegatedValidator) -> None:
    validator_index = get_validator_index_by_pubkey(delegated_validator.validator.pubkey)
    
    if delegated_validator.total_delegated_balance == 0:
        delegated_validator.delegated_validator_quota = 1
    else :
        delegated_validator.delegated_validator_quota = (state.balances[validator_index] /  (delegated_validator.total_delegated_balance + state.balances[validator_index]))
        for index in range(len(delegated_validator.delegators_quotas)):
            delegated_validator.delegators_quotas[index] = delegated_validator.delegated_balances[index] / delegated_validator.total_delegated_balance * (1-delegated_validator.delegated_validator_quota)
``` 
#### New `apply_delegations_rewards`

```python
def apply_delegations_rewards(amount: Gwei, delegated_validator: DelegatedValidator)-> None:
    delegated_validator.total_delegated_balance += amount
    
    for index in range(len(delegated_validator.delegators_quotas)):
        delegated_validator.delegated_balances[index] += amount * delegated_validator.delegators_quotas[index]
```

#### New `apply_delegations_penalties`

```python
def apply_delegations_penalties(amount: Gwei, delegated_validator: DelegatedValidator)-> None:
    delegated_validator.total_delegated_balance -= amount
    
    for index in range(len(delegated_validator.delegators_quotas)):
        delegated_validator.delegated_balances[index] -= amount * delegated_validator.delegators_quotas[index]
```

#### New `apply_delegations_slashing`

```python
def apply_delegations_slashing(delegated_validator: DelegatedValidator, penalty: Gwei, )-> None:
    delegated_validator.total_delegated_balance -= penalty
    
    # slash the delegated balances
    for index in range(len(delegated_validator.delegated_balances)):
        delegated_validator.delegated_balances[index] -= penalty * delegated_validator.delegators_quotas[index]
  ```

## Advanced Delegation Lifecycle

### Beacon state mutators

#### New `decrease_delegator_balance`

```python
def decrease_delegator_balance(state: BeaconState, delegator_index: DelegatorIndex, delta: Gwei) -> None:
    """
    Decrease the delegator balance at index ``delegator_index`` by ``delta``.
    """
    state.delegators_balances[delegator_index] -= delta
```
#### New `increase_delegator_balance`

```python
def increase_delegator_balance(state: BeaconState, delegator_index: DelegatorIndex, delta: Gwei) -> None:
    """
    Increase the delegator balance at index ``delegator_index`` by ``delta``.
    """
    state.delegators_balances[delegator_index] += delta
```

#### New `undelegate_from_validator`

```python
def undelegate_from_validator(undelegation_exit: UndelegationExit) -> (Gwei, Gwei):
    delegated_validator = get_delegated_validator(state, undelegation_exit.validator_pubkey)
    
    delegators_execution_addresses = [d.execution_address for d in state.delegators]
    delegator_index = DelegatorIndex(delegators_execution_addresses.index(undelegation_exit.execution_address))
    
    requested_to_undelegate = undelegation_exit.amount

    max_undelegable = delegated_validator.delegated_balances[delegator_index]
    
    amount_to_undelegate = min(requested_to_undelegate, max_undelegable)
    
    total_delegated_at_withdrawal = delegated_validator.total_delegated_balance
    delegated_validator.delegated_balances[delegator_index] -= amount_to_undelegate
    delegated_validator.total_delegated_balance -= amount_to_undelegate
    
    recalculate_delegators_quotas(state, delegated_validator)
    
    return (amount_to_undelegate, total_delegated_at_withdrawal)
```

#### New `settle_undelegation`

```python
def settle_undelegation(undelegation_exit: UndelegationExit) -> Gwei:
    delegated_validator = get_delegated_validator(state, undelegation_exit.validator_pubkey)
    
    delegators_execution_addresses = [d.execution_address for d in state.delegators]
    delegator_index = DelegatorIndex(delegators_execution_addresses.index(undelegation_exit.execution_address))
    
    validator_pubkeys = [v.pubkey for v in state.validators]
    validator_index = ValidatorIndex(validator_pubkeys.index(undelegation_exit.validator_pubkey))
    
    validator_fee = undelegation_exit.amount * delegated_validator.fee_quotient
    delegator_amount =  undelegation_exit.amount - validator_fee
    
    if not undelegation_exit.is_redelegation:  
        increase_delegator_balance(state, delegator_index, delegator_amount)
    
    increase_balance(state, ValidatorIndex(validator_index), validator_fee)
    
    return delegator_amount
 ```