# EIP-XXX_eODS -- Beacon Chain Accounting

## Table of contents

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Introduction](#introduction)
- [Delegation Lifecycle Functions](#delegation-lifecycle-functions)
    - [New `delegate_to_validator`](#new-delegate_to_validator)
    - [New `undelegate_from_validator`](#new-undelegate_from_validator)
    - [New `settle_undelegation`](#new-settle_undelegation)
- [Accounting helper functions](#accounting-helper-functions)
    - [New `recalculate_delegators_quotas`](#new-recalculate_delegators_quotas)
    - [New `apply_delegations_rewards`](#new-apply_delegations_rewards)
    - [New `apply_delegations_penalties`](#new-apply_delegations_penalties)
    - [New `apply_delegations_slashing`](#new-apply_delegations_slashing)
    - [Beacon state mutators](#beacon-state-mutators)
        - [New `decrease_delegator_balance`](#new-decrease_delegator_balance)
        - [New `increase_delegator_balance`](#new-increase_delegator_balance)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Introduction

*Note:* This specification is built upon [Electra](../../electra/beacon_chain.md) and is under active development.  
This specification defines the accounting logic for eODS (Enshrined Operator-Delegator Separation), responsible for
keeping the delegation-specific balance sheets.

## Delegation Lifecycle Functions

### New `delegate_to_validator`

```python
def delegate_to_validator(state: BeaconState, delegator_index: DelegatorIndex, validator_pubkey: BLSPubkey,
                          delegated_amount: Gwei) -> None:
    # here we decrement the delegators available balance
    decrease_delegator_balance(state, delegator_index, delegated_amount)

    delegated_validator = get_delegated_validator(state, validator_pubkey)

    num_delegated_balances = len(delegated_validator.delegated_balances)

    # ensure we have enough indexes inside the delegated validator to keep them parallel with delegator_index 
    if (delegator_index > num_delegated_balances):
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

### New `undelegate_from_validator`

```python
def undelegate_from_validator(state: BeaconState, undelegation_exit: UndelegationExit) -> (Gwei, Gwei):
    delegated_validator = get_delegated_validator(state, undelegation_exit.validator_pubkey)
    validators = [d.pubkey for d in state.validators]
    validator_index = ValidatorIndex(validators.index(undelegation_exit.validator_pubkey))
    delegators_execution_addresses = [d.execution_address for d in state.delegators]
    delegator_index = DelegatorIndex(delegators_execution_addresses.index(undelegation_exit.execution_address))

    requested_to_undelegate = undelegation_exit.amount

    max_undelegable = delegated_validator.delegated_balances[delegator_index]

    amount_to_undelegate = min(requested_to_undelegate, max_undelegable)

    total_amount_at_exit = delegated_validator.total_delegated_balance + state.balances[validator_index]
    delegated_validator.delegated_balances[delegator_index] -= amount_to_undelegate
    delegated_validator.total_delegated_balance -= amount_to_undelegate

    recalculate_delegators_quotas(state, delegated_validator)

    return (amount_to_undelegate, total_amount_at_exit)
```

### New `slash_exit_queue`

```python
def slash_exit_queue(state: BeaconState, validator_pubkey: BLSPubkey, penalty: Gwei) -> Gwei:
    current_epoch = get_current_epoch(state)
    list_to_slash = [item for item in state.exit_queue if
                     item.validator_pubkey == validator_pubkey and item.exit_queue_epoch < current_epoch]
    total_slashed_in_queue = 0

    for index in range(len(list_to_slash)):
        exit_item = state.list_to_slash[index]

        delegated_quota = exit_item.amount / exit_item.total_amount_at_exit
        to_slash = delegated_quota * penalty

        total_slashed_in_queue += to_slash

        state.exit_queue[index].undelegated_amount -= to_slash

    return total_slashed_in_queue
```

### New `reward_exit_queue`

```python
def reward_exit_queue(state: BeaconState, validator_pubkey: BLSPubkey, reward: Gwei) -> Gwei:
    current_epoch = get_current_epoch(state)
    list_to_reward = [item for item in state.exit_queue if
                      item.validator_pubkey == validator_pubkey and item.exit_queue_epoch > current_epoch]
    total_rewarded_in_queue = 0

    for index in range(len(list_to_reward)):
        exit_item = state.list_to_reward[index]

        delegated_quota = exit_item.amount / exit_item.total_amount_at_exit
        to_reward = delegated_quota * reward

        total_rewarded_in_queue += to_reward

        state.exit_queue[index].undelegated_amount += to_reward

    return total_rewarded_in_queue
```

### New `penalize_exit_queue`

```python
def penalize_exit_queue(state: BeaconState, validator_pubkey: BLSPubkey, penalty: Gwei) -> Gwei:
    current_epoch = get_current_epoch(state)
    list_to_penalize = [item for item in state.exit_queue if
                        item.validator_pubkey == validator_pubkey and item.exit_queue_epoch > current_epoch]
    total_penalized_in_queue = 0

    for index in range(len(list_to_penalize)):
        exit_item = state.list_to_penalize[index]

        delegated_quota = exit_item.amount / exit_item.total_amount_at_exit
        to_penalize = delegated_quota * penalty

        total_penalized_in_queue += to_penalize

        state.exit_queue[index].undelegated_amount -= to_penalize

    return total_penalized_in_queue
```

### New `slash_delegated_validator_and_exit_queue`

```python
def slash_delegated_validator_and_exit_queue(state: BeaconState, validator_index: ValidatorIndex,
                                             validator_pubkey: BLSPubkey, penalty: Gwei) -> None:
    # slash the exit queue
    slashed_in_queue = slash_exit_queue(state, validator_pubkey, penalty)

    rest_to_slash = penalty - slashed_in_queue

    delegated_validator = get_delegated_validator(state, validator_pubkey)

    validator_penalty = delegated_validator.delegated_validator_quota * rest_to_slash
    delegators_penalty = rest_to_slash - validator_penalty

    # slash the operator
    decrease_balance(state, ValidatorIndex(validator_index), validator_penalty)

    # slash the delegations
    apply_delegations_slashing(delegated_validator, delegators_penalty)

```

### New `reward_delegated_validator_and_exit_queue`

```python
def reward_delegated_validator_and_exit_queue(state: BeaconState, validator_index: ValidatorIndex,
                                              validator_pubkey: BLSPubkey, reward: Gwei) -> None:
    # reward the exit queue
    rewarded_in_queue = reward_exit_queue(state, validator_pubkey, reward)

    rest_to_reward = reward - rewarded_in_queue

    delegated_validator = get_delegated_validator(state, validator_pubkey)

    validator_reward = delegated_validator.delegated_validator_quota * rest_to_reward
    delegators_reward = rest_to_reward - validator_reward

    # reward the operator
    increase_balance(state, ValidatorIndex(validator_index), validator_reward)

    # reward the delegations
    apply_delegations_rewards(delegated_validator, delegators_reward)

```

### New `penalize_delegated_validator_and_exit_queue`

```python
def penalize_delegated_validator_and_exit_queue(state: BeaconState, validator_index: ValidatorIndex,
                                                validator_pubkey: BLSPubkey, penalty: Gwei) -> None:
    # reward the exit queue
    penalized_in_queue = penalize_exit_queue(state, validator_pubkey, penalty)

    rest_to_penalize = penalty - penalized_in_queue

    delegated_validator = get_delegated_validator(state, validator_pubkey)

    validator_penalty = delegated_validator.delegated_validator_quota * rest_to_penalize
    delegators_penalty = rest_to_penalize - validator_penalty

    # penalize the operator
    decrease_balance(state, ValidatorIndex(validator_index), validator_penalty)

    # penalize the delegations
    apply_delegations_penalties(delegated_validator, delegators_penalty)

```

### New `settle_undelegation`

```python
def settle_undelegation(state: BeaconState, undelegation_exit: UndelegationExit) -> Gwei:
    delegated_validator = get_delegated_validator(state, undelegation_exit.validator_pubkey)

    delegators_execution_addresses = [d.execution_address for d in state.delegators]
    delegator_index = DelegatorIndex(delegators_execution_addresses.index(undelegation_exit.execution_address))

    validator_pubkeys = [v.pubkey for v in state.validators]
    validator_index = ValidatorIndex(validator_pubkeys.index(undelegation_exit.validator_pubkey))

    validator_fee = undelegation_exit.amount * delegated_validator.fee_quotient
    delegator_amount = undelegation_exit.amount - validator_fee

    if not undelegation_exit.is_redelegation:
        increase_delegator_balance(state, delegator_index, delegator_amount)

    increase_balance(state, ValidatorIndex(validator_index), validator_fee)

    return delegator_amount
 ```

## Accounting helper functions

### New `recalculate_delegators_quotas`

```python
def recalculate_delegators_quotas(state: BeaconState, delegated_validator: DelegatedValidator) -> None:
    validator_pubkeys = [v.pubkey for v in state.validators]
    validator_index = ValidatorIndex(validator_pubkeys.index(delegated_validator.validator.pubkey))

    if delegated_validator.total_delegated_balance == 0:
        delegated_validator.delegated_validator_quota = 1
    else:
        delegated_validator.delegated_validator_quota = (state.balances[validator_index] / (
                    delegated_validator.total_delegated_balance + state.balances[validator_index]))
        for index in range(len(delegated_validator.delegators_quotas)):
            delegated_validator.delegators_quotas[index] = delegated_validator.delegated_balances[
                                                               index] / delegated_validator.total_delegated_balance * (
                                                                       1 - delegated_validator.delegated_validator_quota)
``` 

### New `apply_delegations_rewards`

```python
def apply_delegations_rewards(amount: Gwei, delegated_validator: DelegatedValidator) -> None:
    delegated_validator.total_delegated_balance += amount

    for index in range(len(delegated_validator.delegators_quotas)):
        delegated_validator.delegated_balances[index] += amount * delegated_validator.delegators_quotas[index]
```

### New `apply_delegations_penalties`

```python
def apply_delegations_penalties(amount: Gwei, delegated_validator: DelegatedValidator) -> None:
    delegated_validator.total_delegated_balance -= amount

    for index in range(len(delegated_validator.delegators_quotas)):
        delegated_validator.delegated_balances[index] -= amount * delegated_validator.delegators_quotas[index]
```

### New `apply_delegations_slashing`

```python
def apply_delegations_slashing(delegated_validator: DelegatedValidator, penalty: Gwei, ) -> None:
    delegated_validator.total_delegated_balance -= penalty

    # slash the delegated balances
    for index in range(len(delegated_validator.delegated_balances)):
        delegated_validator.delegated_balances[index] -= penalty * delegated_validator.delegators_quotas[index]
  ```

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