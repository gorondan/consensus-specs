from build.lib.eth2spec.eipxxxx_eods.mainnet import MIN_DEPOSIT_TO_DELEGATE_AMOUNT
from build.lib.eth2spec.test.helpers.keys import pubkeys, privkeys
from eth2spec.test.context import spec_state_test, expect_assertion_error, \
    with_eipxxxx_eods_and_later
from eth2spec.test.helpers.delegation_deposits import sign_deposit_to_delegate_message, run_add_new_delegator



@with_eipxxxx_eods_and_later
@spec_state_test
def test_deposit_to_delegate_request_creates_delegator_if_needed(spec, state):
    initial_delegators_len = len(state.delegators)

    pubkey = pubkeys[1]
    privkey = privkeys[1]
    amount = spec.MIN_DEPOSIT_TO_DELEGATE_AMOUNT
    withdrawal_credentials = (
            spec.COMPOUNDING_WITHDRAWAL_PREFIX
            + b'\x00' * 11  # specified 0s
            + b'\x59' * 20  # a 20-byte eth1 address
    )

    # this is a mock of EL message
    deposit_to_delegate_message = spec.DepositToDelegateMessage(
        pubkey=pubkey,
        withdrawal_credentials=withdrawal_credentials,
        amount=amount,
    )

    deposit_to_delegate_request = sign_deposit_to_delegate_message(spec, deposit_to_delegate_message, privkey)
    spec.process_deposit_to_delegate_request(state, deposit_to_delegate_request)
    spec.process_pending_deposits_to_delegate(state)

    assert len(state.delegators) == initial_delegators_len + 1

    # sign the deposit_to_delegate_message and get a DepositToDelegateRequest
    # call spec.process_deposit_to_delegate_request give it DepositToDelegateRequest, this will add it to state.pending_deposits_to_delegate

    # call spec.process_pending_deposits_to_delegate(state)

    # assert we should have a bigger len(state.delegators) than initial_delegators_len


@with_eipxxxx_eods_and_later
@spec_state_test
def test_deposit_to_delegate_request_does_top_up_if_needed(spec, state):
    pubkey = pubkeys[1]
    privkey = privkeys[1]
    existing_delegator_amount = spec.MIN_DEPOSIT_TO_DELEGATE_AMOUNT
    run_add_new_delegator(spec, state, pubkey, privkey, existing_delegator_amount)

    pre_topup_number_of_delegators = len(state.delegators)

    topup_amount = spec.MIN_DEPOSIT_TO_DELEGATE_AMOUNT

    withdrawal_credentials = (
            spec.COMPOUNDING_WITHDRAWAL_PREFIX
            + b'\x00' * 11  # specified 0s
            + b'\x59' * 20  # a 20-byte eth1 address
    )
    # this is a mock of a NEW EL message
    deposit_to_delegate_message = spec.DepositToDelegateMessage(
        pubkey=pubkey,
        withdrawal_credentials=withdrawal_credentials,
        amount=topup_amount,
    )

    deposit_to_delegate_request = sign_deposit_to_delegate_message(spec, deposit_to_delegate_message, privkey)
    spec.process_deposit_to_delegate_request(state, deposit_to_delegate_request)
    spec.process_pending_deposits_to_delegate(state)

    assert len(state.delegators) == pre_topup_number_of_delegators
    assert state.delegators_balances[0] == 2 * spec.MIN_DEPOSIT_TO_DELEGATE_AMOUNT

@with_eipxxxx_eods_and_later
@spec_state_test
def test_deposit_to_delegate_request_increases_topup_delegator_balance(spec, state):
    assert 1 > 1


@with_eipxxxx_eods_and_later
@spec_state_test
def test_deposit_to_delegate_request_increases_new_delegator_balance(spec, state):
    assert 1 > 1


@with_eipxxxx_eods_and_later
@spec_state_test
def test_deposit_to_delegate_request_respects_churn_value(spec, state):
    assert 1 > 1


@with_eipxxxx_eods_and_later
@spec_state_test
def test_deposit_to_delegate_request_rolls_over_to_new_epoch_when_over_churn_value(spec, state):
    assert 1 > 1


@with_eipxxxx_eods_and_later
@spec_state_test
def test_deposit_unable_to_withdraw_before_withdrawable_epoch(spec, state):
    assert 1 > 1


@with_eipxxxx_eods_and_later
@spec_state_test
def test_deposit_can_withdraw_after_withdrawable_epoch(spec, state):
    assert 1 > 1
